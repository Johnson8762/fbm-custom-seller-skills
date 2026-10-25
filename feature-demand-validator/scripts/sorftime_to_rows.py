#!/usr/bin/env python3
"""把 Sorftime 原始返回（_shared/sorftime_http.py 的输出 JSON）转换为 generate_keyword_csv.py 需要的结构化行。
box 新增脚本：原版由 AI 手工整理；这里给出确定性转换，AI 只需补"变化率/趋势方向/关联度"等判断列。
  python sorftime_to_rows.py --type detail|trend|extends --raw raw.json --keyword "leather journal" -o rows.json
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "amazon-aba-keyword-monitor"))
import sorftime_client as sc  # noqa: E402  复用解析器（兼容新旧 cpc 格式）


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", required=True, choices=["detail", "trend", "extends"])
    ap.add_argument("--raw", required=True)
    ap.add_argument("--keyword", required=True)
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()
    raw = json.load(open(a.raw, encoding="utf-8"))
    if isinstance(raw, dict) and "content" not in raw:  # 允许直接传 text 内容 JSON
        raw = {"content": [{"type": "text", "text": json.dumps(raw, ensure_ascii=False)}]}
    if a.type == "detail":
        d = sc.parse_detail(raw)
        rows = [{"关键词": a.keyword, "周搜索量": round(d["monthly_search_volume"] / 4.33) if d.get("monthly_search_volume") else "N/A",
                 "搜索排名": d.get("weekly_search_rank", "N/A"),
                 "变化率": d.get("rank_change_of_weekly", "N/A"), "CPC": d.get("cpc", "N/A"),
                 "备注": f"周搜索量=月搜索量/4.33 估算（keyword_detail 不返回周量，精确值见 extends 同名行）；月搜索量 {d.get('monthly_search_volume', 'N/A')}；旺季 {d.get('peak_season', '')}"}]
    elif a.type == "trend":
        t = [x for x in sc.parse_trend(raw) if x.get("searchVolume") is not None]
        rows = []
        for i, x in enumerate(t):
            prev = t[i - 1]["searchVolume"] if i else None
            dirn = "N/A" if prev in (None, 0) else ("上升" if x["searchVolume"] > prev * 1.05 else "下降" if x["searchVolume"] < prev * 0.95 else "持平")
            rows.append({"关键词": a.keyword, "日期": x["month"], "月搜索量": x["searchVolume"],
                         "搜索排名": x.get("searchRank", "N/A"), "趋势方向": dirn})
    else:
        rows = [{"延伸词": e["关键词"], "周搜索量": e["周搜索量"], "搜索排名": e["周搜索排名"], "关联度": "待判断"}
                for e in sc.parse_extends(raw)]
    json.dump(rows, open(a.output, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ {a.type}: {len(rows)} 行 → {a.output}")


if __name__ == "__main__":
    main()
