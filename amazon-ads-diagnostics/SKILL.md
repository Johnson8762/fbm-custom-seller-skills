---
name: amazon-ads-diagnostics
description: >-
  当用户要诊断亚马逊 SP 广告表现（Campaign 健康度、关键词 ACOS/CTR/CVR、P0/P1/P2
  调价/否词/暂停动作、流量异常归因）并产出报告和飞书多维表时使用；需要广告后台导出的报告 CSV/XLSX。
---
# 亚马逊 SP 广告诊断

0. **每次启动先确认**：每个 ASIN 的产品阶段（预热/新品测词/成长/成熟/重启）和想要的目标 ACoS，合并成一条消息只问一次；已明确给过的不再问。没给、回"默认"或无人值守运行时，**默认目标 ACoS 30%**，阶段按 SKILL_FULL 第 1 步自行判定，相关结论标 `⚠️ 估算`。确认后再做任何判断。
1. 用 Read 完整读取 `amazon-ads-diagnostics/SKILL_FULL.md`（完整方法论、样本门槛、脚本用法、判断标准、输出模板）。
2. 严格按其中步骤执行；脚本和参考资料都在 `amazon-ads-diagnostics/`，Python 用 `python`，`--target-acos` 传第 0 步确认的值。
3. 写飞书多维表前默认 dry-run，确认目标后才 `--live`；不得删除用户的表或记录。
