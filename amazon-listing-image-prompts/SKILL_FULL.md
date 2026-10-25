---
name: amazon-listing-image-prompts
description: 当用户提供产品实物照片和产品信息，要生成或规划亚马逊图片资产（主图、辅图、场景图、信息图、A+ 图）及其英文 Prompt 时使用；产品一致性优先，严禁 AI 捏造产品细节。
---

# 亚马逊 AI 产品图片资产生成器（amazon-listing-image-prompts）

## 运行环境（box）——合并说明

本技能合并了原 `Image-Skill` 与 `Image-Skill-Gemini`（两者方法论相同，仅出图工具不同）。

- 出图工具：原 `generate_image` / `gemini_generate_image`（Gemini MCP）→ box 内置 **`GenerateImage`**（`cursor` 命名空间）
  - 参数：`description`（英文 Prompt）、`reference_image_paths`（**只放用户产品照片**，对应原 ImagePaths 隔离规则）、`aspect_ratio`（主图/辅图用 `1:1`，A+ 横幅用 `16:9`）、`filename`
  - 生成的文件需复制到 `reports/image-assets/[产品]/generated/`，参考照片与结构蓝图放 `reports/image-assets/[产品]/reference/`
  - 交付时给出生成图的 file:// 链接；每张图仍须按「规则 D」与实物照片逐项比对，不通过就重新生成
- 资料：`amazon-listing-image-prompts/references/`（合规指南、Prompt 工程词典、各类型模板）
- Prompt 可视化：`python amazon-listing-image-prompts/render_image_prompts_html.py <prompts.json> <out.html>`；示例输入 `amazon-listing-image-prompts/examples/sample_prompts.json`
- Sorftime：box 上已接入 Sorftime MCP（`user-sorftime` 命名空间，先 `GetDynamicTools` 看参数再 `CallDynamicTool`）；脚本内调用用 `_shared/sorftime_http.py`（读环境变量 `SORFTIME_KEY`，**绝不打印**）。下文所有 `MCP:工具名` 都指这些 Sorftime 工具。
- 竞品主图（规则 20）：用 Sorftime `product_content` / `product_detail` 取图片链接，或用浏览器打开亚马逊页面；竞品图只做人工分析，**绝不放进 reference_image_paths**
- 原 Gemini 版中的 Gemini 账号切换段（含个人邮箱）已删除，不适用于 box

---


## 定位

接收用户**产品实物照片**和产品信息，结合竞品视觉分析和买家关注点，使用内置 `GenerateImage` 工具**直接生成完整图片资产**，覆盖亚马逊所需的全部图片类型。

**核心理念**：图片不是"好不好看"的问题，而是**"点不点击"**和**"买不买"**的问题。主图决胜 CTR，辅图决胜 CVR，A+ 决定品牌溢价。

> ⛔ **最高优先级 — 产品一致性**：产品一致性高于一切视觉效果和创意表现。如果产品外观一致性与视觉效果发生冲突，**永远选择一致性**。

**上游**：`amazon-listing-writer`（Listing 策略简报 + 关键词布局）、`custom-product-research`（竞品数据）
**下游**：内置 `GenerateImage` 工具

## 目录结构

- `SKILL.md`（本文件 — 核心指令）
- `amazon-listing-image-prompts/references/amazon_image_compliance.md`（亚马逊图片合规指南）
- `amazon-listing-image-prompts/references/prompt_engineering_guide.md`（Prompt 工程指南 — 光影/角度/材质词典）
- `amazon-listing-image-prompts/references/image_type_templates.md`（各类型图片 Prompt 模板库）
- `amazon-listing-image-prompts/render_image_prompts_html.py`（HTML 可视化渲染器）
- `amazon-listing-image-prompts/image_prompt_template.html`（可视化模板）

---

## 产品一致性保障协议（最高优先级 — 贯穿所有 Step）

### AI 图片生成的固有限制

AI 图片生成本质上是**"重新创造"**而非**"精确编辑"**。即使传入参考照片，模型也可能：
- 改变硬件位置（翻盖/扣件/拉链位置偏移）
- 改变整体比例（变宽/变窄/变厚）
- 改变边角形态（直角变圆角、裸边变包边）
- 改变闭合结构（翻盖形状改变）
- **凭空编造未见过的产品细节**（最危险的问题）

### 规则 A：reference_image_paths 隔离原则

1. 每次 `GenerateImage` 调用**只传入用户产品照片**
2. **⛔ 严禁同时传入竞品照片和产品照片** — AI 会"融合"两个产品导致外观走形
3. 竞品照片**仅供人工分析**构图/风格/效果参考，**绝不传入 reference_image_paths**
4. 竞品照片中的效果（如激光雕刻、刺绣）应提取为**纯文字 Prompt 描述**，叠加到以用户产品照片为基底的生成中

