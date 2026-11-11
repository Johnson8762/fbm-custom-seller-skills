---
name: feature-demand-validator
description: >-
  当用户想在开发/上新前验证一个定制化产品或产品新功能是否有真实市场需求（评论、关键词、社区、Pinterest、Etsy、TikTok、1688
  多维信号，输出判定报告+标准 CSV）时使用。
---
# 需求验证（定制模式默认，单一功能特性用功能模式）

1. 先用 Read 完整读取 `feature-demand-validator/SKILL_FULL.md`（完整方法论、数据管线、输出模板）。验证单个功能特性时再读 `feature-demand-validator/references/feature_mode_SKILL.md`。
2. 严格按其中步骤执行。文中的相对路径 `feature-demand-validator/...` 和 `_shared/...` 都相对仓库根目录；Python 用 `python`。
3. `ali1688_similar_product` 只接受中文 search_name。环境里没有 SORFTIME_KEY 时不要用 `_shared/sorftime_http.py`。
4. 不编造数据；工具估算注明是估算；拿不到的信号标注缺失。密钥绝不打印。
5. 若 `feature-demand-validator/` 不存在，先告诉用户仓库里没有这份资料，不要凭记忆硬做。
