#!/usr/bin/env python3
"""Etsy 数据采集（box 版）：直接调用 Etsy Open API v3（只读，无需 OAuth）。
替代原版占位的 "Etsy MCP" 调用。
  python fetch_etsy_data.py keywords.txt -o etsy_data.json [--limit 100] [--max-keywords N]
环境变量：ETSY_API_KEY（keystring）+ ETSY_SHARED_SECRET；不会打印。
限额：5 QPS / 5000 次每天，脚本默认每次请求间隔 0.25s。
"""
import argparse, json, os, sys, time, statistics
from datetime import datetime
import urllib.request, urllib.parse, urllib.error

API = "https://openapi.etsy.com/v3/application/listings/active"


def _headers():
    k, s = os.environ.get("ETSY_API_KEY"), os.environ.get("ETSY_SHARED_SECRET")
    if not k:
        sys.exit("❌ 缺少环境变量 ETSY_API_KEY")
    return {"x-api-key": f"{k}:{s}" if s else k, "User-Agent": "etsy-keyword-db/1.0"}


def _price(p):
    try:
        return p["amount"] / p["divisor"]
    except Exception:
        return None


def fetch_keyword_data(keyword, limit=100, sort_on="score", retries=3):
    q = urllib.parse.urlencode({"keywords": keyword, "limit": limit, "sort_on": sort_on})
    for i in range(retries):
        try:
            req = urllib.request.Request(f"{API}?{q}", headers=_headers())
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < retries - 1:
                time.sleep(2 ** i); continue
            raise RuntimeError(f"Etsy API HTTP {e.code}")
    res = d.get("results", [])
    # 只取 USD 标价（非美元店铺的 amount 不可直接比较），均价用去掉首尾 10% 的截尾均值，避免异常高价拉偏
    usd = [l for l in res if (l.get("price") or {}).get("currency_code") == "USD"]
    prices = sorted(x for x in (_price(l.get("price", {})) for l in usd) if x)
    k = len(prices) // 10
    trimmed = prices[k: len(prices) - k] if len(prices) > 4 else prices
    top = [{"listing_id": l.get("listing_id"), "title": l.get("title", "")[:140],
            "price": _price(l.get("price", {})), "num_favorers": l.get("num_favorers", 0),
            "views": l.get("views"), "personalizable": l.get("is_personalizable"),
            "url": l.get("url")} for l in res[:10]]
    return {
        "keyword": keyword,
        "listing_count": d.get("count", 0),           # Etsy 全站活跃 Listing 数（竞争度）
        "avg_price": round(statistics.mean(trimmed), 2) if trimmed else 0.0,
        "median_price": round(statistics.median(prices), 2) if prices else 0.0,
        "price_range": {"min": min(prices) if prices else 0.0, "max": max(prices) if prices else 0.0},
        "personalizable_ratio": round(sum(1 for l in res if l.get("is_personalizable")) / len(res), 2) if res else 0,
        "sample_size": len(res),
        "usd_sample_size": len(prices),
        "top_listings": top,
        "fetch_time": datetime.now().isoformat(),
    }


def main():
    ap = argparse.ArgumentParser(description="Etsy 关键词数据采集（Etsy API v3）")
    ap.add_argument("input", help="关键词列表文件（每行一个）")
    ap.add_argument("-o", "--output", default="etsy_data.json")
    ap.add_argument("--limit", type=int, default=100, help="每个关键词取样 Listing 数（≤100）")
    ap.add_argument("--max-keywords", type=int, default=0, help="测试用：最多处理 N 个关键词")
    a = ap.parse_args()
    kws = [l.strip() for l in open(a.input, encoding="utf-8") if l.strip()]
    if a.max_keywords:
        kws = kws[: a.max_keywords]
    results = []
    for i, kw in enumerate(kws, 1):
        print(f"[{i}/{len(kws)}] {kw}")
        try:
            results.append(fetch_keyword_data(kw, a.limit))
            r = results[-1]; print(f"   Listing {r['listing_count']:,} | 均价 ${r['avg_price']}")
        except Exception as e:
            print(f"   ❌ {e}"); results.append({"keyword": kw, "error": str(e), "fetch_time": datetime.now().isoformat()})
        time.sleep(0.25)
    out = {"total": len(kws), "success": sum("error" not in r for r in results),
           "failed": sum("error" in r for r in results), "data": results,
           "generated_at": datetime.now().isoformat()}
    json.dump(out, open(a.output, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ 已保存 {a.output}（成功 {out['success']} / 失败 {out['failed']}）")


if __name__ == "__main__":
    main()
