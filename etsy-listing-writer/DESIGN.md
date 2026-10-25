# Etsy Listing 撰写技能（etsy-listing-writer）设计文档

状态：设计中（未开发）｜创建：2026-10-24｜负责人：助手
更新记录：2026-10-24 新建 → 竞品分析 → 3.4 消费场景拆解 → 第 0–7 步结构；**2026-10-25 第一次实测后优化**（见文末「六、更新记录」）。
对标：亚马逊侧 amazon-listing-writer（数据源 Sorftime）。Etsy 侧数据源 = EverBee（搜索量）+ Etsy Open API v3（实时 Listing 数、价格、竞品标题/标签）。

## 一、产出
一个产品按消费场景输出**多条 listing**（每个场景或人群细分一条），而不是只写一条通用的。每条包含：
- 标题
- 13 个 tags（每个 ≤20 字符）
- 描述（按场景定侧重点）及定制说明（Personalization 栏）
- 主图建议
- 类目与属性建议

完成后通过飞书 妙笔 Quill 发汇总和完整文件给老板。

## 二、通用规则
### 数据溯源规则（全流程适用）
- 每个说法都要有出处（EverBee / Etsy 站内页面 / Etsy API / 老板提供的产品信息）。
- 拿不到的数据写「未获取到」，不估算、不编造。
- 报告开头列来源表（编号 V1/S1…）：来源、文件路径、日期；人工照抄的数据要注明「人工照抄自界面」以及原因。
- 文案里任何"推荐"类句子（例如"多数人选 45–60 cm"）没有数据就删掉，或者标成「推荐，非实测」。

### 产品事实清单（写文案前必须核对，只写清单里有的）
每个产品维护一份事实清单，每条注明「老板 YYYY-MM-DD 确认」：面料 / 填充、是否真空包装（哪些尺寸）、变体及是否同价、制作天数、送达天数（从发货还是下单起算）、能做 / 不能做的内容（全身、多人、印字、合成多张照片、修脸）、退换规则、包装 / 礼品卡、拉链。
- 清单里没有的不写（例如没确认的 hidden zipper）。
- **禁止写的内容**：发货地 / 产地（不写 ships from、Made in、海外仓等；同时提醒老板运费模板发货地必须如实，Etsy Seller Policy 要求如实说明 "where it is being shipped from"，https://www.etsy.com/legal/sellers/）；hypoallergenic / non-toxic 等没有检测报告的说法；疗愈、保证类承诺；商标 / IP 词。
- 婴儿相关产品必须加一句：decorative keepsake, not for a crib or infant sleep。

### 场景优先级规则
- 按细分场景的**搜索量总和、竞品数量、Bestseller 占比**排序，先写排在前面的场景。
- **季节窗口例外**：写作顺序按搜索量排，上线顺序可以按季节提前（例如 10–12 月先上圣诞款，即使纪念款搜索量更高），报告里要写明是例外。
- EverBee 的 Score（搜索量相对竞争）高、竞争 <5K 的词优先放标题前部（例：person pillow 2.3K / 1.4K / Score 1630）；竞争 >500K 的泛词（pet lover gift、dog mom gift）不占 tags 位置。

### 防止自家链接互相抢词（同一产品多条 listing 时必做）
- 每条 listing 一个**独占主词**，其他 listing 的标题不能以它开头；在报告里列「主词分配表」。
- 标题前 3 个词不能和其他 listing 相同。
- 任意两条 listing 共用的 tags ≤4 个（`validate_listing.py` 自动检查）。
- 重叠的人群拆开写（例：全身 / 家人 → person pillow；只做头部 / 搞笑 → custom face pillow）。

