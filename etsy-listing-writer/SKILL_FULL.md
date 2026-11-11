# Etsy Listing 撰写（etsy-listing-writer）完整版

本技能面向定制类目、按单定制不备库存的店铺。下面的费用模型示例按墨西哥卖家、结算币种 MXN、可选 RFC 档位编写；请对照你自己店铺的现行 Etsy 费用复核。

## 0. 硬规则（任何一步都适用）
1. **只存草稿，绝不发布**；不改其他在售 listing（除非用户明确批准该条）。进入卖家后台须用户当次授权；只使用已保存的登录会话，不输入密码。
2. **Renewal 一律 Manual**；已在售且为 Automatic 的先列清单给用户，不直接改。
3. **Who made**：按使用者确认的真实生产情况填写，不要猜成某一个固定值；生产合作方、运费模板发货地由使用者在后台如实填写，Agent 不代填。
4. **不写发货地/产地**（ships from / Made in / 海外仓 / 省市名）；运费模板由用户在后台如实填写。
5. **AI 效果图可用**，但每条至少 1 张未修图实拍；描述必须写 AI 效果图说明；后台 AI 选项按实际勾。人形/宠物/全家福抱枕 **03 号位留空**给老板上传实拍，不传占位图。
6. 抱枕类描述必须保留「**选无白边会明显变形**」提醒；**不出现 3D Hug / arms-out** 相关文案、tags、图片。
7. **不编数据**：每个数字注明来源（EverBee 日期 / Etsy API 抓取时间 / 使用者确认 / 供应商页 / 使用者提供的成本），拿不到写「未取得」。EverBee 没标周期就不称"月搜索量"，近义词量不相加。
8. 汇率：成本 CNY→USD 使用 `data/etsy_fees.json` 里的示例规划汇率（默认 6.5，按你的成本口径替换，不是官方汇率）；USD↔MXN 用当日 open.er-api（写明数据时间）。
9. 折扣由老板手动设置（圣诞折扣等），**Agent 不动折扣**；算价时 买家实付 = 标价 × (1 − 折扣)。
10. 如需发飞书，使用你自己的通知脚本；`--text` 里不出现裸 `$`（写 US$ / MX$ 前先转义或用全角）；仅在用户明确要求时发送。没有明确指令不发邮件。

## 1. 产出
一个产品按消费场景输出**多条 listing**（每个场景/人群细分一条）。每条：标题、13 tags、描述、Personalization、变体与价格、类目/属性、图片顺序与 alt、处理时间、运费、退货、分区、Renewal、AI 使用、Who made，以及来源说明与事实核对清单。

## 2. 标准流程
### 第 0 步：数据源
- 搜索量 **只来自 EverBee**（Etsy API 不给）。使用已保存的登录会话；进入需要额外授权的环境前须得到用户当次同意。
- 批量查：搜索框英文逗号分隔多词；导出失败就人工照抄成 CSV（表头 `keyword,volume,competition,score,source`），source 写「EverBee 日期（UI as displayed）」，报告注明人工照抄；K/M 值用 `scripts/parse_everbee_ui.py`。
- 词序/单复数分开统计，主词把几种写法都查，按最高的选。
- 竞争度、价格、可定制占比：Etsy API v3 `/listings/active`（`scripts/keyword_scan.py`），冲突以 Etsy API 实时数据为准。

### 第 1 步：竞品 + VOC + 场景拆解（必做）
- 竞品只在 Etsy 站内找（Highest Reviews / Best Match / Bestseller），5–10 条；记录链接、标题、价格（起价不含运费）、评论、收藏；Etsy API 交叉核对。
- `scripts/review_voc.py`：我方 + 3–5 家竞品评论 → 主题计数、原话摘录；文案卖点要对应 VOC（「VOC → 文案句子」对照表）。
- 场景 → 人群细分两级归类，按「搜索量合计、竞品数、Bestseller 占比」排序；季节窗口例外（如 10–12 月先上圣诞款）需写明。

### 第 2 步：选词
- EverBee 量 + Etsy API 竞争 → 主词/辅词/长尾。Score 高、竞争 <5K 的词靠前；竞争 >500K 的泛词不占 tag 位。
- 查不到的词进「待查词清单」，本次标「未取得」。

### 第 3–5 步：标题 / Tags / 描述
- 标题 ≤140 字符，人能读懂，核心词靠前（建议 6–12 词，最多 14 词）；不用商标词、主观词。
- 13 个 tags，每个 ≤20 字符，只用字母数字空格 - '；每个 tag 在报告里标 EverBee 量或「未查」。
- **防自家抢词**：每条一个独占主词；标题前 3 个词不同；任意两条共用 tags ≤4（理想 ≤2，如纪念抱枕 vs 异地恋人形抱枕只共用 person shaped pillow / custom body pillow）；主推场景分开（纪念场景留给纪念款）。
- 描述按场景改开头，通用模块：SIZE GUIDE（size = 最长边，cm≈in 对照，≥35 cm 真空包装需拍松）、白边/无白边（同价，无白边会明显变形）、TIMING（以 facts.json 为准）、预览与修改、退换（定制品不退，出问题私信）、AI 效果图说明。婴儿相关加 "decorative keepsake, not for a crib or infant sleep"。
- 只写产品事实清单里有的：`products/<id>/facts.json`（模板见 `products/_template/facts.json`）。不要把真实产品事实清单提交到公开仓库。

