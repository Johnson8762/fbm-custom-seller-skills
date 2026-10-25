# SIF 工具参数速查表

## 流量诊断工具

### analyze_traffic_anomaly

**用途**：流量异常总诊断，判断广告问题还是自然问题

**参数**：
```json
{
  "asin": "B0XXXXXX",        // 必需，产品 ASIN
  "amzSite": "US",           // 必需，站点代码
  "days": 7                  // 可选，分析天数，默认 7
}
```

**返回数据**：
- 总流量变化
- 广告流量变化
- 自然流量变化
- 问题类型判断（ad_issue / organic_issue / mixed_issue）

---

### ops_get_asin_traffic_trend

**用途**：获取 ASIN 流量时序趋势

**参数**：
```json
{
  "asin": "B0XXXXXX",
  "amzSite": "US",
  "startDate": "2026-04-01",
  "endDate": "2026-04-15"
}
```

**返回数据**：
- 每日总流量
- 每日广告流量
- 每日自然流量

---

### ops_get_listing_traffic_overview

**用途**：Listing 流量总览

**参数**：
```json
{
  "asin": "B0XXXXXX",
  "amzSite": "US",
  "startDate": "2026-04-01",
  "endDate": "2026-04-15"
}
```

**返回数据**：
- 总流量
- 流量来源分布
- 流量渠道占比

---

### ops_get_listing_traffic_structure

**用途**：流量结构分析（渠道占比）

**参数**：
```json
{
  "asin": "B0XXXXXX",
  "amzSite": "US",
  "startDate": "2026-04-01",
  "endDate": "2026-04-15"
}
```

**返回数据**：
- 搜索流量占比
- 推荐流量占比
- 外部流量占比

---

## 广告分析工具

### ads_get_asin_ad_structure

**用途**：获取 ASIN 的广告结构

**参数**：
```json
{
  "asin": "B0XXXXXX",
  "amzSite": "US"
}
```

**返回数据**：
- SP 广告数量
- SD 广告数量
- SB 广告数量
- Campaign 列表

---

### ads_get_asin_ad_traffic_trend

**用途**：广告流量趋势

**参数**：
```json
{
  "asin": "B0XXXXXX",
  "amzSite": "US",
  "startDate": "2026-04-01",
  "endDate": "2026-04-15"
}
```

**返回数据**：
- 每日广告流量
- 每日广告点击
- 每日广告转化

---

### ads_get_asin_campaign_contribution_overview

**用途**：Campaign 贡献总览

**参数**：
```json
{
  "asin": "B0XXXXXX",
  "amzSite": "US",
  "startDate": "2026-04-01",
  "endDate": "2026-04-15"
}
```

**返回数据**：
- Campaign 列表
- 每个 Campaign 的流量贡献
- 每个 Campaign 的花费
- 每个 Campaign 的 ACOS

---

### ads_get_campaign_contribution_breakdown

**用途**：Campaign 贡献分解（下钻到 Ad Group）

**参数**：
```json
{
  "asin": "B0XXXXXX",
  "amzSite": "US",
  "campaignId": "123456789",
  "startDate": "2026-04-01",
  "endDate": "2026-04-15"
}
```

**返回数据**：
- Ad Group 列表
- 每个 Ad Group 的流量贡献
- 每个 Ad Group 的花费
- 每个 Ad Group 的转化

---

### ads_get_ad_group_traffic_trend

**用途**：Ad Group 流量趋势

**参数**：
```json
{
  "asin": "B0XXXXXX",
  "amzSite": "US",
  "adGroupId": "987654321",
  "startDate": "2026-04-01",
  "endDate": "2026-04-15"
}
```

**返回数据**：
- 每日流量
- 每日点击
- 每日转化

---

### ads_get_ad_group_keyword_breakdown

**用途**：Ad Group 关键词分解

**参数**：
```json
{
  "asin": "B0XXXXXX",
  "amzSite": "US",
  "adGroupId": "987654321",
  "startDate": "2026-04-01",
  "endDate": "2026-04-15"
}
```

**返回数据**：
- 关键词列表
- 每个关键词的花费
- 每个关键词的点击
- 每个关键词的转化
- 每个关键词的 ACOS

---

### ads_get_campaign_structure

**用途**：Campaign 结构详情

**参数**：
```json
{
  "campaignId": "123456789",
  "amzSite": "US"
}
```

