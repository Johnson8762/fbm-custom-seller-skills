#!/usr/bin/env python3
"""Validate Etsy listing drafts before they go into the shop (draft only).

Usage:
  validate_listing.py drafts.json [--product photo_pillow|person_pillow|memorial_pillow|dog_vest|generic]
                      [--facts facts.json] [--everbee everbee.csv|json] [--pricing] [--deliverable deliverable.md]
                      [--cost-json costs.json] [--discount 20]
drafts.json: {"A": {...listing...}, "B": {...}} 或单个 listing 对象。listing 字段：
  title, tags[13], primary_kw, description, personalization, product,
  images: [{"slot":1,"kind":"real|ai|edited|reserved","alt":"...","note":""}],
  variations: [{"name":"30cm","price_mxn":500,"cost_cny":40,"digital":false}],
  renewal ("Manual"), who_made (a value the user confirmed), shipping_profile: {"origin": "..."} , materials, section
Exit code 1 if any ERROR. Example prices are not a shop's prices. Fee math is illustrative.
"""
import argparse, csv, itertools, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BANNED = ['bestseller', 'best seller', 'free shipping', 'sale', 'disney', 'pixar', 'snoopy', 'garfield', 'grinch', 'pokemon',
          'hypoallergenic', 'guarantee', 'guaranteed', 'heal', 'cure', 'etsy pick', 'star seller', 'made in usa', 'usa made',
          'ships from china', 'china', 'overseas', 'international warehouse', 'imported', 'chemical-free', 'non-toxic',
          'mini me', 'forever in my heart']
ORIGIN = [r'ships? from\b', r'\bmade in\b', r'\bfujian\b', r'\bguangdong\b', r'\bshenzhen\b', r'\byiwu\b', r'\bwarehouse\b']
SUBJECTIVE = ['best', 'top', 'perfect', 'amazing', 'awesome', 'cheapest', 'premium', 'luxury', 'unique', 'great']
TRADEMARK_SOFT = ['heat', 'max', 'barbie', 'marvel', 'nfl', 'nba', 'harry potter', 'bluey', 'hello kitty', 'peanuts', 'star wars']
AI_DISCLOSURE = re.compile(r'(\bAI\b|artificial intelligence|digital(ly)? (mockup|rendering|preview|effect)|effect image|preview images?)', re.I)
NO_BORDER_WARN = re.compile(r'(no[- ]border|without (a )?(white )?border|borderless).{0,160}(distort|warp|lose|change|shape)|(distort|warp).{0,160}(no[- ]border|without (a )?(white )?border|borderless)', re.I | re.S)
HUG_3D = re.compile(r'3d ?hug|arms[- ]out|open[- ]arms?|hug(ging)? pose', re.I)
PROFILES = {
    'photo_pillow':   dict(need_no_border_warn=True, forbid_3d_hug=False, reserve_real_slot=3),
    'person_pillow':  dict(need_no_border_warn=True, forbid_3d_hug=True, reserve_real_slot=3),
    'memorial_pillow': dict(need_no_border_warn=True, forbid_3d_hug=True, reserve_real_slot=3),
    'dog_vest':       dict(need_no_border_warn=False, forbid_3d_hug=False, reserve_real_slot=None),
    'generic':        dict(need_no_border_warn=False, forbid_3d_hug=False, reserve_real_slot=None),
}

class R:
    def __init__(self, name): self.name, self.err, self.warn, self.info = name, [], [], []
    def E(self, m): self.err.append(m)
    def W(self, m): self.warn.append(m)
    def I(self, m): self.info.append(m)

def words(s): return re.findall(r"[a-z0-9']+", s.lower())

def load_everbee(path):
    if not path: return None
    if path.endswith('.json'):
        d = json.load(open(path)); rows = d if isinstance(d, list) else d.get('rows', d)
    else:
        rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
    out = {}
    for r in rows:
        r = {k.lower().strip(): v for k, v in (r.items() if isinstance(r, dict) else [])}
        kw = (r.get('keyword') or '').strip().lower()
        if kw: out[kw] = r
    return out

