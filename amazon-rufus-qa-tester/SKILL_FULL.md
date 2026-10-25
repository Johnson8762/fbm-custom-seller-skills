---
name: amazon-rufus-qa-tester
description: 当用户要测试或评估一个亚马逊 Listing 的 Rufus/COSMO 适配性（95 分制评分卡、语义检索、COSMO 知识图谱、Rufus 问答模拟、用户信号、竞品差异化、改进方案和优化文案），通常在上架前验证或老品巡检时使用。
---

# amazon-rufus-qa-tester

## 运行环境（box）

- 报告保存：`reports/rufus-qa/[ASIN]_[日期].md`
- 输入可以是 ASIN 或用户粘贴的 Listing 文本
- Sorftime：box 上已接入 Sorftime MCP（`user-sorftime` 命名空间，先 `GetDynamicTools` 看参数再 `CallDynamicTool`）；脚本内调用用 `_shared/sorftime_http.py`（读环境变量 `SORFTIME_KEY`，**绝不打印**）。下文所有 `MCP:工具名` 都指这些 Sorftime 工具。
  - 产品 `product_detail` / `product_content`，评论 `product_reviews` / `product_customers_say`，流量词 `product_traffic_terms`，竞品 `competitor_product_keywords`，关键词 `keyword_detail` / `keyword_extends`
- 当前页面：`python amazon-listing-health-checker/fetch_amazon_page.py <ASIN>`
- 真实 Rufus 问答（可选）：box 浏览器已登录亚马逊买家账号，可在商品页打开 Rufus 输入测试问题并截取真实回答，与模拟结果对照；未实测时须注明「模拟」
- 原知识库 PDF/DOCX 未随技能打包，方法论已写在本文件中
- 相关：`amazon-listing-checker`（证据型诊断）、`amazon-listing-writer`（重写 Listing）

---


## 1. 技能定位

### 核心理念
**基于 COSMO 算法与 Rufus AI 购物助手的底层逻辑，对 Amazon Listing 进行全维度适配性测试。**

Rufus 是亚马逊 2025 年的核心流量入口，基于 COSMO 深度学习语义算法。本 Skill 通过 9 大板块的系统化诊断，帮助卖家：
- 量化评估 Listing 的 Rufus 适配性（95 分制）
- 识别语义缺失、属性缺失、逻辑断裂等问题
- 验证 Rufus 问答能力（实际问答场景测试）
- 生成优化后的 Title + 5 Bullets + Search Terms

### 知识库基础

本 Skill 基于以下知识库构建：
- 亚马逊全新流量入口-Rufus底层逻辑和应对策略.pdf
- COSMO与Rufus算法分析与运营策略.pdf
- 如何用Rufus写listing.pdf
- Rufus对流量的影响逻辑.pdf
- 2025 Rufus运营新玩法指南.docx
- 如何利用Rufus的QA功能做好Listing运营.docx
- 用Gemini3做出Rufus优化级别的listing撰写智能体.docx

### 工作流位置

```
新品上架流程：
  amazon-listing-writer → 【amazon-rufus-qa-tester：上架前验证】
      → 优化 → 上架

老品优化流程：
  定期巡检 → 【amazon-rufus-qa-tester】→ 发现问题 → 优化 → 复检
```

### 上下游

| 方向 | 技能 | 关系 |
|------|------|------|
| 上游 | amazon-listing-writer | Listing 创建完成后需要验证 Rufus 适配性 |
| 下游 | 人工优化 | 根据诊断报告优化 Listing |
| 下游 | 复检（再次调用本技能） | 优化后重新验证 |

---

## 2. 输入参数

```
/amazon-rufus-qa-tester <ASIN 或 Listing 文本> [产品类目] [核心关键词]
```

| 参数 | 必选 | 说明 | 示例 |
|------|------|------|------|
| ASIN 或 Listing 文本 | ✅ | 10 位 ASIN 或完整 Listing 文本 | B0XXXXXXX4 或 "Title: ...\nBullets: ..." |
| 产品类目 | ❌ | 产品类目（用于匹配 Rufus 高频问题库） | Travel Pillow, Yoga Mat, Dog Vest |
| 核心关键词 | ❌ | 3-5 个主要搜索词（逗号分隔） | "travel pillow, neck support, airplane pillow" |

### 输入方式示例

**方式 1：提供 ASIN**
```
/amazon-rufus-qa-tester B0XXXXXXX4 "Travel Pillow" "travel pillow, neck support"
```

