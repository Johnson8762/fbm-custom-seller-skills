import json,pandas as pd
from kws import KW
def load_titles():
    import os
    if os.path.exists("titles.json"): return json.load(open("titles.json"))
    from bs4 import BeautifulSoup
    t={a:BeautifulSoup(open(f"dpus_{a}.html").read(),"lxml").select_one("#productTitle").get_text(strip=True) for a in KW}
    json.dump(t,open("titles.json","w"),ensure_ascii=False,indent=1); return t
def load_log(log_path,family=True):
    fin={}; pages={}
    for l in open(log_path):
        try: d=json.loads(l)
        except Exception: continue
        k=(d["asin"],d["keyword"])
        if d.get("final"):
            if d.get("status")=="blocked" and k in fin and fin[k].get("status")!="blocked": continue
            fin[k]=d
        else: pages.setdefault(k,[]).append(d)
    if family:  # upgrade old exact-only final records to variant-family matching from their logged organic lists
        import variants
        for k,d in fin.items(): variants.rescore_final(d,pages.get(k,[]))
    return fin,pages
def build(log_path="crawl_log.jsonl",csv_out="amazon_asin_keywords.csv",xlsx_out="amazon_asin_keywords.xlsx",verbose=False):
    titles=load_titles()
    fin,pages=load_log(log_path)
    rows=[]
    for (a,k),d in fin.items():
        f=d["status"]=="found"
        rows.append(dict(asin=a,product_title=titles.get(a,""),keyword=k,found="Y" if f else ("N" if d["status"]=="notfound" else "BLOCKED"),
          page=d.get("page") if f else None,position_on_page=d.get("pos") if f else None,organic_rank_overall=d.get("overall") if f else None,
          pages_scanned=d.get("pages",len(pages.get((a,k),[]))),checked_at_utc=d["ts"],
          matched_asin=d.get("matched_asin") if f else None,matched_variant=d.get("matched_label") if f else None,
          exact_asin_found={"found":"Y","notfound":"N"}.get(d.get("exact_status",d["status"]),"?"),exact_asin_rank=d.get("exact_overall") if d.get("exact_status") else (d.get("overall") if f else None)))
    df=pd.DataFrame(rows,columns=["asin","product_title","keyword","found","page","position_on_page","organic_rank_overall","pages_scanned","checked_at_utc",
                                  "matched_asin","matched_variant","exact_asin_found","exact_asin_rank"])
    df["_s"]=df.found.map({"Y":0,"N":1,"BLOCKED":2})
    df=df.sort_values(["asin","_s","organic_rank_overall"]).drop(columns="_s")
    df.to_csv(csv_out,index=False)
    with pd.ExcelWriter(xlsx_out) as w:
        for a in KW:
            df[df.asin==a].to_excel(w,sheet_name=a,index=False)
    if verbose:
        for a in KW:
            sub=df[df.asin==a]; print("\n==",a,titles[a]); print("checked",len(sub),"found",(sub.found=="Y").sum())
            print(sub[sub.found=="Y"][["keyword","page","position_on_page","organic_rank_overall"]].to_string(index=False))
    return df,fin,pages
if __name__=="__main__":
    df,fin,pages=build(verbose=True)
    # bonus: target asins seen in other keywords' searches
    seen=[]
    for (a,k),ps in pages.items():
        for p in ps:
            for t in KW:
                if t!=a and t in p["organic"]: seen.append((t,k,p["page"],p["organic"].index(t)+1))
    print("cross-hits",seen)