def check_listing(key, v, a, facts, everbee):
    r = R(key); prof = PROFILES.get(v.get('product') or a.product or 'generic', PROFILES['generic'])
    t = v.get('title', ''); tags = v.get('tags', []); desc = v.get('description', '')
    # --- title
    if not t: r.E('missing title')
    if len(t) > 140: r.E(f'title {len(t)}>140')
    nw = len(words(t))
    if nw > 14: r.W(f'title {nw} words (guide 6-12, max 14)')
    subj = [w for w in SUBJECTIVE if re.search(r'\b' + w + r'\b', t.lower())]
    if subj: r.W(f'subjective words in title {subj}')
    # --- tags
    if len(tags) != 13: r.E(f'{len(tags)} tags (need 13)')
    if len({x.lower().strip() for x in tags}) != len(tags): r.E('duplicate tags')
    for x in tags:
        if len(x) > 20: r.E(f'tag too long: {x} ({len(x)})')
        if not all(c.isalnum() or c in " -'" for c in x): r.E(f'bad char in tag: {x}')
    cnt = {}
    for x in tags:
        for w in set(words(x)): cnt[w] = cnt.get(w, 0) + 1
    many = [w for w, c in cnt.items() if c >= 4]
    if many: r.W(f'words in >=4 tags {many}')
    # --- banned / origin / trademark
    blob = ' | '.join([t, ' | '.join(tags), desc, v.get('personalization', ''), ' | '.join(i.get('alt', '') for i in v.get('images', []))]).lower()
    hits = [b for b in BANNED if re.search(r'\b' + re.escape(b) + r'\b', blob)]
    if hits: r.E(f'banned/risky words: {hits}')
    oh = [p for p in ORIGIN if re.search(p, desc.lower())]
    if oh: r.E(f'origin/发货地 statement in description {oh}: 文案不写发货地/产地，运费模板如实填写')
    tm = [b for b in TRADEMARK_SOFT if re.search(r'\b' + re.escape(b) + r'\b', blob)]
    if tm: r.W(f'possible trademark, check context (ok if pet/person name) {tm}')
    # --- shipping / materials / renewal / who made
    sp = v.get('shipping_profile') or {}
    if not sp.get('origin'): r.W('shipping_profile: confirm origin is truthful (如实填写·勿改)')
    if v.get('materials'): r.W('materials free-text field removed from listing form (2026): set Cover/Fill material attributes')
    ren = (v.get('renewal') or '').lower()
    if ren != 'manual': r.E(f'renewal must be Manual (skill default), got {v.get("renewal")!r}')
    if not v.get('who_made'): r.W('who_made not set (user fills this from the real production setup)')
    # --- images / alt / AI disclosure / real photo
    imgs = v.get('images', [])
    for i in imgs:
        alt = i.get('alt', '')
        if i.get('kind') != 'reserved':
            if not alt: r.E(f'image {i.get("slot")}: missing alt text')
            if len(alt) > 250: r.E(f'image {i.get("slot")}: alt {len(alt)}>250')
        if i.get('kind') == 'reserved' and i.get('file'): r.E(f'image {i.get("slot")}: reserved slot must stay empty (不要上传占位图)')
    kinds = [i.get('kind') for i in imgs]
    if imgs and 'real' not in kinds and 'reserved' not in kinds:
        r.E('no unedited real photo and no reserved slot (Etsy: at least one unedited photo of the actual item)')
    elif imgs and 'real' not in kinds:
        r.W('real photo slot reserved for the user to upload — listing must stay draft until the real photo is in')
    if prof['reserve_real_slot'] and imgs:
        s = [i for i in imgs if i.get('slot') == prof['reserve_real_slot']]
        if not s or s[0].get('kind') not in ('reserved', 'real'): r.E(f'slot {prof["reserve_real_slot"]:02d} must be reserved for the unedited real photo')
    if any(k in ('ai', 'edited') for k in kinds):
        if not AI_DISCLOSURE.search(desc): r.E('AI/edited images present but description has no AI-image disclosure')
        r.W('AI mockup images: human check each one matches the real product (colour, texture, border, size)')
    if len(imgs) > 20: r.E(f'{len(imgs)} images > 20')
    # --- product profile rules
    if prof['need_no_border_warn'] and not NO_BORDER_WARN.search(desc):
        r.E('description lacks the "no border → noticeable distortion" warning (无白边会明显变形)')
    if prof['forbid_3d_hug'] and HUG_3D.search(blob): r.E('3D Hug / arms-out wording found (this product profile forbids that pose)')
    # --- facts
    if facts is not None:
        bad = [f for f in facts.get('facts', []) if f.get('status') not in ('已确认', '老板后台填写')]
        for f in bad: r.E(f'fact not confirmed: {f.get("item")} ({f.get("status")})')
        for w in facts.get('do_not_write', []):
            pat = w.get('pattern') if isinstance(w, dict) else w
            if pat and re.search(pat, desc, re.I): r.E(f'description contains do-not-write item: {pat}')
        r.I(f'facts: {len(facts.get("facts", []))} items, {len(bad)} unconfirmed')
    # --- everbee
    if everbee is not None:
        miss = [x for x in tags if x.lower() not in everbee]
        if miss: r.W(f'tags not found in EverBee data (未查量，不要编): {miss}')
        pk = (v.get('primary_kw') or '').lower()
        if pk and pk not in everbee: r.W(f'primary_kw "{pk}" not in EverBee data')
        r.I('everbee: ' + ', '.join(f"{x}({everbee[x.lower()].get('volume', '?')}/{everbee[x.lower()].get('competition', '?')})" for x in tags if x.lower() in everbee))
    # --- pricing + 2026-11-08 low-price variant risk
    vars_ = v.get('variations', [])
    if a.pricing:
        try:
            import pricing as P
        except Exception as e:
            r.E(f'pricing engine import failed: {e}'); P = None
        prices = [x.get('price_mxn') for x in vars_ if x.get('price_mxn') is not None]
        if not prices: r.W('--pricing: no variation prices')
        phys = [x for x in vars_ if not x.get('digital') and x.get('price_mxn') is not None]
        dig = [x for x in vars_ if x.get('digital') and x.get('price_mxn') is not None]
        disc = a.discount if a.discount is not None else v.get('discount_pct', 0)
        for x in phys:
            if P and x.get('cost_cny') is not None:
                c = P.calc(x['price_mxn'], P.cost_to_mxn(cost_cny=x['cost_cny']), disc, True)
                floor = (facts or {}).get('min_margin_pct')
                msg = f"{x.get('name')}: list {x['price_mxn']} → paid {c['paid_mxn']} MXN, margin {c['margin_pct']}% (RFC) / {c['margin_pct_other_rfc_case']}% (no RFC)"
                if c['margin_pct'] < 0: r.E('loss: ' + msg)
                elif floor is not None and c['margin_pct'] < floor: r.E(f'below margin floor {floor}%: ' + msg)
                else: r.I(msg)
            elif x.get('cost_cny') is None:
                r.W(f"{x.get('name')}: no cost_cny → margin not computed (成本无来源时不估)")
        if dig and phys:
            lo = min(x['price_mxn'] for x in dig); plo = min(x['price_mxn'] for x in phys)
            if lo < plo:
                r.W(f'low-price digital variant {lo} < cheapest physical {plo}: it becomes the search "from" price; title/main image must not imply the physical item at that price; describe clearly what the digital variant delivers (2026-11-08 risk check)')
        if prices and max(prices) / max(1e-9, min(prices)) > 5:
            r.W(f'wide price range {min(prices)}–{max(prices)} (Etsy may show wide-price warning)')
    return r