### 规则 B：反捏造协议（Anti-Fabrication Protocol）

> ⛔ **核心原则：只生成你确认知道的，不确认的绝不生成。**

AI 图片生成器会在没有信息的地方"自由发挥"。以下是必须遵守的反捏造规则：

| 规则编号 | 场景 | 禁止行为 | 正确做法 |
|----------|------|---------|---------|
| B-1 | **产品内部结构** | 禁止生成用户未提供照片的产品内部/打开状态 | 只展示用户实物照片中出现过的角度和状态。如需展示内部，必须先向用户索要内部照片 |
| B-2 | **页数/厚度/体积** | 禁止让 AI 自由想象产品厚度 | 根据用户提供的参数（如 96 页）在 Prompt 中明确约束: "thin notebook, only 96 pages, approximately X mm thick" |
| B-3 | **颜色变体** | 禁止生成用户未确认的颜色款式 | 只展示用户明确告知存在的颜色。如需对比图，先向用户确认有哪些颜色可选 |
| B-4 | **五金件/硬件行为** | 禁止想象产品打开时五金件的状态 | 如无用户打开状态照片，不生成产品打开图。翻盖/扣件的行为逻辑必须符合物理现实 |
| B-5 | **包装/赠品/配件** | 禁止编造用户未确认的任何附属物品 | 开箱图只展示用户明确列出的内容物 |
| B-6 | **产品表面细节** | 禁止添加产品上不存在的纹理/图案/文字 | 只在用户要求展示定制效果时才添加，且必须标注为"定制效果展示" |
| B-7 | **场景中的附属物品** | 禁止在场景中添加与产品无关的暗示性物品 | 场景道具只使用通用物品（如桌子、咖啡杯），不暗示产品功能 |
| B-8 | **内部视图结构蓝图** | 禁止在无结构蓝图的情况下生成任何内部/打开状态视图 | 先从参考照片提取结构蓝图（组件清单 + 精确位置 + 连接方式 + 禁止关系），Prompt 中必须包含完整蓝图关键节点，生成后逐组件验证位置和存在性 |

### 规则 C：定制/个性化效果生成策略

当需要展示定制效果（激光雕刻/刺绣/印花等）时：

1. **只传产品照片**到 reference_image_paths — 竞品的定制效果照片仅供人工参考风格
2. Prompt 中必须包含**产品锁定锚点**:
   ```
   CRITICAL: Maintain the EXACT same product as the reference photo — same shape, same closure mechanism, same hardware positions, same edge treatment, same proportions. The personalization (engraving/embroidery) is a SURFACE TREATMENT ONLY — do not alter any physical feature of the product.
   ```
3. 生成后立即与实物照片比对: 翻盖形状? 扣件位置? 边角处理? 比例?
4. 任何物理特征变形 → 重新生成，不可交付

### 规则 D：生成后强制比对清单

每张生成图交付前，必须逐项检查（与用户实物照片对比）：

- [ ] 闭合结构（翻盖/拉链/按扣）形状和位置一致
- [ ] 五金件（按扣/拉链头/D环）数量和位置一致
- [ ] 边角处理（直角/圆角/裸边/包边）一致
- [ ] 整体比例（长宽比/厚度）与产品参数一致
- [ ] 材质纹理风格一致
- [ ] 未出现用户未确认的细节（颜色变体/内部结构/配件等）

> ⛔ 任一项不通过 → 必须重新生成，不可交付

### 规则 D-Interior：内部视图专属验证清单

> ⛔ 对每张内部/打开状态的生成图，必须在通用规则 D 之外**额外执行**以下逐组件验证：

| 检查项 | 检查内容 | 对照物 |
|--------|----------|--------|
| ☐ 组件完整性 | 结构蓝图中列出的**每个组件**是否都出现了？缺失任何一个即不通过 | 结构蓝图 |
| ☐ 组件位置（左/右） | 每个组件是否在正确的侧面？（如：拉链袋在后盖内侧 = 右侧） | 参考照片 |
| ☐ 组件相对位置 | 组件之间的上下/前后/重叠关系是否正确？ | 参考照片 |
| ☐ 组件尺寸比例 | 每个组件的相对大小是否合理？（不得大于其所在面板） | 参考照片 |
| ☐ 连接关系 | 组件是否正确地"附着/缝合"在皮面上？禁止出现漂浮/悬空 | 参考照片 |
| ☐ 无多余组件 | 是否出现了蓝图中**没有**列出的组件/零件/孔洞？ | 结构蓝图 |
| ☐ 外皮颜色 | 外层皮革颜色是否与参考一致？ | 参考照片 |
| ☐ 内衬颜色 | 内衬/绒面颜色是否与参考一致？（常见错误：金棕→深棕） | 参考照片 |
| ☐ 金属件 | 活页环数量、按扣数量/位置、金属颜色是否正确？ | 参考照片 |
| ☐ 翻盖形态 | 翻盖的形状（三角形等）、有无孔洞/铆钉是否与实物一致？ | 参考照片 |

