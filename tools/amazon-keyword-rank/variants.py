"""Variant-family helpers for organic-rank matching.
variants.json: {tracked_asin: {parent, dimensions, children:[{asin,label}]}}  (built 2026-10-25 from amazon.com dp twister data)
family(asin) -> set of ASINs (tracked + parent + all children). Unknown ASIN -> {asin} (exact-only, old behaviour)."""
import json,os
_P=os.path.join(os.path.dirname(os.path.abspath(__file__)),"variants.json")
_V=None
def _load():
    global _V
    if _V is None:
        try: _V=json.load(open(_P))
        except Exception: _V={}
    return _V
def family(asin):
    v=_load().get(asin)
    if not v: return {asin}
    return {c["asin"] for c in v.get("children",[])}|{v.get("parent") or asin,asin}
def label(asin):
    for v in _load().values():
        for c in v.get("children",[]):
            if c["asin"]==asin: return c.get("label","")
    return ""
def score(asin,pages):
    """pages: ordered list of organic-ASIN lists (page 1..n). Returns (family_hit, exact_hit); each None or
    {"page","pos","overall"[,"matched_asin","matched_label"]}."""
    F=family(asin); off=0; ex=fb=None
    for p,org in enumerate(pages,1):
        for i,x in enumerate(org):
            if fb is None and x in F: fb={"page":p,"pos":i+1,"overall":off+i+1,"matched_asin":x,"matched_label":label(x)}
            if ex is None and x==asin: ex={"page":p,"pos":i+1,"overall":off+i+1}
        off+=len(org)
    return fb,ex
def rescore_final(d,page_recs):
    """Upgrade an old exact-only final record to family matching using its logged page records (in place).
    Only applied to records without match_mode. Old logs stop scanning at the exact hit, so the family best
    (always <= exact) is fully determined."""
    if d.get("match_mode") or d.get("status")=="blocked" or not page_recs: return d
    by={}
    for r in page_recs: by[r["page"]]=r.get("organic") or []
    pages=[by.get(p,[]) for p in range(1,max(by)+1)]
    fb,ex=score(d["asin"],pages)
    d["exact_status"]=d["status"]
    if ex: d.update(exact_page=ex["page"],exact_pos=ex["pos"],exact_overall=ex["overall"])
    if fb:
        d.update(status="found",page=fb["page"],pos=fb["pos"],overall=fb["overall"],matched_asin=fb["matched_asin"],matched_label=fb["matched_label"])
    d["match_mode"]="family_rescored"; d["family_size"]=len(family(d["asin"]))
    return d
