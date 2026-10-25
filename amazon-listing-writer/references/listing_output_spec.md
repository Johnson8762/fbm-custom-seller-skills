# Listing 输出格式规范

> Listing-Skill 参考文档。定义 9 个输出模块的结构和格式要求。

---

## 模块 1: 策略分析简报

```markdown
# 策略分析简报

## 产品: [产品关键词]
## 站点: [US/GB/DE/...]
## 生成日期: [YYYY-MM-DD]

### Rufus 核心事实（Top 5）
| # | 事实 | 来源 |
|---|------|------|
| 1 | [量化参数] | [MCP:xxx / 用户输入] |
| ... | ... | ... |

### COSMO 场景映射（Top 3）
| # | 场景 | 目标人群 | 核心需求 | 来源 |
|---|------|---------|---------|------|
| 1 | [使用场景] | [人群画像] | [需解决的问题] | [MCP:xxx] |
| ... | ... | ... | ... | ... |

### 差异化切入点
- **主打差异**: [xxx] — 依据: 竞品痛点 "[xxx]" 频次 [n/总数] [MCP:product_reviews:ASIN]
- **辅助差异**: [xxx]

### 关键词布局策略
- **标题主词**: [xxx] (月搜索量: [n]) [MCP:keyword_detail]
- **五点埋词**: [词1], [词2], [词3], ...
- **ST 补充词**: [词1], [词2], [词3], ...
```

---

## 模块 2: 标题（Title）

### 格式模板
```
[Brand] [Core Keyword] [Core USP] [Key Spec 1] [Key Spec 2] [for Target/Use]
```

### 规则
| 规则 | 要求 |
|------|------|
| 字符上限 | 200 字符（服装类 125 字符） |
| 首字母大写 | 每个实词首字母大写（介词/冠词小写） |
| 同一单词 | 最多出现 2 次 |
| 核心关键词 | 必须在前 80 字符内 |
| 品牌名 | 放最前面 |
| 禁止 | emoji、特殊字符、促销词 |

### 示例
```
GoodBoy Custom Dog Shirt Personalized Name Pet T-Shirt Soft Breathable Cotton for Small Medium Dogs
```

---

## 模块 3: 五点描述（Bullet Points）

### 格式模板
```
[HEADER IN CAPS] — [Benefit statement with quantified data]. [Supporting detail or scenario].
```

### 规则
| 规则 | 要求 |
|------|------|
| 数量 | 恰好 5 条 |
| 前 2 条 | 最核心卖点（移动端优先展示） |
| 每条长度 | 150-250 字符 |
| 量化参数 | 每条至少 1 个 |
| 场景植入 | 每条暗含 1 个使用场景 |
| 禁止 | emoji、HTML 标签、竞品名 |

### 示例
```
1. [PERSONALIZED DESIGN] — Add your pet's name and photo with vibrant UV printing that stays crisp after 50+ washes. Perfect for birthday parties, adoption anniversaries, or everyday walks.

2. [PREMIUM COMFORT] — Made from 180 GSM ring-spun cotton, soft and breathable for all-day wear. Available in sizes XS to 3XL, fitting dogs from 3 to 100 lbs.

3. [FADE-RESISTANT PRINTING] — 6-layer UV curing technology ensures colors stay vivid wash after wash, unlike competitor prints that peel within weeks. [来自竞品痛点分析]

4. [EASY TO MEASURE, EASY TO FIT] — Detailed size chart with video guide helps you find the perfect fit. If it doesn't fit, we'll remake it at no extra cost.

5. [THOUGHTFUL GIFT] — Comes in a branded gift box, ready to surprise any dog lover. Ideal for Christmas, birthdays, or "just because" moments.
```

---

## 模块 4: 产品描述（Product Description）

### 格式
- **叙述式 HTML 结构**（非 FAQ 风格）
- 可使用 HTML 标签（`<h2>`, `<p>`, `<br>`, `<b>`, `<ul>`, `<li>`）
- 禁止外部链接
- ⛔ **禁止 FAQ 板块** — FAQ 留给 A+ Content 展示，避免与 Amazon 原生 Q&A 功能冲突

