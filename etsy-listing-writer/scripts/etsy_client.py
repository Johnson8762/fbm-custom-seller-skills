"""Minimal Etsy Open API v3 client (public endpoints, API-key only, READ-ONLY).
Key is read from env ETSY_API_KEY / ETSY_SHARED_SECRET and sent as header
x-api-key: KEY:SECRET. Never print the key. Sleeps 0.25s/call (<=5 QPS).
Raises MissingEtsyKey if either variable is unset (does not send an empty ":" header).
GET only; no write endpoints.
"""
import os, sys, json, time, urllib.request, urllib.parse, urllib.error
BASE = 'https://openapi.etsy.com/v3/application'
CALLS = 0


class MissingEtsyKey(RuntimeError):
    pass


def headers():
    k, s = os.environ.get('ETSY_API_KEY', ''), os.environ.get('ETSY_SHARED_SECRET', '')
    if not k or not s:
        missing = [n for n, v in (('ETSY_API_KEY', k), ('ETSY_SHARED_SECRET', s)) if not v]
        raise MissingEtsyKey('missing env: ' + ', '.join(missing))
    return {'x-api-key': k + ':' + s}


def get(path, **params):
    global CALLS
    h = headers()
    url = BASE + path + ('?' + urllib.parse.urlencode(params, doseq=True) if params else '')
    err = ''
    for attempt in range(3):
        time.sleep(0.25); CALLS += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as f:
                return json.load(f)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 * (attempt + 1))
                continue
            return {'_error': e.code, '_body': e.read().decode()[:300]}
        except Exception as e:
            time.sleep(1)
            err = str(e)
    return {'_error': 'network', '_body': err}


def paginate(path, max_items=1000, page=100, **params):
    out, off = [], 0
    while off < max_items:
        r = get(path, limit=page, offset=off, **params)
        if '_error' in r:
            out.append(r)
            break
        res = r.get('results', [])
        out += res
        if len(res) < page or off + page >= r.get('count', 0):
            break
        off += page
    return out


if __name__ == '__main__':
    try:
        print(json.dumps(get('/openapi-ping')))
    except MissingEtsyKey as e:
        print('ERROR:', e, file=sys.stderr)
        sys.exit(2)
