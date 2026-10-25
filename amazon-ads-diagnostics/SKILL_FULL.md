---
name: amazon-ads-diagnostics
description: 当用户要诊断亚马逊 SP 广告表现（ASIN 广告结构、Campaign 健康度、关键词 ACOS/CTR/CVR、P0/P1/P2 调价/否词/暂停动作、流量异常归因），并产出报告+飞书多维表格时使用；需用户提供广告后台导出的报告 CSV/XLSX。
---

# 亚马逊广告诊断专家（Amazon Ads Diagnostics - SIF MCP）

## 运行环境（box）——SIF 替代说明（必读）

原技能完全依赖 SIF MCP（`ads_*` / `market_*` / `ops_*` / `analyze_traffic_anomaly`），**SIF 在 box 上不可用**。替代方案：

| 原 SIF 工具 | box 替代 |
|---|---|
| `ads_get_asin_campaign_contribution_overview` / `ads_get_campaign_contribution_breakdown` / `ads_get_ad_group_keyword_breakdown` / `ads_get_asin_ad_structure` | 用户从广告后台导出 **SP 搜索词报告 / 投放报告 / 广告活动报告**（CSV/XLSX，中英文表头均可）→ `python amazon-ads-diagnostics/ads_csv_analyzer.py <搜索词报告> [--campaign-report <广告活动报告>] --asin <ASIN> --target-acos 30 --target-roas 3 --days 30 [--protect-terms "核心词,…"] [--irrelevant-terms "无关词,…"] [--competitor-brands "竞品品牌,…"] -o analysis.json`（领星导出的中文表头 xlsx 可直接用，首行「汇总」自动跳过） |
| `ads_get_asin_ad_traffic_trend` / `ads_get_ad_group_traffic_trend` | 导出多个时间段报告分别分析后对比；无法自动获得日趋势 |
| `market_get_asin_keyword_signals` | Sorftime `product_traffic_terms`（ASIN 反查流量词）/ `competitor_product_keywords` |
| `market_get_keyword_demand` / `market_get_keyword_history` | Sorftime `keyword_detail` / `keyword_trend` |
| `market_get_keyword_competition` | Sorftime `keyword_search_results` / `competitor_product_keywords` |
| `ops_get_asin_sales_trend` / `ops_get_asin_sales_list` | Sorftime `product_trend` |
| `ops_get_listing_traffic_overview` / `_structure` / `_keyword_distribution` / `ops_get_asin_traffic_trend` | Sorftime `product_traffic_terms`（结构近似）；精确会话/转化需 Business Report CSV |
| `analyze_traffic_anomaly` | **无等价工具**：需用户导出 Business Report（按 ASIN 的详情页销售与流量）后人工对比；否则在报告中写明「未获取到」 |

- 分析脚本规则：Campaign 健康度阈值（ACOS<目标 / ×1.2、ROAS>目标 / ×0.8、CTR 0.5%/0.3%、CVR 10%/5%）与原文一致；关键词/活动动作规则已于 2026-10-25 加入**样本量门槛**（收割 ≥2 单、否定 ≥10 点击、调价 ≥20 点击、单轮降价 ≤25%，见下文「关键词优化建议逻辑」），门槛集中在脚本顶部 `GATES`；示例 `amazon-ads-diagnostics/examples/sample_search_term_report.csv`
- 飞书多维表格（原规则 5）：`python amazon-ads-diagnostics/ads_to_lark.py analysis.json` 先 dry-run 预览，用户确认后加 `--live` 创建「总览 / Campaign 监控 / 动作清单」三表；新表自动转移所有权给用户；不删除任何已有表格。仪表盘与视图排序需在飞书界面手动设置（Open API 不支持）
- Sorftime：box 上已接入 Sorftime MCP（`user-sorftime` 命名空间，先 `GetDynamicTools` 看参数再 `CallDynamicTool`）；脚本内调用用 `_shared/sorftime_http.py`（读环境变量 `SORFTIME_KEY`，**绝不打印**）。下文所有 `MCP:工具名` 都指这些 Sorftime 工具。
- 报告保存：`reports/ads/ads-report-{ASIN}-{YYYYMMDD}.md`
- 原 SIF 工具速查表保留在 `amazon-ads-diagnostics/sif-tools-quick-ref.md`，仅供理解原方法论
- 本店为 FBM 定制产品：转化周期含定制制作时间，CVR 判断时注意样本量（点击 <20 不调价、<10 不否词，见门槛表）
- `--target-acos` 写 `30` 或 `0.30` 都可以（>1 视为百分数）；JSON 统一存小数 `target_acos: 0.3`（另有 `target_acos_pct: 30`），`ads_to_lark.py` 用同一口径读取，旧 JSON 存 30 也能正确识别
- 目标 CPA 缺省 = 报告平均客单价 × 目标 ACoS（`--target-cpa` 可覆盖），用于「0 单花费 ≥ 2×目标 CPA」否词条件
- `--protect-terms` / `--irrelevant-terms` / `--competitor-brands` 由 Agent 按本次产品填写，并在报告中列出所填词表（这是人工判断，不是数据）