> ⛔ **任一项不通过 → 必须重新生成**。内部视图的结构准确性高于一切美学效果。

---

## 输入规范

### 必选输入

| 输入项 | 说明 |
|--------|------|
| **产品关键词** | 如 `custom dog shirt`、`leather notebook`、`stainless steel water bottle` |
| **产品实物照片** | 1-3 张产品实拍照片（不同角度更佳）。**这是保证产品一致性的核心输入**，所有 `GenerateImage` 调用都必须将此照片传入 `reference_image_paths` 参数 |

### 可选输入

| 输入项 | 说明 |
|--------|------|
| **竞品/风格参考照片** | 竞品照片**仅供人工分析**构图/风格/效果参考，⛔ **严禁传入 reference_image_paths** |
| 产品属性 | 材质、颜色、尺寸、重量等物理特征 |
| 目标站点 | 默认 `US`，影响审美偏好和合规要求 |
| 品牌名 | 用于 A+ 内容的品牌一致性设计 |
| 品类 | 如 `服装`、`电子`、`家居`、`宠物`，影响模板选择 |
| 上游策略简报 | `amazon-listing-writer` 输出的策略分析简报路径 |
| 竞品 ASIN 列表 | 用于分析竞品视觉策略 |
| 指定模块 | 可只生成部分模块（如仅主图 + 辅图） |

### 产品照片使用规范

1. 用户提供实物照片后，首先保存到 `reports/image-assets/[产品]/reference/` 目录
2. 每次调用 `GenerateImage` 时，**必须**将产品照片路径传入 `reference_image_paths` 参数
3. ⛔ **竞品照片严禁传入 reference_image_paths** — 只供人工分析参考
4. Prompt 中必须包含产品锁定锚点（见规则 C）
5. Prompt 中必须用产品实际参数约束物理特征（如页数→厚度、尺寸→比例）

### 产品可见性边界（Visibility Boundary）

> ⛔ **只生成你见过的**。用户提供了哪些角度/状态的照片，就只生成那些角度/状态。

| 用户提供的照片 | 可以生成 | 不可以生成 |
|---------------|---------|-----------|
| 封面正面照 | 封面各角度合成图 | 产品打开后的内部结构 |
| 封面 + 打开状态照 | 封面 + 打开状态的各种场景 | 用户照片中未出现的内部细节 |
| 仅外观照，无颜色变体确认 | 仅用户照片中的颜色 | 其他颜色变体（黑色/绿色等） |
| 无包装/配件照片或确认 | 产品本体 | 包装盒/赠品/配件 |

**如需展示用户未提供照片的产品状态**：
1. 先向用户索要对应状态的实物照片
2. 用户确认"没有照片但可以生成"后，才能生成，且 Prompt 中必须基于用户口述的详细描述，不可自由发挥

**当用户已提供内部/打开状态照片时的额外强制要求**：

> ⛔ 内部视图是 AI 幻觉的重灾区。必须执行以下额外流程：

1. **执行结构蓝图提取**（见规则 B-8）：逐张分析参考照片，提取每个可见组件的名称、精确位置（以书脊为中心的左右坐标）、与周围组件的空间关系、连接方式（缝合/铆接/夹持）、材质和颜色
2. **生成结构蓝图文档** `reference/structural_blueprint.md`，格式：
```markdown
## [产品名] 结构蓝图

### 打开状态俯视布局
[LEFT COVER INTERIOR] | [SPINE/RINGS] | [RIGHT COVER INTERIOR]

### LEFT COVER INTERIOR 组件清单
- 组件1: [名称], 位置: [描述], 尺寸: [占面积比], 连接: [方式], 材质: [描述]

### RIGHT COVER INTERIOR 组件清单
- 组件1: ...

### 组件间禁止关系
- [组件X] 不得出现在 [位置Y]
- [组件X] 和 [组件Z] 不得重叠
```
3. **Prompt 必须使用 Interior View Template**（见辅图模板 - Interior View 专属模板）
4. **生成后执行 D-Interior 专项验证清单**（见规则 D-Interior）

### 输入降级策略

