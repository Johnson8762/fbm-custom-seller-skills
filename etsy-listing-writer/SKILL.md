---
name: etsy-listing-writer
description: >-
  撰写、改写或审核 Etsy listing（标题、13
  tags、描述、个性化、变体定价、属性、alt、交付稿）时使用：按场景拆多条链接、EverBee+Etsy API 取数、产品事实清单、MXN 定价（RFC
  费用模型、折扣后实付）、交付前风险检查（低价变体、主图一致、相似链接、工艺/成本/安全、披露），校验后只存草稿不发布。
---
# Etsy Listing 撰写

1. 先用 Read 完整读取 `etsy-listing-writer/SKILL_FULL.md`，严格按其中步骤执行。Python 用 `python`。
2. 硬规则摘要：
   - 只存草稿、绝不发布；不改其他在售 listing；Renewal 一律 Manual；Who made 按使用者确认的真实生产情况填写，不要猜；生产合作方与运费模板发货地由使用者在后台如实填写，文案不写发货地/产地。
   - 每条至少 1 张未修图实拍；抱枕类 03 号位留空给老板上传；描述写 AI 效果图说明；抱枕描述保留「无白边会明显变形」；不出现 3D Hug。
   - 只写 `products/<id>/facts.json` 里已确认的事实；所有数字注明来源，拿不到写「未取得」；EverBee 未标周期不称月搜索量。
   - 定价：`scripts/pricing.py` 读取 `data/etsy_fees.json`。表内 MXN/RFC 比例只是示例（有 RFC 15.625% × 买家实付 + 13.6 MXN/单；无 RFC 33.125% + 13.6；CNY/USD 示例汇率 6.5），不是经核对的现行官方费用。买家实付 = 标价 × (1 − 折扣)。Agent 不动折扣。
   - 同产品多链接：独占主词、标题前 3 词不同、共用 tags ≤4、主推场景分开。
3. 交付前做第 8 步风险检查（2026-11-08 增补：低价变体、主图与选项一致、折扣价格证据、相似链接定位、工艺/成本/安全对照共享清单 `references/manufacturing-checklist.md`、披露、IP），再跑
   `python etsy-listing-writer/scripts/validate_listing.py drafts.json --product <类型> --facts products/<id>/facts.json --everbee <csv> --pricing --deliverable <稿.md>`，0 ERROR 才交付。`products/<id>/facts.json` 由使用者按 `products/_template/facts.json` 自备，不要提交真实事实清单。
4. 交付格式：总目录 → 每条链接来源说明 → 按后台顺序 1–16 项、每项一个复制框 → 附录 A 校验结果。完成后直接交付用户；如需发飞书，使用你自己的通知脚本（文本中不要出现未转义的 `$`），仅在用户明确要求时发送。
5. 仅在用户当次明确授权时，使用已登录的卖家会话将稿件存为草稿（绝不发布）；不要输入密码；上传图片每张填写 alt（≤250）；保存后重新打开核对并截图。