**方式 2：提供完整 Listing 文本**
```
/amazon-rufus-qa-tester "
Title: Ergonomic Memory Foam Travel Pillow for Airplane
Bullets:
• DESIGNED FOR COMFORT - Memory foam core adapts to neck shape
• PORTABLE - Compact and lightweight
• EASY TO CLEAN - Machine washable cover
• VERSATILE - Perfect for airplane, train, car
• INCLUDES - Travel pouch and sleep mask
Description: ...
Search Terms: travel pillow, neck support, airplane pillow
" "Travel Pillow" "travel pillow, neck support"
```

---

## 3. 执行流程

### Step 0：输入解析与数据准备

**我会执行以下操作：**

1. **解析输入类型**
   - 如果是 ASIN：通过 WebFetch 抓取 Listing 数据
   - 如果是文本：直接解析 Title、Bullets、Description、Search Terms

2. **提取产品类目**
   - 如果用户提供：直接使用
   - 如果未提供：从 Listing 标题中推断

3. **提取核心关键词**
   - 如果用户提供：直接使用
   - 如果未提供：从 Title 和 Search Terms 中提取前 3-5 个高频词

4. **构建 Rufus 高频问题库**
   - 根据产品类目，构建 10-15 个 Rufus 高频问题
   - 如果类目没有专属问题库，使用通用问题库

5. **与用户确认**
   - 展示解析结果：产品类目、核心关键词、Rufus 问题库
   - 确认无误后开始执行

---

### Step 1：板块 1-2 — 算法评分卡（7 维度量化评分）

**我会对 Listing 进行 7 个维度的量化评分：**

#### 维度 1：语义检索匹配度（15 分）
- 检查 Listing 是否覆盖用户自然语言搜索意图
- Rufus 高频意图：舒适性、便携性、多功能性、卫生性、耐用性、性价比、适用场景、礼物属性

#### 维度 2：查询属性覆盖度（15 分）
- 检查 Listing 是否能回答 Rufus 高频问题
- 逐个验证 10-15 个问题的可回答性

#### 维度 3：COSMO 知识图谱对齐度（15 分）
- 检查 COSMO 四类关系：used for（用途）、capable of（功能）、isA（属性）、cause（优势）
- 检查逻辑链完整性：功能 → 场景 → 优势

#### 维度 4：隐式查询解析友好度（10 分）
- 检查隐式查询词覆盖：礼物场景词、节日词、人群词、场景词

#### 维度 5：Rufus 因果链充要度（15 分）
- 检查每个 Bullet Point 的因果链完整性

#### 维度 6：用户行为信号质量（15 分）
- 评分健康度、差评集中分析、QA 质量

#### 维度 7：可解释比较生成能力（10 分）
- 检查 Rufus 能否基于 Listing 生成产品对比

**输出：总分 X/95 + 等级判定 + 核心问题**

---

### Step 2：板块 3 — 语义检索匹配分析

**我会分析 4 个子维度：**

1. **已覆盖语义维度**：列出 Listing 中已包含的用户搜索意图
2. **缺失高意图语义维度**：列出用户高频搜索但 Listing 未提及的意图
3. **隐式查询未覆盖词库**：列出 Rufus 可能识别但 Listing 未埋入的隐式词
4. **属性值缺失字段**：列出产品属性表中有但 Listing 未体现的参数

---

### Step 3：板块 4 — COSMO 知识图谱节点诊断

**我会识别常识推理链断裂点：**

- 检查 COSMO 四类关系的完整性
- 标记逻辑链缺失环节
- 提供修复建议

---

### Step 4：板块 5 — Rufus 问答能力测试

**我会测试 Rufus 问答能力：**

1. 统计可直接回答、部分可回答、无法回答的问题数量
2. 生成问题测试表格（问题 | 状态 | 原因 | 建议）
3. 标注问题来源（Rufus 对话、竞品 QA、评论）

---

### Step 5：板块 6 — 用户行为信号诊断

**我会分析 3 个子维度：**

1. **评分健康度**：当前评分、评价数量、健康度评估
2. **差评集中分析**：高频差评关键词、Rufus 可能捕捉的负面信号
3. **风险点汇总**：高风险、中风险、低风险问题

---

### Step 6：板块 7 — 竞品差异化提取性

**我会测试 LLM 可读性：**

1. **可被 LLM 直接提取的卖点**：清晰、结构化、易于 AI 理解的卖点
2. **当前缺失的比较表达**：竞品有但本品 Listing 未体现的对比维度

