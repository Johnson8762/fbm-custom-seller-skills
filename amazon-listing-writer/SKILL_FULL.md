---
name: amazon-listing-writer
description: 当用户要为亚马逊产品（尤其定制/个性化产品）写或重写完整 Listing（标题、五点、描述、Search Terms、A+/图片框架），需要符合 A9/Rufus/COSMO 并做违禁词合规校验时使用。
---

# Amazon Listing 智能生成器（amazon-listing-writer）

## 运行环境（box）

- 资料目录：`amazon-listing-writer/`；参考文件在 `amazon-listing-writer/references/`，脚本 `validate_listing.py`、`render_listing_html.py` 在 `amazon-listing-writer/`
- Sorftime：box 上已接入 Sorftime MCP（`user-sorftime` 命名空间，先 `GetDynamicTools` 看参数再 `CallDynamicTool`）；脚本内调用用 `_shared/sorftime_http.py`（读环境变量 `SORFTIME_KEY`，**绝不打印**）。下文所有 `MCP:工具名` 都指这些 Sorftime 工具。
- 每轮并发 Sorftime 调用不超过 3 个（原规则保留）
- 工作成果目录：`reports/listing/[产品关键词]/`（step 文件、最终 MD、HTML）
- 校验：`python amazon-listing-writer/validate_listing.py --input <listing.md> [--apparel]`（原脚本的章节提取正则有 bug，已修复）
- 可视化：`python amazon-listing-writer/render_listing_html.py --input <listing.md> [--output <out.html>]`（含一键复制按钮）
- 示例输出：`amazon-listing-writer/examples/sample_listing_output.md`
- 下游：图片 → `amazon-listing-image-prompts`；上架前验证 → `amazon-rufus-qa-tester`；上架后验收 → `amazon-listing-health-checker`

---


## 定位

接收用户提供的产品信息，结合 Sorftime MCP 自动采集的竞品数据，生成符合 Amazon A9/Rufus/COSMO 算法的高质量 Listing 全套内容。

**核心理念**：Listing 是"双重读者"文档 — 既要说服消费者购买（转化），也要让算法能索引和推荐（Rufus 事实层 + COSMO 意图层）。

**上游**：`custom_product_research`（市场调研）、`custom-validator`（需求验证）
**下游**：图片/视频生成 Skill（后续创建）

## 目录结构

- `SKILL.md`（本文件 — 核心指令）
- `amazon-listing-writer/references/amazon_compliance_blacklist.md`（违禁词库 v1.0）
- `amazon-listing-writer/references/rufus_cosmo_guide.md`（Rufus + COSMO 优化指南）
- `amazon-listing-writer/references/listing_output_spec.md`（输出格式规范）
- `amazon-listing-writer/references/prompt_templates.md`（三代理 Prompt 模板）
- `amazon-listing-writer/validate_listing.py`（合规校验脚本）
- `amazon-listing-writer/render_listing_html.py`（HTML 可视化生成器）
- `（模板已内置于 render_listing_html.py 同目录）`（可视化模板 — 含一键复制按钮）

---

## 数据溯源铁律

> ⛔ **全局硬性规则 #0 — 数据溯源**：Skill 产出的**所有数据点**（关键词搜索量、竞品信息、痛点描述、卖点依据）必须标注可回溯来源。来源格式：
>
> - `[用户输入]` — 用户直接提供的信息
> - `[MCP:工具名:参数]` — 如 `[MCP:product_detail:B0XXXXXX]`
> - `[竞品参考值]` — 从竞品数据推断的品类通用值
> - `[品类通用值-待供应商确认]` — 属性表缺失时的降级值
>
> **严禁任何无来源标注的数据出现在最终 Listing 中**。无法获取的数据必须标注为「数据缺失」，不得编造。

---

## 三代理架构

### 证据代理（Evidence Agent）

**职责**：提取产品物理事实（尺寸、材质、重量、认证等），构建 Rufus 可索引的事实层。

**数据来源限定**：
- ⛔ 仅限用户提供的属性表
- ⛔ 仅限 `product_detail` 返回的结构化规格字段
- ⛔ **不得自行推测或编造任何产品参数**

