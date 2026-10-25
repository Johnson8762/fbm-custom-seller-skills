---
name: etsy-keyword-database
description: 当用户要构建/更新 Etsy 关键词库、查某个 Etsy 关键词的竞争度（Listing 数、均价）、导入 EverBee 导出的 CSV、计算蓝海指数、把 Etsy 关键词同步到飞书多维表格、或筛选 Etsy 蓝海关键词时使用。
---

# Etsy 关键词数据库系统（box 版）

为 Etsy 店铺（定制/个性化产品）构建可持续的关键词资产：采集 → 合并 → 蓝海评分 → 飞书多维表格 → 蓝海报告。

## 运行环境（box）

- 脚本目录：`etsy-keyword-database/`
- Python：`python`（下文简写 `$PY`）
- 环境变量（只检查是否存在，**绝不打印值**）：`ETSY_API_KEY`、`ETSY_SHARED_SECRET`（Etsy Open API v3）、`FEISHU_APP_SECRET`（飞书自建应用）
- 产出目录：`reports/etsy-keyword-db/<日期或项目>/`
- 飞书：通过 `_shared/feishu_bitable.py` 直接调用飞书 Open API（box 上没有 lark-cli）
- 原 Etsy MCP `search_listings` → `fetch_etsy_data.py`（Etsy v3 `/listings/active`，每个关键词 1 次请求）

## 输入 / 输出

**输入**：关键词列表（每行一个，模板见 `templates/keywords_example.txt`）；EverBee CSV（可选，用户上传到 box，如 `./uploads/everbee_export.csv`）；已有飞书表格的 app_token/table_id（可选，默认读脚本目录下 `lark_config.json`）
**输出**：飞书多维表格（关键词数据库）+ 蓝海关键词报告 `keyword_report.txt`

## 字段设计（--setup 自动创建）

`关键词`(文本，主键) · `搜索量`(数字，来自 EverBee) · `Listing数量`(数字，Etsy API) · `平均价格`(数字，Etsy API，USD) · `竞争度评分`(数字) · `蓝海指数`(数字) · `评级`(文本) · `数据来源`(单选 Etsy/EverBee/混合) · `更新时间`(日期) · `备注`(文本，人工标注)

## 蓝海指数计算公式（保持原方法论）

```
蓝海指数 = (搜索量 / Listing数量) × 权重系数

权重系数：
- 搜索量 > 10000 且 Listing < 500：1.5（高潜力）
- 搜索量 5000-10000 且 Listing < 1000：1.2（中潜力）
- 搜索量 1000-5000 且 Listing < 2000：1.0（基础）
- 其他：0.8（低潜力）

评级：> 20 ⭐⭐⭐ 高价值蓝海 | 10-20 ⭐⭐ 中等机会 | 5-10 ⭐ 可考虑 | < 5 ❌ 红海
```

> 注意：没有 EverBee 搜索量时，蓝海指数无法计算（搜索量=0）。Etsy 官方 API 不提供搜索量；搜索量只能来自 EverBee 导出（或用户手动提供）。

## 工作流程

### 阶段一：数据采集

**方式 A：Etsy API 实时数据**（快速验证、获取竞争度）
```bash
cd etsy-keyword-database
$PY fetch_etsy_data.py keywords.txt -o reports/etsy-keyword-db/<项目>/etsy_data.json [--limit 100] [--max-keywords N]
```
每个关键词输出：`listing_count`（Listing 总数=竞争度）、`avg_price`（USD，去掉首尾各 10% 的截尾均值，已排除非 USD 报价）、`median_price`、`price_range`、`personalizable_ratio`（可定制 Listing 占比，对定制类目很有用）、`top_listings`（Top 结果标题/价格/收藏数，用于人工复核）。

**方式 B：EverBee CSV 导入**（批量搜索量）
1. 用户在 EverBee 中搜索关键词 → Export to CSV → 发给我（上传到 box）
2. 必需列：`Keyword`、`Search Volume`、`Competition`、`Avg Price`（可选）
```bash
$PY import_everbee.py ./uploads/everbee_export.csv -o reports/etsy-keyword-db/<项目>/everbee_data.json
```
（EverBee 是浏览器插件，box 上无法自动导出；如用户没有 CSV，可在已登录 Etsy 的浏览器里打开 EverBee 手动导出，或只做方式 A。）

