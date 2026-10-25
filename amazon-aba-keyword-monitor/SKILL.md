---
name: amazon-aba-keyword-monitor
description: 当用户要做亚马逊 ABA 热搜词/爆品关键词监测（每周例行监测、发现类目潜力爆发词、初始化新类目监测词典、或把结果写进飞书多维表格）时使用。
---
# 亚马逊 ABA 关键词监测

1. 先用 Read 完整读取 `amazon-aba-keyword-monitor/SKILL_FULL.md`（完整方法论、脚本用法、判断标准、输出模板）。
2. 严格按其中步骤执行；脚本和参考数据都在 `amazon-aba-keyword-monitor/`，Python 用 `python`。
3. 写飞书多维表前默认 dry-run，确认目标表后才 `--live`；不得删除用户的表或记录。
