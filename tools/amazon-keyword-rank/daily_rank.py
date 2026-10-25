#!/usr/bin/env python3
"""Daily Amazon US organic keyword-rank runner -> Feishu Bitable + local reports.

Usage (from this directory):
  nohup python3 daily_rank.py > daily_$(TZ=Asia/Shanghai date +%Y%m%d).out 2>&1 &
Options:
  --date YYYYMMDD     Beijing date to run for (default: today in Asia/Shanghai)
  --log PATH          crawl log to use (default logs/crawl_YYYYMMDD.jsonl)
  --asins A B ...     only crawl these ASINs        --keywords K ...  only crawl these keywords
  --no-crawl          skip crawling, just publish what is in the log
  --no-feishu         skip Feishu writes            --no-report  skip csv/xlsx regeneration
  --setup-only        only ensure Feishu tables/fields exist (and backfill 查询日期)
Resumable: re-running for the same date skips (asin,keyword) pairs that already have a non-blocked final record
in the date's log; Feishu writes for that date are replaced (not duplicated).
Summary JSON: ./daily_summary_YYYYMMDD.json
"""
import os,sys,json,time,random,argparse,datetime as D,traceback
from zoneinfo import ZoneInfo
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from kws import KW
import report
from fsbt import Client,FeishuError
TZ=ZoneInfo("Asia/Shanghai")
APP=os.environ.get("FEISHU_RANK_BITABLE_TOKEN","<YOUR_BITABLE_APP_TOKEN>")
T_HIST_ID=os.environ.get("FEISHU_RANK_HIST_TABLE_ID","")  # optional: existing history table id
T_HIST="排名历史"; T_CMP="每日对比"; T_SUM="每日汇总"
ASIN_OPTS=[{"name":a,"color":i} for i,a in enumerate(KW)]
STATUS=["新进","掉出","上升","下降","持平","未进前10页","基准","查询失败"]
NUM={"formatter":"0"}; DATEP={"date_formatter":"yyyy/MM/dd","auto_fill":False}
CMP_FIELDS=[("关键词",1,None),("ASIN",3,{"options":ASIN_OPTS}),("日期",5,DATEP),("今日页码",2,NUM),("今日页内位置",2,NUM),
  ("今日自然总排名",2,NUM),("昨日自然总排名",2,NUM),("排名变化",2,NUM),
  ("状态",3,{"options":[{"name":s,"color":i} for i,s in enumerate(STATUS)]}),("对比日期",5,DATEP),
  ("展示变体",1,None),("本ASIN今日排名",2,NUM)]
SUM_FIELDS=[("记录",1,None),("日期",5,DATEP),("ASIN",3,{"options":ASIN_OPTS}),("产品标题",1,None),("检查词数",2,NUM),
  ("进前10页词数",2,NUM),("首页词数",2,NUM),("平均自然排名",2,{"formatter":"0.0"}),("较昨日进前10页词数变化",2,NUM),
  ("较昨日首页词数变化",2,NUM),("查询失败词数",2,NUM),("分析",1,None),("本ASIN进前10页词数",2,NUM),("本ASIN首页词数",2,NUM)]
# variant-family matching (2026-10-25): 页码/页内位置/自然总排名 = best organic position of ANY variant of the listing;
# 展示变体 = which child ASIN showed; 本ASIN自然排名 = the tracked child ASIN itself. Fields are only ever ADDED.
HIST_EXTRA=[("展示变体",1,None),("本ASIN自然排名",2,NUM)]
def log(*a): print(time.strftime("%H:%M:%S"),*a,flush=True)
def day_ms(d): return int(D.datetime(d.year,d.month,d.day,tzinfo=TZ).timestamp()*1000)
def ms_day(ms): return D.datetime.fromtimestamp(ms/1000,TZ).date()
def utc_ms(ts): return int(D.datetime.fromisoformat(ts).replace(tzinfo=D.timezone.utc).timestamp()*1000)
def txt(v):
    if v is None: return None
    if isinstance(v,list): return "".join(x.get("text","") if isinstance(x,dict) else str(x) for x in v)
    if isinstance(v,dict): return v.get("text") or v.get("value")
    return str(v)
