---
name: custom-product-research
description: 当用户要对一个定制化/个性化品类（或任意亚马逊品类）做完整市场调研——Top100 竞品维度拆解、Etsy 对标、VOC 评论分析、定价模型、机会结论，并交付 MD+HTML+Excel+Dashboard 四件套时使用；非定制品类切换通用模式。
---

# 选品分析器（Custom Product Research - 双平台 FBM 定制版）

## 运行环境（box）——合并说明

本技能合并了原 `custom_product_research`（定制化品类调研，**默认模式**，正文即此版）与 `zach-product-research`（通用品类调研，**通用模式**）。
- 通用模式完整流程：`custom-product-research/references/generic_mode_SKILL.md`（脚本 `*_generic.py`，模板 `assets/generic/`、`agents/generic/`、`evals/generic/`，Schema `references/payload_schema_v2.md`、`references/analysis_patterns.md`）
- 定制模式文件：`custom-product-research/scripts/render_deliverables.py`、`parse_top100_dimensions.py`、`cross_analysis.py`；`custom-product-research/references/payload_schema_v2_custom.md`、`analysis_patterns_custom.md`、`html_report_spec.md`；`custom-product-research/agents/`；`custom-product-research/assets/`
- 渲染：`python custom-product-research/scripts/render_deliverables.py all --input <unified_payload.json>`（子命令 `generate` / `validate` / `all`；`--root` 默认 `reports/product-research`，产物落在 `reports/product-research/工作成果/brands/<品牌>/市场调研/<品类>/<版本>/`）
- 冒烟测试：`python custom-product-research/scripts/render_deliverables.py all --input custom-product-research/evals/files/sample_payload_minimal.json --root /tmp/pr_test`
- Sorftime：box 上已接入 Sorftime MCP（`user-sorftime` 命名空间，先 `GetDynamicTools` 看参数再 `CallDynamicTool`）；脚本内调用用 `_shared/sorftime_http.py`（读环境变量 `SORFTIME_KEY`，**绝不打印**）。下文所有 `MCP:工具名` 都指这些 Sorftime 工具。
  - 常用：`category_report` / `category_products` / `category_trend`、`product_detail` / `product_reviews`、`keyword_detail` / `keyword_extends` / `keyword_search_results`、`ali1688_similar_product`
- Etsy 对标：优先 `python etsy-keyword-database/fetch_etsy_data.py`（API，含价格/收藏/在售量，仅美元，无搜索量），需要页面结构（Bestseller 标、个性化选项）时用 box 浏览器（已登录 Etsy）
- 原文的 `write_to_file` / `run_command` = box 上的文件写入 / Shell；payload 组装脚本写到 `./tmp/assemble_payload.py`
- 用户的店铺背景：亚马逊 1 店 + Etsy 1 店，定制产品，FBM 发货——定价模型须包含 FBM 运费与定制工时

---


## 📌 定位

专为 **FBM 定制化/个性化产品** 设计的市场调研工具。

核心理念：**不看类目看需求词，不看系统标品看真实定制选项，双平台（Amazon+Etsy）背靠背验证。**

**数据来源**：
- Amazon 端：依赖 Sorftime MCP 工具获取（结构化底层数据）。
- Etsy 端：依赖浏览器自动化抓取（探索性与非结构化参照数据）。

**下游输出**：选品报告（MD + HTML精简 + Dashboard看板 + Excel），重点在于双平台 Go/No-Go 评分评价与 Tier 1 落地切入矩阵。

## 📁 目录结构与相关文件

- `custom-product-research/scripts/render_deliverables.py` (渲染生成四交付物)
- `custom-product-research/references/payload_schema_v2_custom.md` (定制版 V2 Schema)
- `custom-product-research/references/analysis_patterns_custom.md` (定制分析模式)
- `custom-product-research/agents/data-pipeline.md`, `custom-product-research/agents/insight-writer.md`
- `custom-product-research/assets/` (报告与面板 HTML 模板)

---

## 📥 极简输入要求