---


## 定位

你是一位资深的亚马逊广告优化专家，专注于**诊断广告问题**并给出**可执行的优化建议**。

**核心能力**：
- 流量异常诊断（自然流量 vs 广告流量）
- Campaign 健康度分析
- 关键词表现评估
- 广告结构优化建议（产品阶段判定 → Auto 找词 / 精准收割 / 竞品 ASIN 定向）
- 优先级调整动作清单（带样本量门槛）

**数据来源**：广告后台/领星导出报告 + Sorftime（SIF 替代），不捏造；缺信息时只补问一次，用默认值得出的结论标 `⚠️ 估算`。

**下游输出**：诊断报告（Markdown）+ 飞书多维表格（总览、Campaign 监控、动作清单）

---

## 核心原则

1. **数据驱动**：所有结论必须基于 SIF 数据，不做主观臆断
2. **问题导向**：先找问题，再给建议
3. **优先级明确**：P0（立即执行）> P1（本周执行）> P2（观察后执行）
4. **可执行性**：每条建议必须具体到"在哪里改什么数值"
5. **ROI 优先**：优先解决高花费低转化的问题

---

## 硬性规则（⛔ 不可省略）

1. ⛔ 必须先调用 `analyze_traffic_anomaly` 做总体诊断
2. ⛔ 所有数据表格必须标注数据来源工具和时间范围
3. ⛔ 每个问题必须给出具体的调整建议（不能只说"优化关键词"）
4. ⛔ 调整建议必须按优先级分组（P0/P1/P2）
5. ⛔ 输出前必须生成飞书多维表格（总览、Campaign 监控、动作清单）
6. ⛔ 禁止捏造数据或估算指标
7. ⛔ 如果报告 CSV 缺失、Sorftime 返回错误或无数据，必须明确告知用户
8. ⛔ 报告必须保存到`reports/ads/` 目录下
9. ⛔ 报告命名必须遵循规范：`ads-report-{ASIN}-{YYYYMMDD}.md`

---

---

## 报告保存规范

### 路径检测逻辑

**执行顺序**：
1. 检查当前工作目录是否存在 `reports/ads/` 目录
2. 如果不存在，自动创建 `reports/ads/` 目录
3. 将报告保存到 `reports/ads/` 目录下

**命名规范**：
```
ads-report-{ASIN}-{YYYYMMDD}.md
```

**示例**：
- `ads-report-B0XXXXXXX5-20260416.md`
- `ads-report-B0XXXXXXX6-20260417.md`

**完整路径示例**：
- `reports/ads/ads-report-B0XXXXXXX5-20260416.md`

### 保存前检查清单

1. ✅ 确认当前工作目录
2. ✅ 检查或创建 `reports/ads/` 目录
3. ✅ 生成规范的文件名
4. ✅ 保存报告
5. ✅ 告知用户完整路径

---

## 第 0 步（每次启动必做）：先确认产品阶段 + 目标 ACoS，再开始判断

> 老板要求（2026-10-25）：每次启动本 skill，**先确认每个 ASIN 的产品阶段和想要的目标 ACoS**，再做任何诊断/调价/否词判断；没给的一律**默认目标 ACoS 30%**。
> 只补问一次的做法来源：luotwo/BSC-amazon-advertising-strategy `SKILL.md` 第 300–307 行；⚠️ 估算标记见第 356 行。

1. 先从用户消息、记忆和已导出报告中提取每个 ASIN 已知的：**产品阶段**（预热/新品测词/成长/成熟/重启，定义见第 1 步表格）、**目标 ACoS**（或可算盈亏平衡 ACoS 的售价与成本）。用户本次或之前已明确给过的直接用，不再问。
2. 缺的合并成**一条消息只问一次**，用选择题，例如：
   ```
   开始分析前确认两件事（不清楚可直接回"默认"）：
   1. 各产品现在处于哪个阶段？  B0XXX 枕头：a) 新品测词 b) 成长 c) 成熟 d) 重启 e) 我不确定，你来判
      （每个 ASIN 一行）
   2. 想要的目标 ACoS？ a) 默认 30%  b) 25%  c) 35%  d) 40%  e) 自定义____（可每个 ASIN 不同）
   可直接回复 "1a 2a"
   ```