### 数据源（与亚马逊侧 Sorftime 对等）
| 数据 | 来源 | 说明 |
|---|---|---|
| 关键词搜索量 | **EverBee（唯一来源）** | Etsy API 不提供搜索量 |
| 竞品链接 | Etsy 站内（Highest Reviews / Best Match 排序、Bestseller 标签） | 不用 EverBee 找竞品 |
| 竞品搜索量、标题、tags | EverBee 导出 | 第 1 步拆解用 |
| Listing 数（竞争度）、均价、可定制占比 | Etsy API v3 `/listings/active` | 冲突时以 Etsy API 实时数据为准 |
| 竞品标题、tags、收藏数（交叉核对） | Etsy API v3 | 辅助 |
| 蓝海指数 | etsy-keyword-database 计算 | 依赖 EverBee 搜索量 |

## 三、标准流程

### 第 0 步：EverBee 数据源（必做）
**账号**
- 共享月度账号由老板购买后发给 助手；登录信息存入这台云电脑的凭据库（Vault），由老板通过加密表单填写，不写进任何文件或聊天。
- 助手 自己登录、自己查询、自己导出 CSV。
- 掉线：助手 用凭据库里的登录信息重新登录，并提醒老板。
- 被封或到期：提醒老板；新账号需老板购买后存入凭据库，助手 再登录继续。到期前提醒老板续租。
- 只用 EverBee 查关键词和竞品数据，**不把老板自己的 Etsy 店铺授权连到共享号**。

**频率与用法**
- 每月集中一两次，把要查的词和竞品一次性查完并导出 CSV，不天天登录。
- **批量查询可以用**：在关键词搜索框里用英文逗号分隔一次输入多个词（2026-10-24 实测）。
- **导出按钮可能失败**：失败时人工从界面照抄成 CSV（表头 `keyword,volume,competition,score,source`），source 列写「EverBee 日期（UI as displayed）」，报告来源表注明「人工照抄」。
- 界面数值是 1K / 9.1K / 2.13M 这种近似值，用 `scripts/parse_everbee_ui.py` 解析（支持 K/M、不区分表头大小写、按场景求和）；`etsy-keyword-database/import_everbee.py` 要求 `Keyword`/`Volume` 表头并且用 int()，会把这类值读成 0，修好之前不要用它导这种 CSV。
- EverBee 对词序和单复数分开统计（custom pet pillow 171 / custom pet pillows 1,123 / custom pillow pet 1,147），所以主词要把几种写法都查一遍，按最高的那个选。
- CSV 按日期归档到 `./uploads/everbee/YYYY-MM-DD.csv`（竞品数据为 `competitors_YYYY-MM-DD.csv`）。
- 导入关键词库后一个月内，撰写时一律读库里的数据，不临时登录 EverBee。

**作用**：CSV 补上 Etsy 搜索量后，蓝海指数才算得准，选标签、做新品判断也更有底。

### 第 1 步：竞争对手分析（必做，文案流程的第一步）
**1.1 找竞品：只在 Etsy 站内找，不用 EverBee 找竞品**
- 从 Etsy 站内抓 5–10 个头部竞品链接：搜索结果页排序选 Highest Reviews 或 Best Match，取靠前的同类定制款；或类目页里带 Bestseller 标签的商品。
- 记录每个竞品的链接、标题、价格、评论数、是否 Bestseller。
- 可用 Etsy API v3 补充竞品的标题、tags、价格、收藏数作交叉核对。

**1.2 用 EverBee 导出竞品数据**：拿到链接后，在 EverBee 里导出这些竞品的搜索量、标题、tags。

**1.2b 评论 VOC 分析（必做，我方 + 竞品）**
- `python3 scripts/review_voc.py <shop_id>`：拉取我方和 3–5 家竞品的全部评论，统计各星级、≤3★ 占比，按主题（质量、像不像、尺寸、印刷、沟通、发货、柔软度、预览图）分类计数，并摘录原话（注明日期 / 星级）。
- 输出：我方的问题 / 优势表、竞品的好评点 / 差评点表、使用场合和收礼人统计；每条文案卖点都要能对应到一条 VOC（报告里列「VOC → 文案句子」对照表）。
- 我方差评点先在描述里正面回应（例如白边说明、预览确认、真空包装要先拍松），产品质量问题单独提醒老板，不能只靠文案解决。

