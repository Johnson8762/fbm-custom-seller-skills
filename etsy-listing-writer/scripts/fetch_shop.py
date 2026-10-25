"""Usage: python3 fetch_shop.py SHOP_ID [SHOP_ID...] --out DIR [--max-reviews 1000]
Saves DIR/shop_<id>.json, listings_<id>.json (active), reviews_<id>.json."""
import sys, json, os, argparse
sys.path.insert(0, os.path.dirname(__file__)); from etsy_client import get, paginate
ap = argparse.ArgumentParser(); ap.add_argument('ids', nargs='+'); ap.add_argument('--out', default='.')
ap.add_argument('--max-reviews', type=int, default=1000); ap.add_argument('--max-listings', type=int, default=500)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
for sid in a.ids:
    shop = get(f'/shops/{sid}')
    lis = paginate(f'/shops/{sid}/listings/active', a.max_listings)
    rev = paginate(f'/shops/{sid}/reviews', a.max_reviews)
    for n, v in [('shop', shop), ('listings', lis), ('reviews', rev)]:
        json.dump(v, open(f'{a.out}/{n}_{sid}.json', 'w'), ensure_ascii=False)
    print(sid, shop.get('shop_name'), 'sales', shop.get('transaction_sold_count'), 'reviews', shop.get('review_count'),
          'rating', shop.get('review_average'), '| got listings', len(lis), 'reviews', len(rev))