**最小必需输入**：
1. **产品关键词**：如 `custom dog vest`, `personalized leather notebook`
2. **目标站点**：默认 `US`

**可选加分项**（如不填，系统会自动从市场及竞品反推建议）：
- 你的核心工艺（UV 打印/激光雕刻/热转印等）
- 你的主发物流时效（如 3-8 天/云途 8-12 天）
- 目标定价区间

---

## ⛔ 硬性规则（不可省略）

1. **⛔ 核心入口必须是需求词池，而非类目 TopSale**：定制品在类目报告排名靠后。必须通过关键词搜索抓取自然位产品作为分析基础池。
2. **⛔ 竞品筛选必须限定 FBM 或明确提供定制选项的产品**：使用 `product_search` 时需筛选交付方式或人工二次排除不提供定制的白牌标品。
3. **⛔ 属性萃取必须围绕"定制项"**：提取诸如定制部位、可选工艺材质、可定制文字/图片数量等维度，而非纯标品参数（如功率/容量）。
4. **⛔ 差评痛点分析必须映射为你的差异化卖点**：发现"刻字容易掉"的差评，必须转化为"采用深压花工艺，不掉色不起皮"的产品策略建议。
5. **⛔ 财务测算必须使用 FBM 模型**：包含生产制造成本 + 跨境直发尾程运费。**剔除任何 FBA 仓储与派送费用。**
6. **⛔ 交付链路必须使用 `render_deliverables.py`**：禁止随意手敲最终 Markdown 报告，必须输出包含 `MD + HTML + Excel + Dashboard` 的四件套。
7. **⛔ 必须执行双平台平行检测**：不能只看 Amazon。Etsy 的售价上限与定制丰富度是不可或缺的对标参考。
8. **⛔ 中文关键词必须经过搜索结果反向校验**：将中文产品名翻译为英文后，必须对 ≥ 2 个候选翻译词各执行一次 `keyword_search_results`（仅首页），检查 Top 5 产品标题是否与用户目标品类一致。明确匹配时自动采用，有歧义时才请求用户确认。**不信翻译，信搜索结果。**
9. **⛔ MCP 调用节奏控制（防 ECONNREFUSED）**：每轮 tool call 中**并发 MCP 调用不得超过 3 个**。完成一批后，下一批必须在新的 turn 中发起。连续密集调用会导致 MCP Server 进程崩溃并拒绝重连。如果遇到 `ECONNREFUSED` 错误，**停止所有 MCP 调用，等待用户确认 MCP 服务已恢复后再继续**。
10. **⛔ 大 JSON 输出必须走脚本写入（防 streaming EOF）**：`unified_payload.json` 等超过 200 行的 JSON 内容**禁止在对话中直接输出**。必须通过 `write_to_file` 或 Python 脚本（`run_command` 执行）写入磁盘。这可以防止模型流式输出因内容过长而被框架截断（`unexpected EOF`）。具体做法：**先用 `write_to_file` 创建 payload 文件，再调用 `run_command` 执行 `render_deliverables.py`**。

---

## 🛠️ MCP 与浏览器工具清单

| 类别 | 工具 / 方式 | 用途 | 优先级 |
|------|------------|------|--------|
| **Amazon 需求探测** | `keyword_detail` / `keyword_trend` | 验证主词与长尾词的搜索量及变动趋势 | ⛔ 必调 |
| | `keyword_extends` | 挖掘具体的定制工艺词和场景词 | ⛔ 必调 |
| **Amazon 竞品提取** | `keyword_search_results` | 直接提取搜索结果自然位，建立竞品池 | ⛔ 必调 |
| | `product_search` | 辅助筛选特定条件（如 FBM）的竞品 | 📋 按需 |
| **Amazon 详情与 VOC** | `product_detail` | 提取竞品提供哪些 Customization 选项 | ⛔ 必调 |
| | `product_reviews` | 收集竞品差评，挖掘定制体验痛点 | ⛔ 必调 |
| **Etsy 市场对标** | box 浏览器 / Etsy API (或直接页面调用) | 获取对应目标词下的产品列表页结构（价格带、Bestseller比例）与代表竞品详情（定制拉下框选项、加工交期） | ⛔ 必调 |
| **供应链参考** | `ali1688_similar_product` | 提取可用于定制的"白板/底模"裸产品采购价基准 | 📋 按需 |

