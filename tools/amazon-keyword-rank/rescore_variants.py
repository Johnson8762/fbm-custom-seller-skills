"""Re-score existing crawl logs with variant-family matching (read-only; does not touch Feishu).
Usage: python3 rescore_variants.py LOG [LOG...]  -> prints comparison, writes rescore_<logname>.json"""
import json,sys,os
from kws import KW
V=json.load(open("variants.json"))
def fam(a):
    v=V.get(a); 
    if not v: return {a}
    return {c["asin"] for c in v["children"]}|{v["parent"],a}
LBL={c["asin"]:c["label"] for v in V.values() for c in v["children"]}
def rescore(fp):
    pages={}
    for l in open(fp):
        d=json.loads(l)
        if d.get("final"): continue
        pages.setdefault((d["asin"],d["keyword"]),{})[d["page"]]=d["organic"]
    out={}
    for (a,k),ps in pages.items():
        F=fam(a); off=0; ex=None; fb=None
        for p in sorted(ps):
            org=ps[p]
            for i,x in enumerate(org):
                if x==a and ex is None: ex={"page":p,"pos":i+1,"overall":off+i+1}
                if x in F and fb is None: fb={"page":p,"pos":i+1,"overall":off+i+1,"matched_asin":x,"label":LBL.get(x,"")}
            off+=len(org)
        out[(a,k)]={"exact":ex,"family":fb,"pages":len(ps)}
    return out
if __name__=="__main__":
    allres={}
    for fp in sys.argv[1:]:
        r=rescore(fp); print("\n=====",fp)
        rows=[]
        for a in KW:
            R={k:v for (x,k),v in r.items() if x==a}
            e10=sum(1 for v in R.values() if v["exact"]); e1=sum(1 for v in R.values() if v["exact"] and v["exact"]["page"]==1)
            f10=sum(1 for v in R.values() if v["family"]); f1=sum(1 for v in R.values() if v["family"] and v["family"]["page"]==1)
            print(f"{a}: crawled {len(R)}/{len(KW[a])} | exact top10pages {e10}, page1 {e1} | family top10pages {f10}, page1 {f1}")
            for k,v in sorted(R.items(),key=lambda kv:(kv[1]["family"] or {"overall":9999})["overall"]):
                if v["family"] and (not v["exact"] or v["family"]["matched_asin"]!=a):
                    f=v["family"]; e=v["exact"]
                    print(f"   {k!r}: family #{f['overall']} (p{f['page']} pos{f['pos']}) via {f['matched_asin']} [{f['label']}]; exact: "+(f"#{e['overall']} p{e['page']}" if e else "not in scanned pages"))
            rows.append({"asin":a,"exact_top10":e10,"exact_page1":e1,"family_top10":f10,"family_page1":f1,
                         "details":{k:v for k,v in R.items()}})
        allres[fp]=rows
    json.dump(allres,open("rescore_variants_result.json","w"),ensure_ascii=False,indent=1)