**返回数据**：
- Campaign 名称
- Campaign 类型（SP/SD/SB）
- Campaign 状态
oup 列表

---

### ads_get_campaign_traffic_trend

**用途**：Campaign 流量趋势

**参数**：
```json
{
  "campaignId": "123456789",
  "amzSite": "US",
  "startDate": "2026-04-01",
  "endDate": "2026-04-15"
}
```

**返回数据**：
- 每日流量
- 每日花费
- 每日转化

---

## 关键词分析工具

### market_get_asin_keyword_signals

**用途**：获取 ASIN 的关键词信号

**参数**：
```json
{
  "asin": "B0XXXXXX",
  "amzSite": "US"
}
```

**返回数据**：
- 关键词列表
- 每个关键词的自然排名
- 每个关键词的广告排名
- 每个关键词的流量贡献

---

### market_get_keyword_demand

**用途**：关键词需求判断

**参数**：
```json
{
  "keyword": "portable charger",
  "amzSite": "US"
}
```

**返回数据**：
- 搜索量
- 竞争度
- 季节性
- 生命周期阶段

---

### market_get_keyword_history

**用途**：关键词历史数据

**参数**：
```json
{
  "keyword": "portable charger",
  "amzSite": "US"
}
```

**返回数据**：
- 历史搜索量趋势
- 历史竞争度趋势

---

### market_get_keyword_root_trend

**用途**：词根趋势分析

**参数**：
```json
{
  "keyword": "portable charger",
  "amzSite": "US"
}
```

**返回数据**：
- 词根列表
- 每个词根的趋势

---

### market_get_keyword_competition

**用途**：关键词竞争格局

**参数**：
```json
{
  "keyword": "portable charger",
  "amzSite": "US"
}
```

**返回数据**：
- 竞争产品列表
- 价格带分布
- 评分分布

---

## 销量分析工具

### ops_get_asin_sales_trend

**用途**：ASIN 销量趋势

**参数**：
```json
{
  "asin": "B0XXXXXX",
  "amzSite": "US",
  "startDate": "2026-04-01",
  "endDate": "2026-04-15"
}
```

**返回数据**：
- 每日销量
- 销量变化趋势

---

### ops_get_asin_sales_list

**用途**：ASIN 销量列表

**参数**：
```json
{
  "asin": "B0XXXXXX",
  "amzSite": "US"
}
```

**返回数据**：
- 销量明细
- 销量排名

---

## 站点代码

| 站点 | 代码 |
|------|------|
| 美国 | US |
| 英国 | UK |
| 德国 | DE |
| 法国 | FR |
| 意大利 | IT |
| 西班牙 | ES |
| 日本 | JP |
| 加拿大 | CA |
| 墨西哥 | MX |
| 澳大利亚 | AU |

---

## 日期格式

所有日期参数使用 ISO 8601 格式：`YYYY-MM-DD`

示例：`2026-04-16`

---

## 常见错误

### 错误 1：ASIN 不存在

```json
{
  "error": "ASIN not found",
  "message": "The specified ASIN does not exist in the given marketplace"
}
```

**解决方案**：
- 确认 ASIN 是否正确
- 确认站点是否匹配

---

### 错误 2：日期范围超出限制

```json
{
  "error": "Date range too large",
  "message": "Maximum date range is 90 days"
}
```

**解决方案**：
- 缩短日期范围到 90 天以内

---

### 错误 3：无数据

```json
{
  "error": "No data available",
  "message": "No data available for the specified parameters"
}
```

**解决方案**：
- 该 ASIN 可能没有广告数据
- 尝试其他时间范围

---

## 调用示例

### Python

```python
import os
import requests

url = "https://mcp.sif.com/mcp"
headers = {
    "Authorization": "Bearer " + os.environ["SIF_API_TOKEN"],
    "Content-Type": "application/json"
}

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "analyze_traffic_anomaly",
        "arguments": {
            "asin": "B0XXXXXX",
            "amzSite": "US",
            "days": 7
        }
    }
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

### cURL

```bash
curl -X POST https://mcp.sif.com/mcp \
  -H "Authorization: Bearer ${SIF_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "analyze_traffic_anomaly",
      "arguments": {
        "asin": "B0XXXXXX",
        "amzSite": "US",
        "days": 7
      }
    }
  }'
```