*(注：Etsy 数据提取为轻量级探索，获取首页前列产品价格中位数与最高位，以及几个 Star Seller 对应的产品定制结构即可，不需要抓取几百条深层数据)*

> ⚠️ **节奏控制**：以上工具每轮最多并发调用 3 个。`keyword_detail` × 5 必须拆为 2 轮（3+2）。`product_detail` × 5 同理。违规将触发 MCP Server 崩溃（`ECONNREFUSED`）。

---

## 🔄 完整执行流程 (Step 0 - 6)

### Step 0: 信息收集（交互式）

收到调用后，确认：站点、产品关键词、(可选)自身工艺优势、(可选)承诺物流时效。未提供可选信息时系统使用探测数据反推。

### Step 0.5: 关键词意图校验门（自动执行）

当用户提供的产品关键词为**中文**时，必须执行以下自动校验流程：

1. **候选词生成**：基于用户的中文产品描述，生成 **≥ 3 个**不同角度的英文候选关键词。
   - 例：用户说"狗狗定制背心" → 候选: `custom dog vest`, `custom dog tank top`, `personalized dog shirt sleeveless`
2. **搜索结果反校验**：对每个候选词调用 `keyword_search_results`（仅第 1 页），提取 Top 5 产品标题。
3. **意图匹配判定**：检查 Top 5 产品是否与用户描述的产品形态一致。
   - ✅ 标题中出现穿的衣服（shirt, clothing, wear）→ 匹配
   - ❌ 标题中出现背带/绳具（harness, leash, strap）→ 不匹配
4. **自动决策**：
   - **有且仅有一组候选词明确匹配** → 直接采用，无需打扰用户
   - **多组都匹配** → 选搜索量最大的那个
   - **全部不匹配或有歧义** → 向用户展示各候选词 Top 5 结果，请求确认

> ⛔ 此步骤为**零成本守护**：仅增加 2-3 次首页搜索调用，即可避免整条调研链从源头偏移。

### Step 1: 需求探测 (双平台)

**目标**：验证这个定制品有多少人想买？

1. **Amazon 关键词矩阵裂变**：
   - 围绕主词裂变出：**品类词**、**定制词**、**场景词**。调用 `keyword_detail`。
2. **Amazon 核心池构建**：
   - 使用核心定制词调用 `keyword_search_results`（可并用 `product_search`）提取前排真实定制竞品 80-150 款。
   - ⛔ **必须按月销量降序排列，从中挑选销量最高的 10 个真实定制竞品**进入详细分析池。
3. **Etsy 平行探测**：
   - 使用浏览器访问 Etsy 搜索页。提取：主流价格带分布区间，Bestseller 及 Star Seller 店铺的热门款式特征。

> **⛔ Step 1 硬性数据量标准**
>
> | 检查项 | 最低要求 |
> |--------|----------|
> | `keyword_detail` 覆盖精准定制词 | ≥ 3 个 |
> | `keyword_detail` 覆盖品类大词 | ≥ 2 个 |
> | `keyword_extends` 调用 | ≥ 1 次 |
> | `keyword_search_results` 抓取页数 | ≥ 3 页（≥ 80 条自然位产品） |
> | 每个 keyword_detail 必须包含字段 | 月搜索量、CPC、旺季月份 |
> | **定制细分词 (segment=“定制词”)** | **≥ 3 个（如 custom dog shirt, personalized dog shirt, custom pet shirt）** |
> | **keyword_extends Top 10 存储** | **必须将按月搜索量排序的前 10 个延伸词存入 `ch02.keyword_extends_top10`** |

### Step 2: 定制竞品画像与时效线提取

**目标**：谁在做？怎么做的？门槛多高？交期多久？

1. **动态维度萃取**：
   - 调用 Amazon 代表性竞品的 `product_detail` 以及分析 Etsy 页面。
   - 提取该品类核心定制维度。例如：刻字方式(激光/压印)、定制位置(单面/双面)、附带配件等。
