---
name: amazon-listing-writer
description: >-
  当用户要为亚马逊产品（尤其定制/个性化产品）写或重写完整 Listing（标题、五点、描述、Search Terms、A+/图片框架），并做
  A9/Rufus/COSMO 适配和违禁词校验时使用。
---
# 亚马逊 Listing 撰写

1. 先用 Read 完整读取 `amazon-listing-writer/SKILL_FULL.md`（完整方法论、写作规则、校验与输出模板）。
2. 严格按其中步骤执行；校验和渲染脚本在 `amazon-listing-writer/`，Python 用 `python`（共享 venv）。
3. **标题上限 75 字符 + 商品亮点（Item Highlights）≤125 字符**（亚马逊 2026-07-27 新规；SKILL_FULL 末尾修订一节覆盖上文的 200 字符）；`validate_listing.py` 已按此校验。Brand 无品牌备案时填 Generic，标题首词为你的店铺名 `<YOUR_BRAND>`。

