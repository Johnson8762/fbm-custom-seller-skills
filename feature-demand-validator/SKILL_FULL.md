---
name: feature-demand-validator
description: 当用户想在开发/上新前验证一个定制化产品或产品新功能/新特性是否有真实市场需求（Review、关键词、社区、Pinterest、Etsy、TikTok、1688 多维信号，输出判定报告+标准 CSV）时使用；默认定制模式，验证单个功能特性时切换功能模式。
---


## 运行环境（box）——合并说明

本技能合并了原 `custom-validator`（定制化产品需求验证，**默认模式**，正文即此版）与 `zach-feature-demand-validator`（单一功能特性验证，**功能模式**）。
- 功能模式完整流程：`feature-demand-validator/references/feature_mode_SKILL.md`（对应参考文件为 `*_feature.md`，校验脚本 `validate_deliverables_feature.py`）
- 脚本：`feature-demand-validator/scripts/`；Python：`python`；参考：`feature-demand-validator/references/`；示例证据包：`feature-demand-validator/examples/review-source-pack/`
- Sorftime：box 上已接入 Sorftime MCP（`user-sorftime` 命名空间，先 `GetDynamicTools` 看参数再 `CallDynamicTool`）；脚本内调用用 `_shared/sorftime_http.py`（读环境变量 `SORFTIME_KEY`，**绝不打印**）。下文所有 `MCP:工具名` 都指这些 Sorftime 工具。
  - 路线 A（Sorftime 完整版）在 box 上**可用**：`product_reviews`、`keyword_detail` / `keyword_trend` / `keyword_extends`、`tiktok_*`、`ali1688_similar_product`
  - Sorftime 原始返回 → 标准行：`python feature-demand-validator/scripts/sorftime_to_rows.py --type detail|trend|extends --raw raw.json --keyword "<词>" -o rows.json`，再交给 `generate_keyword_csv.py`（AI 只补判断列）
- 社区：WebSearch（Reddit/Quora）或 Sorftime `reddit_post_search` / `quora_question_search`
- Pinterest：WebSearch + WebFetch；被拦时用 box 浏览器
- Etsy：`python etsy-keyword-database/fetch_etsy_data.py`（Etsy v3 API，环境变量 `ETSY_API_KEY`/`ETSY_SHARED_SECRET`，绝不打印）取在售数量与价格带；Etsy API **没有搜索量**
- 输出目录：`reports/feature-validation/<产品或功能>_<日期>/`
- 原 `WINDOWS_USAGE.md` 不适用，已省略

---

## 定位

亚马逊 + Etsy 双平台卖家的定制化产品开发，核心问题不是"做不做定制"，而是：

- **消费者到底在意定制化的哪个方面？**（材质？印花工艺？尺码？）
- **现有定制产品的痛点在哪？**（工艺质量差？设计不符预期？）
- **搜索行为能否验证购买意愿？**

这个 Skill 的定位是：

**通过多维度数据交叉验证，判断定制化产品方向是否是真实市场需求，以及需求的具体方向。**

| 维度类型 | 维度 | 数据源 |
|---------|------|--------|
| 判定维度 | Review 信号 | Sorftime `product_reviews` / WebSearch 抓取 |
| 判定维度 | 关键词信号 | Sorftime `keyword_detail` / `keyword_trend` / `keyword_extends` |
| 判定维度 | 社区信号 | WebSearch（Reddit + Quora） |
| 判定维度 | Pinterest 趋势 | WebSearch + WebFetch（Pinterest Trends） |
| 参考维度 | Etsy 市场对标 | Etsy 搜索/API + WebSearch |
| 参考维度 | TikTok 电商对标 | Sorftime TikTok 工具集 |
| 参考维度 | 1688 供应参考 | Sorftime `ali1688_similar_product` |

## 上游 / 下游

