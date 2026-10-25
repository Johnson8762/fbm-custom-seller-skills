#!/usr/bin/env python3
"""亚马逊前台下拉框词采集（替代浏览器插件）
  python amazon_autocomplete.py "leather journal" [--expand a-z] [--site US] -o suggest.json
--expand 时对 "词根 + a..z" 逐个请求（27 次请求，注意频率）。
"""
import argparse, json, string, time, urllib.parse, urllib.request

SITES = {"US": ("completion.amazon.com", "ATVPDKIKX0DER"), "UK": ("completion.amazon.co.uk", "A1F83G8C2ARO7P"),
         "DE": ("completion.amazon.co.uk", "A1PA6795UKMFR9"), "CA": ("completion.amazon.com", "A2EUQ1WTGCTBG2")}

def suggest(prefix, site="US"):
    host, mid = SITES[site]
    q = urllib.parse.urlencode({"prefix": prefix, "mid": mid, "alias": "aps", "limit": 11, "plain-mid": 1,
                                "client-info": "amazon-search-ui", "suggestion-type": "KEYWORD"})
    req = urllib.request.Request(f"https://{host}/api/2017/suggestions?{q}", headers={"User-Agent": "Mozilla/5.0"})
    d = json.load(urllib.request.urlopen(req, timeout=15))
    return [s["value"] for s in d.get("suggestions", [])]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("root"); ap.add_argument("--expand", action="store_true")
    ap.add_argument("--site", default="US"); ap.add_argument("-o", "--output", default="autocomplete.json")
    a = ap.parse_args()
    prefixes = [a.root] + ([f"{a.root} {c}" for c in string.ascii_lowercase] if a.expand else [])
    out = {}
    for p in prefixes:
        try:
            out[p] = suggest(p, a.site)
        except Exception as e:
            out[p] = {"error": str(e)[:120]}
        time.sleep(0.4 if a.expand else 0)
    words = sorted({w for v in out.values() if isinstance(v, list) for w in v})
    json.dump({"root": a.root, "site": a.site, "by_prefix": out, "keywords": words}, open(a.output, "w"), ensure_ascii=False, indent=1)
    print(f"✅ {len(words)} 个下拉词 → {a.output}")

if __name__ == "__main__":
    main()
