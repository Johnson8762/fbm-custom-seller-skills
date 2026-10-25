# 定制双平台统一数据包 Schema v2_custom

`render_deliverables.py` 使用统一 JSON 数据包作为输入。

## 顶层结构

```json
{
  "schema_version": "2.0_custom",
  "metadata": {
    "brand": "string",
    "category": "string",
    "version": "string (v1_YYYYMMDD)",
    "date": "string (YYYYMMDD)",
    "site": "string (US)",
    "keyword": "string",
    "created": "string (YYYY-MM-DD HH:MM)",
    "topic": "string",
    "type": "选品报告-定制版",
    "data_sources": ["Sorftime MCP", "Etsy Browser Scraping"]
  },
  "chapters": { ... },
  "excel_sheets": { ... },
  "artifacts": { ... }
}
```

## chapters 结构 (适配 6 步定制流程)

### ch01_executive_summary
- `conclusions[]`: ≥ 3 条核心结论
- `go_nogo_verdict`: GO / CONDITIONAL GO / HOLD / NO-GO (基于双平台综合)
- `one_line_summary`: 核心市场的一句话画像

### ch02_demand_detection (Step 1 需求探测)
- `amazon_keywords[]`: Amazon 核心需求词矩阵
- `keyword_extends_top10[]`: keyword_extends 按月搜索量排序的前 10 个延伸词，每条含 `{keyword, monthly_search, cpc, segment}`
- `etsy_search_overview`: Etsy 首页列表核心概览（价格区间，热度标签）
- `insight`: 双平台需求热度解读

### ch03_custom_dimensions (Step 2 竞品画像)
- `customization_options[]`: 核心定制维度（如：刻字/材质/包装等）
- `logistics_timelines[]`: 竞品交期分布
- `insight`: 竞品提供哪些定制化服务，行业标配是什么？

### ch04_voc_pain_points (Step 3 买家声音)
- `by_dimension[]`: 按定制维度归类的差评痛点（Amazon+Etsy）
- `brand_opportunity`: 痛点向品牌优势转换的策略说明

### ch05_opportunity_gaps_pricing (Step 4 供需与定价)
- `gaps[]`: 需求旺盛但供给单薄的定制属性组合
- `price_radar`: 双平台价格雷达（如：Amz均价 $20, Etsy均价 $35）
- `fbm_cost_alert`: 直发安全成本警戒线

### ch06_dual_platform_scorecard (Step 5 双平台评分)
- `amazon_scorecard`: Amazon 侧 5 维度评分
- `etsy_scorecard`: Etsy 侧 5 维度评分
- `insight`: 两个平台的竞争差异及最终 Go/No-Go 评分理由

### ch07_strategic_recommendations (Step 6 落地矩阵)
- `tiers[]`: 至少提供 Tier 1 产品详细规格设计、切入平台、成本要求与首发主张。

### ch08_appendix
- `tool_calls[]` 以及数据抓取时间

## excel_sheets (定制版特有 Sheet)
- `数据来源说明`
- `需求词矩阵_双平台`
- `定制竞品_标杆分析` (含具体定制开放选项及交期时长)
- `VOC_核心痛点_双平台`
- `定价模型_FBM直发` (摒弃 FBA 费用结构，包含头程/直发小包运费)
- `双平台_Go-NoGo评分表`