def num(v):
    if v in (None,""): return None
    if isinstance(v,list): v=txt(v)
    try: return float(v)
    except Exception: return None

# ---------------- Feishu schema
def ensure_schema(c):
    tabs={t["name"]:t["table_id"] for t in c.tables()}
    ids={}
    if T_HIST not in tabs:
        if T_HIST_ID in tabs.values():
            c.call("PATCH",f"/bitable/v1/apps/{APP}/tables/{T_HIST_ID}",{"name":T_HIST}); log("renamed",T_HIST_ID,"->",T_HIST)
            ids[T_HIST]=T_HIST_ID
        else: raise FeishuError("history table %s not found"%T_HIST_ID)
    else: ids[T_HIST]=tabs[T_HIST]
    hf={f["field_name"] for f in c.fields(ids[T_HIST])}
    if "查询日期" not in hf:
        c.call("POST",f"/bitable/v1/apps/{APP}/tables/{ids[T_HIST]}/fields",{"field_name":"查询日期","type":5,"property":DATEP}); log("added 查询日期")
    for n,t,p in HIST_EXTRA:
        if n not in hf:
            c.call("POST",f"/bitable/v1/apps/{APP}/tables/{ids[T_HIST]}/fields",{"field_name":n,"type":t,**({"property":p} if p else {})}); log("added field",T_HIST,n)
    for name,flds in ((T_CMP,CMP_FIELDS),(T_SUM,SUM_FIELDS)):
        if name in tabs: ids[name]=tabs[name]
        else:
            d=c.call("POST",f"/bitable/v1/apps/{APP}/tables",{"table":{"name":name,"default_view_name":"表格",
                "fields":[{"field_name":n,"type":t,**({"property":p} if p else {})} for n,t,p in flds]}})
            ids[name]=d["table_id"]; log("created table",name,ids[name])
        have={f["field_name"] for f in c.fields(ids[name])}
        for n,t,p in flds:
            if n not in have:
                c.call("POST",f"/bitable/v1/apps/{APP}/tables/{ids[name]}/fields",{"field_name":n,"type":t,**({"property":p} if p else {})}); log("added field",name,n)
    return ids
def backfill_hist_date(c,tid):
    recs=c.list_records(tid,field_names=["查询时间","查询日期"])
    up=[{"record_id":r["record_id"],"fields":{"查询日期":day_ms(ms_day(r["fields"]["查询时间"]))}}
        for r in recs if r["fields"].get("查询时间") and not r["fields"].get("查询日期")]
    if up: c.batch_update(tid,up)
    return len(up)
def blank_records(c,tid,key):
    return [r["record_id"] for r in c.list_records(tid) if not txt(r["fields"].get(key))]

# ---------------- data
def load_today(log_path):
    if not os.path.exists(log_path): return {},{}
    fin,pages=report.load_log(log_path)
    for k,d in fin.items():
        if "pages" not in d: d["pages"]=len({p["page"] for p in pages.get(k,[])})
    return fin,pages
def prev_from_feishu(c,tid,today):
    """Most recent 查询日期 < today in 排名历史 -> (date, {(asin,kw): {'found','page','pos','overall'}})"""
    recs=c.list_records(tid,field_names=["关键词","ASIN","查询日期","查询时间","是否进前10页","页码","页内位置","自然总排名"])
    by={}
    for r in recs:
        f=r["fields"]; ms=f.get("查询日期") or f.get("查询时间")
        if not ms: continue
        d=ms_day(ms)
        if d>=today: continue
        by.setdefault(d,[]).append(f)
    if not by: return None,{}
    pd_=max(by); out={}
    for f in by[pd_]:
        k=(txt(f.get("ASIN")),txt(f.get("关键词")))
        fd=txt(f.get("是否进前10页"))=="是"
        out[k]={"found":fd,"page":num(f.get("页码")),"pos":num(f.get("页内位置")),"overall":num(f.get("自然总排名"))}
    return pd_,out