**1.3 拆解**：卖点、描述的文案结构、标题写法（核心词位置、长度、修饰词）、tags 组合（哪些词被多数竞品共用、哪些是差异词）。拆解结果存进报告，作为后续步骤的依据；反推写成我们自己的文案，不照抄竞品原文。

**1.4（原 3.4）消费场景分类拆解（必做）**
同一款产品往往对应多个消费场景，每个场景是一批不同的搜索词和买家。参考案例：某竞品店铺把同一款产品做成 4 条 Bestseller，分别对应宠物、人物、情侣等不同场景。
1. 按场景归类竞品：宠物、人物/家人、情侣、日常自用、送礼、节日（圣诞、母亲节、情人节等）；一个竞品可归入多个场景。
2. 场景下再拆人群细分：例如宠物分猫主人、狗主人、宠物纪念；情侣分纪念日、日常、订婚/婚礼；送礼分送妈妈、送闺蜜、送老师。每个细分对应不同的标题和 tags 写法。
3. 输出：按「场景 → 人群细分」两级归类，每个细分列出对应竞品链接（及是否 Bestseller）、对应关键词（EverBee 搜索量，拿不到写「未获取到」）、竞品在该细分里的标题写法和 tags 组合特点。
4. 按场景优先级规则排序，决定先写哪些场景。

### 第 2 步：关键词库与选词
- 把 EverBee CSV（界面照抄的先用 `parse_everbee_ui.py` 转成数字）导进关键词库（飞书多维表，所有者为老板），Etsy API 补实时 Listing 数和价格，计算蓝海指数。
- 按每个消费场景（及人群细分）分别筛选关键词：主词（放标题前部）、辅词（放标题后部和 tags）、长尾词（放 tags 和描述）。
- 库里查不到的新词记进「待查词清单」，下次集中查询时补上；本次撰写时该词搜索量标「未获取到」。

### 第 3 步：标题撰写
- 按场景分别写标题，每个场景（或人群细分）一条。
- 参考第 1 步竞品标题的写法和结构（核心词位置、长度、修饰词），结合我们的产品卖点和第 2 步该场景的关键词。
- 标题写短、写成人能读懂的句子，核心词靠前；不照抄竞品原文，不碰商标词。

### 第 4 步：Tags 撰写
- 每个 listing 写 13 个 tags，每个 ≤20 字符。
- 按该场景对应的关键词组合，参考竞品 tags 的写法特点（共用词与差异词）。
- tags 与标题互补，尽量覆盖标题没写进去的词，不重复堆同一个词。
- 只能用字母、数字、空格、- 和 '；每个 tag 后面在报告里标 EverBee 搜索量或「未查」。
- 写完用校验脚本：`python3 scripts/validate_listing.py drafts.json`，格式 `{"A": {"title": "…", "tags": [13 个], "primary_kw": "…", "description": "可选"}}`。会检查：标题 ≤140、13 个不重复且 ≤20 字符、禁用词（bestseller、free shipping、商标、made in usa、ships from china、hypoallergenic、guarantee 等）、listing 之间共用 tags >4 报警告、主词重复报错。有错误退出码为 1，必须修到 0。

### 第 5 步：描述撰写
- 按场景写描述，侧重点不同（例如宠物场景讲纪念意义和照片定制，情侣场景讲纪念日和刻字，送礼场景讲包装和到货时间）。
- 结合产品卖点，只写能证实的内容。
- 写清定制说明：怎么填定制信息、制作天数、包装、尺寸材质。
- 所有 listing 共用同一个「通用模块」，只改场景开头：
  - SIZE GUIDE：size = 最长边，cm ≈ in 对照（25/30/35/40/45/50/60/70 cm ≈ 10/12/14/16/18/20/24/28 in），误差约 2–4 cm；≥35 cm 写真空包装、拆开后要拍松静置。
  - 白边 / 无白边：写清两种效果和变形风险，同价。
  - TIMING：Production 3–5 business days after preview approval；Delivery usually about 8–12 days after it ships (estimated)。不写发货地。
  - 退换：定制品不退，出问题私信处理。