**输出格式**：每条事实必须附带来源标签
```
事实: 材质为 100% 纯棉 [用户输入]
事实: 重量 180g [MCP:product_detail:B0XXXXXX - 竞品参考值]
事实: 尺码范围 S-3XL [品类通用值-待供应商确认]
```

**Rufus 优化原则**：
- Rufus 喜欢**不可辩驳的事实数据**（"3000mAh"、"304不锈钢"）
- Rufus 厌恶**模糊形容词**（"high quality"、"premium"、"best"）
- 每个 Bullet Point 至少包含 1 个可量化参数

### 逻辑代理（Logic Agent）

**职责**：建立"产品-场景-人群"映射，触发 COSMO 意图偏好。

**数据来源限定**：
- ⛔ 仅限 `product_reviews` 提取的**真实使用场景**
- ⛔ 仅限 `keyword_extends` 延伸词揭示的**需求意图**
- ⛔ 仅限 `competitor_product_keywords` 中的**高流量场景词**

**输出格式**：
```
场景1: 宠物主人为狗狗生日定制纪念T恤 [MCP:product_reviews:B0XXXXXX - 正面评论#23]
人群1: 养中大型犬的女性用户(25-45岁) [MCP:keyword_extends:"custom dog shirt" - 延伸词分析]
痛点1: 照片印刷洗几次就掉色 (频次:12/50条差评) [MCP:product_reviews:B0XXXXXX - 负面评论统计]
```

**COSMO 优化原则**：
- COSMO 通过"在什么场景下解决什么人群的什么问题"来匹配搜索意图
- 每个 Bullet Point 暗含一个使用场景
- Product Description 需要叙述式结构（Who Is This For / What Makes It Special / Specs），将常见购买疑问的答案自然融入描述段落中，**禁止使用 FAQ 板块**（避免与 Amazon 原生 Q&A 功能冲突）

### 创作代理（Creative Agent）

**职责**：基于前两个代理的输出，执行最终撰写 + 语义降级 + 合规过滤。

**硬性约束**：
- ⛔ 禁止引入未经证据代理或逻辑代理确认的事实
- ⛔ 引用事实时必须交叉检查来源标注，无来源标注的事实自动剔除
- ⛔ 对照 `amazon-listing-writer/references/amazon_compliance_blacklist.md` 过滤违禁词
- ⛔ 语义降级规则：将不合规表达转为合规表达（如"治疗疼痛"→"缓解不适"）
- ⛔ 不使用 emoji
- ⛔ 不使用最高级（best、#1、top）

---

## 输入规范

### 必选输入

| 输入项 | 说明 |
|--------|------|
| **产品关键词** | 如 `custom dog shirt`、`personalized leather wallet` |

### 可选输入

| 输入项 | 说明 |
|--------|------|
| 目标站点 | 默认 `US` |
| 本品属性表 | 产品参数、材质、包装清单、认证等。**允许只描述 1-2 项** |
| 核心卖点 | 用户手动总结的差异化卖点 |
| 竞品 ASIN 列表 | 至少 5 个；不足时 skill 自动补齐 |
| 价格区间 | 目标售价范围 |

### 属性表降级策略

当用户无法提供完整属性表时：
1. 从 5 个竞品的 `product_detail` 中提取该品类的**通用基础属性**（如材质、尺码范围）
2. 这些属性在输出中标注 `[品类通用值-待供应商确认]`
3. **不使用任何最高级描述**
4. **不编造具体数值**（如不编造"承重50kg"这类未经证实的数据）

> ⛔ 属性表可以不完整，但严禁夸张、严禁编造参数。宁可保守也不可虚假。

---

## MCP 工具清单