def prev_from_local(today,only=None):
    """Latest local crawl day < today (or exactly `only`), family-matched (report.load_log rescores old exact-only logs)."""
    by={}
    files=[os.path.join("logs",x) for x in os.listdir("logs") if x.startswith("crawl_") and x.endswith(".jsonl")]+["crawl_log.jsonl"]
    for fp in files:
        if not os.path.exists(fp): continue
        fin,_=report.load_log(fp)
        for k,d in fin.items():
            if d.get("status")=="blocked": continue
            dd=D.datetime.fromisoformat(d["ts"]).replace(tzinfo=D.timezone.utc).astimezone(TZ).date()
            if fp!="crawl_log.jsonl" and os.path.basename(fp)[6:14].isdigit():
                dd=D.datetime.strptime(os.path.basename(fp)[6:14],"%Y%m%d").date()
            if dd>=today or (only and dd!=only): continue
            by.setdefault(dd,{})[k]={"found":d["status"]=="found","page":d.get("page"),"pos":d.get("pos"),"overall":d.get("overall")}
    if not by: return None,{}
    pd_=max(by); return pd_,by[pd_]

def compare(today_fin,prev):
    rows=[]
    for a in KW:
        for kw in KW[a]:
            t=today_fin.get((a,kw)); p=prev.get((a,kw))
            r={"asin":a,"keyword":kw,"page":None,"pos":None,"overall":None,"prev":None,"change":None,"matched_asin":None,"matched_label":None,"exact_overall":None,"exact_page":None}
            if p and p["found"]: r["prev"]=int(p["overall"]) if p["overall"] is not None else None
            if t is None or t["status"]=="blocked": r["status"]="查询失败"
            elif t["status"]=="found":
                r.update(page=t["page"],pos=t["pos"],overall=t["overall"],matched_asin=t.get("matched_asin",a),matched_label=t.get("matched_label"))
                if t.get("exact_status","found")=="found": r.update(exact_overall=t.get("exact_overall",t["overall"]),exact_page=t.get("exact_page",t["page"]))
                if p is None: r["status"]="基准"
                elif not p["found"]: r["status"]="新进"
                else:
                    r["change"]=r["prev"]-r["overall"]
                    r["status"]="上升" if r["change"]>0 else "下降" if r["change"]<0 else "持平"
            else:
                r["status"]="掉出" if (p and p["found"]) else "未进前10页"
            rows.append(r)
    return rows
def summarize(rows,prev,titles,first_run):
    per={}
    for a in KW:
        R=[r for r in rows if r["asin"]==a]
        chk=[r for r in R if r["status"]!="查询失败"]; fnd=[r for r in chk if r["overall"] is not None]
        ok={(r["asin"],r["keyword"]) for r in chk}  # compare counts only over keywords successfully checked today
        pv=[(k,v) for k,v in prev.items() if k[0]==a and k in ok]
        pf=sum(1 for k,v in pv if v["found"]); pp=sum(1 for k,v in pv if v["found"] and v["page"]==1)
        s={"title":titles.get(a,""),"checked":len(chk),"found_top10_pages":len(fnd),"page1":sum(1 for r in fnd if r["page"]==1),
           "avg_rank":round(sum(r["overall"] for r in fnd)/len(fnd),1) if fnd else None,"blocked":len(R)-len(chk),
           "prev_found":pf if pv else None,"prev_page1":pp if pv else None,
           "exact_found_top10_pages":sum(1 for r in chk if r["exact_overall"] is not None),"exact_page1":sum(1 for r in chk if r["exact_page"]==1),
           "sibling_only":sum(1 for r in fnd if r["exact_overall"] is None)}
        s["delta_found"]=s["found_top10_pages"]-pf if pv else None
        s["delta_page1"]=s["page1"]-pp if pv else None
        up=sorted([r for r in R if r["status"]=="上升"],key=lambda r:-r["change"]); dn=sorted([r for r in R if r["status"]=="下降"],key=lambda r:r["change"])
        s["gainers"]=[{"keyword":r["keyword"],"prev":r["prev"],"today":r["overall"],"change":r["change"]} for r in up]
        s["losers"]=[{"keyword":r["keyword"],"prev":r["prev"],"today":r["overall"],"change":r["change"]} for r in dn]
        s["new_entries"]=[{"keyword":r["keyword"],"today":r["overall"],"page":r["page"]} for r in R if r["status"]=="新进"]
        s["dropouts"]=[{"keyword":r["keyword"],"prev":r["prev"]} for r in R if r["status"]=="掉出"]
        s["page1_keywords"]=sorted([{"keyword":r["keyword"],"pos":r["pos"],"overall":r["overall"],"prev":r["prev"],"change":r["change"],"status":r["status"],
            "matched_asin":r["matched_asin"],"matched_label":r["matched_label"],"exact_overall":r["exact_overall"]} for r in fnd if r["page"]==1],key=lambda x:x["overall"])
        def sg(x): return "持平" if x==0 else ("%+d"%x)
        parts=[f"检查{s['checked']}词，进前10页{s['found_top10_pages']}词，首页{s['page1']}词"+(f"，平均排名{s['avg_rank']}" if s['avg_rank'] else "")
               +f"（按全部变体统计；本ASIN自身前10页{s['exact_found_top10_pages']}词、首页{s['exact_page1']}词）"]
        if not pv: parts.append("基准日数据（无历史对比）")
        else:
            parts.append(f"较上次进前10页{sg(s['delta_found'])}、首页{sg(s['delta_page1'])}")
            if up: parts.append("上升："+"；".join(f"{x['keyword']} {x['prev']}→{x['today']}" for x in s["gainers"][:3]))
            if dn: parts.append("下降："+"；".join(f"{x['keyword']} {x['prev']}→{x['today']}" for x in s["losers"][:3]))
            if s["new_entries"]: parts.append("新进："+"；".join(f"{x['keyword']}(#{x['today']})" for x in s["new_entries"][:5]))
            if s["dropouts"]: parts.append("掉出："+"；".join(f"{x['keyword']}(原#{x['prev']})" for x in s["dropouts"][:5]))
        if s["blocked"]: parts.append(f"{s['blocked']}词查询失败")
        s["analysis"]="。".join(parts)+"。"
        per[a]=s
    return per

