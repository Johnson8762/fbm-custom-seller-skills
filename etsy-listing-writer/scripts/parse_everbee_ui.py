"""Parse an EverBee keyword CSV that was hand-transcribed from the UI (values like 1K, 9.1K, 2.13M).
Usage: python3 parse_everbee_ui.py everbee.csv [--groups groups.json] [--out everbee.json]
- Accepts header names in any case: keyword, volume, competition, score, source (extra columns kept).
- Normalizes K/M -> numbers (approximate: '1K' means EverBee displayed 1K, i.e. 1,000-1,099 range).
- Adds ratio = volume / competition (higher = easier).
- --groups: {"scenario": ["kw1", "kw2", ...]} -> prints per-scenario volume sum for scenario ranking.
Why not etsy-keyword-database/import_everbee.py: it expects 'Keyword'/'Volume' headers and int() values,
so 'volume'/'1K' rows silently become 0 (checked 2026-10-24)."""
import csv, json, sys, argparse
def num(s):
    s = (s or '').strip().replace(',', '').replace('$', '')
    if not s or s in {'-', '—', 'N/A'}: return None
    m = 1
    if s[-1] in 'kK': m, s = 1_000, s[:-1]
    elif s[-1] in 'mM': m, s = 1_000_000, s[:-1]
    try: return round(float(s) * m)
    except ValueError: return None
def load(path):
    rows = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            r = {k.strip().lower(): (v or '').strip() for k, v in r.items() if k}
            if not r.get('keyword'): continue
            out = dict(r)
            out['keyword'] = r['keyword'].lower()
            out['volume_raw'] = r.get('volume'); out['volume'] = num(r.get('volume'))
            out['competition_raw'] = r.get('competition'); out['competition'] = num(r.get('competition'))
            out['score'] = num(r.get('score'))
            v, c = out['volume'], out['competition']
            out['ratio'] = round(v / c, 3) if v and c else None
            rows.append(out)
    return rows
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--groups'); ap.add_argument('--out')
    a = ap.parse_args(); rows = load(a.csv); idx = {r['keyword']: r for r in rows}
    for r in sorted(rows, key=lambda r: -(r['volume'] or 0)):
        print(f"{r['keyword']:<28} vol {r['volume_raw']:>6} comp {r['competition_raw']:>6} score {r.get('score')} ratio {r['ratio']}")
    if a.groups:
        print('\nScenario volume sums (only keywords present in CSV):')
        for g, kws in json.load(open(a.groups)).items():
            hit = [k for k in kws if k in idx]; miss = [k for k in kws if k not in idx]
            s = sum(idx[k]['volume'] or 0 for k in hit)
            print(f"  {g}: {s:,}  ({len(hit)} kws; missing: {', '.join(miss) or '-'})")
    if a.out: json.dump(rows, open(a.out, 'w'), indent=1, ensure_ascii=False)
