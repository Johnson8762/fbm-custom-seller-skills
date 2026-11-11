---
name: etsy-listing-image-generator
description: >-
  为 Etsy listing 规划、生成、处理或审核商品图（主图、副图、尺寸图、实拍位、alt text、缩略图总览）时使用：v3.3
  五步流程（问齐信息→买家顾虑→先出 2 张样图→每图附理由→手机与本土化检查），2026-11-08
  逐图验收（独立用途、新增信息、镜像/尺寸差/白边画面可见、工艺一致），03 号位留给未修图实拍，不做 3D Hug，含质检与抠图去白边脚本。
---
# Etsy 商品图生成（v3.3 + 2026-11-08 逐图验收）

1. 先用 Read 完整读取 `etsy-listing-image-generator/SKILL_FULL.md`，以及 `etsy-listing-image-generator/references/etsy-photo-rules.md`、`etsy-listing-image-generator/references/product_physics.md`、`etsy-listing-writer/references/manufacturing-checklist.md`（两技能共用一份）。
2. 必走五步：开工前问齐产品信息 → 调研买家顾虑（差评/问答/Reddit 或用户提供的社区反馈）→ 先出主图 + 最难一张样图待确认（老板明确说直接出全套才跳过）→ 每张图附做图理由 → 手机缩略图与本土化检查（美国站 inch/lb）。
3. 硬规则：不编造产品，没有实拍不出成品图；每条至少 1 张未修图实拍，人形/宠物/全家福抱枕 03 号位留空不传占位图；AI 图须在描述披露；人物抱枕场景里抱枕的人 = 抱枕上印的人；无白边款不得出现白色描边；填充变形 = 细部变小变尖、轮廓更怪、印花拉伸，绝不变胖变圆；不做 3D Hug；纪念款克制，不做流程图/纯文字图/示意简图；alt ≤250，终图出来后对着画面写。
4. 逐图验收：每张图唯一 job、相对前图的 new_info、声称的差异要有画面证据（镜像用非对称人物、尺寸差拉开、白边宽度同实物），工艺与清单一致；不通过就重做或删除并记录原因。
5. 工具（`python`）：`etsy-listing-image-generator/scripts/render_plan.py plan.json --md out.md` 校验方案并出总览；`etsy-listing-image-generator/scripts/etsy_image_qc.py --plan plan.json --sheet sheet.png` 逐图质检 + 手机缩略图总览；`etsy-listing-image-generator/scripts/clean_cutout_alpha.py in.png out.png [--from-white 245]` 抠图去白边并出对比图；模板 `etsy-listing-image-generator/templates/image_plan.example.json`。
6. 交付：总目录 → 每张图来源（实拍/改动/AI）→ 一张图一个 alt 复制框 → 缩略图总览 → 校验结果；完成后直接交付用户。