# ---------------- crawl
def run_crawl(log_path,targets,errors):
    import crawl
    done=crawl.done_pairs(log_path)
    todo=[(a,k) for a,k in targets if (a,k) not in done]
    log(f"crawl: {len(targets)} targets, {len(targets)-len(todo)} already done, {len(todo)} to go -> {log_path}")
    try: crawl.new_session()
    except Exception as e: errors.append({"stage":"amazon_session","error":repr(e)}); log("session error",e)
    consec=0
    for i,(a,k) in enumerate(todo):
        try: fin=crawl.crawl_pair(a,k,log_path)
        except Exception as e:
            fin={"status":"blocked"}; errors.append({"stage":"amazon","asin":a,"keyword":k,"error":repr(e)})
            with open(log_path,"a") as f: f.write(json.dumps({"final":True,"asin":a,"keyword":k,"status":"blocked","error":repr(e),"pages":0,"ts":crawl._utcnow()})+"\n")
        if fin["status"]=="blocked":
            consec+=1; errors.append({"stage":"amazon","asin":a,"keyword":k,"error":fin.get("error") or "blocked/captcha after retries",
                                      **({"loc":fin.get("loc")} if fin.get("error")=="US location not set" else {})})
            if consec>=3: errors.append({"stage":"amazon","error":"3 consecutive blocked keywords; crawl stopped early, %d not crawled"%(len(todo)-i-1)}); log("too many blocks, stopping crawl"); break
            log("blocked; cooling down 5-8 min"); time.sleep(random.uniform(300,480))
            try: crawl.new_session(rotate=True)
            except Exception as e: log("session error",e)
        else: consec=0
        time.sleep(random.uniform(2,5))