### 第 6 步：主图建议
- 每个场景的 listing 给出主图建议：画面主体、场景道具、模特或宠物、文字/定制内容展示方式，并参考该场景竞品主图的共同点与可差异化的地方。
- 产品细节以实物为准，不捏造。
- **AI 图片检查**：主图 / 辅图不能用 AI 生成的"成品图"冒充实拍（旧主图 ✦ 是 Gemini 水印）。每条 listing 至少 1 张真实背景下未编辑的实物照片（Etsy Seller Handbook https://www.etsy.com/seller-handbook/article/1522733284810 ；AI 披露要求见 https://www.etsy.com/legal/sellers/ 、https://www.etsy.com/seller-handbook/article/1275449912004 ）。没有样品图的新链接先打样，不上线。

### 第 7 步：收尾（自审与交付）
1. 合规自审：不写无法证实的承诺，不碰商标词；对照产品事实清单逐句核对；跑 `validate_listing.py` 直到退出码为 0；发货地 / AI 图片 / 质量问题写进报告的「合规提醒」。
2. 数据溯源自检：每个数字注明来源（EverBee / Etsy API / Etsy 站内 / 未获取到）。
3. 通过妙笔 Quill 发汇总 + 完整文件给老板（**老板明确要求时才发**；只要求出文件时只存 `artifacts/`）。
4. 报告最后列：数据缺口、要问老板的问题、文件路径。

### 脚本（`etsy-listing-writer/scripts/`）
| 脚本 | 用途 |
|---|---|
| `etsy_client.py` | Etsy API v3 客户端（`x-api-key: $ETSY_API_KEY:$ETSY_SHARED_SECRET`，密钥只从环境变量读，不打印；限速 5 QPS / 每天 5000 次） |
| `fetch_shop.py` | 店铺信息 + 在售 listing（标题 / tags / 价格 / 收藏 / 类目） |
| `review_voc.py` | 评论拉取 + 星级统计 + 主题分类 + 原话摘录 |
| `keyword_scan.py` | 关键词的实时 Listing 数、均价 |
| `parse_everbee_ui.py` | 解析 EverBee 界面照抄的 CSV（K/M）+ 按场景求和 |
| `validate_listing.py` | 标题 / tags / 禁用词 / 自家链接抢词校验 |
限制：库存、运费模板需要 OAuth；listing 网页会 403，拿不到的写「未获取到」。

## 四、复用 amazon-listing-writer 的部分
数据溯源规则、证据 → 策略 → 文案的结构、合规自审。不复用五点、Search Terms、A9/Rufus/COSMO 规则和亚马逊违禁词表。

## 五、参考
Etsy Seller Handbook（SEO、标题、标签相关文章）；etsy-keyword-database 技能。

## 六、更新记录
- **2026-10-25**（第一次实测：A–G 七条 listing）：
  - 新增：产品事实清单 + 禁止写的内容（发货地、无检测的安全说法）；婴儿免责声明。
  - 新增：1.2b 评论 VOC 分析（必做，我方 + 竞品），以及「VOC → 文案」对照表。
  - 新增：防止自家链接互相抢词的规则（独占主词、标题前 3 个词不同、共用 tags ≤4）。
  - 新增：季节窗口例外；按 EverBee Score / 竞争度选词。
  - 新增：EverBee 实测经验（逗号批量查可以用；导出按钮可能失败，失败就人工照抄并注明来源；K/M 值用 parse_everbee_ui.py；import_everbee.py 不兼容；词序 / 单复数分开统计）。
  - 新增：描述通用模块（尺寸表 + 真空包装、白边同价、制作 / 送达时间）。
  - 新增：AI 图片检查 + Etsy 政策链接；validate_listing.py 及 drafts.json 格式；脚本清单。
  - 修改：只在老板明确要求时才发飞书。