| 工具 | 用途 | 调用时机 | 优先级 |
|------|------|---------|--------|
| `keyword_search_results` | 验证关键词搜索结果相关性 | Step 0 | ⛔ 必调 |
| `product_search` | 按关键词搜索竞品，补齐 ASIN 池 | Step 1 | ⛔ 必调 |
| `product_detail` | 获取竞品标题、五点、描述、价格、规格 | Step 2 | ⛔ 必调 |
| `product_reviews`（Negative + Positive） | 获取竞品评论，提取痛点和使用场景 | Step 2 | ⛔ 必调 |
| `competitor_product_keywords` | 获取竞品的核心流量词和自然排名 | Step 3 | ⛔ 必调 |
| `keyword_detail` | 查询关键词月搜索量/CPC/旺季 | Step 3 | ⛔ 必调 |
| `keyword_extends` | 挖掘长尾词和语义延伸词 | Step 3 | ⛔ 必调 |
| `product_traffic_terms` | 获取竞品近期曝光关键词 | Step 3 | 📋 按需 |

> ⚠️ **节奏控制**：每轮 tool call 并发 MCP 调用不超过 3 个。`product_detail` × 5 必须拆为 2 轮（3+2）。遇到 `ECONNREFUSED` 立即停止，等待用户确认 MCP 恢复。

---

## 完整执行流程 (Step 0 - 7)

### Step 0: 解析用户输入 + 关键词意图校验

1. **确认输入**：产品关键词、站点、属性表（可选）、竞品 ASIN（可选）、卖点（可选）
2. **中文关键词校验**：如用户提供中文关键词，生成 >= 3 个英文候选词，对每个调用 `keyword_search_results` 首页，检查 Top 5 产品是否匹配
3. **意图确认**：明确匹配则自动采用；有歧义则请求用户确认

### Step 1: 竞品池构建

**目标**：确保至少 5 个高质量竞品 ASIN

1. **用户提供 >= 5个 ASIN** → 直接使用，跳转 Step 2
2. **用户提供 < 5个 ASIN** → 用 `product_search` 搜索产品关键词，按月销量降序，从前排结果中补齐至 5 个
3. **用户未提供 ASIN** → 用 `product_search` 搜索产品关键词，取月销量 Top 5

**竞品筛选标准**：
- 月销量 > 0
- 评论数 > 10
- 与产品关键词高度相关（标题含核心词）
- 优先选择提供定制化选项的产品（如本品为定制型）

### Step 2: 竞品深度分析

**目标**：获取竞品 Listing 结构 + 买家痛点

1. **产品详情采集**：对 5 个竞品 ASIN 调用 `product_detail`
   - 提取：标题结构、五点写法、价格、评分、评论数、规格参数
   - ⛔ 每条数据标注 `[MCP:product_detail:ASIN]`

2. **差评分析**：对 5 个竞品调用 `product_reviews`（Negative）
   - 提取高频痛点，按维度分类（质量/尺码/外观/功能/包装）
   - 统计每个痛点频次
   - ⛔ 每条痛点标注 `[MCP:product_reviews:ASIN - 评论#ID]`

3. **正面评价分析**：对 Top 3 竞品调用 `product_reviews`（Positive）
   - 提取买家最认可的卖点和使用场景
   - ⛔ 每条场景标注来源

> **⛔ Step 2 硬性数据量标准**
>
> | 检查项 | 最低要求 |
> |--------|----------|
> | `product_detail` 调用 | >= 5 个 ASIN |
> | `product_reviews`(Negative) | >= 5 个 ASIN |
> | `product_reviews`(Positive) | >= 3 个 ASIN |
> | 每个竞品必须提取 | 标题、五点、价格、评分、评论数 |

### Step 3: 关键词矩阵构建

**目标**：建立完整的关键词布局，替代人工 ABA 数据和竞品出单词报告

1. **核心词搜索量**：对产品主词 + 2-3 个变体词调用 `keyword_detail`
   - 获取月搜索量、CPC、旺季月份

2. **长尾词挖掘**：对主词调用 `keyword_extends`
   - 取搜索量 Top 20 延伸词
   - 分类为：核心词、场景词、属性词、长尾词

3. **竞品流量词**：对 Top 3 竞品调用 `competitor_product_keywords`
   - 获取竞品在哪些关键词下有自然排名
   - 提取高频共现词作为必埋词

