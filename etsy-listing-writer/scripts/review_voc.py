"""Rule-based review / VOC analysis for Etsy shop reviews (reproducible, no LLM).
Usage: python3 review_voc.py reviews_<id>.json [...] --listings listings_<id>.json [...] --out voc.json
Themes are regex dictionaries below; edit them per product category.
Outputs per shop: rating dist, theme counts (all / low<=3), occasions, recipients,
top n-grams in 5-star reviews, sample quotes (date, listing_id, rating)."""
import json, re, sys, html, argparse, collections, datetime
THEMES = {
 # praise / complaint dimensions
 'looks_like_pet(像本人/像照片)': r"look(s|ed)? (just )?(exactly )?like (him|her|them|my|our|the)|spitting image|exact (replica|likeness)|true to (the )?(photo|picture|life)|so realistic|lifelike|looks? so real|resembl|captured|identical",
 'quality_material(质量/做工)': r"quality|well made|well-made|sturdy|stitch|seam|material|fabric|durable",
 'soft_cuddly(柔软)': r"\bsoft\b|cuddl|plush|squish|velvet",
 'print_color(印刷/颜色清晰)': r"\bprint|colou?rs?\b|vibrant|vivid|detail|clear|crisp|sharp|high.?res",
 'size(尺寸)': r"\bsize|bigger|smaller|too small|too big|larger|tiny|huge|inch|\bcm\b",
 'shipping_speed(物流快)': r"fast (shipping|delivery)|shipped (fast|quick)|quick(ly)? (shipping|delivery)|arrived (early|quickly|fast|on time|before|so fast)|on time|ahead of|in time for|super fast|so fast",
 'communication(沟通/客服)': r"communicat|responsive|respond|customer service|seller was|helpful|kind|patient|answered|accommodat",
 'proof_preview(预览/确认)': r"proof|preview|mock.?up|approv",
 'packaging(包装)': r"packag|wrapped|vacuum|box(ed)?\b|gift wrap",
 'emotional(情绪/感动)': r"\bcr(y|ied|ying)\b|tears|teared|emotional|heart ?warm|touched|melt|speechless",
 # complaint-specific
 'shape_distortion(变形/轮廓)': r"distort|misshap|lopsid|deform|weird shape|odd shape|wonky|crooked|squash|warp|out of proportion",
 'white_border(白边)': r"white (line|edge|border|outline|trim)|border",
 'underfilled(填充不足)': r"stuffing|filling|flat\b|under.?fill|not (enough )?stuffed|deflat|limp",
 'not_like_photo(不像)': r"(doesn.?t|does not|didn.?t|did not) look like|not look like|look(s|ed)? (ill|weird|nothing like|different)|nothing like|unrecogni",
 'ai_quality(AI/修图)': r"\bai\b|artificial|generated|photoshop|cartoon",
 'late_delay(延迟)': r"\blate\b|delay|took (so )?long|never arrived|still waiting|missed",
 'blurry_pixel(模糊)': r"blurr|pixel|grain|fuzzy|low.?res",
}
OCCASIONS = {'christmas':r"christmas|xmas|holiday|stocking",'birthday':r"birthday|bday",'memorial/loss':r"passed|memorial|lost (him|her|our|my)|rainbow bridge|in memory|loss|crossed|sympathy|died|rip\b|angel",
 "mother's day":r"mother.?s day",'valentine/anniversary':r"valentine|anniversar",'college/dorm':r"college|dorm|university|school",'wedding':r"wedding|bride|groom|bachelor",
 "father's day":r"father.?s day",'graduation':r"graduat",'coworker/boss':r"cowork|co-work|\bboss|retire|office party|secret santa"}
RECIPIENTS = {'mom/mother':r"\bmom\b|mother|\bmum\b|mama",'dad/father':r"\bdad\b|father",'wife/girlfriend':r"\bwife\b|girlfriend|fianc",'husband/boyfriend':r"husband|boyfriend",
 'daughter':r"daughter",'son':r"\bson\b",'grandparent':r"grand(ma|pa|mother|father|parent)|nana|granny",'sister/brother':r"sister|brother|sibling",'friend':r"\bfriend|bestie|bff",
 'kid/child':r"\bkid|child|toddler|granddaughter|grandson|niece|nephew",'self':r"for myself|for me\b",'partner':r"partner|\bspouse"}
