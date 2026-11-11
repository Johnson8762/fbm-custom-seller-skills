#!/usr/bin/env python3
"""Etsy 定价引擎（MXN 示例）。
费用模型见 data/etsy_fees.json。表内 MXN/RFC 数字只演示算法，不是经核对的现行官方费用；使用前按 Etsy 现行费用和你的店铺修改该文件。

费用模型（data/etsy_fees.json 示例，非官方核验）：
  Etsy 费用 = 买家实付 × 15.625%（有 RFC 示例）/ 33.125%（无 RFC 示例） + 13.6 MXN/单
  买家实付 = 标价 × (1 − 折扣)
  净利 = 买家实付 − Etsy 费用 − 落地成本(MXN)；利润率 = 净利 / 买家实付
  若被收站外广告（Offsite Ads 15%）：利润率再减 15 个百分点（按买家实付计）
  成本换算：CNY→USD 使用示例规划汇率 6.5（可在 etsy_fees.json 里替换）；USD↔MXN 用 --mxn-per-usd（示例默认 18.614，算新价请传当日 open.er-api 值）

用法（数字都是示例，不是店铺报价）：
  # 1) 给定标价，看利润
  pricing.py margin --list 500 --cost-cny 30 [--discount 20] [--no-rfc] [--mxn-per-usd 18.6]
  # 2) 反推：目标利润率 → 最低标价
  pricing.py floor --cost-cny 50 --target-margin 30 [--discount 20]
  # 3) 反推：目标买家实付 USD → 标价（÷(1-折扣)）
  pricing.py from-paid --paid-usd 25 --discount 20
  # 4) 等利润：参考尺寸（标价 L_ref、成本 C_ref）的利润率，套到其他尺寸成本 → 标价
  pricing.py match --ref-list 700 --ref-cost-cny 60 --cost-cny 40 45 --discount 20
  # 5) 批量表：JSON {"rows":[{"name":"10cm","list":500,"cost_cny":40},...], "discount":20}
  pricing.py table rows.json [--md]
所有命令加 --json 输出机器可读结果。
"""
import argparse, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FEES = json.load(open(os.path.join(HERE, '..', 'data', 'etsy_fees.json')))
D = FEES['derived']
CNY_PER_USD = FEES['fx']['CNY_per_USD']

def pct(rfc=True):
    return (D['pct_of_buyer_paid_with_rfc'] if rfc else D['pct_of_buyer_paid_without_rfc']) / 100.0

def calc(list_mxn, cost_mxn, discount=0.0, rfc=True, mxn_per_usd=None):
    mxn_per_usd = mxn_per_usd or FEES['fx']['MXN_per_USD_default']
    paid = list_mxn * (1 - discount / 100.0)
    fee = paid * pct(rfc) + D['fixed_mxn_per_order']
    fee_other = paid * pct(not rfc) + D['fixed_mxn_per_order']
    net = paid - fee - cost_mxn
    net_other = paid - fee_other - cost_mxn
    m = net / paid if paid else float('nan')
    return dict(list_mxn=round(list_mxn, 2), discount_pct=discount, paid_mxn=round(paid, 2),
                paid_usd=round(paid / mxn_per_usd, 2), etsy_fee_mxn=round(fee, 2), cost_mxn=round(cost_mxn, 2),
                net_mxn=round(net, 2), net_usd=round(net / mxn_per_usd, 2), margin_pct=round(100 * m, 1),
                margin_pct_other_rfc_case=round(100 * net_other / paid, 1) if paid else None,
                margin_pct_if_offsite_ads=round(100 * m - FEES['components']['offsite_ads_pct_optional'], 1),
                rfc=rfc, mxn_per_usd=mxn_per_usd)

def cost_to_mxn(cost_cny=None, cost_usd=None, cost_mxn=None, mxn_per_usd=None):
    mxn_per_usd = mxn_per_usd or FEES['fx']['MXN_per_USD_default']
    if cost_mxn is not None: return cost_mxn
    if cost_usd is not None: return cost_usd * mxn_per_usd
    if cost_cny is not None: return cost_cny / CNY_PER_USD * mxn_per_usd
    sys.exit('ERROR: 需要 --cost-cny / --cost-usd / --cost-mxn 之一（成本无来源时不要估）')