2. **时效竞争线提取**：
   - 提取头部竞品承诺的 Delivery Time（制作期 Processing Time + 运输期 Shipping Time）。建立你的跨境直发时效对照准星。

> **⛔ Step 2 硬性数据量标准**
>
> | 检查项 | 最低要求 |
> |--------|----------|
> | `product_detail` 调用竞品 ASIN 数 | ≥ 10 个真实定制竞品（从 Step 1 池中按月销量取 Top 10） |
> | 每个竞品必须提取字段 | 价格、评论数、星级、上线天数、卖家来源(US/CN)、定制选项描述 |

### Step 3: 买家声音深度分析 (VOC)

**目标**：深挖买家痛点，找准切入品牌主张。

1. 抽取 Amazon 高销量低星竞品调取 `product_reviews` (Negative)，结合 Etsy 的评价氛围。
2. **按定制属性清洗痛点**：
   - 定制质量（字迹模糊/照片失真）
   - 交期管理（超出承诺时间）
   - 定制准确性（名字刻错）
   - 材质落差（与图片材质严重不符）
3. **⛔ 必须将痛点映射为你的策略**：例如痛点是"照片掉色" -> 你的产品矩阵中必须包含"采用 6 层超强 UV 固化"工艺及作为主打卖点。

> **⛔ Step 3 硬性数据量标准**
>
> | 检查项 | 最低要求 |
> |--------|----------|
> | `product_reviews(Negative)` 调用竞品数 | ≥ 10 个竞品（全部 Top 10 均需差评分析） |
> | 差评分类 | 必须按定制维度分类，含频次计数 |
> | `ali1688_similar_product` | ≥ 1 次（供应链采购参考） |

### Step 4: 供需缺口与定价门槛分析

**目标**：利润够不够空间？有没有蓝海空白组合？

1. **缺口碰撞**：将高频需求词（Step1）与现存定制选项（Step2）交叉。发现搜索量大但提供对应定制选项较少的组合。
2. **价格倒逼雷达模型**：
   - 对比 Amazon 均价与 Etsy 折溢价空间。
   - 反推得出预警结论："双平台安全均价 $X，要保持 30% 毛利，包含尾程的综合制造成本安全线为 $Y"。

### Step 5: 双平台 Go / No-Go 评分卡

**评估维度一表双柱横向对比**，分别对 Amazon 和 Etsy 给出 **GO / CONDITIONAL GO / HOLD / NO-GO**：

| 评估维度 (权重) | Amazon 核心指标 | Etsy 核心指标 |
|-----------------|----------------|---------------|
| **需求规模 (25%)** | 精准搜索量+趋势 | 搜索卡片热度(Bestseller数量/评级数) |
| **竞争硬度 (20%)** | 标品碾压度、FBM同级对手评价数 | 专注该细分的老店数量 |
| **痛点密度 (20%)** | 星级、退货隐患 | 星级、服务满分率 |
| **溢价空间 (15%)** | 均价、能否突破低价内卷 | 均价分布最高位 |
| **时效容忍度 (20%)**| 你的物流时效相比竞品的优劣势 | 你的物流时效相比竞品的优劣势 |

### Step 6: 切入建议与产品矩阵落地

基于分析交付 **Tier 1 首攻策略**：
- **首发主战场推荐**：Amazon 先上还是 Etsy 先上？
- **最佳工艺组合推荐**：什么材料配什么定制方式最好卖？
- **建议定价与成本警戒线**
- **必须打出的差异化卖点**（直接回应 Step 3 最严重的痛点）

---

## 💾 中间数据持久化规则

防止会话中断，每完成一个重度节点，必须将会话中的核心提取数据保存为 JSON 文件于统一目录中 `reports/product-research/工作成果/brands/[品牌]/市场调研/[品类]/[version]/`：

- `step1_keywords_pool.json`
- `step1_etsy_raw.json` ← **Etsy 原始数据（必须持久化）**
- `step2_custom_dimensions.json`
- `step3_voc_analysis.json`
- `step4_pricing_model.json`