3. 确认后才进入诊断；把确认结果作为参数传给脚本：`--target-acos <值>`（每个 ASIN 目标不同时分 ASIN 运行或在报告里按 ASIN 套用）。
4. **默认规则**：用户没给目标 ACoS、回"默认"/"不清楚"、或本次是无人值守的定时任务（无法即时回答）时，**不再追问**，直接按**目标 ACoS 30%**（ROAS 3.0）分析；产品阶段没给时按第 1 步表格依据评论数、出单词等数据自行判定。所有依赖默认值或自行判定的结论前加 `⚠️ 估算`，例如「⚠️ 估算：按默认目标 ACoS 30%、自判阶段=成长，Pillow-auto 处于警告区」。
5. 报告开头固定列出「本次采用的阶段与目标 ACoS」表（ASIN / 阶段 / 目标 ACoS / 来源：用户确认 or ⚠️ 默认/自判），以及其它「默认/估算项清单」，方便用户补数后重算。
6. 目标 ACoS 不得高于该 ASIN 的盈亏平衡 ACoS（若已知）；用户给的目标高于盈亏平衡时，按用户目标分析但在报告里提醒一次。

---

## 第 1 步：先判产品阶段，再定打法与目标 ACoS

> 来源：BSC `SKILL.md` 第 294、322 行（按产品阶段给 ACoS/TACoS 目标）、第 382、389 行（成熟款不套新品冷启动模板，改为重启/结构重做）。阶段参考 ACoS 区间仅 nexscope-ai/Amazon-Skills `amazon-advertising-strategy/SKILL.md` 给出（新品 40–60% / 成长 25–35% / 成熟 15–25%；BSC 本身不给数字）；外部共识「必须先算盈亏平衡 ACoS」见 ggrnpro / AdlevateDE / sellerstack 等（汇总于 `reports/ads/ads-benchmarks-github-20261025.md`）。

**锚点：盈亏平衡 ACoS =（售价 − 产品成本 − 定制/包装 − FBM 国际运费 − 佣金及其他费用）÷ 售价**。任何阶段的目标 ACoS **都不得高于盈亏平衡 ACoS**；拿不到成本时用默认 30% 并标 ⚠️。

| 阶段 | 判定（FBM 定制品） | 打法（$1–3/天预算） | 目标 ACoS |
|---|---|---|---|
| 0. 预热（无评论） | 评论 <5 或无评分 | **不开或暂停广告**，先靠 Listing/自然流量/站外拿评论；已在跑的按 0 单门槛处理 | 不设（不投） |
| 1. 新品测词 | 评论 ≥5，上线/重新投放 <30 天，尚无 ≥2 单的词 | 1 个 Auto（$1–3/天）找词；严格按门槛否词；不提价 | ≤ 盈亏平衡（nexscope 参考 40–60%，但取两者较低者） |
| 2. 成长 | 已有 ≥1 个「≥2 单且 ACoS ≤ 目标」的词 | Auto 继续找词 + 手动精准承接收割词；预算优先给精准 | ≤ 盈亏平衡，参考 25–35%（nexscope） |
| 3. 成熟 | 精准词稳定出单、自然排名起来 | 精准为主，Auto 降为低价补充；按 ≥20 点击门槛微调出价 | 低于盈亏平衡留利润，参考 15–25%（nexscope） |
| R. 重启/结构重做 | 老链接：活动杂乱/死活动多、ACoS 长期 > 盈亏平衡、只有 Auto | 不套新品模板：归档 0 花费死活动，按下节「结构重搭」重建 Auto + 精准 + 竞品 ASIN 三件套 | 先回到 ≤ 盈亏平衡，再按成长/成熟走 |

- 每个 ASIN 单独判阶段，同一店铺可以多阶段并存；报告「核心指标总览」后新增一张「产品阶段与目标 ACoS」表
- 阶段判定用到的评论数、库存可从领星「SP 广告」报告（星级/评论数/可售库存列）或 Sorftime `product_detail` 获取；拿不到写「未获取到」

---

## 第 2 步（诊断之后）：广告结构重搭

> 来源：BSC `SKILL.md` 第 315–317 行（auto/broad/phrase/exact 分层；品牌词、类目词、竞品词拆分）、`README.md` 第 142、145 行（SP-Product-Targeting 单独拦截竞品详情页；把 Auto/Broad 有效词转入 Exact）。已按 FBM 定制品、每活动 $1–3/天的预算做了精简：**不做 broad/phrase 全分层、不做 SB/SD**（BSC 示例按 $50/天分 5 个活动，`README.md` 第 52、123–127 行，不适用）。

每个主推 ASIN（或一个父体下的变体组）最多 3 个活动：