### 第 6 步：定价（MXN）
- 费用模型示例见 `data/etsy_fees.json`（墨西哥卖家、MXN、RFC 两档的**示例**，不是经核对的现行官方费用；请按你的店铺现行费率改表）：有 RFC 15.625% × 买家实付 + 13.6 MXN/单；无 RFC 33.125% + 13.6；若被收站外广告再减 15 个百分点。
- 引擎 `scripts/pricing.py`（下面的价格和折扣都是示例，不是店铺报价）：
  - `margin --list 500 --cost-cny 30 [--discount 20]`：看利润率
  - `floor --cost-cny 50 --target-margin 30 --discount 20`：最低标价
  - `from-paid --paid-usd 25 --discount 20`：目标实付 → 标价（实付 ÷ (1 − 折扣)）
  - `match --ref-list 700 --ref-cost-cny 60 --cost-cny 40 45 --discount 20`：参考一档的利润率，推其他尺寸的标价
  - `table rows.json --md`：出 A/B/C 档位表（标价、实付、费用、成本、净利、有/无 RFC、站外广告）
- 成本只用使用者提供的分尺寸落地成本（含工厂价 + 头程/尾程）；没有就不算利润，列为缺口。

### 第 7 步：图片
- 交给 etsy-listing-image-generator（逐图验收、03 号位、alt ≤250 终图后写）。listing 稿里只放顺序、来源与 alt 复制框。

### 第 8 步：交付前风险检查（2026-11-08 增补；借鉴 Tony11081 listing-auditor 的审查思路）
逐项写结论（通过 / 风险 / 待确认 + 证据），**风险不等于违规**：
1. **低价变体**：数字/PNG 等低价变体会成为搜索起价 → 标题、主图不能让人以为实物是这个价；描述写清低价变体交付什么（如 Only Png Pic = 预览确认后经 Messages 发 PNG，不发实物）。`validate_listing.py --pricing` 会提示。
2. **主图与实际选项一致**：首图展示的尺寸/款式/白边状态必须是可选项；个性化首图需是定制成品。
3. **折扣价格证据**：涉及折扣的利润、"原价/折后"说法须有后台或老板确认截图/时间；Agent 不动折扣。
4. **相似链接定位**：同产品多链接的主词、标题前 3 词、tags 重合、主推场景是否分开（避免自己抢流量、避免被判重复 listing）。
5. **工艺/成本/安全**：对照 `references/manufacturing-checklist.md`（与图片技能共用一份）；缺供应链、材质、安全资料时列阻塞项，不捏造可销售产品。
6. **披露**：AI 图说明、生产合作方、Who made、发货地如实。
7. **IP/商标**：标题、tags、图上文字、设计元素。

### 第 9 步：校验与交付
- `scripts/validate_listing.py drafts.json --product <photo_pillow|person_pillow|memorial_pillow|dog_vest|generic> --facts products/<id>/facts.json --everbee <csv> --pricing --deliverable <交付稿.md>`，0 ERROR 才交付；WARN 在附录逐条解释。
- **交付格式**：最上面总目录（几条链接、各自场景、ID）→ 每条链接：来源说明（竞品 · 标签 · 场景 · 定价依据 · 事实归属）→ 按 Etsy 后台顺序逐项（1 照片与视频 / 2 标题 / 3 类目 / 4 属性 / 5 描述 / 6 变体 / 7 个性化 / 8 Tags / 9 处理时间 / 10 运费 / 11 退货 / 12 分区 / 13 续期 / 14 AI 使用 / 15 Who made / 16 事实核对清单），**每项一个复制框，框内不夹解释** → 附录 A 校验结果。需要粘贴的文字放代码块。
- md + html 两份存到 `artifacts/etsy_rewrite/` 或 `reports/<project>/`（本地目录，不要提交真实交付稿）。

### 第 10 步：存草稿（仅在用户授权该条时）
1. 使用用户当次授权的已登录卖家会话；不要输入密码；不要打开与本任务无关的账号或环境。
2. 只 Save as draft，绝不发布；上传图片每张填 alt（≤250）；保存后重新打开核对并逐项截图；把草稿 ID、截图、缩略图总览交给用户。
3. 店里没有的分区（如 Memorial Pillows）先设 None 并报告；材质下拉没有精确词时选最接近项并报告。

## 3. 脚本
| 脚本 | 用途 | 状态 |
|---|---|---|
| `scripts/etsy_client.py` | Etsy API v3 只读客户端；`x-api-key: ETSY_API_KEY:ETSY_SHARED_SECRET`，缺 key 清楚报错 | 原文 + 增补 |
| `scripts/fetch_shop.py` | 店铺 + 在售 listing + 评论 | 原文（10-25） |
| `scripts/keyword_scan.py` | 关键词实时 listing 数、中位价、可定制占比 | 原文（10-25） |
| `scripts/parse_everbee_ui.py` | EverBee 界面照抄 CSV（K/M）解析 + 场景求和 | 原文（10-25） |
| `scripts/review_voc.py` | 评论 VOC | 原文（10-25） |
| `scripts/validate_listing.py` | 校验（见第 9 步） | 随本技能提供 |
| `scripts/pricing.py` + `data/etsy_fees.json` | 定价引擎（示例费率） | 随本技能提供 |
| `products/_template/facts.json` | 产品事实清单模板；真实清单由使用者自备 | 模板 |
| `references/manufacturing-checklist.md` | 共享工艺清单 | 随本技能提供 |
Python：`python`。限制：库存、运费模板需要 OAuth；listing 网页会 403，拿不到写「未取得」。