以上 JSON 同时也是组装成最终 `unified_payload.json` 供 render 脚本使用的来源。

### 🛡️ 崩溃恢复协议

> 遭遇 `ECONNREFUSED` 或 `unexpected EOF` 后的恢复流程：

1. **不要重复已完成的 MCP 调用**。检查已持久化的 `step*_*.json` 文件，跳过已有数据的步骤。
2. **确认 MCP 服务状态**：请用户确认 Sorftime MCP 服务已恢复（可通过一次轻量调用如 `get_time` 验证）。
3. **从断点继续**：从最后一个已保存的 step 文件之后的步骤开始执行。

### 📦 Payload 组装规则

> ⛔ **禁止在对话中直接生成完整 `unified_payload.json` 内容。**

正确做法：
1. 使用 `write_to_file` 工具创建一个 Python 脚本 (`./tmp/assemble_payload.py`)，脚本内逻辑为：读取各 `step*_*.json` → 映射到 v2 schema → 写入 `unified_payload.json`
2. 通过 `run_command` 执行该脚本
3. 再通过 `run_command` 执行 `render_deliverables.py all --input unified_payload.json`

这样可以完全避免因大 JSON 输出导致的 `unexpected EOF`。

### Etsy 原始数据格式规范 (`step1_etsy_raw.json`)

```json
{
  "search_query": "custom dog shirt",
  "scrape_date": "2026-03-26",
  "total_results_estimate": 10000,
  "products": [
    {
      "title": "...",
      "price": 25.99,
      "original_price": 32.99,
      "shop_name": "...",
      "is_bestseller": true,
      "is_star_seller": true,
      "reviews_count": 1234,
      "rating": 4.8,
      "customization_options": ["name", "font", "color"],
      "processing_time": "1-3 business days",
      "shipping_time": "5-10 business days",
      "free_shipping": true
    }
  ],
  "price_stats": {
    "min": 6.5,
    "max": 45.0,
    "median": 22.0,
    "p25": 15.0,
    "p75": 30.0
  }
}
```

> ⛔ 浏览器抓取完成后必须立即保存此 JSON，不得仅将数据留存在会话上下文中。

---

## 🏁 Pre-Render 数据完整性自检清单 (DoD)

在执行最终 `render_deliverables.py` 前，**逐项检查**以下 10 条，未达标不得渲染：

| # | 检查项 | 合格标准 | 对应 payload 区域 |
|---|--------|---------|-------------------|
| 1 | Amazon 关键词数据 | ≥ 5 个关键词含月搜索量+CPC | `ch02.keyword_comparison` |
| 2 | keyword_search_results 产品池 | ≥ 80 条真实自然位产品 | `excel_sheets.类目销量TopSale_明细` |
| 3 | 竞品 product_detail | ≥ 10 个 ASIN 含完整属性（按月销量 Top 10 挑选） | `ch05.competitor_selection_logic` |
| 4 | 差评 VOC | ≥ 3 个竞品的 Negative reviews | `ch06.by_dimension` 各 pain_point 有 frequency |
| 5 | Etsy 数据 | 有价格范围+至少 10 个产品数据 | `step1_etsy_raw.json` 或 payload insight 中引用 |
| 6 | 1688 供应链参考 | 至少 1 次 ali1688 调用 | `ch08` 或 `excel_sheets.定价模型_FBM直发` |
| 7 | 定制维度提取 | ≥ 2 个定制维度含分布数据 | `ch03.dimensions` |
| 8 | FBM 成本模型 | 无 FBA 费用项，含直发运费 | `excel_sheets.定价模型_FBM直发` |
| 9 | Go/No-Go 评分 | 5 维度均有评分和依据 | `ch09.go_nogo_scorecard` |
| 10 | Tier 策略 | ≥ 1 个 Tier 含完整规格和对标 ASIN | `ch08.tiers` |

> ⛔ 任何一项未达标时，必须返回对应 Step 补充数据，不得用估算值填充。