- **上游**：`custom_product_research`、`zach-product-research`、`zach-competitor-deep-dive`
- **下游**：`zach-new-product-listing-writer`

---

## 执行优先级

### 路线 A：Sorftime 完整版

适用条件：当前环境可调用 Sorftime MCP。

1. Review 维度走 Sorftime `product_reviews`
2. 关键词维度走 Sorftime 关键词工具
3. 社区维度走 WebSearch
4. Pinterest 维度走 WebSearch + WebFetch
5. Etsy 参考维度走 WebSearch / Etsy API
6. TikTok 参考维度走 Sorftime TikTok 工具
7. 1688 参考维度走 Sorftime `ali1688_similar_product`

### 路线 B：无 Sorftime 替代版

适用条件：当前环境没有 Sorftime MCP。

1. Review 维度：WebSearch + WebFetch 抓取 Amazon Review；降级到用户提供 `review_source_pack`
2. 关键词维度：Google Trends + Amazon Autocomplete + 第三方工具
3. 社区维度：继续走 WebSearch
4. Pinterest 维度：继续可执行（不依赖 Sorftime）
5. Etsy 参考维度：继续可执行（不依赖 Sorftime）
6. TikTok 参考维度：标注为"未验证"
7. 1688 参考维度：标注为"未验证"

**注意**：替代版的数据精度不如 Sorftime，报告中需标注数据来源差异。

---

## 输入方式

### 业务输入

| 输入方式 | 示例 | 处理逻辑 |
|---------|------|---------| 
| 品类 + 定制化方向 | `dog shirt + custom printing` | 搜索定制化关键词，找热销定制产品 |
| ASIN + 定制化方向 | `B0XXXX + personalized name` | 围绕指定产品和相邻竞品验证 |
| 品类（泛）| `custom dog apparel` | 广泛验证该品类的定制化需求 |

默认站点：`US`

---

## 执行流程

### Step 0：解析任务与构造关键词

1. 确认输入类型和站点（默认 `US`）
2. 基于 `feature-demand-validator/references/keyword_construction_guide.md` 构造 5-8 个定制化关键词变体
3. 判断当前走 Sorftime 完整版还是替代版
4. 与用户确认关键词列表后再执行

### Step 1：Review 信号采集

#### 1.1 Review 池构建策略

**核心原则：从定制化关键词搜索结果中选产品，不用类目 Top 100。**

定制化产品单品销量低但覆盖面广，需要大样本才有统计意义。

**产品池构建流程：**

1. 用定制化核心关键词（如 `custom dog shirt`、`personalized dog hoodie`）搜索
2. 从搜索结果**前 3 页**（约 72-144 个产品）中筛选真正的定制化产品
3. 用关键词变体（如 `dog name shirt`、`custom pet apparel`、`embroidered dog bandana`）补充搜索
4. **目标：至少 100 个定制化产品进入评论池**
5. 从这 100+ 产品中采集 Review

**产品分两组：**

| 组别 | 定义 | 分析目的 |
|------|------|----------|
| A 组：定制化产品 | 标题/描述中明确提供定制服务的产品（80+ 个） | 分析消费者对定制体验的真实评价 |
| B 组：标品对照组 | 同品类但不提供定制的高销量产品（20+ 个） | 分析差评中是否有定制化需求信号 |

#### 1.2 Sorftime 完整版采集

1. 对每个定制化关键词调 `keyword_search_results` 获取前 3 页产品
2. 筛选标题含定制化标志词的产品进入 A 组
3. 调 `product_search` 获取同品类标品高销量产品进入 B 组
4. 对每个目标 ASIN 调 `product_reviews`
5. 保存为 JSON 后调用脚本：

macOS / Linux:
```bash
python feature-demand-validator/scripts/parse_reviews.py \
  --mode custom \
  --input <reviews.json> \
  --asin <ASIN> \
  --keywords-file <分维度关键词配置.json> \
  --source-url "sorftime://product_reviews/<ASIN>" \
  --output <数据源目录>/01_review_信号_原始数据.csv
```

