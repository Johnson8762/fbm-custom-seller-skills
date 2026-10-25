# Amazon Listing 违禁词库 v1.0

> 本文档为 Listing-Skill 内建的合规检查词库。创作代理在生成 Listing 后，必须对照本文档逐项检查。
>
> 版本：v1.0 — 基于 2025-2026 Amazon 政策整理
> 更新策略：实际使用中发现新的违规项时追加

---

## 1. 促销/营销词（Promotional Terms）

以下词汇/短语**禁止**出现在标题、五点、描述中：

```
Best Seller
#1 Product
#1 Best
Free Shipping
Discount
On Sale
Limited Offer
Limited Time
Best Price
Unbeatable Price
Super Sale
Spring Sale / Summer Sale / Winter Sale / Fall Sale
Huge Sale
Special Promo
Wholesale Price
Perfect Gift
Gift Idea
Buy Now
Act Now
Don't Miss
Hurry
Clearance
Closeout
Liquidation
```

**替换建议**：删除即可，不需要替换。卖点应通过产品事实来体现。

---

## 2. 未经验证的声明（Unverified Claims）

以下声明**禁止使用**，除非持有经 Amazon 审核的认证文件：

```
FDA Approved
EPA Registered
Clinically Proven
Clinically Tested
Dermatologist Tested
Doctor Recommended
Lab Tested
Scientifically Proven
100% Natural
100% Organic
100% Quality Guaranteed
100% Satisfaction Guaranteed
100% Value
Made in USA (unless verified via Amazon's program)
```

**替换建议**：
- "FDA Approved" → 删除，或改为描述产品符合的具体标准
- "Clinically Proven" → 删除
- "100% Natural" → "Made with natural materials"（如果材质确实是天然的）

---

## 3. 医疗/健康声明（Medical Claims）

以下医疗相关词汇**严格禁止**（除非产品为 Amazon 批准的医疗器械类目）：

```
cure / cures
treat / treats / treatment
heal / heals / healing
diagnose / diagnosis
prevent / prevents / prevention
remedy
therapeutic
medicinal
prescription
antibiotic
anti-inflammatory
pain relief / pain killer / pain management
blood pressure
cholesterol
diabetes
cancer
arthritis
anxiety
depression
ADHD
AIDS / HIV
immune deficiency
```

**替换建议**（语义降级）：
- "pain relief" → "comfort support" 或 "helps ease discomfort"
- "anti-inflammatory" → "soothing" 或 "calming"
- "healing" → "recovery support"
- "treats skin conditions" → "gentle on sensitive skin"

---

## 4. 农药/抗菌声明（Pesticide & Antimicrobial Claims）

以下词汇会触发 Amazon 的农药/抗菌政策审查，**除非产品有 EPA 注册**：

```
kills (germs/bacteria/viruses/bugs/insects)
repels (insects/mosquitoes/pests)
disinfects / disinfectant
sanitizes / sanitizer
antibacterial
antifungal
antimicrobial
antiviral
germicidal
pesticide
insecticide
herbicide
fungicide
mold resistant
mildew resistant
```

**替换建议**：
- "antibacterial" → "easy to clean"
- "repels insects" → 删除（除非有 EPA 注册）
- "kills 99.9% of germs" → 删除

---

## 5. 禁用特殊字符与格式（Forbidden Characters）

### 标题中禁止使用的字符：
```
!  (感叹号)
$  (美元符号，价格相关)
?  (问号)
_  (下划线)
{  }  (花括号)
^  (脱字符)
¬  ¦  (特殊排版符号)
★ ☆ ♥ ✓ ✔ ➤ ►  (装饰性符号)
所有 emoji 表情
```

### 标题中限制使用的字符（仅特定语境允许）：
```
|  (仅用于分隔产品标识符)
-  (仅用于连接词组或尺寸范围)
~  (仅用于近似值)
#  (仅用于型号编号)
<  >  (仅用于尺寸对比)
*  (仅用于注释引用)
```

### 全文禁止：
```
全角字符（如：（）【】）
HTML 标签（标题和五点中）
超链接 / URL
联系方式（电话、邮箱）
```

---

## 6. 标题格式规则（Title Policy）

| 规则 | 限制 |
|------|------|
| 最大字符数（通用） | 200 字符（含空格） |
| 最大字符数（服装/Apparel） | 125 字符（含空格） |
| 同一单词重复次数 | 最多 2 次（介词/冠词/连词除外） |
| Emoji | 完全禁止 |
| 全大写 | 仅品牌名和规范缩写允许全大写 |
| 促销文案 | 禁止（如 "Sale"、"Free Shipping"） |

---

## 7. 其他受限表达

### 对比/竞争类：
```
比 [竞品品牌] 更好
[竞品品牌] 替代品
compatible with [品牌] (需要经过品牌授权)
```

### 时效/库存类：
```
New Arrival
Just Launched
Limited Stock
Only X Left
Back in Stock
Pre-order
```

### 主观/无法验证类：
```
World's Best
Industry Leading
Revolutionary
Groundbreaking
Unmatched
Unparalleled
One of a Kind
```

**替换建议**：用具体数据替代主观描述
- "Industry Leading" → "Rated 4.8/5 by 10,000+ customers"（仅当数据真实时）
- "Revolutionary" → 描述具体创新点

---

## 快速自检清单

在最终输出前，逐项检查：

- [ ] 标题中无促销词
- [ ] 标题字符数不超限
- [ ] 标题中同一单词不超过 2 次
- [ ] 五点中无医疗声明
- [ ] 五点中无未经验证的认证声明
- [ ] 全文无 emoji
- [ ] 全文无禁用特殊字符
- [ ] Search Terms 不超过 249 bytes
- [ ] 无竞品品牌名
- [ ] 无主观最高级表达（除非有数据支撑）