# ---------------- feishu publish
def publish(c,ids,today,fin,rows,per,prev_date,titles,res):
    th=ids[T_HIST]; tms=day_ms(today)
    # 1) history: replace rows for today's 查询日期
    old=[r["record_id"] for r in c.list_records(th,field_names=["查询日期"]) if r["fields"].get("查询日期") and ms_day(r["fields"]["查询日期"])==today]
    if old: c.batch_delete(th,old)
    hist=[]
    for a in KW:
        for kw in KW[a]:
            d=fin.get((a,kw))
            if not d or d["status"]=="blocked": continue
            f=d["status"]=="found"
            row={"关键词":kw,"ASIN":a,"产品标题":titles.get(a,""),"是否进前10页":"是" if f else "否","已扫描页数":d.get("pages") or 0,
                 "查询时间":utc_ms(d["ts"]),"查询日期":tms}
            if f:
                row.update({"页码":d["page"],"页内位置":d["pos"],"自然总排名":d["overall"]})
                ma=d.get("matched_asin",a); row["展示变体"]=ma+(f"（{d['matched_label']}）" if d.get("matched_label") else "")+("" if ma==a else " [同款其他变体]")
            if d.get("exact_status",d["status"])=="found": row["本ASIN自然排名"]=d.get("exact_overall",d.get("overall"))
            hist.append(row)
    c.batch_create(th,hist); res["排名历史"]={"replaced_today":len(old),"appended":len(hist)}; log("history: -%d +%d"%(len(old),len(hist)))
    # 2) comparison: full refresh
    tc=ids[T_CMP]
    old=[r["record_id"] for r in c.list_records(tc,field_names=["关键词"])]
    if old: c.batch_delete(tc,old)
    cr=[]
    for r in rows:
        x={"关键词":r["keyword"],"ASIN":r["asin"],"日期":tms,"状态":r["status"]}
        if prev_date: x["对比日期"]=day_ms(prev_date)
        if r.get("matched_asin"): x["展示变体"]=r["matched_asin"]+(f"（{r['matched_label']}）" if r.get("matched_label") else "")
        if r.get("exact_overall") is not None: x["本ASIN今日排名"]=r["exact_overall"]
        for fk,rk in (("今日页码","page"),("今日页内位置","pos"),("今日自然总排名","overall"),("昨日自然总排名","prev"),("排名变化","change")):
            if r[rk] is not None: x[fk]=r[rk]
        cr.append(x)
    c.batch_create(tc,cr); res["每日对比"]={"deleted":len(old),"written":len(cr)}; log("compare: -%d +%d"%(len(old),len(cr)))
    # 3) summary: replace today's rows
    ts_=ids[T_SUM]
    old=[r["record_id"] for r in c.list_records(ts_,field_names=["日期"]) if r["fields"].get("日期") and ms_day(r["fields"]["日期"])==today]
    if old: c.batch_delete(ts_,old)
    sr=[]
    for a,s in per.items():
        x={"记录":f"{today.isoformat()} {a}","日期":tms,"ASIN":a,"产品标题":s["title"],"检查词数":s["checked"],"进前10页词数":s["found_top10_pages"],
           "首页词数":s["page1"],"查询失败词数":s["blocked"],"分析":s["analysis"],
           "本ASIN进前10页词数":s["exact_found_top10_pages"],"本ASIN首页词数":s["exact_page1"]}
        if s["avg_rank"] is not None: x["平均自然排名"]=s["avg_rank"]
        if s["delta_found"] is not None: x["较昨日进前10页词数变化"]=s["delta_found"]
        if s["delta_page1"] is not None: x["较昨日首页词数变化"]=s["delta_page1"]
        sr.append(x)
    c.batch_create(ts_,sr); res["每日汇总"]={"replaced_today":len(old),"written":len(sr)}; log("summary: -%d +%d"%(len(old),len(sr)))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--date"); ap.add_argument("--log"); ap.add_argument("--asins",nargs="*"); ap.add_argument("--keywords",nargs="*")
    ap.add_argument("--no-crawl",action="store_true"); ap.add_argument("--no-feishu",action="store_true"); ap.add_argument("--no-report",action="store_true")
    ap.add_argument("--setup-only",action="store_true"); ap.add_argument("--summary-out")
    a=ap.parse_args()
    today=D.datetime.strptime(a.date,"%Y%m%d").date() if a.date else D.datetime.now(TZ).date()
    ds=today.strftime("%Y%m%d")
    os.makedirs("logs",exist_ok=True); os.makedirs("reports",exist_ok=True)
    log_path=a.log or f"logs/crawl_{ds}.jsonl"
    summ_path=a.summary_out or f"daily_summary_{ds}.json"
    errors=[]; res={}; started=D.datetime.now(TZ).isoformat(timespec="seconds")
    lock=f"logs/.lock_{ds}"
    if not a.setup_only and not a.no_crawl:
        if os.path.exists(lock):
            try: pid=int(open(lock).read()); os.kill(pid,0); log("another run (pid %d) is active for %s; exiting"%(pid,ds)); sys.exit(3)
            except (ValueError,ProcessLookupError,PermissionError): pass
        open(lock,"w").write(str(os.getpid()))
    try:
        c=Client(APP); ids=None
        if not a.no_feishu:
            try:
                ids=ensure_schema(c)
                n=backfill_hist_date(c,ids[T_HIST]); 
                if n: log("backfilled 查询日期 for",n,"rows")
            except Exception as e:
                errors.append({"stage":"feishu_schema","error":str(e)}); log("FEISHU schema error",e); ids=None
        if a.setup_only: print(json.dumps({"ids":ids,"errors":errors},ensure_ascii=False)); return
        targets=[(x,k) for x in KW for k in KW[x] if (not a.asins or x in a.asins) and (not a.keywords or k in a.keywords)]
        if not a.no_crawl: run_crawl(log_path,targets,errors)
        fin,_=load_today(log_path)
        titles=report.load_titles()
        prev_date,prev,src=None,{},None
        if ids:
            try: prev_date,prev=prev_from_feishu(c,ids[T_HIST],today); src="feishu"
            except Exception as e: errors.append({"stage":"feishu_read_prev","error":str(e)})
            if prev_date:  # like-for-like: overlay family-matched values from the local log of the same day (older Feishu rows are exact-only)
                try:
                    _,lp=prev_from_local(today,only=prev_date)
                    if lp: prev.update(lp); src="feishu+local_family"
                except Exception as e: errors.append({"stage":"local_prev_family","error":repr(e)})
        if not prev:
            prev_date,prev=prev_from_local(today); src="local" if prev else None
        rows=compare(fin,prev)
        per=summarize(rows,prev,titles,first_run=not prev)
        if ids:
            try: publish(c,ids,today,fin,rows,per,prev_date,titles,res)
            except Exception as e: errors.append({"stage":"feishu_write","error":str(e)}); log("FEISHU write error",e); traceback.print_exc()
        if not a.no_report:
            try:
                report.build(log_path,"amazon_asin_keywords.csv","amazon_asin_keywords.xlsx")
                report.build(log_path,f"reports/amazon_asin_keywords_{ds}.csv",f"reports/amazon_asin_keywords_{ds}.xlsx")
                res["files"]=["amazon_asin_keywords.csv","amazon_asin_keywords.xlsx",f"reports/amazon_asin_keywords_{ds}.xlsx"]
            except Exception as e: errors.append({"stage":"report","error":repr(e)})
        def allof(key): return [dict(asin=x,**y) for x,s in per.items() for y in s[key]]
        gain=sorted(allof("gainers"),key=lambda r:-r["change"]); lose=sorted(allof("losers"),key=lambda r:r["change"])
        out={"date":today.isoformat(),"timezone":"Asia/Shanghai","started":started,"finished":D.datetime.now(TZ).isoformat(timespec="seconds"),
             "crawl_log":log_path,"match_mode":"family","variants_file":"variants.json","compared_with":prev_date.isoformat() if prev_date else None,"prev_source":src,
             "keywords_total":len(rows),"keywords_crawled_ok":sum(1 for r in rows if r["status"]!="查询失败"),
             "status_counts":{s:sum(1 for r in rows if r["status"]==s) for s in STATUS},
             "per_asin":{x:{k:v for k,v in s.items() if k not in ("gainers","losers","new_entries","dropouts")} for x,s in per.items()},
             "top_gainers":gain[:10],"top_losers":lose[:10],"new_entries":allof("new_entries"),"dropouts":allof("dropouts"),
             "blocked_keywords":[{"asin":r["asin"],"keyword":r["keyword"]} for r in rows if r["status"]=="查询失败"],
             "feishu":res,"feishu_url":os.environ.get("FEISHU_BASE_URL_PREFIX","https://<your-tenant>.feishu.cn/base/")+APP,"errors":errors}
        json.dump(out,open(summ_path,"w"),ensure_ascii=False,indent=1)
        log("summary ->",summ_path,"errors:",len(errors))
    finally:
        if os.path.exists(lock) and open(lock).read().strip()==str(os.getpid()): os.remove(lock)
if __name__=="__main__": main()
