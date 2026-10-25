# 图片类型 Prompt 模板库

> Image-Skill 参考文档。按品类和图片类型提供即用型 Prompt 模板。

---

## 1. Hero Image 通用模板

```text
# Role: Professional Amazon Product Photographer & Prompt Engineer
# Context: Hero Image for Amazon listing — maximize CTR

[Product Description]
A {{product_name}} made of {{material}}, in {{color}}.
{{key_visual_features}}.

[Masterful Composition - Hero Angle]
The product is positioned at a {{angle}} to showcase {{what_angle_reveals}}.
Product occupies 85% of the frame, {{orientation}}.
{{additional_composition_notes}}.

[Professional Lighting]
{{lighting_mode}} setup: {{lighting_description}}.
{{secondary_light_if_applicable}}.

[Texture & Surface — CRITICAL]
{{material_specific_texture_description}}.
{{finish_description}}.
{{detail_visible_at_this_scale}}.

[Technical Quality]
Shot on {{lens}}mm lens, f/{{aperture}}, ultra-realistic, 8K resolution,
cinematic product photography. Color-accurate rendering, no color cast.

[Amazon Compliance — NON-NEGOTIABLE]
- Pure white background (Hex: #FFFFFF)
- No logos, no watermarks, no text overlay
- No props, no lifestyle elements
- Product only, clean and isolated
- Product occupies at least 85% of the frame
```

---

## 2. Hero Image 品类变体

### 2.1 服装类 Hero Image

```text
[Product Description]
A {{garment_type}} in {{color}}, made of {{fabric}}.
{{design_details: print/embroidery/pattern}}.

[Composition]
Worn by a {{gender}} model standing straight, front-facing,
arms relaxed at sides. Full body or 3/4 body shot.
Clean, confident pose. Product is the focus.

[Lighting]
Clamshell lighting — even illumination, no harsh shadows on the garment.
Light reveals fabric texture and print quality.

[Texture & Surface]
{{fabric}} with {{weave_pattern/knit_texture}}.
Print/embroidery shows {{quality_description: crisp edges, vibrant colors}}.
Natural fabric drape visible.

[Technical]
85mm f/5.6, 8K, photorealistic.

[Amazon Compliance]
Pure white background (#FFFFFF). No accessories unrelated to garment.
Model in natural pose, no excessive styling.
```

### 2.2 电子产品 Hero Image

```text
[Product Description]
A {{device_name}} in {{color/finish}}, featuring {{key_visual_elements}}.

[Composition]
3/4 hero view, tilted 15 degrees. Showcases the main interface/screen/panel
and side profile. Product occupies 85% frame.

[Lighting]
Clamshell lighting with controlled specular highlights on {{finish_type}} surface.
No excessive glare on screens or glossy surfaces.

[Texture & Surface]
{{finish: brushed aluminum / matte plastic / glossy polycarbonate}}.
Buttons and ports clearly visible and sharp.
LED indicators {{on/off}} as appropriate.

[Technical]
100mm f/11, 8K, ultra-sharp focus across entire product.

[Amazon Compliance]
Pure white background. Screen shows {{default/blank/branded}} display.
No power cables or accessories unless sold together.
```

### 2.3 家居用品 Hero Image

```text
[Product Description]
A {{item_name}} in {{color/material}}, {{dimensions}}.
{{design_style: modern minimalist / rustic / industrial}}.

[Composition]
{{45_degree_top_down / 3/4_hero / straight_on}} view.
Product centered, stable, well-balanced composition.

[Lighting]
Clamshell lighting, warm color temperature (5500K).
Soft shadows that suggest depth without distraction.

[Texture & Surface]
{{material_texture_details}}.
{{surface_finish}}.

[Technical]
85mm f/8, 8K, color-accurate.

[Amazon Compliance]
Pure white background. No food/decoration styling.
Show the item as a customer would receive it.
```

### 2.4 宠物用品 Hero Image

```text
[Product Description]
A {{pet_product}} in {{color/pattern}}, made of {{material}}.
Designed for {{pet_size_range}} {{pet_type}}.

[Composition]
3/4 hero view. If wearable by pet, show on a {{pet_type}} model.
If accessory/toy, show product isolated.

[Lighting]
Bright clamshell lighting, cheerful and inviting.
Reveals fabric/material quality clearly.

[Texture & Surface]
{{material_texture}}.
{{stitching/hardware details visible}}.

[Technical]
85mm f/5.6, 8K, photorealistic.

[Amazon Compliance]
Pure white background. Pet model allowed for wearable items.
No human hands visible in main image.
```

---

## 3. 辅图 6 类模板

### 3.1 Usage Context（场景使用图）