#### 1.3 无 Sorftime 时的 Review 采集

**第一步：用定制化关键词定向搜索 ASIN**

1. WebSearch 搜索 `amazon.com custom dog shirt`、`amazon.com personalized dog hoodie` 等
2. 从搜索结果中提取带定制化标志词的真实 ASIN（A 组）
3. 搜索 `amazon.com dog shirt best seller` 获取标品对照组 ASIN（B 组）
4. ⛔ 严禁使用 `B0XXXXX` 等占位符，必须是真实 10 位 ASIN

**第二步：抓取 Review**

对每个 ASIN：
- WebFetch 访问 Amazon Review 页面
- 被反爬则用 WebSearch + 第三方评论聚合站

**第三步：数据量要求**

- A 组（定制化产品）：至少 80 个产品的 Review
- B 组（标品对照）：至少 20 个产品的 Review
- 总目标不低于 100 个产品
- 实际采集量和 A/B 分组写入报告

**降级路径：用户提供 review_source_pack**

仅当 WebSearch + WebFetch 均无法获取足够数据时，才要求用户提供证据包。
格式规范见 `feature-demand-validator/references/review_fallback_pack.md`。

#### 1.4 Review 分析维度

定制化 Review 分析的 **5 个判定子维度 + 1 个排除维度**：

| 子维度 | 关键词/表达示例 | 分析目标 |
|--------|----------------|----------|
| **材质需求** | `cotton, polyester, breathable, soft, organic, material quality, fabric` | 消费者是否有换材质的强烈诉求？ |
| **定制形式** | `name, photo, logo, text, embroidered, printed, sublimation, custom design` | 最受欢迎的定制方式是什么？ |
| **工艺质量** | `print quality, fade, wash, peel, crack, color, lasting, durable, blurry` | 现有定制产品的工艺痛点在哪？ |
| **尺码合身** | `size, fit, too small, too big, sizing chart, measure, doesn't fit` | 尺码是否是核心痛点？ |
| **设计满意度** | `cute, love the design, exactly what I wanted, looks great, disappointed` | 定制结果是否符合消费者预期？ |
| **排除维度：交付周期** | `shipping, delivery, arrived late, took forever` | 仅标记，不计入阈值判定 |

判定标准见 `feature-demand-validator/references/judgment_criteria.md`。

### Step 2：关键词信号采集

#### 2.1 有 Sorftime 时

对关键词变体依次调用：

- `keyword_detail`
- `keyword_trend`
- `keyword_extends`

导出标准 CSV：

```bash
python feature-demand-validator/scripts/generate_keyword_csv.py \
  --type detail \
  --data <detail.json> \
  --source-ref "keyword_detail:custom dog shirt" \
  --output <数据源目录>/02_keyword_信号_搜索量数据.csv
```

#### 2.2 无 Sorftime 时的替代采集

通过 Google Trends + Amazon Autocomplete + 第三方工具获取替代数据。
CSV 输出要求不变，来源类型标为 `google_trends` / `web_search_estimate` / `amazon_autocomplete`。

⛔ 关键词数据不得伪造。采集失败标为"采集失败 + 原因"。

### Step 3：社区信号采集

1. WebSearch 搜索 Reddit / Quora：
   - `site:reddit.com "custom dog shirt"`
   - `site:reddit.com "personalized dog apparel"`
   - `site:quora.com custom dog shirt worth it`
2. 保留标题、URL、发布日期、态度摘要
3. 导出标准 CSV：

```bash
python feature-demand-validator/scripts/generate_community_csv.py \
  --data <community.json> \
  --source-ref 'site:reddit.com "custom dog shirt"' \
  --output <数据源目录>/05_社区_信号_讨论摘要.csv
```

### Step 4：Pinterest 趋势信号采集

