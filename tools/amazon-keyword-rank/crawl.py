"""Amazon organic-rank crawler.
Importable: crawl_pair(asin, kw, log_path) -> final record dict (also appended to log_path).
CLI (unchanged): python3 crawl.py [ASIN ...]  -> appends to crawl_log.jsonl, skips pairs already final there,
exits 2 on block."""
import json,time,random,datetime,os,sys,re
from bs4 import BeautifulSoup
from loc import mk,H
from kws import KW
import variants
LOG="crawl_log.jsonl"
IMPS=["chrome","chrome131","chrome124","chrome120","safari17_0"]
imp_i=0
s=None
def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")
def new_session(rotate=False):
    global s,imp_i
    if rotate: imp_i=(imp_i+1)%len(IMPS)
    s,_=mk(IMPS[imp_i])
    return s
US_ZIP="10001"   # must match zipCode set in loc.py mk()
LOC_RETRIES=3    # extra session rebuilds (each re-runs loc.py location setup) when a page lacks the US location
def loc_ok(loc): return bool(loc) and US_ZIP in loc
def page_loc(t):
    l=BeautifulSoup(t,"lxml").select_one("#glow-ingress-line2")
    return l.get_text(strip=True) if l else None
def fetch_us(url):
    """fetch() + US-location guard. Returns (html, loc, loc_retries) or (None, loc, n) on block / location failure;
    loc is the last detected location (None if blocked before any page)."""
    t=fetch(url); n=0
    if t is None: return None,None,0
    loc=page_loc(t)
    while not loc_ok(loc) and n<LOC_RETRIES:
        n+=1; print(f"LOC GUARD: page shows {loc!r}, expected zip {US_ZIP}; new session + refetch ({n}/{LOC_RETRIES})",flush=True)
        time.sleep(random.uniform(5,15))
        try: new_session(rotate=True)
        except Exception as e: print("SESSION ERR",e,flush=True); continue
        t=fetch(url)
        if t is None: return None,loc,n
        loc=page_loc(t)
    return t,loc,n
def is_sp(it):
    cls=' '.join(it.get('class',[]))
    if 'AdHolder' in cls: return True
    if it.select_one(".puis-sponsored-label-text, .s-sponsored-label-text, .puis-sponsored-label-info-icon, [data-component-type='sp-sponsored-result']"): return True
    for sp in it.find_all("span"):
        if sp.get_text(strip=True)=="Sponsored": return True
    return False
def fetch(url,attempts=5):
    global s
    if s is None: new_session()
    for att in range(attempts):
        try:
            x=s.get(url,headers=H,timeout=30)
            t=x.text
            if x.status_code==200 and 'captcha' not in t.lower()[:20000] and 's-search-result' in t or (x.status_code==200 and 'No results for' in t):
                return t
            print("BLOCK?",x.status_code,len(t),flush=True)
        except Exception as e: print("ERR",e,flush=True)
        time.sleep(30*(att+1)+random.uniform(0,10))
        try: new_session(rotate=True)
        except Exception as e: print("SESSION ERR",e,flush=True)
    return None
def done_pairs(log_path):
    done=set()
    if os.path.exists(log_path):
        for l in open(log_path):
            try: d=json.loads(l)
            except Exception: continue
            if d.get("final") and d.get("status")!="blocked": done.add((d["asin"],d["keyword"]))
    return done
def crawl_pair(asin,kw,log_path=LOG,max_pages=10):
    """Scan up to max_pages search pages for kw. Matches the whole variant family of asin (variants.json):
    status/page/pos/overall = best organic position of ANY family ASIN, matched_asin = which variant showed;
    exact_status/exact_page/exact_pos/exact_overall = the given child ASIN itself (secondary).
    Stops when the exact ASIN is found (family best is then known too) or pages run out, i.e. same page budget
    as the old exact-only crawler. Appends page + final records."""
    F=variants.family(asin)
    rank=0; res=None; pages=0; fb=None; ex=None; loc_fail=False
    for p in range(1,max_pages+1):
        url="https://www.amazon.com/s?k="+kw.replace(" ","+")+("&page=%d"%p if p>1 else "")
        t,loc,lr=fetch_us(url)
        if t is None: res={"status":"blocked"}; break
        if not loc_ok(loc):   # never log/score a non-US page; keyword stays retryable
            res={"status":"blocked","error":"US location not set","loc":loc}; loc_fail=True; break
        b=BeautifulSoup(t,"lxml")
        items=b.select("div[data-component-type='s-search-result']")
        org=[]
        for it in items:
            a=it.get("data-asin")
            if not a or is_sp(it): continue
            if a in org: continue
            org.append(a)
        pages=p
        rec={"asin":asin,"keyword":kw,"page":p,"loc":loc,"loc_ok":True,"loc_retries":lr,"n_items":len(items),"organic":org,"ts":_utcnow()}
        with open(log_path,"a") as f: f.write(json.dumps(rec)+"\n")
        for i,x in enumerate(org):
            if fb is None and x in F: fb={"page":p,"pos":i+1,"overall":rank+i+1,"matched_asin":x}
            if ex is None and x==asin: ex={"page":p,"pos":i+1,"overall":rank+i+1}
        rank+=len(org)
        if ex: res={"status":"found"}; break
        has_next=b.select_one("a.s-pagination-next") is not None
        time.sleep(random.uniform(2,5))
        if not has_next or not org: res={"status":"notfound","end_page":p}; break
    if res is None: res={"status":"notfound","end_page":pages}
    blocked=res["status"]=="blocked"
    if loc_fail: out=dict(res)   # location guard failed: whole keyword marked blocked so resume re-crawls it
    elif fb:   # family hit is valid even if a later page got blocked (pages are scanned in order)
        out={"status":"found","page":fb["page"],"pos":fb["pos"],"overall":fb["overall"],"matched_asin":fb["matched_asin"],
             "matched_label":variants.label(fb["matched_asin"])}
        if "end_page" in res: out["end_page"]=res["end_page"]
    else: out=dict(res)
    out["exact_status"]="found" if ex else ("incomplete" if blocked else "notfound")
    if ex: out.update(exact_page=ex["page"],exact_pos=ex["pos"],exact_overall=ex["overall"])
    out.update(match_mode="family",family_size=len(F))
    fin={"final":True,"asin":asin,"keyword":kw,**out,"pages":pages,"ts":_utcnow()}
    with open(log_path,"a") as f: f.write(json.dumps(fin)+"\n")
    print(json.dumps(fin,ensure_ascii=False),flush=True)
    return fin
def main(targets):
    done=done_pairs(LOG)
    new_session()
    for asin in targets:
        for kw in KW[asin]:
            if (asin,kw) in done: continue
            fin=crawl_pair(asin,kw,LOG)
            if fin["status"]=="blocked": print("stopping due to block"); sys.exit(2)
            time.sleep(random.uniform(2,5))
if __name__=="__main__":
    main(sys.argv[1:] or list(KW))