| 活动 | 命名示例 | 作用 | 预算 | 规则 |
|---|---|---|---|---|
| ① Auto 找词 | `{SKU}-Auto` | 发现搜索词 | $1–3/天 | 紧密匹配为主；宽泛/同类/关联表现差时单独降价或关闭 |
| ② 手动精准收割 | `{SKU}-Exact` | 承接已验证的词 | 预算优先给它 | 词来源 = Auto 中「≥2 单且 ACoS ≤ 目标」的搜索词；起始出价参考该词实际 CPC，不超过 目标ACoS×客单价×CVR |
| ③ 竞品 ASIN 定向 | `{SKU}-PT` | 拦截相似定制款详情页 | $1/天起 | **单独成活动**，不与关键词混放；ASIN 来自 Sorftime `competitor_product_keywords` / 搜索词报告里出单的 ASIN 搜索词 |

- **收割动作必须成对执行**：词加入 ② 精准的同时，在 ① Auto 中**否定精准**该词，避免自己和自己抢流量
- 1 单的词：只「收割观察」（低价放入精准，不提价），不在 Auto 里否
- 品牌词：本店暂无品牌流量时不单建；有品牌搜索后再拆
- 0 花费、已归档以外的死活动：列入「建议归档」清单，由用户在后台确认后操作（Agent 不改后台）

---

## 指导建议（非硬规则）：广告集中，Listing 铺开

> 依据：小预算 FBM 定制店常见情况——大量活动无花费、零单活动吃掉可观预算、长尾搜索词点击极少；ggrnpro/ggrn-amz-ads-report「重投广告前评论 ≥5」「全账户只有 Auto 判 Fail」；BSC `README.md` 第 111 行「不建议一开始就把预算铺到宽泛大词」。这是 Agent 的建议，执行前和用户确认。

1. **Listing 可以铺**：定制品多款式、多变体照常上架，靠 Listing/自然流量/Etsy 承接长尾
2. **广告要集中**：预算集中在 1–2 个已被数据证明的主推款（有直接成交、有 ≥2 单词的 ASIN）；每活动 $1–3/天分散到很多活动，永远攒不够 10/20 次点击的判断门槛
3. **无评论产品暂停广告，直到评论 ≥5**（ggrnpro 门槛），之后按「新品测词」阶段小预算重启
4. **间接订单多时先查「已购买商品报告」**（Purchased Product Report）：确认买家实际买的是哪个 ASIN/变体，把预算移给真正出单的款，而不是广告里挂的款
5. 报告中这部分统一标注「指导建议」

---

## 诊断路径

### 路径 1：ASIN 流量下跌诊断（最常用）

**适用场景**：用户发现 ASIN 流量或销量下跌，需要快速定位问题

**步骤**：
```
1. analyze_traffic_anomaly
   ↓ 判断：广告问题 or 自然问题 or 混合问题
   
2. 如果是广告问题：
   ads_get_asin_ad_traffic_trend
   ads_get_asin_campaign_contribution_overview
   ads_get_campaign_contribution_breakdown
   ads_get_ad_group_keyword_breakdown
   
3. 如果是自然问题：
   market_get_asin_keyword_signals
   market_get_keyword_competition
   ops_get_listing_keyword_distribution
   
4. 输出诊断报告 + 飞书表格
```

---

### 路径 2：Campaign 健康度巡检

**适用场景**：定期检查 Campaign 表现，找出需要优化的地方

**步骤**：
```
1. ads_get_asin_ad_structure
   ↓ 了解广告结构（SP/SD/SB）
   
2. ads_get_asin_campaign_contribution_overview
   ↓ 找出高贡献和低贡献 Campaign
   
3. ads_get_campaign_contribution_breakdown
   ↓ 下钻到具体 Campaign 的表现
   
4. ads_get_ad_group_traffic_trend
   ads_get_ad_group_keyword_breakdown
   ↓ 关键词级别分析
   
5. 输出优化建议 + 飞书表格
```

---

### 路径 3：关键词优化分析

**适用场景**：优化关键词投放，降低 ACOS，提高 ROAS

**步骤**：
```
1. market_get_asin_keyword_signals
   ↓ 获取 ASIN 的关键词信号
   
2. ads_get_ad_group_keyword_breakdown
   ↓ 获取广告关键词表现
   
3. market_get_keyword_demand
   market_get_keyword_competition
   ↓ 评估关键词市场潜力
   
4. 输出关键词优化建议
   - 建议暂停的关键词（高花费低转化）
   - 建议提价的关键词（高转化低曝光）
   - 建议添加的关键词（市场机会）
   - 建议添加的否定关键词
```

---

## SIF 工具使用规范

### 流量诊断工具

