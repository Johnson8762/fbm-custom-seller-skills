# CSV Schema — 定制化需求验证的标准数据文件

## 目录结构

```text
YYYY-MM-DD_[品类slug]_[定制方向slug]_数据源/
├── 01_review_信号_原始数据.csv
├── 02_keyword_信号_搜索量数据.csv
├── 03_keyword_信号_趋势数据.csv
├── 04_keyword_信号_延伸词.csv
├── 05_社区_信号_讨论摘要.csv
├── 06_pinterest_趋势信号.csv
├── 07_etsy_市场信号.csv
├── 08_tiktok_市场信号.csv
├── 09_1688_供应参考.csv
└── review_source_pack/              # 仅 Review fallback 场景需要
    ├── source_manifest.json
    └── raw/
```

## 全 CSV 通用要求

所有 CSV 使用 UTF-8，包含以下核查字段：

| 列名 | 说明 |
|------|------|
| `数据来源` | 具体工具名称 |
| `来源类型` | `sorftime_mcp` / `public_web_search` / `pinterest_trends` / `etsy_search` / `tiktok_mcp` / `ali1688_mcp` 等 |
| `来源链接/查询词` | 来源 URL、Query，或内部调用标识 |
| `原始文件名` | 原始文件名 |
| `采集时间` | `YYYY-MM-DD HH:MM:SS` |

---

## CSV 01：Review 信号原始数据

| 列名 | 说明 |
|------|------|
| `ASIN` | 产品 ASIN |
| `产品组别` | `A组:定制化产品` / `B组:标品对照` |
| `评论日期` | 原始评论日期 |
| `星级` | 1.0 - 5.0 |
| `评论内容` | 标题 + 正文，截断到 300 字符 |
| `定制化相关(Y/N)` | 是否与定制化任一子维度相关 |
| `子维度分类` | `材质需求` / `定制形式` / `工艺质量` / `尺码合身` / `设计满意度` / `排除维度:交付周期` / `无关` |
| `情感(正/负/中)` | ≥4 正，3 中，≤2 负 |
| `需求信号` | 是否命中 `wish it had` 等表达 |
| `数据来源` | `mcp_sorftime_product_reviews` / `web_search` 等 |
| `来源类型` | `sorftime_mcp` / `public_web_search` 等 |
| `来源链接/查询词` | Sorftime 调用标识或 Amazon 评论页 URL |
| `原始文件名` | 原始文件名 |
| `采集时间` | 采集时间 |

---

## CSV 02：关键词搜索量数据

| 列名 | 说明 |
|------|------|
| `关键词` | 查询词 |
| `周搜索量` | 周搜索量 |
| `搜索排名` | 搜索排名 |
| `变化率` | 变化情况 |
| `CPC` | CPC |
| `数据来源` | `mcp_sorftime_keyword_detail` 等 |
| `来源类型` | `sorftime_mcp` / `google_trends` / `web_search_estimate` |
| `来源链接/查询词` | 如 `keyword_detail:custom dog shirt` |
| `原始文件名` | 原始文件名 |
| `采集时间` | 采集时间 |

---

## CSV 03：关键词趋势数据

| 列名 | 说明 |
|------|------|
| `关键词` | 查询词 |
| `日期` | 原始时间点 |
| `月搜索量` | 月搜索量 |
| `搜索排名` | 搜索排名 |
| `趋势方向` | 上升/平稳/下降/波动 |
| `数据来源` | `mcp_sorftime_keyword_trend` 等 |
| `来源类型` | `sorftime_mcp` / `google_trends` |
| `来源链接/查询词` | 查询标识 |
| `原始文件名` | 原始文件名 |
| `采集时间` | 采集时间 |

---

## CSV 04：关键词延伸词

| 列名 | 说明 |
|------|------|
| `延伸词` | 延伸词 |
| `周搜索量` | 周搜索量 |
| `搜索排名` | 搜索排名 |
| `关联度(高/中/低)` | 与定制化的相关度 |
| `数据来源` | `mcp_sorftime_keyword_extends` 等 |
| `来源类型` | `sorftime_mcp` / `amazon_autocomplete` |
| `来源链接/查询词` | 查询标识 |
| `原始文件名` | 原始文件名 |
| `采集时间` | 采集时间 |

---

## CSV 05：社区讨论摘要

