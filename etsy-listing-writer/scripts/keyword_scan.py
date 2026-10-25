"""Etsy API demand/competition scan per keyword (no search volume - that is EverBee only).
Usage: python3 keyword_scan.py "kw one" "kw two" --fx fx_usd.json --out scan.json
For each kw: total active listing count, top-100 (sort_on=score) median USD price,
% personalizable, top-10 favorites sum, top-3 listings (id, favs, title)."""
import sys, os, json, argparse, statistics, html
sys.path.insert(0, os.path.dirname(__file__)); from etsy_client import get
ap = argparse.ArgumentParser(); ap.add_argument('kws', nargs='+'); ap.add_argument('--fx', required=True); ap.add_argument('--out', default='scan.json')
a = ap.parse_args(); fx = json.load(open(a.fx))['rates']; fx['USD'] = 1.0
out = {}
for k in a.kws:
    r = get('/listings/active', keywords=k, sort_on='score', limit=100)
    if '_error' in r: print(k, 'ERR', r['_error']); continue
    res = r['results']
    usd = [l['price']['amount'] / l['price']['divisor'] / fx[l['price']['currency_code']] for l in res if l['price']['currency_code'] in fx]
    favs = sorted([l['num_favorers'] for l in res], reverse=True)
    top = sorted(res, key=lambda l: -l['num_favorers'])[:3]
    out[k] = dict(count=r['count'], n=len(res), median_usd=round(statistics.median(usd), 2) if usd else None,
                  pct_personalizable=round(100 * sum(l['is_personalizable'] for l in res) / max(1, len(res))),
                  top10_favs=sum(favs[:10]), top=[(l['listing_id'], l['num_favorers'], html.unescape(l['title'])[:70]) for l in top])
    o = out[k]; print(f"{k} | {o['count']} | ${o['median_usd']} | {o['pct_personalizable']}% | top10 favs {o['top10_favs']}")
json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