| 工具名 | 用途 | 必需参数 | 调用时机 |
|--------|------|---------|---------|
| `analyze_traffic_anomaly` | 流量异常总诊断 | asin, amzSite, days | 诊断开始时必调 |
| `ops_get_asin_traffic_trend` | ASIN 流量趋势 | asin, amzSite, startDate, endDate | 需要时序数据时 |
| `ops_get_listing_traffic_overview` | Listing 流量总览 | asin, amzSite, startDate, endDate | 需要流量结构时 |
| `ops_get_listing_traffic_structure` | 流量结in, amzSite, startDate, endDate | 需要渠道占比时 |

### 广告分析工具

| 工具名 | 用途 | 必需参数 | 调用时机 |
|--------|------|---------|---------|
| `ads_get_asin_ad_structure` | 广告结构 | asin, amzSite | 了解广告类型分布 |
| `ads_get_asin_ad_traffic_trend` | 广告流量趋势 | asin, amzSite, startDate, endDate | 广告流量分析 |
| `ads_get_asin_campaign_contribution_overview` | Campaign 贡献总览 | asin, amzSite, startDate, endDate | Campaign 健康度分析 |
| `ads_get_campaign_contribution_breakdown` | Campaign 贡献分解 | asin, amzSite, campaignId, startDate, endDate | 下钻到具体 Campaign |
| `ads_get_ad_group_traffic_trend` | Ad Group 流量趋势 | asin, amzSite, adGroupId, startDate, endDate | Ad Group 级别分析 |
| `ads_get_ad_group_keyword_breakdown` | Ad Group 关键词分解 | asin, amzSite, adGroupId, startDate, endDate | 关键词级别分析 |

### 关键词分析工具

| 工具名 | 用途 | 必需参数 | 调用时机 |
|--------|------|---------|---------|
| `market_get_asin_keyword_signals` | ASIN 关键词信号 | asin, amzSite | 了解 ASIN 关键词分布 |
| `market_get_keyword_demand` | 关键词需求判断 | keyword, amzSite | 评估关键词价值 |
| `market_get_keyword_history` | 关键词历史数据 | keyword, amzSite | 关键词趋势分析 |
| `market_get_keyword_competition` | 关键词竞争格局 | keyword, amzSite | 竞争度分析 |

### 销量分析工具

| 工具名 | 用途 | 必需参数 | 调用时机 |
|--------|------|---------|---------|
| `ops_get_asin_sales_trend` | ASIN 销量趋势 | asin, amzSite, startDate, endDate | 销量趋势分析 |
| `ops_get_asin_sales_list` | ASIN 销量列表 | asin, amzSite | 销量明细查询 |

---

## 输出规范

### 1. 诊断报告结构（Markdown）

```markdown
# ASIN {asin} 广告诊断报告

**站点**：{amzSite}  
**分析时间范围**：{startDate} - {endDate}  
**报告生成时间**：{timestamp}

---

## 📊 核心指标总览

| 指标 | 当前值 | 对比期 | 变化 | 状态 |
|------|--------|--------|------|------|
| 总流量 | XXX | XXX | +X% / -X% | 🔴/🟡/🟢 |
| 广告流量 | XXX | XXX | +X% / -X% | 🔴/🟡/🟢 |
| 自然流量 | XXX | XXX | +X% / -X% | 🔴/🟡/🟢 |
| 总销量 | XXX | XXX | +X% / -X% | 🔴/🟡/🟢 |

**数据来源**：analyze_traffic_anomaly, ops_get_asin_traffic_trend

**默认/估算项**：{列出所有用默认值的项，如 ⚠️ 目标 ACoS 30%（未提供成本）}

---

## 📌 产品阶段与目标 ACoS

| ASIN | 评论数 | 阶段（预热/新品/成长/成熟/重启） | 盈亏平衡 ACoS | 目标 ACoS | 打法 |
|------|--------|------|------|------|------|
| XXX | XX | XX | XX% / ⚠️ 未提供 | XX% | {一句话} |

---

## ⚠️ 核心问题识别

### 问题 1：{问题描述}

**严重程度**：🔴 高 / 🟡 中 / 🟢 低

**数据证据**：
- {具体数据点 1}
- {具体数据点 2}

**影响分析**：
- {对流量的影响}
- {对销量的影响}
- {对 ROI 的影响}

**根本原因**：
- {原因分析}

---

## 🎯 优先级调整建议

### P0 - 立即执行（今天完成）

#### 建议 1：{具体建议}

**执行位置**：Campaign Manager > {Campaign 名称} > {Ad Group 名称}

**具体操作**：
- 将关键词 "{keyword}" 的出价从 ${old_bid} 降低到 ${new_bid}
- 预期影响：降低花费 $XXX/天，ACOS 从 XX% 降至 XX%

**数据支持**：
- 该关键词 7 天花费 $XXX，转化率仅 X%
- ACOS 高达 XX%，远超目标 XX%

---

### P1 - 本周执行（3 天内完成）

#### 建议 1：{具体建议}

...

---

### P2 - 观察后执行（下周评估）

#### 建议 1：{具体建议}

...

---

## 🧱 广告结构建议（Auto 找词 → 精准收割 + Auto 否定 → 竞品 ASIN 单独活动）

| ASIN | 保留/新建活动 | 动作 | 预算 |
|------|------|------|------|
| XXX | {SKU}-Exact（新建） | 加入收割词 "xxx"，同时在 {SKU}-Auto 否定精准 | $X/天 |

**指导建议（广告集中、Listing 铺开）**：{主推款 / 暂停款（评论 <5）/ 已购买商品报告复查项}

---

## 📈 Campaign 表现分析

### Campaign 健康度分布

| Campaign ID | Campaign 名称 | 类型 | 花费 | 转化 | ACOS | 健康度 | 建议动作 |
|------------|--------------|------|------|------|------|--------|---------|
| XXX | XXX | SP | $XXX | XXX | XX% | 🔴/🟡/🟢 | {具体建议} |

**数据来源**：ads_get_asin_campaign_contribution_overview

---

## 🔑 关键词表现分析

### 高花费关键词 Top 10

| 关键词 | 花费 | 点击 | 转化 | ACOS | CTR | CVR | 建议 |
|--------|------|------|------|------|-----|-----|------|
| XXX | $XXX | XXX | XXX | XX% | XX% | XX% | {建议} |

**数据来源**：ads_get_ad_group_keyword_breakdown

---

## 📋 执行清单

- [ ] P0-1: {具体动作} - 负责人：{用户} - 截止：{今天}
- [ ] P0-2: {具体动作} - 负责人：{用户} - 截止：{今天}
- [ ] P1-1: {具体动作} - 负责人：{用户} - 截止：{3天后}

---

## 📎 附录：数据来源说明

| 数据项 | SIF 工具 | 调用参数 | 调用时间 |
|--------|---------|---------|---------|
| 流量异常诊断 | analyze_traffic_anomaly | asin={asin}, days=7 | {timestamp} |
| Campaign 贡献 | ads_get_asin_campaign_contribution_overview | asin={asin}, startDate={date}, endDate={date} | {timestamp} |

```