当用户仅提供产品关键词而无详细属性时：
1. 通过 `product_search` + `product_detail` 获取品类通用的视觉特征
2. 通过 `product_reviews` 提取买家最关注的视觉细节（如"颜色准不准""质感如何"）
3. 根据品类自动匹配最佳模板组合
4. 所有推测属性标注 `[品类推断-待确认]`

> ⛔ **无产品照片时的降级处理**：如果用户未提供产品实物照片，仅生成 Prompt 文本，不调用 `GenerateImage`。明确告知用户需要提供产品照片才能生成图片。

---

## MCP 工具清单

| 工具 | 用途 | 调用时机 | 优先级 |
|------|------|---------|--------|
| `product_search` | 搜索竞品，获取视觉参考基准 | Step 0 | 📋 按需（无上游数据时） |
| `product_detail` | 获取竞品产品图片数量、规格、变体 | Step 0 | 📋 按需 |
| `product_reviews`（Positive） | 提取买家对视觉的正面评价（颜色好看/质感好等） | Step 0 | 📋 按需 |
| `product_reviews`（Negative） | 提取买家对视觉的不满（色差/图片不符/质感差等） | Step 0 | 📋 按需 |
| `similar_product_feature` | 查询品类产品特征，确定视觉呈现重点 | Step 0 | 📋 按需 |

> ⚠️ **节奏控制**：如果已有上游 `amazon-listing-writer` 的策略简报，可跳过大部分 MCP 调用。独立使用时才需执行完整数据采集。

---

## 完整执行流程 (Step 0 - 6)

### Step 0: 输入解析 + 视觉情报采集

1. **解析输入**：确认产品关键词、属性、品类、站点
2. **产品照片确认**：
   - 确认用户提供的实物照片数量和角度
   - 将照片保存到 `reports/image-assets/[产品名]/reference/`
3. **竞品主图参考获取**（自动降级逻辑）：
   - 如用户提供了参考照片 → 直接使用用户参考照片
   - 如用户**未提供参考照片** → 自动通过 `product_search` 搜索品类 Top 3 竞品 → 通过 `product_detail` 获取竞品主图 URL → 下载保存到 `reference/competitor_*.jpg`
   - 竞品主图用途：参考构图角度、场景风格，**不可复制竞品品牌元素**
4. **上游数据检查**：
   - 如有 `amazon-listing-writer` 策略简报 → 提取核心卖点、差异化切入点、目标人群、使用场景
   - 如无上游数据 → 执行 MCP 数据采集（`product_search` → `product_detail` → `product_reviews`）
5. **视觉情报提取**：
   - 从竞品评论中提取**视觉相关关键词**（颜色、质感、尺寸视觉、包装印象）
   - 识别买家**视觉痛点**（色差、图片不符实物、质感廉价感等）
   - 确定品类的**视觉基准**（该品类通常使用什么角度、什么背景）
6. **包装/配件确认**：
   - 向用户确认实际包装内容（包装盒、赠品、配件等）
   - **未经用户确认的物品，严禁出现在任何图片中**

**输出**：视觉策略简报（Visual Strategy Brief）

```markdown
## 视觉策略简报

### 产品视觉特征
- 核心材质: [xxx] — 视觉呈现: [xxx texture/finish]
- 核心颜色: [xxx]
- 形态特征: [软性/硬性/规则/不规则]
- 尺寸感知: [需要参照物 / 直观明了]

### 竞品视觉基准
- 主图角度: [品类常用角度]
- 辅图侧重: [该品类辅图通常展示什么]
- 视觉短板: [竞品图片的常见问题]

### 买家视觉关注点
- 正面: [买家最赞赏的视觉点]
- 负面痛点: [色差/不符/廉价感等]

### 差异化视觉策略
- [基于痛点的视觉差异化方向]
```

---

### Step 1: Module 1 — 主图 Hero Image（决胜 CTR）

> 主图是亚马逊流量的生死门。核心不是"好看"，而是**"点击欲望"**。

#### 执行策略

1. **确定产品类型**：
   - **定制产品 (Custom/Personalized)** → 主图**必须展示定制后的效果**（如刻字、刺绣、印花），让买家一眼看到"定制后是什么样"
   - **标准产品** → 主图展示产品最佳角度和特征

2. **参考图选择**（reference_image_paths 策略 — 遵循规则 A 隔离原则）：
   - **必传且唯一**：用户产品实物照片（reference_image_paths 只放产品照片）
   - ⛔ **严禁将竞品照片传入 reference_image_paths** — 竞品照片仅供人工分析构图/风格
   - 对于定制产品：人工分析竞品定制效果照片的风格，将效果用**纯文字 Prompt**描述，叠加到产品照片基底上
   - Prompt 中必须包含产品锁定锚点（见产品一致性保障协议 - 规则 C）
   - Prompt 中必须包含产品物理参数约束（如: "thin notebook with only 96 pages"）