def cross(D, rs):
    out = []
    for (a, va), (b, vb) in itertools.combinations(D.items(), 2):
        sh = {x.lower() for x in va.get('tags', [])} & {x.lower() for x in vb.get('tags', [])}
        if len(sh) > 4: out.append(('WARN', f'cannibalization {a}-{b}: {len(sh)} shared tags {sorted(sh)}'))
        else: out.append(('INFO', f'{a}-{b}: {len(sh)} shared tags {sorted(sh)}'))
        if va.get('primary_kw') and va.get('primary_kw', '').lower() == vb.get('primary_kw', '').lower():
            out.append(('ERROR', f'{a}-{b} share primary keyword "{va["primary_kw"]}"'))
        if words(va.get('title', ''))[:3] == words(vb.get('title', ''))[:3]:
            out.append(('WARN', f'{a}-{b} titles share the first 3 words — 主推场景要分开（相似链接定位）'))
    return out

def check_deliverable(path):
    s = open(path, encoding='utf-8').read(); errs = []
    for need in ['总目录', '来源说明']:
        if need not in s: errs.append(f'deliverable missing section: {need}')
    if not re.search(r'```', s) and '复制' not in s: errs.append('deliverable has no copy blocks (每项一个复制框)')
    return errs

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('drafts'); ap.add_argument('--product', default=None, choices=list(PROFILES))
    ap.add_argument('--facts'); ap.add_argument('--everbee'); ap.add_argument('--pricing', action='store_true')
    ap.add_argument('--deliverable'); ap.add_argument('--discount', type=float, default=None)
    a = ap.parse_args()
    D = json.load(open(a.drafts))
    if 'title' in D: D = {'listing': D}
    facts = json.load(open(a.facts)) if a.facts else None
    everbee = load_everbee(a.everbee)
    fail = False
    for k, v in D.items():
        r = check_listing(k, v, a, facts, everbee)
        print(f'[{k}] title {len(v.get("title", ""))} chars | {len(v.get("tags", []))} tags')
        print('     ' + ', '.join(f'{x}({len(x)})' for x in v.get('tags', [])))
        for m in r.err: print('     ERROR', m)
        for m in r.warn: print('     WARN', m)
        for m in r.info: print('     INFO', m)
        print('RESULT:', 'FAIL' if r.err else ('PASS (review WARN lines)' if r.warn else 'PASS'))
        fail |= bool(r.err)
    for lvl, m in cross(D, None):
        print(lvl, m); fail |= lvl == 'ERROR'
    if a.deliverable:
        for m in check_deliverable(a.deliverable): print('ERROR', m); fail = True
    print('OVERALL:', 'FAIL' if fail else 'PASS')
    sys.exit(1 if fail else 0)

if __name__ == '__main__':
    main()