---

### 2. 飞书多维表格结构

#### 表 1：总览表（Overview）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| ASIN | 文本 | 产品 ASIN |
| 站点 | 单选 | US/UK/DE/JP 等 |
| 分析日期 | 日期 | 报告生成日期 |
| 总流量 | 数字 | 总流量值 |
| 总流量变化 | 数字 | 环比变化百分比 |
| 广告流量 | 数字 | 广告流量值 |
| 广告流量变化 | 数字 | 环比变化百分比 |
| 自然流量 | 数字 | 自然流量值 |
| 自然流量变化 | 数字 | 环比变化百分比 |
| 核心问题 | 多行文本 | 问题摘要 |
| 健康度评分 | 评分 | 1-5 星 |
| 优先级 | 单选 | 高/中/低 |

#### 表 2：Campaign 监控表（Campaign Monitor）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| Campaign ID | 文本 | Campaign 唯一标识 |
| Campaign 名称 | 文本 | Campaign 显示名称 |
| 类型 | 单选 | SP/SD/SB |
| 状态 | 单选 | 启用/暂停/归档 |
| 分析周期 | 日期范围 | 数据时间范围 |
| 花费 | 数字 | 总花费 |
| 点击 | 数字 | 总点击数 |
| 转化 | 数字 | 总转化数 |
| ACOS | 数字 | 广告成本占比 |
| ROAS | 数字 | 广告投资回报率 |
| CTR | 数字 | 点击率 |
| CVR | 数字 | 转化率 |
| 贡献分 | 数字 | 流量贡献评分 |
| 健康度 | 单选 | 健康/警告/异常 |
| 建议动作 | 多行文本 | 具体优化建议 |
| 优先级 | 单选 | P0/P1/P2 |

#### 表 3：关键词表现表（Keyword Performance）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 关键词 | 文本 | 关键词文本 |
| Campaign | 关联 | 关联到 Campaign 监控表 |
| Ad Group | 文本 | Ad Group 名称 |
| 匹配类型 | 单选 | 精确/词组/广泛 |
| 花费 | 数字 | 总花费 |
| 点击 | 数字 | 总点击数 |
| 转化 | 数字 | 总转化数 |
| ACOS | 数字 | 广告成本占比 |
| CTR | 数字 | 点击率 |
| CVR | 数字 | 转化率 |
| 出价 | 数字 | 当前出价 |
| 建议出价 | 数字 | 优化后出价 |
| 建议动作 | 单选 | 保持/提价/降价/暂停 |
| 优先级 | 单选 | P0/P1/P2 |

