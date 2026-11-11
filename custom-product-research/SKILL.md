---
name: custom-product-research
description: >-
  当用户要对定制化/个性化品类（或任意亚马逊品类）做完整市场调研、决定是否真正上架时使用：第一关先用 Sorftime
  专利工具做专利审核（每日新品推荐不用），再做 Top100 竞品拆解、Etsy 对标、VOC 评论分析、定价模型、机会结论，交付
  MD+HTML+Excel+Dashboard。
---
# 定制品类市场调研

1. 第一关：如果使用者已经接入 Sorftime 的专利查询，先做专利审核，有明显侵权风险就先停下报告给用户。没有这个工具就写明「未取得」，不要编造。每日新品推荐不跑这一关。
2. 用 Read 完整读取 `custom-product-research/SKILL_FULL.md`（完整方法论、数据管线、输出模板）；非定制品类再读 `custom-product-research/references/generic_mode_SKILL.md`。
3. 严格按其中步骤执行。文中的相对路径 `custom-product-research/...` 和 `_shared/...` 都相对仓库根目录；Python 用 `python`。
4. 环境里没有 SORFTIME_KEY 时不要用 `_shared/sorftime_http.py`。Etsy 用 Etsy Open API v3（需要 ETSY_API_KEY 和 ETSY_SHARED_SECRET，绝不打印；没有就标注 Etsy 数据缺失）。
5. 不编造数据，估算注明是估算。若 `custom-product-research/` 不存在，先告诉用户仓库里没有这份资料，不要凭记忆硬做。