3. **选择 Hero Angle**：
   - 3/4 Hero View（默认） — 展示正面 + 侧面立体感
   - 正面平视 — 对称型产品（如手表、手机壳）
   - 45° 俯视 — 餐具/收纳/小物件
   - 穿戴展示 — 服装/配饰类（Amazon 允许服装主图使用模特）

4. **设定光影模式**：
   - **Clamshell Lighting**（默认） — 消除硬阴影，突出轮廓
   - **Rembrandt Lighting** — 质感产品（皮革/金属/木材）
   - **Rim Light** — 需要突出轮廓的透明/半透明产品

5. **材质质感描述**：参考 `amazon-listing-image-prompts/references/prompt_engineering_guide.md` 的材质词典

6. **合规约束**：参考 `amazon-listing-image-prompts/references/amazon_image_compliance.md`

#### 主图 Prompt 结构

```text
# Role: Professional Amazon Product Photographer & Prompt Engineer
# Context: Hero Image for Amazon listing — maximize CTR

[Product Description]
A [product name] made of [material], in [color], [key visual feature].

[Masterful Composition - Hero Angle]
The product is positioned at a [angle] to showcase [what this angle reveals].
Product occupies 85% of the frame. [Orientation: portrait/landscape].

[Professional Lighting]
[Lighting mode] setup: [specific description of light behavior on this material].
[Secondary light details if applicable].

[Texture & Surface — CRITICAL]
[Material-specific texture description from prompt_engineering_guide.md]

[Technical Quality]
Shot on [lens], [aperture], ultra-realistic, 8K resolution, cinematic product photography.
Color-accurate rendering, no color cast.

[Amazon Compliance — NON-NEGOTIABLE]
- Pure white background (Hex: #FFFFFF)
- No logos, no watermarks, no text overlay
- No props, no lifestyle elements
- Product only, clean and isolated
```

---

### Step 2: Module 2 — 辅图 Secondary Images × 6（决胜 CVR）

> 辅图的任务是**消除疑虑、拉动转化**。每张图回答一个购买决策问题。

#### 6 张辅图策略流

| 图序 | 类型 | 核心问题 | 设计方向 |
|------|------|---------|---------|
| 副图 1 | **Usage Context（场景使用图）** | "这个产品怎么用？" | 产品在真实使用场景中，有人物互动 |
| 副图 2 | **Technical / Specs（技术参数图）** | "具体参数是什么？" | 尺寸标注、材质标识、AI 辅助生成信息图 |
| 副图 3 | **Lifestyle Immersive（沉浸式生活方式图）** | "适合我的生活吗？" | 高级感场景（现代厨房/极简书房/户外），氛围感 |
| 副图 4 | **Close-up Detail（细节微距图）** | "做工靠谱吗？" | 工艺细节、材质纹理、缝线/按钮/接口特写 |
| 副图 5 | **What's in the Box（开箱清单图）** | "买到手有什么？" | **仅展示用户确认的实际包装内容**，严禁编造赠品/配件 |
| 副图 6 | **Trust / Social Proof（信任背书图）** | "别人用得好吗？" | 认证标识、好评截图风格、竞品对比氛围 |

#### 每张辅图 Prompt 结构

```text
# Goal: [Image Type] for [Product Name]
# Amazon Secondary Image #[N]

[Scene Description]
Scenario: [Detailed scene description]
Environment: [Indoor/Outdoor, specific location]
Time of Day: [Morning light / Afternoon warmth / Evening ambiance]

[Atmosphere & Mood]
Overall Feel: [Warm/Cool/Professional/Cozy/Premium]
Color Palette: [Dominant colors in the scene]

[Product Placement]
Position: [On table / In hand / Being worn / Flat lay]
Interaction: [How a person interacts with the product, if applicable]
Product Visibility: [What features/angles are shown]

[Lighting]
[Scene-appropriate lighting description]

[Technical]
Style: [Editorial photography / Lifestyle photography / Product infographic]
Resolution: 8K, photorealistic, depth of field.

[Text Overlay — If Applicable]
[For infographic-style images: specify callout text, arrows, dimensions]
```

#### Interior View 专属 Prompt 模板

> ⛔ 所有内部/打开状态视图**必须使用此模板**，不得使用通用辅图模板。结构准确性优先于美学效果。