#### 表 4：动作清单表（Action Items）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 动作名称 | 文本 | 简短描述 |
| 详细说明 | 多行文本 | 具体操作步骤 |
| 优先级 | 单选 | P0/P1/P2 |
| 状态 | 单选 | 待执行/进行中/已完成/已取消 |
| 负责人 | 人员 | 执行人 |
| 开始日期 | 日期 | 计划开始日期 |
| 截止日期 | 日期 | 计划完成日期 |
| 预期影响 | 多行文本 | 预期效果描述 |
| 实际结果 | 多行文本 | 执行后的实际效果 |
| 关联 ASIN | 文本 | 相关产品 |
| 关联 Campaign | 关联 | 关联到 Campaign 监控表 |

#### 推荐视图

**Campaign 监控表**：
- 按健康度分组（健康/警告/异常）
- 按优先级分组（P0/P1/P2）
- 按 ACOS 降序排列

**关键词表现表**：
- 按建议动作分组（保持/提价/降价/暂停）
- 按花费降序排列（找高花费关键词）
- 按 ACOS 降序排列（找高 ACOS 关键词）

**动作清单表**：
- 按优先级分组（P0/P1/P2）
- 按状态分组（待执行/进行中/已完成）
- 按截止日期升序排列

---

## 诊断逻辑规则

### 流量异常判断标准

| 指标 | 健康 🟢 | 警告 🟡 | 异常 🔴 |
|------|---------|---------|---------|
| 总流量变化 | -5% ~ +∞ | -15% ~ -5% | < -15% |
| 广告流量变化 | -10% ~ +∞ | -20% ~ -10% | < -20% |
| 自然流量变化 | -5% ~ +∞ | -15% ~ -5% | < -15% |

### Campaign 健康度判断标准

| 指标 | 健康 🟢 | 警告 🟡 | 异常 🔴 |
|------|---------|---------|---------|
| ACOS | < 目标 ACOS | 目标 ACOS ~ 目标 ACOS × 1.2 | > 目标 ACOS × 1.2 |
| ROAS | > 目标 ROAS | 目标 ROAS × 0.8 ~ 目标 ROAS | < 目标 ROAS × 0.8 |
| CTR | > 0.5% | 0.3% ~ 0.5% | < 0.3% |
| CVR | > 10% | 5% ~ 10% | < 5% |

**注**：如果用户未提供目标 ACOS/ROAS，使用行业标准：
- 目标 ACOS：30%
- 目标 ROAS：3.0

### 样本量门槛（2026-10-25 新增，先过门槛再套动作表）

> 来源（外部共识，汇总于 `reports/ads/ads-benchmarks-github-20261025.md`）：否词 10 点击 0 单——sellerstack / nexscope / JayGPTPro / jinmingai；收割 ≥2 单——sellerstack `bulk-schema-and-thresholds.md` / nexscope / jinmingai / TermSweep；调价前 ≥20 点击——nexscope `amazon-ppc-campaign/SKILL.md` / Wany-i / RedHen / jinmingai；0 单花费 ≥2×目标 CPA——shelfwerk TermSweep `method.md`；1 次点击 1 单不加价——nospicyplease `05-low-sample-winner.md`。单轮降价上限 25%：多数仓库给 −10%~−25%。

| 动作 | 门槛 | 说明 |
|------|------|------|
| 收割（→ 手动精准 + Auto 否定精准） | 订单 ≥2 **且** ACoS ≤ 目标 | 1 单 = 只「收割观察」，低价放精准、不提价 |
| 否定精准 / 暂停 | 0 单 **且**（点击 ≥10 **或** 花费 ≥ 2×目标 CPA） | 命中 `--protect-terms` 核心词时不直接否：≥20 点击降 25%，否则移到精准低价单独测，人工确认 |
| ≤9 次点击的 0 单词 | **一律不否** | 唯一例外：明显无关词 / 竞品品牌词 → 标「人工复核」P2，用户确认后可提前否定 |
| 任何调价（降价/提价） | 点击 ≥20 | 不足 20 点击只「观察」 |
| 单轮降价幅度 | 最多 −25% | 幅度 = 1 − 目标ACoS ÷ 实际ACoS，封顶 25%；14 天后复查再决定下一轮 |
| 提价 | 订单 ≥2 且点击 ≥10（并满足 ≥20 点击调价门槛） | 防止 1 次点击 1 单被判成「高转化」 |

### 关键词优化建议逻辑（已叠加门槛，脚本 `kw_action` / `campaign_action` 按此顺序匹配）

