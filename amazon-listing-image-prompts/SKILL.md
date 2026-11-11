---
name: amazon-listing-image-prompts
description: >-
  当用户提供产品实物照片和信息，要生成或规划亚马逊图片资产（主图、辅图、场景图、信息图、A+ 图）及英文 Prompt
  时使用；产品一致性优先，不得捏造产品细节。
---
# 亚马逊图片资产与 Prompt

1. 先用 Read 完整读取 `amazon-listing-image-prompts/SKILL_FULL.md`（完整方法论、Prompt 规则、输出模板）。
2. 严格按其中步骤执行；模板和脚本在 `amazon-listing-image-prompts/`，Python 用 `python`（共享 venv）。
3. 出图只用用户的产品实物照片做参考，成品放到 `reports/image-assets/<product>/generated/`。
4. **必走 5 步**（SKILL_FULL 末尾修订一节）：先问齐产品信息表 → 调研买家顾虑 → 先出 2 张样图等确认（用户说「直接出全套」才跳过）→ 每张图写做图理由（design_rationale.md）→ 手机缩略图与本土化检查；出图后跑 `amazon-listing-image-prompts/image_qc.py`。AI 生成图（尤其带人像）要写入 AI 元数据（`amazon-listing-image-prompts/write_ai_metadata.py`）。

