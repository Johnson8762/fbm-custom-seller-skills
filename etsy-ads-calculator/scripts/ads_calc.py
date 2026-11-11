#!/usr/bin/env python3
"""Etsy Ads 测算：保本 ROAS / 最高 CPC / 逐 listing 止亏建议。只读计算，不改广告。
ROAS = 广告收入 / 广告花费，保本 ROAS = 1 / 广告前利润率。
费用模型复用 etsy-listing-writer/data/etsy_fees.json 与 scripts/pricing.py（示例费率，不是经核对的现行官方费用）。

用法：
  ads_calc.py breakeven --margin 40                       # 已知广告前利润率（%）
  ads_calc.py breakeven --list 500 --cost-cny 50 --discount 20   # 示例：由标价/成本/折扣算利润率
  ads_calc.py roas --spend 100 --revenue 250 [--margin 40]   # 实际 ROAS vs 保本线
  ads_calc.py maxcpc --margin 40 --aov-usd 25 --cvr 2.0           # 每次点击最多能花多少（保本）
  ads_calc.py listings ads.csv [--margin 40 | --margins margins.json]
      ads.csv 列：listing_id,title,spend_usd,orders,revenue_usd[,clicks]
      规则（全部由利润率推导，不设拍脑袋阈值）：
        orders=0 且 spend ≥ 保本 CPA（=AOV×利润率；AOV 用该表有单 listing 的平均客单）→ 建议暂停
        ROAS < 保本 → 建议降价/降预算或暂停；ROAS ≥ 保本 → 保留
注意：Etsy Ads 收入口径含折后售价、按 Etsy 归因（30 天点击），与订单表不完全一致；站外广告（Offsite Ads 15%）是另一笔费用，不在 ROAS 里。
"""
import argparse, csv, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'etsy-listing-writer', 'scripts'))

def margin_from(a):
    if getattr(a, 'margin', None) is not None: return a.margin / 100.0
    if getattr(a, 'list', None) is not None:
        import pricing as P
        c = P.calc(a.list, P.cost_to_mxn(cost_cny=a.cost_cny, cost_usd=getattr(a, 'cost_usd', None)), a.discount or 0, not a.no_rfc)
        return c['margin_pct'] / 100.0
    return None

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    def m(p):
        p.add_argument('--margin', type=float, help='广告前利润率 %%'); p.add_argument('--list', type=float); p.add_argument('--cost-cny', type=float)
        p.add_argument('--discount', type=float, default=0); p.add_argument('--no-rfc', action='store_true')
    p = sub.add_parser('breakeven'); m(p)
    p = sub.add_parser('roas'); m(p); p.add_argument('--spend', type=float, required=True); p.add_argument('--revenue', type=float, required=True)
    p = sub.add_parser('maxcpc'); m(p); p.add_argument('--aov-usd', type=float, required=True); p.add_argument('--cvr', type=float, required=True, help='转化率 %%')
    p = sub.add_parser('listings'); m(p); p.add_argument('csv'); p.add_argument('--margins', help='{listing_id: margin_pct}')
    a = ap.parse_args(); mg = margin_from(a)
    if a.cmd == 'breakeven':
        if not mg: sys.exit('ERROR: 需要 --margin 或 --list + --cost-cny')
        print(f'广告前利润率 {mg:.1%} → 保本 ROAS {1 / mg:.2f}（ACoS 上限 {mg:.1%}）')
    elif a.cmd == 'roas':
        r = a.revenue / a.spend if a.spend else float('inf')
        line = f'ROAS {r:.2f}（收入 US${a.revenue:.2f} / 花费 US${a.spend:.2f}），ACoS {a.spend / a.revenue:.1%}' if a.revenue else f'ROAS 0（花费 US${a.spend:.2f}，无收入）'
        if mg: line += f'；保本 {1 / mg:.2f} → ' + ('盈利' if r >= 1 / mg else '亏损')
        print(line)
    elif a.cmd == 'maxcpc':
        if not mg: sys.exit('ERROR: 需要利润率')
        print(f'保本最高 CPC = AOV×CVR×利润率 = {a.aov_usd}×{a.cvr / 100:.3f}×{mg:.3f} = US${a.aov_usd * a.cvr / 100 * mg:.2f}')
    elif a.cmd == 'listings':
        rows = list(csv.DictReader(open(a.csv, encoding='utf-8-sig')))
        margins = json.load(open(a.margins)) if a.margins else {}
        with_orders = [r for r in rows if float(r.get('orders') or 0) > 0]
        aov = sum(float(r['revenue_usd']) for r in with_orders) / max(1, sum(float(r['orders']) for r in with_orders)) if with_orders else None
        print(f'口径：AOV {"US$%.2f" % aov if aov else "未取得"}（有单 listing 平均）')
        tot_s = tot_r = 0
        for r in rows:
            s, o, rev = float(r['spend_usd'] or 0), float(r['orders'] or 0), float(r['revenue_usd'] or 0); tot_s += s; tot_r += rev
            lm = (float(margins[r['listing_id']]) / 100) if r['listing_id'] in margins else mg
            be = 1 / lm if lm else None; roas = rev / s if s else None
            if not lm: act = '缺利润率，无法判断'
            elif o == 0 and aov and s >= aov * lm: act = f'暂停（花费 ≥ 保本 CPA US${aov * lm:.2f} 仍 0 单）'
            elif o == 0: act = '观察（0 单，花费未到保本 CPA）'
            elif roas < be: act = '亏损：降预算/暂停或提价'
            else: act = '保留'
            print(f"{r['listing_id']} {r.get('title', '')[:40]:<40} 花费 {s:7.2f} 单 {o:3.0f} 收入 {rev:8.2f} ROAS {roas if roas is not None else 0:5.2f} 保本 {be if be else 0:4.2f} → {act}")
        if tot_s: print(f'合计：花费 US${tot_s:.2f}，收入 US${tot_r:.2f}，ROAS {tot_r / tot_s:.2f}' + (f'，保本 {1 / mg:.2f}' if mg else ''))

if __name__ == '__main__':
    main()
