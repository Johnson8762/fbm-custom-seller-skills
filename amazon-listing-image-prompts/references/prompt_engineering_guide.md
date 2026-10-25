# AI 图片 Prompt 工程指南

> Image-Skill 参考文档。标准化 Prompt 的结构、词汇和技术参数。

---

## 1. Prompt 结构框架（5 层模型）

每个完整的产品图片 Prompt 应包含以下 5 层，按顺序排列：

```
Layer 1: [Product Description] — 什么产品、什么材质、什么颜色
Layer 2: [Composition]        — 角度、构图、产品占比
Layer 3: [Lighting]            — 光影模式、光源方向、阴影特征
Layer 4: [Material & Texture]  — 材质质感的精确描述词
Layer 5: [Technical & Constraints] — 镜头参数、分辨率、合规约束
```

### 示例：完整 5 层 Prompt

```text
[Product Description]
A handmade crazy horse leather notebook, A5 size, dark brown color,
with visible natural grain patterns and slight color variations.
Wraparound cover with leather strap closure.

[Composition]
3/4 hero view angle, product tilted 15 degrees to the right,
showcasing front cover and spine simultaneously.
Product occupies 85% of the frame, centered.
Portrait orientation.

[Lighting]
Rembrandt lighting setup from upper left at 45 degrees.
Key light creates a soft gradient across the leather surface,
highlighting the grain texture. Subtle fill light on the right
to prevent deep shadows. Warm color temperature (5000K).

[Material & Texture — CRITICAL]
Crazy horse leather surface shows natural pull-up effect —
lighter streaks where the leather bends. Matte finish with
subtle waxy sheen. Visible pores and natural imperfections
that prove authenticity. Edge finish shows hand-burnished
darker border.

[Technical & Constraints]
Shot on 85mm f/8 lens, ultra-realistic, 8K resolution.
Pure white background (#FFFFFF).
No logos, no watermarks, no text.
Color-accurate to actual dark brown leather.
```

---

## 2. 光影模式词典

### Clamshell Lighting（蛤壳灯光）
- **特点**：前方上下两盏灯，消除硬阴影，轮廓均匀
- **适用**：大部分 Amazon 主图（默认推荐）
- **Prompt 描述**：
```
Clamshell lighting setup — main key light positioned directly above
at 45 degrees, fill light below to eliminate harsh shadows.
Soft, diffused professional studio light creating even illumination
across all product surfaces. Minimal shadow, maximum clarity.
```

### Rembrandt Lighting（伦勃朗灯光）
- **特点**：45° 侧光，产生三角形光影，突出质感
- **适用**：皮革、木材、金属等需要展示质感的产品
- **Prompt 描述**：
```
Rembrandt lighting from upper left at 45 degrees, creating a
distinctive triangle of light on the shadow side. Rich tonal
gradation that emphasizes surface texture and material depth.
Warm, dimensional lighting that conveys premium craftsmanship.
```

### Rim Light / Edge Light（轮廓光）
- **特点**：从后方/侧后方照射，勾勒产品轮廓
- **适用**：透明/半透明产品、需要突出形状的产品
- **Prompt 描述**：
```
Strong rim light from behind, creating a luminous edge outline
around the product silhouette. Separates the product from the
background with a halo-like glow. Combined with soft frontal
fill light for balanced exposure.
```

### Natural Daylight（自然日光）
- **特点**：模拟窗边自然光，温暖柔和
- **适用**：生活方式辅图、场景图
- **Prompt 描述**：
```
Natural sunlight streaming through a large window from the left,
creating soft dappled shadows and warm golden highlights.
Golden hour quality light (warm 4500K color temperature).
Ambient light fills the room naturally.
```

### Moody / Cinematic（暗调电影感）
- **特点**：低调光影，高对比度，戏剧性
- **适用**：A/B 测试变体、高端品牌、广告素材
- **Prompt 描述**：
```
Cinematic low-key lighting with dramatic contrast. Single directional
key light creating deep, intentional shadows. Dark, moody atmosphere
with rich blacks and selective highlights on key product features.
Film-grade color grading with slight desaturation.
```

---

## 3. 角度词汇表

| 英文术语 | 中文 | 视觉效果 | 适用品类 |
|---------|------|---------|---------|
| **3/4 Hero View** | 3/4 英雄视角 | 展示正面 + 侧面，立体感最强 | 默认首选，适用大部分产品 |
| **Eye-Level Straight-On** | 平视正面 | 对称、正式、直观 | 手表、手机壳、相框 |
| **45° Top-Down Angle** | 45° 俯视 | 同时看到顶面和正面 | 餐具、收纳盒、小工具 |
| **Flat Lay / Top-Down** | 平铺俯拍 | 展示全部配件/套装 | 包装清单、配件组合 |
| **Low Angle (Power View)** | 仰视/力量视角 | 产品显得高大、有力量感 | 工具、运动装备、电子设备 |
| **Close-up Macro** | 微距特写 | 展示细节、纹理、工艺 | 手工制品、珠宝、皮具 |
| **Profile / Side View** | 侧面轮廓 | 展示厚度/深度 | 笔记本、手机、书籍 |
| **Exploded View** | 爆炸分解图 | 展示内部结构/组件 | 电子产品、组装家具 |
| **In-Hand / Scale Reference** | 手持/比例参照 | 展示实际大小 | 小物件需要尺寸感知的 |