> **⛔ Step 3 硬性数据量标准**
>
> | 检查项 | 最低要求 |
> |--------|----------|
> | `keyword_detail` | >= 3 个关键词 |
> | `keyword_extends` | >= 1 次，取 Top 20 |
> | `competitor_product_keywords` | >= 3 个竞品 ASIN |

### Step 4: 策略分析

**目标**：输出差异化定位和内容策略，指导 Step 5 的具体撰写

基于 Step 2-3 的数据产出：
1. **Rufus 事实摘要**：从证据代理输出中选取 Top 5 最重要的产品规格事实
2. **COSMO 场景映射**：从逻辑代理输出中选取 Top 3 使用场景和对应人群
3. **差异化切入点**：基于竞品痛点(Step 2) + 用户卖点(输入) 确定主打差异
4. **关键词布局策略**：基于 Step 3 确定标题主词、五点埋词、ST 补充词

**策略简报格式**：
```markdown
## 策略分析简报

### Rufus 核心事实（Top 5）
1. [事实] — 来源: [xxx]
...

### COSMO 场景（Top 3）
1. [场景-人群-需求] — 来源: [xxx]
...

### 差异化切入点
- 主打: [xxx] — 依据: 竞品痛点 [xxx] 频次 [n]
- 辅助: [xxx]

### 关键词布局
- 标题主词: [xxx] (月搜索量: [n]) [MCP:keyword_detail]
- 五点埋词: [词1], [词2], ...
- ST 补充词: [词1], [词2], ...
```

### Step 5: Listing 内容生成

**目标**：三代理协作输出完整 Listing

按照 `amazon-listing-writer/references/listing_output_spec.md` 和 `amazon-listing-writer/references/prompt_templates.md` 中的规范，依次生成 9 个模块：

> ⛔ **输出分区规则**：最终交付文件必须分为两个区域：
> 1. **📋 可复制区（Platform-Ready）**：标题、五点、描述、Search Terms — **不含任何来源标签、MCP标记、竞品ASIN**，可直接复制粘贴到 Amazon Seller Central
> 2. **📊 分析参考区（Internal Reference）**：策略简报、图片/A+/视频 Prompt、数据溯源表 — 含完整来源标签，供内部参考
>
> 五点和描述中的卖点必须转化为**纯消费者语言**，所有数据来源引用集中在文末溯源表中。

1. **策略分析简报**（Step 4 的输出）— 📊 分析参考区
2. **标题（Title）** — 📋 可复制区
   - 格式：Brand + Core Keyword + Core USP + Key Specs
   - 上限 200 字符（服装类 125 字符）
   - 同一单词最多出现 2 次
3. **五点描述（Bullet Points）** — 📋 可复制区
   - 格式：`[HEADER] — [Benefit + Data Proof]`
   - 前 2 点必须包含最核心卖点（移动端优先）
   - 每点至少 1 个可量化参数
   - ⛔ **五点正文中不得出现 [MCP:xxx] 来源标签或竞品 ASIN**
4. **产品描述（Product Description）** — 📋 可复制区
   - 叙述式 HTML 结构："Who Is This For?" + "What Makes It Special?" + "Product Specifications"
   - ⛔ **禁止使用 FAQ 板块**（FAQ 留给 A+ Content 模块呈现）
   - 将竞品痛点对应的卖点自然融入 "What Makes It Special?" 段落
   - 包含使用场景和人群定位
   - ⛔ **描述正文中不得出现 [MCP:xxx] 来源标签或竞品 ASIN**
5. **后台搜索词（Search Terms）** — 📋 可复制区
   - 249 bytes 上限
   - 排除已在标题/五点中出现的词
   - 聚焦同义词和场景词
6. **主图设计 Prompt** — 📊 分析参考区
7. **副图设计 Prompt**（6 张）— 📊 分析参考区
8. **A+ 内容设计 Prompt** — 📊 分析参考区
9. **视频脚本 Prompt** — 📊 分析参考区

### Step 6: 合规自审

**目标**：确保输出内容 100% 合规