### 结构模板
```html
<h2>Who Is This For?</h2>
<p>[目标人群和场景描述 — 来源: COSMO 场景映射]</p>

<h2>What Makes It Special?</h2>
<p>[核心差异化卖点 — 将竞品痛点对应的卖点自然融入叙述中]</p>
<p>[补充卖点：定制选项、可替换设计、材质特性等关键信息]</p>

<h2>Product Specifications</h2>
<ul>
  <li>Material: [xxx]</li>
  <li>Sizes Available: [xxx]</li>
  <li>Weight: [xxx]</li>
  <li>Care Instructions: [xxx]</li>
</ul>
```

> **原则**：买家常见疑问（如"是不是真皮？""会掉色吗？"）的答案应融入 "What Makes It Special?" 段落中，以自然叙述方式呈现，而非以 Q&A 格式列出。

---

## 模块 5: 后台搜索词（Search Terms）

### 规则
| 规则 | 要求 |
|------|------|
| 字节上限 | 249 bytes |
| 分隔符 | 空格（不用逗号） |
| 排除 | 已在标题/五点中出现的词 |
| 排除 | 品牌名、竞品名、ASIN |
| 聚焦 | 同义词、场景词、属性词 |
| 格式 | 全小写 |

### 示例
```
dog tee pet clothing canine apparel puppy outfit personalized name custom print photo gift birthday party matching owner
```

---

## 模块 6: 主图设计 Prompt

### 输出格式
```markdown
### 主图设计需求

**构图**: 纯白背景，产品居中，占画面 85% 以上
**角度**: [正面/45度/平铺] — 根据品类选择最佳展示角度
**质感**: 3D 渲染感，柔和阴影，专业产品摄影风格
**要求**:
- 无文字、无 logo 水印（Amazon 主图规则）
- 产品颜色准确还原
- 高分辨率 (至少 2000x2000px)
- [品类特殊要求，如服装需展示穿着效果]

**图片生成提示词**:
> [English prompt for AI image generation]
```

---

## 模块 7: 副图设计 Prompt（6 张）

### 6 张副图模板

| 图序 | 类型 | 内容 |
|------|------|------|
| 副图 1 | 功能图 | 展示核心功能/卖点，可带文字标注 |
| 副图 2 | 场景图 | 产品在使用场景中的展示 |
| 副图 3 | 规格图 | 尺寸标注、材质说明 |
| 副图 4 | 信任图 | 认证标识、好评截图、对比图 |
| 副图 5 | 细节图 | 工艺细节、材质纹理特写 |
| 副图 6 | 包装图 | 包装全貌、配件清单 |

每张图提供详细的设计需求和 AI 图片生成提示词。

---

## 模块 8: A+ 内容设计 Prompt

### 结构模板
```markdown
### A+ 内容设计需求

**风格**: [品牌色系/视觉风格]
**模块规划**:
1. **品牌故事 Banner**: 品牌理念 + 核心价值主张
2. **产品对比表**: 本品 vs 同品牌其他款式（非竞品对比）
3. **场景展示**: 3-4 个使用场景的生活方式图
4. **技术亮点**: 核心技术/工艺图解
5. **FAQ 图文**: 常见问题的可视化解答
6. **尺码指南**: 可视化尺码表（服装类）

**图片生成提示词**: [每个模块的提示词]
```

---

## 模块 9: 视频脚本 Prompt

### 结构模板
```markdown
### 视频脚本设计需求

**时长**: 15-30 秒
**风格**: [产品展示/生活方式/开箱]

**分镜**:
| 时间 | 画面 | 文字/配音 | 动作 |
|------|------|----------|------|
| 0-3s | [开场画面] | [品牌/产品名] | [吸引注意] |
| 3-10s | [核心卖点展示] | [主打卖点文案] | [产品特写] |
| 10-20s | [使用场景] | [场景化文案] | [真实使用演示] |
| 20-25s | [细节/差异化] | [技术亮点] | [工艺特写] |
| 25-30s | [CTA 结尾] | [品牌名 + 行动号召] | [Logo 展示] |

**AI 视频生成提示词**: [详细提示词]
```

---

## 交付格式

最终 Listing 输出保存为 Markdown 文件，包含以上全部 9 个模块，每个模块独立章节，并在文件头部标注数据来源汇总。