```text
# Secondary Image #1 — Usage Context
# Purpose: Answer "How do I use this product?"

[Scene]
{{realistic_usage_scenario}}.
Location: {{specific_location: modern kitchen / home office / dog park}}.
Time: {{time_of_day: morning sunlight / afternoon warmth}}.

[Human Interaction]
A {{demographic: young woman / middle-aged man / child}} is {{action: using / wearing / holding}} the {{product}}.
Expression: {{natural, pleased, focused}}.
The interaction feels genuine and unposed.

[Product Visibility]
Product is clearly visible and in sharp focus.
Key feature {{specific_feature}} is highlighted through the usage angle.

[Atmosphere]
{{Warm and inviting / Clean and professional / Active and energetic}}.
Color palette: {{scene_colors}} with product as the focal point.

[Lighting]
Natural {{window light / outdoor daylight / warm indoor light}}.

[Technical]
Lifestyle photography, shallow depth of field (f/2.8), 8K.
Background slightly blurred to keep focus on product.
```

### 3.2 Technical / Specs（技术参数图）

```text
# Secondary Image #2 — Technical Specifications
# Purpose: Answer "What are the exact specs?"

[Layout]
Product centered on a {{clean white / light grey}} background.
Dimension lines and callout labels overlaid.

[Callout Details]
- Callout 1: "{{dimension_1}}" with measurement line
- Callout 2: "{{material}}" pointing to surface
- Callout 3: "{{key_spec}}" with icon
- Callout 4: "{{weight/capacity}}" with indicator

[Visual Style]
Clean infographic style. Thin lines, modern sans-serif font.
Color accent: {{brand_color}} for callout boxes.

[Product Rendering]
Same angle as hero image for consistency.
Slightly scaled down to make room for annotations.

[Technical]
Clean vector-style overlay on photorealistic product, 8K.
```

### 3.3 Lifestyle Immersive（沉浸式生活方式图）

```text
# Secondary Image #3 — Lifestyle Immersive
# Purpose: Answer "Does this fit my lifestyle?"

[Scene]
{{aspirational_scene_description}}.
This is the "dream scenario" — the life the buyer aspires to.

[Environment]
{{Detailed environment: A sun-drenched minimalist loft with floor-to-ceiling
windows, concrete floors, and a single potted fiddle leaf fig}}.

[Product Placement]
Product placed {{on the marble coffee table / being used casually}}.
It belongs naturally in this environment — not staged.

[Atmosphere]
{{Premium, aspirational, effortless}}.
The viewer should think: "I want that life, and that product is part of it."

[Color & Mood]
{{Warm earth tones / Cool Scandinavian palette / Vibrant boho}}.
Consistent with brand identity.

[Lighting]
{{Golden hour natural light / Soft overcast daylight}}.
Cinematic depth with bokeh background.

[Technical]
Editorial lifestyle photography, 35mm f/1.8, 8K, magazine quality.
```

### 3.4 Close-up Detail（细节微距图）

```text
# Secondary Image #4 — Close-up Detail
# Purpose: Answer "Is the quality/craftsmanship good?"

[Focus Area]
Extreme close-up of {{specific_detail: stitching / button / connector / texture}}.
Fills 90% of the frame.

[What to Reveal]
- {{Detail 1: Hand-stitched saddle stitch with waxed thread}}
- {{Detail 2: Precision edge finishing}}
- {{Detail 3: Hardware quality — brushed metal zipper pull}}

[Background]
Blurred product body provides context without distraction.
Shallow depth of field isolates the detail.

[Lighting]
{{Raking light from the side}} to emphasize texture depth.
Every fiber/pore/grain is visible.

[Technical]
Macro lens, f/4, extreme detail, 8K.
The viewer should feel they can reach out and touch the material.
```

### 3.5 What's in the Box（开箱清单图）

```text
# Secondary Image #5 — What's in the Box
# Purpose: Answer "What exactly do I get?"

[Layout]
Flat lay / top-down view of all package contents.
Neatly arranged on a {{white / light}} background.

[Contents — Arranged Neatly]
- Main product (centered, largest)
- {{Accessory 1}} (positioned left)
- {{Accessory 2}} (positioned right)
- {{User manual / warranty card}} (positioned below)
- {{Packaging / gift box}} (background or corner)

[Visual Style]
Organized, symmetrical, satisfying arrangement.
Each item clearly separated with even spacing.
Labels optionally overlaid: "1× {{item}}", "1× {{item}}"

[Lighting]
Even overhead lighting, no harsh shadows.
Each item equally illuminated.

[Technical]
Top-down flat lay, f/11 for full sharpness, 8K.
```

### 3.6 Trust / Social Proof（信任背书图）