```text
# INTERIOR VIEW — STRUCTURAL FIDELITY MODE
# ⚠️ This is an interior/opened product view.
# Structural accuracy takes ABSOLUTE priority over aesthetic quality.

[STRUCTURAL BLUEPRINT — MANDATORY]
Product: [product name] opened flat, viewed from [angle]
Layout: LEFT COVER INTERIOR | SPINE ([ring type]) | RIGHT COVER INTERIOR

LEFT COVER INTERIOR — Components (listed top to bottom):
1. [Component name]: Located at [exact position on left panel],
   covers approximately [X]% of panel area,
   [connection method: sewn/riveted/clipped] to the [suede/leather] surface,
   material: [material description], color: [color]
2. [Next component]: ...

RIGHT COVER INTERIOR — Components (listed top to bottom):
1. [Component name]: Located at [exact position on right panel],
   covers approximately [X]% of panel area,
   [connection method] to the [surface],
   material: [material description], color: [color]
2. [Next component]: ...

[SPATIAL PROHIBITIONS — CRITICAL]
- Do NOT place [component X] on the [LEFT/RIGHT] side — it belongs on the [opposite] side
- Do NOT add any holes, studs, rivets, or hardware not specified in the blueprint above
- Do NOT create any pockets, slots, or compartments not listed in the blueprint above
- [Component X] must be PHYSICALLY ATTACHED TO [surface Y], not floating or separate
- Do NOT alter the closure flap shape — maintain [exact shape description, e.g. triangular, no holes]
- The total number of [rings/snaps/hardware] must be exactly [N], no more, no less

[MATERIAL & COLOR ANCHORS — from reference photos]
- Exterior leather: [exact color and texture description]
- Interior suede/lining: [exact color — be specific, e.g. "golden amber tan" not just "brown"]
- Metal hardware: [exact color, e.g. "brushed silver" or "antique brass"]
- Edge treatment: [raw/finished/painted]

[PHYSICAL ANCHOR — PRODUCT IDENTITY]
Maintain EXACT same product as reference: same closure flap shape,
same hardware positions, same edge treatment, same proportions.
The scene context is SECONDARY — product structure must not change.

[SCENE CONTEXT — Secondary priority, apply ONLY after structure is locked]
Scenario: [scene description]
Props inside pockets: [what items are shown, if any]
Lighting: [lighting description]
Style: Editorial product photography, 8K, photorealistic
```

> ⚠️ **Prompt 填写规则**：
> 1. `STRUCTURAL BLUEPRINT` 段的内容必须直接来自 `reference/structural_blueprint.md`
> 2. `SPATIAL PROHIBITIONS` 必须列出**至少 3 条**具体禁令，根据过往生成失败经验定制
> 3. `MATERIAL & COLOR ANCHORS` 必须从参考照片中实际提取颜色，不可使用泛称
> 4. `SCENE CONTEXT` 放在最后，权重最低——AI 必须先确保结构正确，再处理场景

---

### Step 3: Module 3 — A+ Content Images（品牌溢价）

> A+ 是品牌讲故事的地方。核心是**视觉风格一致性**，让整个页面像一本品牌画册。

#### A+ 模块规划

| 模块 | 类型 | 内容 |
|------|------|------|
| A+ 模块 1 | **品牌故事 Banner** | 品牌理念 + 核心价值主张，全幅大图 |
| A+ 模块 2 | **产品对比表** | 本品不同款式/规格对比（非竞品对比） |
| A+ 模块 3 | **场景展示 × 3** | 3 个核心使用场景的生活方式大图 |
| A+ 模块 4 | **技术亮点图解** | 核心工艺/技术的可视化解说 |
| A+ 模块 5 | **FAQ 图文** | 常见问题的可视化解答 |
| A+ 模块 6 | **尺码/规格指南** | 可视化尺码表或规格参照图 |

#### A+ 一致性约束

```text
# Design Language: Contemporary minimalist brand aesthetic
# Color Palette: [Brand primary] + [Brand secondary] + [Neutral]
# Typography Style: [Clean sans-serif / Modern serif]

Visual Consistency Rules:
1. All images share the same [lighting style] — [e.g., soft natural daylight]
2. All images share the same [background texture] — [e.g., warm linen / cool concrete]
3. Color grading must be consistent — [e.g., warm tones with +10 warmth]
4. If using models, maintain same [ethnicity/age range/style] across all images
5. Maintain consistent [shadow direction] and [shadow softness] throughout
```

---

### Step 4: Module 4 — 广告素材 Ad Creative Variants（ROAS 倍增）

> 广告需要**多样性赛马**。在分钟级生成多种风格素材，快速测试最优组合。

#### 三变体赛马策略

| 变体 | 风格 | 适用场景 |
|------|------|---------|
| **Variant A** | Clean Product Focus | Sponsored Products 广告，干净产品展示 |
| **Variant B** | Extreme Usage Scenario | Sponsored Brands 视频，极端/夸张使用场景 |
| **Variant C** | Comparison Atmosphere | Sponsored Display，对比暗示，高级感氛围 |