1. 对照 `amazon-listing-writer/references/amazon_compliance_blacklist.md` 逐项检查
2. 检查项：
   - [ ] 无违禁促销词
   - [ ] 无未经验证的医疗/健康声明
   - [ ] 无农药/抗菌声明（除非有认证）
   - [ ] 无禁用特殊字符
   - [ ] 无 emoji
   - [ ] 标题字符数 <= 200（服装 <= 125）
   - [ ] Search Terms <= 249 bytes
   - [ ] 同一单词在标题中不超过 2 次
3. 发现违规项 → 自动替换为合规表达 → 标注替换记录

### Step 7: 数据溯源验证（最终自检）

**目标**：确保交付内容的每个数据点均可回溯

1. **生成数据溯源表**：
   | 数据点 | 出现位置 | 来源工具 | 调用参数 | 时间戳 |
   |--------|---------|---------|---------|--------|
   | 月搜索量 12,000 | 策略简报 | keyword_detail | "custom dog shirt" | 2026-xx-xx |
   | 差评痛点"掉色" | 五点 #3 | product_reviews | B0XXXXXX(Negative) | 2026-xx-xx |

2. **交叉校验**：
   - 每个事实描述 → 是否有 `[来源标签]`？
   - 每个竞品引用 → ASIN 是否在 Step 1 的竞品池中？
   - 每个搜索量数据 → 是否来自 `keyword_detail` 调用？

3. **清理**：无法回溯的数据点 → 删除或标注 `[待确认]`

4. **输出校验结果**：PASS（全部数据可回溯）/ FAIL（列出问题项）

> ⛔ Step 7 返回 FAIL 时，必须返回对应 Step 补充数据，不得交付。

---

## 硬性规则汇总

1. ⛔ **数据溯源**：所有数据点必须标注来源，严禁幻想数据
2. ⛔ **属性保守**：属性表缺失时使用品类通用值，标注 `[待供应商确认]`，严禁夸张
3. ⛔ **竞品最低量**：至少 5 个竞品 ASIN，不足自动补齐
4. ⛔ **合规检查**：对照违禁词库逐项过滤，违规自动替换
5. ⛔ **MCP 节奏控制**：每轮并发不超过 3 个 MCP 调用
6. ⛔ **事实一致性**：创作代理不得引入证据代理和逻辑代理未确认的事实
7. ⛔ **无最高级**：禁止 best、#1、top、most popular 等最高级表达
8. ⛔ **无 emoji**：标题和五点中禁止使用 emoji
9. ⛔ **字符/字节限制**：标题 <= 200字符，ST <= 249 bytes
10. ⛔ **Step 7 不可跳过**：数据溯源验证必须通过才能交付
11. ⛔ **输出可复制**：标题、五点、描述、Search Terms 正文中**禁止出现** MCP 来源标签（如 `[MCP:xxx]`）、竞品 ASIN（如 `B0XXXXXX`）、内部注释。这些内容必须是纯消费者语言，可直接复制到 Amazon Seller Central。来源引用集中在文末**数据溯源表**中。

---

## 中间数据持久化

每完成一个步骤，将核心数据保存至 `reports/listing/[产品关键词]/` 目录：

- `step1_competitor_pool.json` — 竞品 ASIN 池
- `step2_competitor_analysis.json` — 竞品详情 + 痛点分析
- `step3_keyword_matrix.json` — 关键词矩阵
- `step4_strategy_brief.md` — 策略分析简报
- `step5_listing_output.md` — 完整 Listing 内容
- `step6_compliance_report.md` — 合规检查报告
- `step7_data_provenance.md` — 数据溯源表
- `listing_visual.html` — **可视化展示页面**（含一键复制按钮，由 `render_listing_html.py` 生成）

### 崩溃恢复协议

遭遇 `ECONNREFUSED` 或 `unexpected EOF` 后：
1. 不要重复已完成的 MCP 调用，检查已保存的 `step*` 文件
2. 请用户确认 MCP 服务已恢复
3. 从断点继续

---

## 参考文档

- `amazon-listing-writer/references/amazon_compliance_blacklist.md`
- `amazon-listing-writer/references/rufus_cosmo_guide.md`
- `amazon-listing-writer/references/listing_output_spec.md`
- `amazon-listing-writer/references/prompt_templates.md`
