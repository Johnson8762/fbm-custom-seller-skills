"""Minimal Etsy Open API v3 client (public endpoints, API-key only).
Key is read from env ETSY_API_KEY / ETSY_SHARED_SECRET and sent as header
x-api-key: KEY:SECRET. Never print the key. Sleeps 0.25s/call (<=5 QPS)."""
import os, json, time, urllib.request, urllib.parse, urllib.error
BASE = 'https://openapi.etsy.com/v3/application'
_H = {'x-api-key': os.environ.get('ETSY_API_KEY', '') + ':' + os.environ.get('ETSY_SHARED_SECRET', '')}
CALLS = 0
def get(path, **params):
    global CALLS
    url = BASE + path + ('?' + urllib.parse.urlencode(params, doseq=True) if params else '')
    for attempt in range(3):
        time.sleep(0.25); CALLS += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=_H), timeout=30) as f:
                return json.load(f)
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(2 * (attempt + 1)); continue
            return {'_error': e.code, '_body': e.read().decode()[:300]}
        except Exception as e:
            time.sleep(1); err = str(e)
    return {'_error': 'network', '_body': err if 'err' in dir() else ''}
def paginate(path, max_items=1000, page=100, **params):
    out, off = [], 0
    while off < max_items:
        r = get(path, limit=page, offset=off, **params)
        if '_error' in r: out.append(r); break
        res = r.get('results', []); out += res
        if len(res) < page or off + page >= r.get('count', 0): break
        off += page
    return out
