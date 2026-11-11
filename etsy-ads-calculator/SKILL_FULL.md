# Etsy 广告测算（etsy-ads-calculator）

> MXN/RFC 数字来自 etsy-listing-writer 的示例费用表，不是经核对的现行官方费率。

## 用途
- 算保本 ROAS、ACoS 上限、保本最高 CPC；
- 用 Etsy Ads 后台导出的逐 listing 数据（花费、订单、收入）给出「保留 / 观察 / 降预算 / 暂停」建议；
- 周报里写广告结论（例：某周花费 US$100、ROAS 1.50，低于约 1.80 保本线 → 逐 listing 止亏）。

## 口径
- ROAS = Etsy Ads 归因收入 / 广告花费（同为 USD）；保本 ROAS = 1 / 广告前利润率；ACoS = 花费 / 收入。
- 广告前利润率 = 买家实付扣 Etsy 费用（示例：有 RFC 15.625% + 13.6 MXN/单，不是经核对的现行官方费用）和落地成本后的利润 / 买家实付；用 `etsy-listing-writer/scripts/pricing.py` 或 `etsy-ads-calculator/scripts/ads_calc.py breakeven --list --cost-cny --discount`。`ads.csv` 由使用者提供。
- 成本只用使用者提供的落地成本；没有就写「未取得」，不估。
- 站外广告 Offsite Ads（15%）是单独费用，不进 ROAS；被收时利润率再减 15 个百分点。
- 止亏规则全部由利润率推导：0 单且花费 ≥ 保本 CPA（AOV × 利润率）→ 建议暂停；不自定拍脑袋阈值。
- **只给建议，不改广告、预算、价格或折扣**；任何调整需老板确认。

## 数据来源
- Etsy Ads 后台（只读；进入须用户当次授权，使用已登录会话、不输入密码）→ 导出或照抄逐 listing 数据，注明时间范围与抓取时间（北京时间）。
- 周报统计周期写清（如 11-03~11-09）；收入币种 MXN 与广告 USD 不要直接相减。

## 命令（`python etsy-ads-calculator/scripts/ads_calc.py ...`）
- `breakeven --margin 40` / `breakeven --list 500 --cost-cny 50 --discount 20`
- `roas --spend 100 --revenue 250 --margin 40`
- `maxcpc --margin 40 --aov-usd 25 --cvr 2.0`
- `listings ads.csv --margin 40`（列：listing_id,title,spend_usd,orders,revenue_usd）

## 输出
结论一句话 → 合计 ROAS vs 保本 → 逐 listing 表（花费/单/收入/ROAS/保本/建议）→ 数据来源与缺口。用中文，时间用北京时间。