| 列名 | 说明 |
|------|------|
| `来源(Reddit/Quora)` | 讨论来源 |
| `帖子标题` | 帖子或问题标题 |
| `URL` | 原始链接 |
| `发布日期` | 原始发布时间 |
| `讨论热度` | 高/中/低/无结果 |
| `用户态度摘要` | 期待/推荐/质疑/吐槽 |
| `WebSearch查询词` | 具体搜索词 |
| `数据来源` | `web_search` |
| `来源类型` | `public_web_search` |
| `来源链接/查询词` | 搜索词或 URL |
| `原始文件名` | 原始文件名 |
| `采集时间` | 采集时间 |

---

## CSV 06：Pinterest 趋势信号

| 列名 | 说明 |
|------|------|
| `查询词` | Pinterest 搜索词 |
| `趋势方向` | 上升/平稳/下降 |
| `趋势时间范围` | 如"2025-04 至 2026-03" |
| `相关搜索词` | Pinterest Related Terms |
| `相关度(高/中/低)` | 与定制化的相关度 |
| `热门Pin内容摘要` | 关键 Pin 的内容描述 |
| `数据来源` | `pinterest_trends` / `web_search` |
| `来源类型` | `pinterest_web` / `public_web_search` |
| `来源链接/查询词` | URL 或搜索词 |
| `原始文件名` | 原始文件名 |
| `采集时间` | 采集时间 |

---

## CSV 07：Etsy 市场信号

| 列名 | 说明 |
|------|------|
| `查询词` | Etsy 搜索词 |
| `竞争密度评估` | 翻页深度/API结果数/eRank数据 |
| `市场阶段` | 市场成熟/新兴市场/小众市场 |
| `产品标题` | 热销产品标题 |
| `价格` | 产品价格 |
| `Review数量` | 产品 Review 数 |
| `星级` | 产品评分 |
| `定制选项` | 该产品提供的定制维度 |
| `材质` | 产品材质 |
| `店铺名` | 卖家店铺名 |
| `店铺销量` | 店铺总销量（如可获取） |
| `数据来源` | `etsy_search` / `etsy_api` / `erank` |
| `来源类型` | `etsy_web` / `etsy_api` / `third_party_tool` |
| `来源链接/查询词` | URL 或搜索词 |
| `原始文件名` | 原始文件名 |
| `采集时间` | 采集时间 |

---

## CSV 08：TikTok 市场信号

| 列名 | 说明 |
|------|------|
| `产品ID` | TikTok 产品 ID |
| `产品标题` | 产品标题 |
| `价格` | 产品价格 |
| `总销量` | 总销量 |
| `月销量` | 月销量 |
| `星级` | 产品评分 |
| `带货视频数` | 关联带货视频数量 |
| `带货达人数` | 关联达人数量 |
| `品类` | 所属品类 |
| `数据来源` | `mcp_sorftime_tiktok_similar_product` / `mcp_sorftime_tiktok_category_report` |
| `来源类型` | `sorftime_mcp` |
| `来源链接/查询词` | 调用标识 |
| `原始文件名` | 原始文件名 |
| `采集时间` | 采集时间 |

---

## CSV 09：1688 供应参考

| 列名 | 说明 |
|------|------|
| `供应商名称` | 供应商公司名 |
| `产品标题` | 样品产品标题 |
| `价格区间` | 报价范围 |
| `起订量` | 最小起订量 |
| `支持工艺` | 支持的定制工艺类型 |
| `是否支持定制` | Y/N |
| `供应商资质` | 如"实力商家"/"源头工厂"等 |
| `产品链接` | 1688 产品链接 |
| `数据来源` | `mcp_sorftime_ali1688_similar_product` |
| `来源类型` | `sorftime_mcp` |
| `来源链接/查询词` | 搜索词 |
| `原始文件名` | 原始文件名 |
| `采集时间` | 采集时间 |

---

## Review fallback 额外要求

如果 `01_review_信号_原始数据.csv` 中的 `来源类型` 含有 `manual` 或 `amazon`，则交付目录必须额外包含：

- `review_source_pack/source_manifest.json`
- `review_source_pack/raw/` 下至少 1 个原始文件

`source_manifest.json` 必须包含：

- `asin`
- `site`
- `captured_at`
- `source_url`
- `export_method`
