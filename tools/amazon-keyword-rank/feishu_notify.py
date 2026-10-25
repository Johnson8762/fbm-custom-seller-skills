"""Send the daily Amazon keyword rank summary to the owner on Feishu via a Feishu app bot (env FEISHU_SCOUT_*).
Usage: python3 feishu_notify.py [daily_summary_YYYYMMDD.json] [--note "额外分析文字"] [--dry]"""
import json,sys,glob,argparse
from feishu_send import send as fsend
SHORT={"B0XXXXXXX1":"示例产品A","B0XXXXXXX2":"示例产品B"}  # 可选：ASIN -> 中文简称
def sg(x): return "持平" if not x else "%+d"%x
def build(d,note=None):
    c=d["status_counts"]; first=d.get("compared_with") is None
    L=[]
    L.append(f"日期：{d['date']}（北京时间）"+("，基准日，暂无对比" if first else f"，对比 {d['compared_with']}"))
    L.append(f"成功查询 {d['keywords_crawled_ok']}/{d['keywords_total']} 个词。")
    if not first:
        L.append(f"上升 {c['上升']}，下降 {c['下降']}，持平 {c['持平']}，新进 {c['新进']}，掉出 {c['掉出']}，未进前10页 {c['未进前10页']}。")
    L.append("")
    L.append("【各链接】")
    for a,s in d["per_asin"].items():
        line=f"{SHORT.get(a,a)}（{a}）：前10页 {s['found_top10_pages']}/{s['checked']} 词，首页 {s['page1']} 词"
        if s.get("avg_rank"): line+=f"，平均第 {s['avg_rank']} 名"
        if s.get("delta_found") is not None: line+=f"；较上次 前10页{sg(s['delta_found'])}，首页{sg(s['delta_page1'])}"
        if s.get("exact_found_top10_pages") is not None and d.get("match_mode")=="family":
            line+=f"（其中本ASIN自身 前10页 {s['exact_found_top10_pages']} 词、首页 {s['exact_page1']} 词）"
        if s.get("blocked"): line+=f"；{s['blocked']} 词查询失败"
        L.append("• "+line)
        for k in s.get("page1_keywords",[]):
            t=f"    - {k['keyword']}：首页第 {k['pos']} 名"
            if k.get("change") is not None: t+=f"（上次第 {k['prev']} 名，{'持平' if k['change']==0 else ('上升 %d' % k['change'] if k['change']>0 else '下降 %d' % -k['change'])}）"
            elif k.get("status")=="新进": t+="（新进）"
            if k.get("matched_asin") and k["matched_asin"]!=a: t+=f"［展示变体 {k['matched_asin']}"+(f" {k['matched_label']}" if k.get("matched_label") else "")+"］"
            L.append(t)
    def sec(title,items,fmt):
        if items:
            L.append(""); L.append(title)
            for x in items[:5]: L.append("• "+fmt(x))
            if len(items)>5: L.append(f"  …另有 {len(items)-5} 个")
    sec("【上升最多】",d.get("top_gainers",[]),lambda x:f"{SHORT.get(x['asin'],x['asin'])}｜{x['keyword']}：第{x['prev']}→第{x['today']}名（+{x['change']}）")
    sec("【下降最多】",d.get("top_losers",[]),lambda x:f"{SHORT.get(x['asin'],x['asin'])}｜{x['keyword']}：第{x['prev']}→第{x['today']}名（{x['change']}）")
    sec("【新进前10页】",d.get("new_entries",[]),lambda x:f"{SHORT.get(x['asin'],x['asin'])}｜{x['keyword']}：第{x['today']}名（第{x['page']}页）")
    sec("【掉出前10页】",d.get("dropouts",[]),lambda x:f"{SHORT.get(x['asin'],x['asin'])}｜{x['keyword']}：原第{x['prev']}名")
    if note: L.append(""); L.append("【分析】"); L.append(note.strip())
    if d.get("errors"): L.append(""); L.append(f"⚠️ 本次运行有 {len(d['errors'])} 个错误，表格数据可能不完整。")
    L.append(""); L.append("说明：排名为不含广告的自然排名，美国站，查前10页"+("；按同一父体下所有变体（颜色/尺寸等）中排名最靠前的一个计算，［展示变体］为实际出现的子ASIN。" if d.get("match_mode")=="family" else "。"))
    content=[[{"tag":"text","text":l}] for l in L]+[[{"tag":"a","text":"打开多维表格查看明细","href":d.get("feishu_url","https://<your-tenant>.feishu.cn/base/<YOUR_BITABLE_APP_TOKEN>")}]]
    return {"zh_cn":{"title":f"亚马逊关键词排名日报 {d['date']}","content":content}}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("summary",nargs="?"); ap.add_argument("--note"); ap.add_argument("--dry",action="store_true")
    a=ap.parse_args()
    p=a.summary or sorted(glob.glob("daily_summary_*.json"))[-1]
    post=build(json.load(open(p)),a.note)
    if a.dry: print(json.dumps(post,ensure_ascii=False,indent=1)); return
    r=fsend("scout",post=post)  # 智巡 Scout = Amazon rank daily report
    print("feishu send:",r.get("code"),r.get("msg")); sys.exit(0 if r.get("code")==0 else 1)
if __name__=="__main__": main()