#### 广告素材 Prompt 结构

```text
# Ad Creative — Variant [A/B/C]
# Campaign Type: [Sponsored Products / Brands / Display]
# Goal: [Click / Brand Awareness / Retargeting]

[Visual Concept]
[Detailed description of the visual approach for this variant]

[Key Message Focus]
Primary USP to convey: [xxx]
Visual emphasis on: [xxx]

[Composition]
[How the product is framed for ad context — may differ from listing images]

[Mood & Color]
[Variant-specific atmosphere]

[Format Specifications]
Aspect Ratio: [1:1 / 16:9 / 9:16]
Safe Zone: [Text-safe area specification]
```

---

### Step 5: Module 5 — A/B 测试变体（科学增长）

> 数据胜过感觉。为每张关键图生成测试变量，用数据找到最优组合。

#### 三维测试变量

基于主图（或指定图片）生成 3 个测试变体：

| 维度 | 原版 | 变体描述 |
|------|------|---------|
| **光影** | Bright Studio | → Moody / Cinematic lighting |
| **角度** | Eye-level | → Low-angle (Power View) |
| **投影** | Floating (no shadow) | → Contact shadow / Reflection |

#### A/B 测试 Prompt 结构

```text
# A/B Test Variation — Based on [Original Image Type]
# Test Hypothesis: [What we're testing and why]

[Base Configuration — Same as Original]
Product: [same product description]
Background: [same]
Technical: [same]

[Variable Being Tested]
Original: [current setting]
Variation: [new setting]
Rationale: [Why this change might improve CTR/CVR]

[Full Modified Prompt]
[Complete prompt with the single variable changed]
```

---

### Step 6: 输出交付 + 合规终审

#### 交付物清单

| 序号 | 文件 | 内容 |
|------|------|------|
| 1 | `step0_visual_strategy.md` | 视觉策略简报 |
| 2 | `step1_hero_image.md` | 主图 Prompt + 设计策略 |
| 3 | `step2_secondary_images.md` | 6 张辅图 Prompt + 策略 |
| 4 | `step3_aplus_content.md` | A+ 各模块 Prompt + 一致性约束 |
| 5 | `step4_ad_creatives.md` | 3 个广告变体 Prompt |
| 6 | `step5_ab_test.md` | A/B 测试变体 Prompt |
| 7 | `generated/` | **所有生成的图片文件**（主图 + 辅图 + A+ + 广告 + A/B 测试） |
| 8 | `reference/` | 用户提供的产品实物照片和竞品参考图 |
| 9 | `image_prompts_visual.html` | 全部 Prompt + 生成图片可视化页面 |

#### 合规终审检查清单

对每个 Prompt 逐条检查：

