---
name: etsy-keyword-database
description: >-
  当用户要构建/更新 Etsy 关键词库、查 Etsy 关键词竞争度（Listing 数、均价）、导入 EverBee
  CSV、计算蓝海指数、同步到飞书多维表或筛选 Etsy 蓝海词时使用。
---
# Etsy 关键词库

1. 先用 Read 完整读取 `etsy-keyword-database/SKILL_FULL.md`（完整方法论、脚本用法、蓝海指数规则）。
2. 严格按其中步骤执行；脚本在 `etsy-keyword-database/`，Python 用 `python`；Etsy API 用环境变量 ETSY_API_KEY 和 ETSY_SHARED_SECRET，绝不打印。
3. 写飞书多维表前默认 dry-run，确认目标后才 `--live`；新建的表要把所有权转给用户。
