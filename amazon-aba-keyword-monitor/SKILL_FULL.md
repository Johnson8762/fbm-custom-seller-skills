---
name: amazon-aba-keyword-monitor
description: 当用户要做亚马逊 ABA 热搜词/爆品关键词监测（每周例行监测、发现某类目潜力爆发词、给新类目初始化监测词典、或把本周结果写进飞书多维表格）时使用。支持多类目（已有：定制姓名耳环 personalized-name-earrings、定制皮革笔记本 custom-leather-notebook），数据来自 AMZ123 ABA 榜单 + Sorftime。
---

# 亚马逊 ABA 爆品关键词监测（通用多类目版）

从 AMZ123 的亚马逊 ABA 热搜词榜单中抓取关键词，用类目词典 + LLM 分类筛出本类目相关词，按排名变化分 Tier，
Tier1/Tier2 再查 Sorftime（趋势/详情/延伸词），最后写入飞书多维表格（每周追加，积累历史），同时可出本地 HTML 报告。

代码目录：`amazon-aba-keyword-monitor/`（下文简称 `$ABA`）
Python：`python`（下文简称 `$PY`）

## 前提（box 环境）

- 环境变量：`SORFTIME_KEY`（Sorftime MCP key，HTTP 直连，不需 MCP 客户端）、`FEISHU_APP_SECRET`（飞书自建应用，同时需要 `FEISHU_APP_ID`、`FEISHU_OWNER_OPEN_ID`）。**永远不要打印这些值**。
- 不再需要 lark-cli：飞书写入走 Open API（`_shared/feishu_bitable.py`）。
- **新建的多维表格会自动把所有权转给用户**（open_id 来自 `环境变量 FEISHU_OWNER_OPEN_ID`）。脚本只新增表/字段/记录，**绝不删除用户的表格或记录**。
- 每个类目的数据在 `$ABA/data/<slug>/`：`category_config.json`（含已绑定的多维表格 token）、`category_dict.json`、`exclusion_rules.json`、`history.db`（历史排名，SQLite）、`.exchange/`（与 Agent 交换的 JSON）。
- 报告/日志输出：`reports/aba/<slug>/`。

## 快速开始

- 查看已有类目：`$PY $ABA/main.py list`
- 每周例行（以皮革笔记本为例）：依次执行下方 Step1 → Agent 分类 → Step2 → Agent 写摘要 → Step3。
- 先试跑不写飞书：`step3 --dry-run`（只打印并保存 `bitable_dryrun_<周>.json`）。**第一次对某个类目写飞书前，先 dry-run 给用户看。**

所有命令都要带 `--category <slug>`（或设环境变量 `ABA_CATEGORY`）。

## 首次使用：新类目初始化

### Step 0：初始化（非交互）
```bash
$PY $ABA/main.py init --name "定制宠物项圈" --slug custom-pet-collar
```
生成 `$ABA/data/<slug>/.exchange/dict_draft.json`（需要 Sorftime key 已配置）。

### Agent 任务：生成类目词典
读取 `dict_draft.json`，按其中 prompt 生成初始词典和排除规则，写入同目录 `dict_draft_output.json`：
```json
{
  "category_dict": {"ingredients": [...], "benefits": [...], "brands": [...], "health_markers": [...]},
  "exclusion_rules": {"exclude_patterns": [...], "exclude_keywords": [...]},
  "classification_labels": {"description": "各标签含义描述"}
}
```
（字段名沿用原版：ingredients=核心产品/材质词，benefits=功能/场景词，brands=品牌，health_markers=类目标记词。）

### Step 0.5：确认词典
先把词典摘要展示给用户确认，再执行：
```bash
$PY $ABA/main.py init-confirm --category <slug> --yes
```

## 日常监测流程（3 步 + 2 个 Agent 任务）

### Step 1：抓取 + 本地词典匹配
```bash
$PY $ABA/main.py step1 --category <slug>
```
抓取 AMZ123 ABA 榜单（多组排名/涨幅组合 × 默认 5 页），本地词典匹配；可疑词写入 `.exchange/llm_input.json`。
若输出"所有关键词已由本地词典匹配"，可直接进入 Step 2。