- [ ] 主图：纯白背景 (#FFFFFF)，无水印/logo/文字
- [ ] 主图：产品占比 ≥ 85%
- [ ] 主图：无道具/无生活方式元素（服装类允许模特）
- [ ] 辅图：文字标注清晰可读（如有）
- [ ] 所有图片：无裸露/暴力/敏感内容指示
- [ ] 所有图片：分辨率要求 ≥ 2000×2000px
- [ ] A+ 图片：符合模块尺寸规范
- [ ] 广告素材：符合广告位尺寸和安全区规范
- [ ] 所有 Prompt：无竞品品牌名

> ⛔ 合规检查不通过 → 自动修正 Prompt 中的违规描述 → 标注修正记录

---

## 中间数据持久化

每完成一个模块，将数据保存至 `工作成果/image_prompts/[产品关键词]/` 目录：

```
工作成果/image_prompts/[产品关键词]/
├── reference/                    # 用户提供的参考图片
│   ├── product_photo_1.jpg        # 产品实物照片
│   ├── product_photo_2.jpg        # 多角度实物照片（可选）
│   └── competitor_ref.jpg         # 竞品参考图（可选）
├── generated/                    # AI 生成的图片资产
│   ├── hero_image.png             # 主图
│   ├── secondary_1_usage.png      # 副图 1
│   ├── secondary_2_specs.png      # 副图 2
│   ├── ...                        # 副图 3-6
│   ├── aplus_1_banner.png         # A+ 模块 1
│   ├── ...                        # A+ 模块 2-5
│   ├── ad_variant_a.png           # 广告变体 A
│   ├── ...                        # 广告变体 B-C
│   └── ab_test_*.png              # A/B 测试变体
├── step0_visual_strategy.md       # 视觉策略简报
├── step1_hero_image.md            # 主图 Prompt
├── step2_secondary_images.md      # 辅图 Prompt × 6
├── step3_aplus_content.md         # A+ Content Prompt
├── step4_ad_creatives.md          # 广告素材 Prompt × 3
├── step5_ab_test.md               # A/B 测试变体 Prompt × 3
└── image_prompts_visual.html      # 全部可视化页面
```

---

## 硬性规则汇总

### 产品一致性（最高优先级）

1. ⛔ **产品一致性至上**：产品一致性高于一切视觉效果和创意表现。如一致性与效果冲突，永远选择一致性
2. ⛔ **reference_image_paths 隔离**：每次 `GenerateImage` 调用只传入用户产品照片。⛔ 严禁同时传入竞品照片 — AI 会融合两个产品
3. ⛔ **产品锁定锚点**：每个 Prompt 必须包含产品外观锁定描述（见规则 C），明确约束产品不可变形
4. ⛔ **生成后强制比对**：每张图交付前必须与实物照片逐项比对（见规则 D 清单），任一项不通过则重新生成

### 反捏造（Anti-Fabrication）

5. ⛔ **禁止生成未见过的产品状态**：用户未提供照片的产品角度/状态（如打开后的内部、背面等），必须先向用户索要照片或获得明确许可后才能生成
6. ⛔ **物理参数约束**：产品的页数/厚度/尺寸/重量必须在 Prompt 中用具体数值约束（如 "thin notebook, only 96 pages, approximately 10mm thick"），禁止让 AI 自由想象
7. ⛔ **颜色变体须确认**：禁止生成用户未明确告知存在的颜色款式。如需对比图，先向用户确认可选颜色
8. ⛔ **五金件行为逻辑**：产品打开/使用时，五金件（翻盖/扣件/拉链）的行为必须符合物理现实。如无打开状态照片参考，不生成产品打开图
9. ⛔ **禁止无中生有**：包装、赠品、配件、产品表面不存在的纹理/图案/文字，必须由用户明确确认后才能出现
10. ⛔ **场景道具克制**：场景中的附属物品不得暗示产品不具备的功能或特征

### 图片合规与质量

11. ⛔ **主图纯白**：主图背景必须是 #FFFFFF 纯白，无例外
12. ⛔ **无水印文字**：主图严禁任何 logo、水印、文字（产品自身的定制文字如激光雕刻/刺绣除外）
13. ⛔ **产品占比**：主图产品至少占画面 85%
14. ⛔ **材质精准**：Prompt 中的材质描述必须与产品实际材质一致，不得美化
15. ⛔ **A+ 一致性**：A+ 所有图片必须共享相同的光影/色调/背景风格
16. ⛔ **英文 Prompt**：所有图片生成 Prompt 必须使用英文
17. ⛔ **合规终审不可跳过**：Step 6 合规检查必须通过才能交付

### 流程与路径

18. ⛔ **图片输出路径**：所有生成图片必须保存到 `reports/image-assets/[产品]/generated/`，不得保存在会话目录或项目根目录
19. ⛔ **定制产品主图**：如果产品为定制/个性化类型，主图必须展示定制后的效果（如刻字/刺绣/印花成品），不可只展示空白产品
20. ⛔ **竞品参考自动获取**：当用户未提供参考照片时，必须在 Step 0 自动通过 MCP 获取竞品主图（仅供人工分析，⛔ 不传入 reference_image_paths）
21. ⛔ **内部视图需蓝图**：任何内部/打开状态视图的生成，必须先完成结构蓝图提取（规则 B-8），生成 `reference/structural_blueprint.md`。Prompt 中必须逐组件描述位置和连接关系，不可笼统描述
22. ⛔ **空间禁止描述**：内部视图 Prompt 必须包含明确的 `SPATIAL PROHIBITIONS` 段——列出至少 3 条不应出现的组件/位置/关系的具体禁令，防止 AI 填充想象。禁令应基于过往生成失败的经验定制
23. ⛔ **内部视图专项验证**：内部视图生成后必须执行 D-Interior 逐组件验证清单（10项），任一组件的位置/存在性/颜色不通过则必须重新生成，结构准确性高于一切美学效果

---

## 与上游 Skill 衔接协议

### 接收 amazon-listing-writer 数据

当 Listing Skill 包含图片相关输出（模块 6-9）时：
1. **复用策略简报**：直接使用 Listing Skill 的 Rufus 核心事实、COSMO 场景映射、差异化切入点
2. **增强 Prompt 深度**：将 Listing Skill 的粗框架 Prompt 扩展为专业级完整 Prompt
3. **保持数据溯源**：保留上游的来源标注，新增视觉分析数据单独标注

### 独立使用模式

当独立运行（无上游数据）时：
1. 执行完整的 Step 0 数据采集
2. 自建视觉策略简报
3. 所有数据点标注 MCP 来源
