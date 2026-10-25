# fbm-custom-seller-skills

面向 **FBM 定制/个性化产品卖家**（亚马逊 + Etsy）的 AI 助手技能库：选品调研、需求验证、关键词、Listing 撰写与诊断、图片 Prompt、广告诊断、关键词自然排名日报等。

> 本仓库为脱敏副本：所有密钥、Token、飞书 App ID / open_id / 多维表格 token、店铺名、真实 ASIN 等均已移除或替换为 `<YOUR_...>` / `B0XXXXXXX1` 之类占位符。凭据一律通过环境变量提供，见 `.env.example`。

## 目录约定

每个技能一个目录：

- `<skill>/SKILL.md` —— 入口指针（给 Agent 的简短触发说明，指向 SKILL_FULL.md）
- `<skill>/SKILL_FULL.md` —— 完整方法论、步骤、判断标准、输出模板
- 其余为脚本 / references / examples / templates
- `_shared/` —— 公共脚本：`feishu_bitable.py`（飞书多维表格客户端，默认 dry-run 友好）、`sorftime_http.py`（Sorftime MCP HTTP 客户端）、`samples/`（Sorftime 返回样例）
- `tools/amazon-keyword-rank/` —— 亚马逊关键词自然排名每日追踪工具

文档中的路径均为**相对仓库根目录**（如 `amazon-ads-diagnostics/ads_csv_analyzer.py`），报告默认输出到 `reports/`（已 git 忽略）。

## 技能列表

| 技能 | 一句话用途 | 入口文件 | 依赖 / 需要 |
|---|---|---|---|
| amazon-aba-keyword-monitor | 每周 ABA 热搜词监测，发现类目潜力爆发词，可写入飞书多维表 | `SKILL.md` → `SKILL_FULL.md`；`main.py` | httpx, selectolax, jinja2；`SORFTIME_KEY`；飞书（可选）；类目数据目录 `data/<slug>/` 需自行初始化（`category_init.py`） |
| amazon-ads-diagnostics | SP 广告诊断（Campaign 健康度、ACOS/CTR/CVR、P0/P1/P2 调价/否词/暂停） | `SKILL_FULL.md`；`ads_csv_analyzer.py`、`ads_to_lark.py` | pandas, openpyxl；广告后台导出报表 CSV/XLSX；飞书（可选） |
| amazon-keyword-analyzer | 从词根 + 竞品 ASIN 构建关键词库（分类、词频、否词、广告分组、埋词） | `SKILL_FULL.md`；`build_keyword_library.py`、`amazon_autocomplete.py` | openpyxl；Sorftime MCP |
| amazon-listing-checker | 单 ASIN 证据化 Listing 诊断（7 维评分、改进建议、重写文案） | `SKILL_FULL.md` | Sorftime MCP / 浏览器 |
| amazon-listing-health-checker | Listing 健康检查/上架验收/巡检（狗页、购物车、Customize Now、BSR、搜索可见性） | `SKILL_FULL.md`；`fetch_amazon_page.py`、`fetch_amazon_search.py` | curl、bs4 |
| amazon-listing-image-prompts | 根据产品实物照片规划主图/辅图/A+ 图并生成英文 Prompt | `SKILL_FULL.md`；`render_image_prompts_html.py` | 标准库 |
| amazon-listing-writer | 写/重写完整 Listing（标题、五点、描述、Search Terms、A+），A9/Rufus/COSMO 适配 + 违禁词校验 | `SKILL_FULL.md`；`validate_listing.py`、`render_listing_html.py` | 标准库；Sorftime MCP（可选） |
| amazon-rufus-qa-tester | Rufus/COSMO 适配性测评（95 分制评分卡、问答模拟、改进方案） | `SKILL_FULL.md` | Sorftime MCP / 浏览器 |
| custom-product-research | 定制化（或通用）品类完整市场调研，交付 MD + HTML + Excel + Dashboard | `SKILL_FULL.md`；`scripts/render_deliverables.py` | openpyxl；Sorftime MCP；通用模式见 `references/generic_mode_SKILL.md` |
| etsy-keyword-database | 构建/更新 Etsy 关键词库，计算蓝海指数，同步飞书多维表 | `SKILL_FULL.md`；`fetch_etsy_data.py`、`import_everbee.py`、`sync_to_lark.py` | `ETSY_API_KEY`、`ETSY_SHARED_SECRET`；飞书（可选）；EverBee CSV（可选） |
| etsy-listing-writer | Etsy Listing 撰写流程设计文档 + 辅助脚本（设计中） | `DESIGN.md`；`scripts/` | `ETSY_API_KEY`、`ETSY_SHARED_SECRET`；EverBee 导出 |
| feature-demand-validator | 上新前验证产品/功能的真实需求（评论、关键词、社区、Pinterest、Etsy、TikTok、1688），输出判定报告 + CSV | `SKILL_FULL.md`；`scripts/` | 标准库；Sorftime MCP；功能模式见 `references/feature_mode_SKILL.md` |
| youtube-notebook-summarizer | YouTube 视频抓字幕并生成中文长文笔记 | `SKILL_FULL.md`；`fetch_youtube_transcript.py` | youtube-transcript-api |

### tools/amazon-keyword-rank

亚马逊美国站关键词**自然排名**（不含广告）每日追踪：按变体家族匹配、10001 邮编定位、断点续跑，结果写入飞书多维表格并推送日报。

| 文件 | 用途 |
|---|---|
| `kws.example.py` | ASIN → 关键词清单示例；复制为 `kws.py`（已 git 忽略）后填写 |
| `loc.py` | 建立 curl_cffi 会话并把配送地址设为美国 10001（需 `LOC_PROBE_ASIN`） |
| `crawl.py` | 搜索结果页抓取 + 自然位次识别 |
| `variants.py` / `rescore_variants.py` | 变体家族匹配（读取本地 `variants.json`，已忽略）/ 旧日志重算 |
| `report.py` | 生成 CSV / XLSX 报表 |
| `daily_rank.py` | 每日主流程：抓取 → 对比 → 写飞书多维表（需已有名为「排名历史」的表，或设置 `FEISHU_RANK_HIST_TABLE_ID`） |
| `feishu_notify.py` / `feishu_send.py` / `feishu.py` / `fsbt.py` | 飞书日报推送 / 消息发送 / API 基础 / 多维表格客户端 |

依赖：curl_cffi、beautifulsoup4、lxml、pandas、openpyxl；环境变量 `FEISHU_APP_ID`、`FEISHU_APP_SECRET`、`FEISHU_RANK_BITABLE_TOKEN`、`FEISHU_SCOUT_*`。

## 快速开始

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 填入你自己的值，切勿提交
set -a && source .env && set +a
```

## 安全约定

- 密钥只从环境变量读取，脚本不会打印；不要把任何 Token、Cookie、Authorization 头写进文件或产物。
- 写飞书多维表默认 dry-run，确认后才 `--live`；脚本不提供删除表/记录的能力。
- 数据文件（日志、jsonl、xlsx/csv 报表、HTML 快照、上传文件、类目数据库）均已在 `.gitignore` 中排除。

## License

`amazon-aba-keyword-monitor/` 保留其 MIT License（Copyright (c) 2026，无个人署名）。`feature-demand-validator/` 不再附带上游 License。