### Agent 任务：LLM 分类 + 中文翻译
读取 `$ABA/data/<slug>/.exchange/llm_input.json`，对每个关键词分类并翻译（标签见文件内 prompt），写入同目录 `llm_output.json`：
```json
{"keyword": {"label": "ingredient", "zh": "中文翻译"}, ...}
```

### Step 2：分层 + Sorftime 查询
```bash
$PY $ABA/main.py step2 --category <slug>
```
按排名变化分 Tier（阈值与原版一致，见 `$ABA/config.py`），Tier1 查 keyword_trend + keyword_detail + keyword_extends，Tier2 只查趋势；并发上限 3（`SORFTIME_CONCURRENCY`）。写入 history.db，输出 `.exchange/analysis_input.json`。

### Agent 任务：写分析摘要
读取 `analysis_input.json`，为每个 Tier1 关键词写分析摘要，写入同目录 `analysis_output.json`：
```json
{
  "keyword_analysis": {"keyword": "分析摘要", ...},
  "tracks": [{"name": "赛道名", "icon": "emoji", "keywords": [...], "summary": "描述"}],
  "core_findings": ["发现1", "发现2", ...]
}
```

### Step 3：写入飞书多维表格（必须执行）
```bash
$PY $ABA/main.py step3 --category <slug> --dry-run   # 先预览
$PY $ABA/main.py step3 --category <slug>             # 正式写入
```
- 类目已绑定表格（`category_config.json` 有 bitable_token）→ 复用并追加；旧表缺少的字段/子表只会**新增**，不会删改已有字段。
- 未绑定 → 自动新建多维表格（3 张表 + 2 个筛选视图）并把所有权转给用户，配置写回 `category_config.json`。
- 完成后把多维表格链接发给用户。
- 可选本地 HTML 报告：`$PY $ABA/main.py html --category <slug>`。

## 飞书多维表格结构

| 表名 | 内容 |
|:---|:---|
| 关键词监测 | 主表，每周关键词的排名/搜索量/CPC/爆发类型/AI分析等 17 个字段 |
| 扩展关键词 | Tier1 关键词的延伸变体词 |
| 周报摘要 | 每周一条汇总（抓取数、各 Tier 数量、核心发现） |

筛选视图：**Tier 1 高优先级**、**Tier 2 观察区**（按 Tier 过滤）。

⚠️ box 版限制：飞书 Open API 不支持创建仪表盘，视图的"按排名变化降序"排序也需在飞书界面手动设置一次。原版 5 个图表（关键词总数卡片、Tier 分布饼图、爆发类型饼图、分类分布饼图、周搜索量柱状图）如需要，请让用户在飞书里手动添加仪表盘（一次即可，之后数据自动更新）。

## 测试/限流开关（环境变量）
- `ABA_MAX_COMBOS=1 ABA_MAX_PAGES=1`：只抓 1 组 × 1 页（试跑）
- `ABA_SORFTIME_MAX_TIER1=N` / `ABA_SORFTIME_MAX_TIER2=N`：最多查 N 个（0 = 不查）
- `ABA_REPORT_ROOT`：报告根目录

## 踩坑经验
- **benefit/ingredient 通用词误匹配**：如对讲机类的 "portable/wireless/rechargeable"；定制类目里 "custom/personalized"、耳环里 "crystal" 都会误匹配（例："crystal lake" 被判为耳环词）。在 `exclusion_rules.json` 中加入高频泛品类词/专有名词，或把过泛的词从词典移除。
- Sorftime `keyword_trend` 的 cpc_trend 实际返回为 [yyyyMM, 美元] 二元组（文档写的是分为单位的四元组），解析器两种都兼容。
- httpx 日志会打印带 key 的 URL，main.py 已把 httpx 日志级别调到 WARNING；不要再把它调回 INFO。

## 已有类目参考
- `personalized-name-earrings`（定制姓名耳环）：已绑定用户现有多维表格（主表字段名与本版不同，首次正式写入会新增缺失字段并补建「扩展关键词」「周报摘要」两张表——写入前先告知用户）。
- `custom-leather-notebook`（定制皮革笔记本）：词典来自 Leather 版的完整草稿（ingredients 68 / benefits 48 / brands 15 / markers 35，排除规则 16 条 pattern + 44 个词），尚未绑定表格，首次 step3 会新建。