1. WebFetch 访问 `https://trends.pinterest.com/search?q=custom+dog+shirt&geo=US`
2. 获取过去 12 个月的搜索趋势曲线
3. 记录 Related Terms（相关搜索词推荐）
4. WebSearch 搜索 `site:pinterest.com "custom dog shirt"` 分析热门 Pin 内容
5. 导出标准 CSV：

```bash
python feature-demand-validator/scripts/generate_pinterest_csv.py \
  --data <pinterest.json> \
  --source-ref 'pinterest_trends:custom dog shirt' \
  --output <数据源目录>/06_pinterest_趋势信号.csv
```

### Step 5：Etsy 市场对标（参考维度）

**Etsy 数据用于补全竞争视角，不参与综合判定打分。**

采集内容：

| 数据项 | 采集方式 |
|--------|----------|
| 品类竞争密度 | 搜索后翻页记录最大可达页数 × 每页产品数；或 Etsy API `count` 字段；或 eRank/Marmalead |
| 价格带分布 | 前 3 页产品价格统计 |
| 热销产品特征 | 前 3 页产品的定制选项（材质、印花方式、尺码范围） |
| Review 评分与痛点 | 热销产品 Review 采样，与 Amazon 对比 |
| 定制选项丰富度 | 卖家提供的定制维度数量 |
| 店铺成熟度 | 头部卖家开店时长、总销量 |

导出：

```bash
python feature-demand-validator/scripts/generate_etsy_csv.py \
  --data <etsy.json> \
  --source-ref 'etsy_search:custom dog shirt' \
  --output <数据源目录>/07_etsy_市场信号.csv
```

### Step 6：TikTok 电商对标（参考维度）

**TikTok 数据用于验证短视频驱动型需求信号，不参与综合判定打分。**

1. 调 `tiktok_similar_product` 搜索相关产品
2. 调 `tiktok_category_name_search` 找到对应品类
3. 调 `tiktok_category_report` 获取品类数据报告
4. 对感兴趣的产品调 `tiktok_product_detail` 和 `tiktok_product_trend`
5. 导出标准 CSV：

```bash
python feature-demand-validator/scripts/generate_tiktok_csv.py \
  --data <tiktok.json> \
  --source-ref 'tiktok_similar:custom dog shirt' \
  --output <数据源目录>/08_tiktok_市场信号.csv
```

### Step 7：1688 供应参考（参考维度）

**1688 数据用于快速评估供给侧可行性，不参与综合判定打分。**

1. 调 `ali1688_similar_product` 搜索定制化供应商
2. 记录：是否有可定制打样的供应商、大致起订量、工艺报价区间、支持的工艺类型
3. 导出标准 CSV：

```bash
python feature-demand-validator/scripts/generate_1688_csv.py \
  --data <1688.json> \
  --source-ref '1688_search:定制狗衣服' \
  --output <数据源目录>/09_1688_供应参考.csv
```

### Step 8：综合判定

**四维度判定 + 三参考维度交叉验证：**

| 判定 | 条件 | 建议 |
|------|------|------|
| ✅ 强真需求 | 4 个判定维度中 ≥ 3 个有正面信号 | 立项开发，优先攻 Review 痛点子维度 |
| ⚠️ 弱真需求 | 4 个判定维度中 2 个有正面信号 | 小批量测试，补数据 |
| ❓ 待验证 | 仅 1 个维度有信号 | 暂缓，做更多调研 |
| ❌ 伪需求 | 无正面信号，或 ≥ 2 个维度出现 ⚠️ 负面信号 | 放弃该方向 |

参考维度（Etsy / TikTok / 1688）在报告的"风险提示"和"行动建议"中必须引用。

判定阈值标注为 `v1.0 — 待校准`，第一次实跑后根据真实数据微调。

### Step 9：生成报告

交付固定包括：

