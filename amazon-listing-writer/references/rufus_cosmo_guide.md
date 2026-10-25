# Rufus + COSMO 双算法优化指南

> Listing-Skill 参考文档。指导三代理在生成 Listing 内容时如何同时满足 Rufus（事实索引）和 COSMO（意图匹配）两套算法的要求。

---

## Rufus 优化（事实索引层）

### Rufus 是什么

Amazon Rufus 是 Amazon 的生成式 AI 购物助手，直接从 Listing 内容中提取信息回答消费者问题。如果 Listing 中缺少事实数据，Rufus 将无法推荐该产品。

### Rufus 喜欢的内容

| 类别 | 示例 | 说明 |
|------|------|------|
| 量化参数 | "3000mAh battery"、"304 stainless steel" | 可直接引用的硬数据 |
| 产品规格 | "Weight: 180g"、"Size: 12x8x3 inches" | 结构化的规格信息 |
| 材质说明 | "100% ring-spun cotton, 180 GSM" | 具体材质和克重 |
| 认证信息 | "UL certified"、"CE marked" | 可验证的认证标识 |
| 包装内容 | "Includes: 1x device, 1x USB-C cable, 1x manual" | 明确的包装清单 |
| 兼容性 | "Compatible with iPhone 15/14/13 series" | 具体型号列表 |

### Rufus 厌恶的内容

| 类别 | 示例 | 问题 |
|------|------|------|
| 模糊形容词 | "high quality"、"premium"、"top-notch" | 无法被索引，浪费位置 |
| 空洞承诺 | "best in class"、"industry leading" | 无法验证 |
| 纯情感词 | "amazing"、"incredible"、"gorgeous" | 不回答任何具体问题 |

### Rufus 写作规则

1. **每个 Bullet Point 至少包含 1 个可量化参数**
2. **FAQ 思维**：写每句话时问自己"这句话能回答消费者的什么问题？"
3. **参数优先**：先写数据，再写感受（"180 GSM ring-spun cotton provides all-day comfort"）
4. **不编造参数**：没有的数据宁可不写

---

## COSMO 优化（意图匹配层）

### COSMO 是什么

Amazon COSMO (Common Sense Knowledge behind Amazon Shopping Mission Understanding) 是 Amazon 的意图理解算法。它不看关键词匹配，而是理解消费者的购物任务（shopping mission）和使用场景。

### COSMO 的匹配逻辑

```
消费者意图: "我需要给狗狗生日派对准备一件定制T恤"
    ↓ COSMO 解析
场景: 宠物生日派对
人群: 狗主人
需求: 定制化 + 纪念意义 + 快速交付
    ↓ 匹配 Listing
含有"birthday"、"personalized"、"pet party"等场景词的产品
```

### COSMO 优化策略

1. **场景植入**：在五点和描述中自然嵌入使用场景
   - 差：`"Custom dog shirt with printed name"`
   - 好：`"Celebrate your pup's birthday or adoption day with a personalized name shirt"`

2. **人群明示**：让 COSMO 知道你的产品为谁设计
   - 差：`"Suitable for dogs"`
   - 好：`"Designed for small to medium breed dog owners who love matching outfits"`

3. **问题回答**：每个 Bullet Point 暗含一个常见问题的答案
   - 问题：这件狗狗衣服好洗吗？
   - Bullet：`"[EASY CARE] Machine washable at 30C, tumble dry low — keeps vibrant colors after 50+ washes"`

4. **场景词布局**：
   | 场景类型 | 关键词示例 |
   |---------|----------|
   | 事件场景 | birthday, holiday, party, photo shoot, adoption day |
   | 日常场景 | daily walk, outdoor adventure, home wear, travel |
   | 礼物场景 | gift for dog lovers, pet memorial, surprise gift |
   | 季节场景 | summer cooling, winter warmth, spring outdoor |

---

## 双算法协同检查清单

在生成每个 Listing 模块时，交叉验证：

### 标题
- [ ] 包含核心关键词（A9 SEO）
- [ ] 包含 1-2 个可量化参数（Rufus）
- [ ] 暗含使用场景或人群（COSMO）

### 五点（Bullet Points）
- [ ] 每点有 `[HEADER]` 方便扫读
- [ ] 前 2 点为最核心卖点（移动端截断优化）
- [ ] 每点至少 1 个量化参数（Rufus）
- [ ] 每点暗含 1 个使用场景（COSMO）
- [ ] 至少 1 点回应竞品高频痛点

### 产品描述
- [ ] FAQ 风格（Rufus 直接提取回答）
- [ ] 包含 "Who is this for?" 段落（COSMO 人群匹配）
- [ ] 包含 "When to use?" 段落（COSMO 场景匹配）
- [ ] 包含产品规格表（Rufus 事实索引）

### Search Terms
- [ ] 排除已在标题/五点中的词（避免浪费）
- [ ] 包含同义词和场景词
- [ ] 不超过 249 bytes
- [ ] 无品牌名/竞品名
