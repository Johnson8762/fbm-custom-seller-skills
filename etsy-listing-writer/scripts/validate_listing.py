"""Validate Etsy listing drafts. Usage: python3 validate_listing.py drafts.json
drafts.json = {"A": {"title": "...", "tags": [13 strings], "primary_kw": "..."}, ...}
Checks: title <=140 chars; exactly 13 unique tags; each tag <=20 chars, only letters/digits/space/-/';
banned / risky words (trademarks, unverifiable claims, origin statements);
cross-listing cannibalization: same primary_kw used twice, or >4 shared tags between two listings.
Exit code 1 if any hard error."""
import json, sys, itertools, re
BANNED = ['bestseller', 'best seller', 'free shipping', 'sale', 'disney', 'pixar', 'snoopy', 'garfield', 'grinch', 'pokemon',
          'hypoallergenic', 'guarantee', 'heal', 'cure', 'etsy pick', 'star seller', 'made in usa', 'usa made',
          'ships from china', 'china', 'overseas', 'international warehouse', 'imported', 'ai generated', 'chemical-free', 'non-toxic']
def check(D):
    err = 0
    for k, v in D.items():
        t, tags = v['title'], v['tags']
        msgs = []
        if len(t) > 140: msgs.append(f'title {len(t)}>140'); err = 1
        if len(tags) != 13: msgs.append(f'{len(tags)} tags'); err = 1
        if len({x.lower() for x in tags}) != len(tags): msgs.append('duplicate tags'); err = 1
        for x in tags:
            if len(x) > 20: msgs.append(f'tag too long: {x} ({len(x)})'); err = 1
            if not all(c.isalnum() or c in " -'" for c in x): msgs.append(f'bad char: {x}'); err = 1
        low = (t + ' | ' + ' | '.join(tags) + ' | ' + v.get('description', '')).lower()
        hits = [b for b in BANNED if re.search(r'\b' + re.escape(b) + r'\b', low)]
        if hits: msgs.append(f'banned/risky words: {hits}'); err = 1
        print(f'[{k}] title {len(t)} chars | tags ok={not any("tag" in m for m in msgs)} | ' + ('; '.join(msgs) or 'OK'))
        print('     ' + ', '.join(f'{x}({len(x)})' for x in tags))
    for (a, va), (b, vb) in itertools.combinations(D.items(), 2):
        sh = {x.lower() for x in va['tags']} & {x.lower() for x in vb['tags']}
        if len(sh) > 4: print(f'WARN cannibalization {a}-{b}: {len(sh)} shared tags {sorted(sh)}')
        if va.get('primary_kw') and va.get('primary_kw') == vb.get('primary_kw'):
            print(f'ERROR {a}-{b} share primary keyword "{va["primary_kw"]}"'); err = 1
    return err
if __name__ == '__main__':
    sys.exit(check(json.load(open(sys.argv[1]))))