---

### Step 7：板块 8 — 改进方案表格

**我会生成改进方案表格：**

| 问题类型 | 具体问题 | 优先级 | 改进方案 | 预期提升 |
|---|---|---|---|---|
| 语义缺失 | ... | 高/中/低 | ... | ... |
| 属性缺失 | ... | 高/中/低 | ... | ... |
| 逻辑断裂 | ... | 高/中/低 | ... | ... |

---

### Step 8：板块 9 — 优化后文案

**我会生成优化后的文案：**

1. **Optimized Title**：核心词 + 场景词 + 功能词，融入 COSMO 四类关系
2. **5 条 Bullets**：痛点狙击、场景沉浸、硬核参数、适用人群/礼物、售后/信任
3. **Backend Search Terms**：同义词、互补词、隐式查询词

---

## 4. 输出格式

### 4.1 Markdown 报告

生成完整的 Markdown 报告，包含 9 大板块的详细内容，保存至：
```
reports/rufus-qa/[ASIN]_[日期].md
```

### 4.2 YAML Frontmatter

报告顶部包含 YAML 元数据：
```yaml
---
title: Rufus QA 测试报告 - [产品名称]
date: 2026-04-01
asin: B0XXXXXXX4
category: Travel Pillow
keywords: travel pillow, neck support, airplane pillow
total_score: 66/95
grade: 需改进
tags:
  - rufus
  - qa-test
  - listing-optimization
type: 测试报告
status: 完成
---
```

---

## 5. Rufus 高频问题库

### 5.1 通用问题库

如果类目没有专属问题库，我会使用以下通用问题：

1. 这个产品的材质是什么？
2. 这个产品的尺寸是多少？
3. 这个产品适合什么场景使用？
4. 这个产品有什么优势？
5. 这个产品适合送礼吗？
6. 这个产品的质量如何？
7. 这个产品可以清洗吗？
8. 这个产品适合什么人群？
9. 这个产品的配送时间是多久？
10. 这个产品有售后保障吗？

### 5.2 类目专属问题库示例

**Travel Pillow（旅行枕）**：
1. 这个旅行枕适合长途飞行吗？
2. 会导致脖子僵硬吗？
3. 能放进随身行李吗？
4. 可以机洗吗？
5. 适合侧睡吗？
6. 材质会不会太硬/太软？
7. 有没有异味？
8. 适合什么身高/体型的人？
9. 会不会容易变形？
10. 有没有便携收纳袋？

**Yoga Mat（瑜伽垫）**：
1. 这个瑜伽垫防滑吗？
2. 厚度适合初学者吗？
3. 材质环保吗？
4. 容易清洁吗？
5. 适合热瑜伽吗？
6. 会不会有异味？
7. 尺寸适合高个子吗？
8. 耐用吗？
9. 便携吗？
10. 适合户外使用吗？

---

## 6. 核心算法逻辑

### 6.1 语义检索匹配度评分算法

```
评分 = (已覆盖意图数 / Rufus 高频意图总数) × 15
```

### 6.2 COSMO 知识图谱对齐度评分算法

```
评分 = (四类关系完整度 × 0.6 + 逻辑链完整度 × 0.4) × 15
```

### 6.3 Rufus 问答能力评分算法

```
评分 = (可直接回答数 × 1.0 + 部分可回答数 × 0.5) / 总问题数 × 15
```

### 6.4 用户行为信号质量评分算法

```
评分 = (评分健康度 × 0.5 + 评论质量 × 0.3 + QA 质量 × 0.2) × 15
```

---

## 7. 注意事项

1. **类目差异**：不同类目的 Rufus 高频问题不同，我会动态调整问题库
2. **实时更新**：Rufus 算法持续迭代，评分标准会定期更新
3. **合规优先**：优化建议必须符合亚马逊 Listing 合规要求
4. **数据隐私**：不保存用户的 ASIN 和 Listing 数据（除非用户明确要求）

---

## 8. 相关 Skills

- [[amazon-listing-writer]] - 生成 Rufus 优化级别的 Listing
- [[Image-Skill]] - 生成符合 Rufus 场景化需求的产品图
- [[custom-validator]] - 验证定制化产品的 Rufus 适配性

---

**Skill 版本**：v1.0  
**最后更新**：2026-04-01  
**作者**：<YOUR_NAME>  
**基于知识库**：Rufus&Cosmo 全系列文档