def floor_list(cost_mxn, target_margin, discount=0.0, rfc=True):
    # paid*(1-p) - fixed - cost = t*paid  => paid = (fixed+cost)/(1-p-t)
    denom = 1 - pct(rfc) - target_margin / 100.0
    if denom <= 0: return None
    paid = (D['fixed_mxn_per_order'] + cost_mxn) / denom
    return paid / (1 - discount / 100.0)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    def common(p):
        p.add_argument('--discount', type=float, default=0.0, help='全店折扣百分比，如 35')
        p.add_argument('--no-rfc', action='store_true'); p.add_argument('--mxn-per-usd', type=float)
        p.add_argument('--json', action='store_true')
    def cost(p):
        p.add_argument('--cost-cny', type=float); p.add_argument('--cost-usd', type=float); p.add_argument('--cost-mxn', type=float)
    p = sub.add_parser('margin'); p.add_argument('--list', type=float, required=True); cost(p); common(p)
    p = sub.add_parser('floor'); p.add_argument('--target-margin', type=float, required=True); cost(p); common(p)
    p = sub.add_parser('from-paid'); p.add_argument('--paid-usd', type=float, required=True); common(p)
    p = sub.add_parser('match'); p.add_argument('--ref-list', type=float, required=True); p.add_argument('--ref-cost-cny', type=float, required=True)
    p.add_argument('--cost-cny', type=float, nargs='+', required=True); p.add_argument('--round-to', type=int, default=10, help='四舍五入到 x9 尾数的步长（默认 10 → …9）'); common(p)
    p = sub.add_parser('table'); p.add_argument('rows'); p.add_argument('--md', action='store_true'); common(p)
    a = ap.parse_args(); rfc = not a.no_rfc; fx = a.mxn_per_usd or FEES['fx']['MXN_per_USD_default']
    out = None
    if a.cmd == 'margin':
        out = calc(a.list, cost_to_mxn(a.cost_cny, a.cost_usd, a.cost_mxn, fx), a.discount, rfc, fx)
    elif a.cmd == 'floor':
        c = cost_to_mxn(a.cost_cny, a.cost_usd, a.cost_mxn, fx); L = floor_list(c, a.target_margin, a.discount, rfc)
        out = dict(min_list_mxn=round(L, 2) if L else None, cost_mxn=round(c, 2), target_margin_pct=a.target_margin, discount_pct=a.discount, rfc=rfc)
    elif a.cmd == 'from-paid':
        paid_mxn = a.paid_usd * fx; out = dict(paid_usd=a.paid_usd, paid_mxn=round(paid_mxn, 2), list_mxn=round(paid_mxn / (1 - a.discount / 100.0), 2), discount_pct=a.discount, mxn_per_usd=fx)
    elif a.cmd == 'match':
        ref = calc(a.ref_list, cost_to_mxn(a.ref_cost_cny, mxn_per_usd=fx), a.discount, rfc, fx); rows = []
        for c in a.cost_cny:
            L = floor_list(cost_to_mxn(c, mxn_per_usd=fx), ref['margin_pct'], a.discount, rfc)
            Lr = math.ceil(L / a.round_to) * a.round_to - 1 if a.round_to else L
            rows.append(dict(cost_cny=c, exact_list_mxn=round(L, 2), suggested_list_mxn=Lr, check=calc(Lr, cost_to_mxn(c, mxn_per_usd=fx), a.discount, rfc, fx)))
        out = dict(reference=ref, rows=rows)
    elif a.cmd == 'table':
        spec = json.load(open(a.rows)); disc = spec.get('discount', a.discount); rows = []
        for r in spec['rows']:
            c = cost_to_mxn(r.get('cost_cny'), r.get('cost_usd'), r.get('cost_mxn'), fx)
            rows.append(dict(name=r.get('name', ''), **calc(r['list'], c, disc, rfc, fx)))
        out = dict(rows=rows)
        if a.md and not a.json:
            print('| 档位 | 标价 MXN | 折后实付 MXN | ≈USD | Etsy 费用 MXN | 成本 MXN | 净利 MXN | 利润率(%s) | 利润率(%s) | 若收站外广告 15%% |' % ('有 RFC' if rfc else '无 RFC', '无 RFC' if rfc else '有 RFC'))
            print('|---|---|---|---|---|---|---|---|---|---|')
            for r in rows:
                print(f"| {r['name']} | {r['list_mxn']:.0f} | {r['paid_mxn']:.1f} | ${r['paid_usd']:.2f} | {r['etsy_fee_mxn']:.1f} | {r['cost_mxn']:.1f} | {r['net_mxn']:.1f} | {r['margin_pct']}% | {r['margin_pct_other_rfc_case']}% | {r['margin_pct_if_offsite_ads']}% |")
            print(f"\n口径：折扣 {disc}%；1 USD = {fx} MXN；CNY→USD 示例汇率 6.5；费用模型 data/etsy_fees.json（示例表日期 {FEES['example_as_of']}，非官方核验）")
            return
    if a.json or a.cmd in ('match', 'table'):
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        for k, v in out.items(): print(f'{k}: {v}')

if __name__ == '__main__':
    main()