**方式 C：混合模式（推荐）**：先 EverBee 拿搜索量 → 再 Etsy API 补实时 Listing 数和价格 → 合并计算（两者冲突时以 Etsy API 实时数据为准，EverBee 作参考）。

### 阶段二：合并、计算、同步飞书

**首次（新建多维表格）**：
```bash
$PY sync_to_lark.py --setup --name "Etsy 关键词数据库" --etsy etsy_data.json --everbee everbee_data.json --dry-run   # 先预览
$PY sync_to_lark.py --setup --name "Etsy 关键词数据库" --etsy etsy_data.json --everbee everbee_data.json             # 用户确认后再真跑
```
`--setup` 会：创建多维表格 → **把所有权转给用户**（`/drive/v1/permissions/{token}/members/transfer_owner?type=bitable`，open_id 读自 `环境变量 FEISHU_OWNER_OPEN_ID`）→ 建字段 → 把 app_token/table_id 存进 `lark_config.json`（只在真跑时保存）。

**日常增量更新**：
```bash
$PY sync_to_lark.py --etsy etsy_data.json --everbee everbee_data.json [--app-token X --table-id Y] [--dry-run]
```
- 按 `关键词` upsert：已存在则更新，新词追加；**从不删除记录**（用户的表格绝不删除）
- `更新时间` 自动写入（毫秒时间戳）
- 同时生成蓝海报告：`--report reports/etsy-keyword-db/keyword_report.txt`（默认路径）
- 写入用户真实表格前，先 `--dry-run` 给用户看将写入的行数和示例

### 阶段三：蓝海关键词筛选

**基础筛选**：蓝海指数 > 10；搜索量 > 1000；Listing 数量 < 2000
**进阶筛选**：平均价格 > $15（利润空间）；竞争度评分 < 60；数据更新时间 < 7 天
**人工复核**：看 `top_listings` 里 Top 10 质量；评估定制化难度（参考 `personalizable_ratio`）；分析评论需求（可在已登录的浏览器里打开 Etsy 搜索页查看）

**飞书视图**（脚本可建视图和筛选条件；飞书 API 不支持设置视图排序/分组，需要用户在飞书里手动点一下）：
- 视图 1「蓝海机会」：蓝海指数 > 15，排序蓝海指数降序，按竞争度分组
- 视图 2「待验证」：蓝海指数 10-15，排序搜索量降序
- 视图 3「红海预警」：蓝海指数 < 5

## 使用场景

1. **新品选品**：列 20-30 个候选词 → EverBee 导入 → Etsy API 补数据 → 筛蓝海指数 > 15 → 人工复核 Top 3 定主推词
2. **关键词库维护**：每周全量更新一次（可让我设成定时任务）；对比上周标记趋势；新增热门词；淘汰持续下降的词
3. **团队协作**：分享飞书表格，运营在「备注」列标注意见

## 最佳实践

- 频率：日常每周一次；上新前实时验证；大促前 2 周更新
- 数量：初始库 50-100；精选库 20-30；投放库 5-10
- 质量：清理搜索量 < 100 的词；标记蓝海指数突变；季节词在「备注」标注（如「圣诞季」），提前 2-3 个月布局，淡季降权不删除
- 蓝海指数门槛：新手 > 15；成熟卖家 10-15；品牌卖家可挑战 < 10

## 报告示例

```
=== Etsy 蓝海关键词分析报告 ===
【高价值蓝海】（蓝海指数 > 20）
1. custom notebook - 指数 25.5 ⭐⭐⭐  搜索量 15000 | Listing 450 | 价格 $18.5  建议：主推词，立即布局
【中等机会】（10-20）...
【红海预警】（< 5）...
【总结】共分析 N 个关键词，发现 X 个高价值蓝海，建议主推：...
```

## 已知限制

- Etsy API 不提供搜索量 → 必须 EverBee CSV 或用户提供
- 飞书 API 无法设置视图排序/分组、无法建仪表盘 → 提示用户手动设置
- Etsy API 有频率限制；批量时脚本逐个请求，测试时用 `--max-keywords 2`