---

## 4. 材质描述词典

### 皮革类（Leather）
```
Genuine leather / Full-grain leather / Crazy horse leather / PU leather / Vegan leather

Surface: natural grain patterns, visible pores, slight color variation
Finish: matte / semi-gloss / waxy sheen / oil-tanned patina
Texture: supple, soft to touch, hand-feel warmth
Pull-up effect: lighter streaks where leather bends (for crazy horse/oil-tanned)
Edge: hand-burnished, clean-cut, raw-edge, painted edge
Stitching: saddle-stitched, hand-stitched with [color] thread
```

### 金属类（Metal）
```
Stainless steel / Aluminum / Brushed nickel / Chrome / Copper / Brass

Surface: brushed texture with linear micro-grooves / mirror-polished / satin finish
Reflection: subtle glints from studio light / controlled specular highlights
Texture: industrial precision / hand-hammered artisan imperfections
Finish: powder-coated matte / anodized / electroplated
```

### 棉布/织物类（Fabric & Textile）
```
Ring-spun cotton / Organic cotton / Polyester blend / Canvas / Linen / Silk

Surface: visible weave pattern / smooth jersey knit / ribbed texture
Drape: soft natural folds / structured stiffness / flowing movement
Texture: breathable micro-perforations visible / fuzzy brushed finish
Print: vibrant sublimation / embroidered raised texture / screen-printed matte
```

### 木材类（Wood）
```
Bamboo / Walnut / Oak / Pine / Maple / Teak / Reclaimed wood

Surface: natural wood grain running [direction], visible growth rings
Finish: lacquered gloss / hand-oiled matte / raw unfinished / wax-sealed
Texture: smooth sanded / rough-hewn / live-edge natural bark
Color variation: natural light-to-dark gradient, knots, character marks
```

### 塑料/硅胶类（Plastic & Silicone）
```
ABS plastic / Polycarbonate / TPU / Food-grade silicone / BPA-free Tritan

Surface: glossy injection-molded / matte textured grip / frosted translucent
Finish: piano gloss / soft-touch rubber coating / anti-fingerprint matte
Transparency: crystal clear / frosted semi-transparent / opaque solid color
```

### 陶瓷/玻璃类（Ceramic & Glass）
```
Porcelain / Stoneware / Borosilicate glass / Crystal / Tempered glass

Surface: smooth glazed finish / rustic unglazed / hand-thrown irregularities
Reflection: controlled glass reflections / ceramic matte non-reflective
Transparency: (glass) clear with visible light refraction / color-tinted
Glaze: consistent gloss / reactive glaze with unique color pooling
```

---

## 5. 负面提示词（Negative Prompt 参考）

> 用于防止 AI 生成常见问题。根据工具不同可在 negative prompt 或正向约束中使用。

### 通用负面提示词
```
Avoid: blurry, out of focus, low quality, pixelated, grainy,
watermark, logo, text overlay, signature, border, frame,
oversaturated colors, unrealistic proportions, distorted perspective,
extra objects, cluttered background, artificial glow
```

### 产品图片专用负面提示词
```
Avoid: incorrect material texture, wrong number of components,
floating products without ground shadow, unnatural color cast,
plastic-looking when should be [actual material], symmetry errors,
inconsistent lighting direction across surfaces, background not pure white
```

### 人物/模特场景负面提示词
```
Avoid: extra fingers, deformed hands, unnatural body proportions,
cross-eyed, blurry face, aging artifacts, uncanny valley expression,
culturally insensitive elements
```

---

## 6. AI 工具适配说明

### 内置 `generate_image` 工具
- 直接使用完整的 5 层 Prompt
- 支持直接生成，结果保存为 artifact
- 适合快速原型和迭代
- Prompt 建议长度：100-300 词

### Midjourney
- 使用 `/imagine` 命令格式
- 在 Prompt 末尾添加参数：`--ar 1:1 --v 6 --style raw`
- 使用 `--no` 标签放置负面提示词
- 质量参数：`--q 2` 获得最高质量

### Flux (fal.ai)
- 使用完整的描述性 Prompt
- 支持 ControlNet 进行姿态/边缘控制
- 适合需要精确控制的产品图
- 支持 img2img 进行风格迁移

### DALL·E (OpenAI)
- 描述性自然语言 Prompt 效果最佳
- 不需要技术参数（如镜头/光圈）
- 支持 inpainting（局部修改）
- 适合创意类和生活方式场景图

---

## 7. Prompt 优化技巧

### 权重控制
- 将最重要的描述放在 Prompt 前部（attention window）
- 使用具体数字代替模糊形容词（"85% of frame" vs "large"）
- 重复关键质感词增加权重（"matte leather, genuine matte finish"）

### 一致性保持
- 为系列图片建立 **Style Anchor**：
```
[Style Anchor — Apply to ALL images in this set]
Color grading: warm tones, +5 warmth, slight amber cast
Shadow quality: soft diffused, no hard edges
Background consistency: all pure white / all warm linen texture
Lighting angle: all from upper-left 45 degrees
```

### 迭代优化
1. 先生成粗版 → 识别问题
2. 在 Prompt 中 **明确排除** 问题元素
3. **增加具体性** 到问题区域（如质感描述从 2 词增加到 10 词）
4. 保持其他部分不变，只改变一个变量
