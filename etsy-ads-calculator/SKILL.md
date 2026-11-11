---
name: etsy-ads-calculator
description: >-
  计算或评估 Etsy Ads 时使用：保本 ROAS / ACoS 上限 / 保本最高 CPC，按 listing 给出保留、观察、降预算或暂停建议，写
  Etsy 周报里的广告结论。只读计算，不改广告、预算、价格或折扣。
---
# Etsy 广告测算

1. 先用 Read 读取 `etsy-ads-calculator/SKILL_FULL.md`。
2. 口径：ROAS = Etsy Ads 归因收入 / 广告花费（USD）；保本 ROAS = 1 / 广告前利润率；广告前利润率用 etsy-listing-writer 的示例费用模型（有 RFC 时示例为 15.625% × 买家实付 + 13.6 MXN/单，不是经核对的现行官方费用；买家实付 = 标价 × (1 − 折扣)；成本只用使用者提供的落地成本）。
3. 命令：`python etsy-ads-calculator/scripts/ads_calc.py breakeven|roas|maxcpc|listings ...`。
4. 逐 listing 止亏：0 单且花费 ≥ 保本 CPA（AOV × 利润率）→ 建议暂停；ROAS < 保本 → 降预算/暂停或提价；不自定拍脑袋阈值。
5. 只给建议，不改广告、预算、价格或折扣；数据注明统计周期与抓取时间（北京时间）；MXN 收入与 USD 广告费不直接相减。