1. `[日期]_[品类]_[定制方向]_定制化需求验证报告.md`
2. 九个标准 CSV（01-09）
3. 若走 Review fallback，还要附上证据包

### Step 10：交付校验

```bash
python feature-demand-validator/scripts/validate_deliverables.py --dir <output_dir>
```

只有返回 `validate_ok` 才算完成。

---

## 标准输出

```text
reports/feature-validation/
├── YYYY-MM-DD_[品类]_[定制方向]_定制化需求验证报告.md
└── YYYY-MM-DD_[品类]_[定制方向]_数据源/
    ├── 01_review_信号_原始数据.csv
    ├── 02_keyword_信号_搜索量数据.csv
    ├── 03_keyword_信号_趋势数据.csv
    ├── 04_keyword_信号_延伸词.csv
    ├── 05_社区_信号_讨论摘要.csv
    ├── 06_pinterest_趋势信号.csv
    ├── 07_etsy_市场信号.csv
    ├── 08_tiktok_市场信号.csv
    ├── 09_1688_供应参考.csv
    └── review_source_pack/               # 仅 fallback 场景需要
        ├── source_manifest.json
        └── raw/
```

所有 CSV 都必须包含：

- `数据来源`
- `来源类型`
- `来源链接/查询词`
- `原始文件名`
- `采集时间`

---

## Script Directory

| 脚本 | 用途 |
|------|------|
| `feature-demand-validator/scripts/parse_reviews.py` | 解析 Review JSON，支持 `--mode custom` 分维度分析 |
| `feature-demand-validator/scripts/parse_review_source_pack.py` | 解析手动导出的 Review 证据包 |
| `feature-demand-validator/scripts/generate_keyword_csv.py` | 关键词数据导出为标准 CSV |
| `feature-demand-validator/scripts/generate_community_csv.py` | 社区讨论导出为标准 CSV |
| `feature-demand-validator/scripts/generate_pinterest_csv.py` | Pinterest Trends 数据导出为标准 CSV |
| `feature-demand-validator/scripts/generate_etsy_csv.py` | Etsy 市场数据导出为标准 CSV |
| `feature-demand-validator/scripts/generate_tiktok_csv.py` | TikTok 电商数据导出为标准 CSV |
| `feature-demand-validator/scripts/generate_1688_csv.py` | 1688 供应商数据导出为标准 CSV |
| `feature-demand-validator/scripts/validate_deliverables.py` | 校验 MD + 9 个 CSV 是否完整 |

---

## 硬性规则

1. ⛔ Review 池必须来自定制化关键词搜索结果，不用类目 Top 100
2. ⛔ Review 池目标 ≥ 100 个产品，从搜索结果前 3 页筛选，实际采集量写入报告
3. ⛔ ASIN 必须是真实可验证的（B0 开头 10 位），严禁使用占位符
4. ⛔ Review 原始数据必须走 Python 脚本解析，不能把原始 JSON/HTML 塞进报告
5. ⛔ 每条 Review 必须标记命中的子维度（材质/定制形式/工艺/尺码/设计/交付周期-排除）
6. ⛔ 交付周期相关 Review 仅标记不计入阈值判定，子维度标为 `排除维度:交付周期`
7. ⛔ 每个 CSV 必须保留可核查来源字段
8. ⛔ 负面信号必须写入报告
9. ⛔ 所有结论都要引用具体数据，不允许空泛判断
10. ⛔ 参考维度（Etsy/TikTok/1688）不参与综合判定打分，但必须在风险提示中引用
11. ⛔ 阈值标注为 `v1.0 — 待校准`，第一次实跑后根据真实数据微调

---

## 参考文档

- `feature-demand-validator/references/csv_schema.md`
- `feature-demand-validator/references/report_template.md`
- `feature-demand-validator/references/judgment_criteria.md`
- `feature-demand-validator/references/keyword_construction_guide.md`
- `feature-demand-validator/references/review_fallback_pack.md`