SUBJECT = {'dog':r"\bdog|pup|puppy|doggo",'cat':r"\bcats?\b|kitty|kitten",'person/face':r"\bface\b|my (husband|wife|boyfriend|girlfriend|son|daughter)'?s? (face|picture|photo)|of (my|our) (husband|wife|son|daughter|kids?|family|grand)",'horse/other':r"horse|bunny|rabbit|bird|parrot|guinea|hamster|lizard"}
STOP=set('the a an and to of i it my was is for this in with so they her his he she we our be that very on at as are were had have me you but not just all one them it\'s from would will got am been out up can'.split())
def clean(t): return html.unescape(t or '').replace('\n',' ').strip()
def ngrams(texts,n):
    c=collections.Counter()
    for t in texts:
        w=re.findall(r"[a-z']+",t.lower())
        for i in range(len(w)-n+1):
            g=w[i:i+n]
            if g[0] in STOP or g[-1] in STOP: continue
            c[' '.join(g)]+=1
    return c
def analyse(revs, titles):
    out={'n':len(revs),'with_text':0,'rating':collections.Counter(),'themes':{},'themes_low':{},'occasion':{},'recipient':{},'subject':{},'quotes':{}}
    texts=[];five=[]
    for r in revs:
        t=clean(r.get('review')); out['rating'][r['rating']]+=1
        if not t: continue
        out['with_text']+=1; texts.append((r,t))
        if r['rating']==5: five.append(t)
    def tally(d,key,only_low=False):
        res={}
        for k,pat in d.items():
            hits=[(r,t) for r,t in texts if re.search(pat,t,re.I) and (not only_low or r['rating']<=3)]
            res[k]=len(hits)
            if hits and not only_low or (only_low and hits):
                qk=(key+':'+k)
                hits.sort(key=lambda x:(x[0]['rating'] if only_low else -x[0]['rating'],-x[0]['create_timestamp']))
                out['quotes'][qk]=[dict(date=str(datetime.date.fromtimestamp(r['create_timestamp'])),rating=r['rating'],listing_id=r['listing_id'],
                    listing=titles.get(r['listing_id'],'(inactive/unknown)')[:60],text=t[:220]) for r,t in hits[:3]]
        return res
    out['themes']=tally(THEMES,'all'); out['themes_low']=tally(THEMES,'low',True)
    out['occasion']=tally(OCCASIONS,'occ'); out['recipient']=tally(RECIPIENTS,'rec'); out['subject']=tally(SUBJECT,'sub')
    out['bigrams']=ngrams(five,2).most_common(40); out['trigrams']=ngrams(five,3).most_common(40)
    out['rating']=dict(out['rating'])
    return out
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('reviews',nargs='+'); ap.add_argument('--listings',nargs='*',default=[]); ap.add_argument('--out',default='voc.json'); ap.add_argument('--filter',default='',help='regex on listing title; keep only matching listings (unknown/inactive listings dropped)')
    a=ap.parse_args(); titles={}
    for f in a.listings:
        for l in json.load(open(f)):
            if 'listing_id' in l: titles[l['listing_id']]=clean(l['title'])
    res={}
    for f in a.reviews:
        revs=[r for r in json.load(open(f)) if 'rating' in r]
        if a.filter: revs=[r for r in revs if re.search(a.filter,titles.get(r['listing_id'],''),re.I)]
        sid=str(revs[0]['shop_id']) if revs else f
        res[sid]=analyse(revs,titles)
        d=res[sid]; print('==',sid,'n',d['n'],'text',d['with_text'],'rating',d['rating'])
        print('  themes',{k:v for k,v in d['themes'].items() if v}); print('  low',{k:v for k,v in d['themes_low'].items() if v})
        print('  occasion',{k:v for k,v in d['occasion'].items() if v}); print('  recipient',{k:v for k,v in d['recipient'].items() if v}); print('  subject',d['subject'])
    json.dump(res,open(a.out,'w'),ensure_ascii=False,indent=1)