```text
# Secondary Image #6 — Trust & Social Proof
# Purpose: Answer "Can I trust this product/brand?"

[Layout Options — Choose One]
Option A: Certification & Quality Badges
- Display relevant certifications: {{FDA / CE / SGS / OEKO-TEX / RoHS}}
- Golden seal / badge design
- "Tested & Certified" tagline

Option B: Before/After or Comparison
- Side-by-side of {{our product feature}} vs {{generic alternative}}
- NOT using competitor brand names
- "Standard" vs "Our {{product}}" labeling

Option C: Satisfaction Guarantee
- Shield icon or guarantee badge
- "{{Satisfaction Guarantee / Free Replacement / Lifetime Warranty}}"
- Clean, trustworthy design

[Visual Style]
Professional, confidence-inspiring design.
Brand colors {{primary}} and {{secondary}} accent.
Modern, clean typography.

[Technical]
Infographic style, high contrast, 8K.
```

---

## 4. A+ Content 模板

### 4.1 品牌故事 Banner

```text
# A+ Module 1 — Brand Story Banner
# Size: 970 × 600 px

[Visual]
Wide cinematic shot: {{brand_atmosphere_scene}}.
Product subtly visible in the scene.
Brand logo in the {{upper-left / center-top}} corner.

[Text Overlay]
Headline: "{{Brand tagline / value proposition}}"
Subtext: "{{Brief brand story in one line}}"

[Color Palette]
Brand primary: {{color}}
Brand secondary: {{color}}
Text: {{white / dark}} for contrast

[Mood]
Aspirational, authentic, premium.
```

### 4.2 场景展示（× 3 张）

```text
# A+ Module 3 — Lifestyle Scene {{N}} of 3
# Size: 970 × 600 px

[Scene]
{{Specific_COSMO_scenario from Listing Skill strategy brief}}.

[Visual Consistency — CRITICAL]
Same lighting style as all other A+ images: {{specified_lighting}}.
Same color grading: {{specified_grading}}.
Same background texture family: {{specified_texture}}.

[Product]
Product naturally integrated into the scene.
Not staged — it belongs here.

[Technical]
Editorial quality, 8K, consistent with brand aesthetic system.
```

---

## 5. Ad Creative 三变体模板

### Variant A: Clean Product Focus

```text
# Ad Creative — Variant A: Clean Product Focus
# Format: 1200 × 628 px

[Visual]
Product on {{gradient / solid color}} background.
Clean, minimal, all attention on the product.
Product occupies 60% of frame (leaving room for ad copy).

[Text Safe Zone]
Right 40% reserved for headline and CTA.

[Key Message]
"{{Primary USP in 5 words or fewer}}"
```

### Variant B: Extreme Usage Scenario

```text
# Ad Creative — Variant B: Extreme Usage
# Format: 1200 × 628 px

[Visual]
{{Dynamic, action-packed scenario showing the product in extreme/impressive use}}.
High energy, compelling, stop-scrolling visual.

[Product Visibility]
Product clearly visible despite dynamic scene.
Brand logo subtly placed.

[Mood]
Exciting, impressive, aspirational.
```

### Variant C: Comparison Atmosphere

```text
# Ad Creative — Variant C: Comparison
# Format: 1200 × 628 px

[Visual]
Split composition: left side {{dull/ordinary}}, right side {{vibrant/premium}}.
Product is on the premium side.
Visual contrast conveys quality difference without naming competitors.

[Mood]
Confident, superior, evidence-based.
```

---

## 6. A/B Test 三维变量模板

### Test 1: Lighting Variation

```text
# A/B Test — Lighting
# Hypothesis: Moody lighting may increase perceived premium value and CTR

[Keep Same]
Product, angle, composition, background — all identical to original.

[Change]
Original: Bright Clamshell Studio Lighting
Variation: Moody Cinematic Lighting — single directional key light,
deeper shadows, warm color temperature, dramatic contrast.

[Full Modified Prompt]
{{Copy entire original prompt, replace only the [Lighting] section}}
```

### Test 2: Angle Variation

```text
# A/B Test — Angle
# Hypothesis: Low-angle view may convey more authority/premium feel

[Keep Same]
Product, lighting, background — all identical to original.

[Change]
Original: Eye-level / 3/4 hero view
Variation: Low-angle (Power View) — camera below product looking up,
creating an imposing, authoritative perspective.

[Full Modified Prompt]
{{Copy entire original prompt, replace only the [Composition] section}}
```

### Test 3: Shadow Variation

```text
# A/B Test — Shadow
# Hypothesis: Contact shadow may improve perceived "realness"

[Keep Same]
Product, lighting, angle — all identical to original.

[Change]
Original: Floating product, no shadow
Variation: Subtle contact shadow — soft diffused shadow directly
beneath the product, implying it sits on a surface.
Shadow opacity: 15-20%, feathered edges.

[Full Modified Prompt]
{{Copy entire original prompt, add shadow directive to [Composition]}}
```