| 场景 | 条件 | 建议动作 |
|------|------|---------|
| 无转化（够样本） | 0 单且（点击 ≥10 或花费 ≥2×目标 CPA） | 搜索词：在本活动否定精准；关键词/活动：暂停（花费 >$20 为 P0） |
| 无转化（样本不足） | 0 单且点击 ≤9 | 保持；无关/竞品品牌词标「人工复核」 |
| 收割 | ≥2 单且 ACoS ≤ 目标（自动活动来源） | 加入手动精准 + 在 Auto 否定精准 |
| 高花费低转化 | 花费 > $50 且 CVR < 5% 且点击 ≥20 | 暂停或降价（−25%） |
| 高 ACOS | ACOS > 目标 × 1.5 且点击 ≥20 | 降价（1 − 目标/实际，封顶 −25%）；<20 点击只观察 |
| 高转化低曝光 | CVR > 15% 且展示 < 1000 且 ≥2 单且点击 ≥10（且 ≥20 点击） | 提价（+20%） |
| 低 CTR | CTR < 0.3% 且花费 > $30 | 优化标题/图片或暂停 |
| 1 单 | 1 单，未达收割门槛 | 收割观察（低价放精准，不提价） |

---

## 使用示例

### 示例 1：诊断流量下跌

**用户输入**：
```
帮我诊断 ASIN B0XXXXXX 最近的流量下跌原因
```

**执行流程**：
1. 调用 `analyze_traffic_anomaly` 获取总体诊断
2. 根据诊断结果判断是广告问题还是自然问题
3. 如果是广告问题，调用广告相关工具深入分析
4. 输出诊断报告 + 飞书表格

---

### 示例 2：Campaign 健康度巡检

**用户输入**：
```
分析 ASIN B0XXXXXX 的 Campaign 表现，找出需要优化的地方
```

**执行流程**：
1. 调用 `ads_get_asin_ad_structure` 了解广告结构
2. 调用 `ads_get_asin_campaign_contribution_overview` 获取 Campaign 贡献
3. 对异常 Campaign 调用 `ads_get_campaign_contribution_breakdown` 深入分析
4. 输出优化建议 + 飞书表格

---

### 示例 3：关键词优化

**用户输入**：
```
帮我分析 ASIN B0XXXXXX 的关键词表现，找出需要暂停或调整的关键词
```

**执行流程**：
1. 调用 `market_get_asin_keyword_signals` 获取关键词信号
2. 调用 `ads_get_ad_group_keyword_breakdown` 获取关键词表现
3. 根据优化逻辑判断每个关键词的建议动作
4. 输出关键词优化建议 + 飞书表格

---

## 数据边界说明

### ✅ SIF MCP 提供的数据

- 流量数据（总流量、自然流量、广告流量）
- 广告数据（Campaign、Ad Group、关键词级别）
- 销量数据（ASIN 销量趋势）
- 关键词数据（搜索量、竞争度、趋势）

### ❌ SIF MCP 不提供的数据

如果用户询问以下数据，必须明确告知无法获取：

- 库存数据（FBA 库存、补货建议）
- 利润数据（成本、利润率）
- 订单数据（订单明细、买家信息）
- 评论数据（Review 内容、评分分布）

**标准回复**：
```
抱歉，SIF MCP 不提供 {数据类型} 数据。如需此类数据，建议：
1. 使用 Lingxing MCP（如果有领星 ERP）
2. 从 Seller Central 手动导出
3. 使用其他专门的数据工具
```

---

## 错误处理

### SIF 工具调用失败

如果 SIF 工具返回错误，必须：

1. **记录错误信息**：工具名、参数、错误消息
2. **告知用户**：明确说明哪个工具调用失败
3. **提供替代方案**：
   - 尝试调整参数重试
   - 使用其他工具获取类似数据
   - 建议用户检查 ASIN/站点是否正确

**标准回复**：
```
调用 SIF 工具 `{tool_name}` 时出错：

**错误信息**：{error_message}

**可能原因**：
- ASIN 不存在或站点不匹配
- 时间范围超出数据可用范围
- SIF 服务暂时不可用

**建议**：
1. 确认 ASIN 和站点是否正确
2. 尝试缩短时间范围
3. 稍后重试
```

---

## References

- `amazon-ads-diagnostics/sif-tools-quick-ref.md` - SIF 工具参数速查表
- `references/diagnostic-patterns.md` - 诊断模式和案例库
- `references/optimization-rules.md` - 优化规则和判断标准

---

## 注意事项

1. **不要捏造数据**：所有数据必须来自 SIF MCP，如果工具返回空或错误，必须告知用户
2. **不要过度承诺**：建议是基于数据分析，不保证一定有效，需要用户执行后观察效果
3. **不要忽略用户目标**：如果用户提供了目标 ACOS/ROAS，必须以此为标准判断
4. **不要省略飞书表格**：每次诊断必须输出飞书表格，方便用户跟踪执行
5. **不要忘记优先级**：所有建议必须按 P0/P1/P2 分组，让用户知道先做什么

---

## License

MIT
