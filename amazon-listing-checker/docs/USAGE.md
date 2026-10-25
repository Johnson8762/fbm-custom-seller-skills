# 使用指南

## 快速开始

### 基础用法

最简单的调用方式：

```text
分析 B0XXXXXXX1
```

### 完整用法

推荐的完整调用方式：

```text
请基于真实证据，分析 B0XXXXXXX1，输出完整 10 板块 COSMO + Rufus 报告，并给我优化后的标题、5条 Bullet、Backend Search Terms、6条 Q&A、图片卖点和 A+ 方案，结果保存到 OutPut 目录
```

## 输入参数

### 必需参数

- **ASIN**：Amazon 产品标识符（如 B0XXXXXXX1）

### 可选参数

- **站点**：默认 US，可指定 UK、DE、JP 等
- **补充证据**：评论截图、竞品 ASIN、旧文案等

## 输出说明

### 10 板块报告结构

1. **产品概览**：基础信息、价格、评分、BSR
2. **算法评分卡**：7 维度评分（0-100 分）
3. **语义检索盲区分析**：哪些查询意图未被覆盖
4. **COSMO 节点诊断**：Who/When-Where/Problem/Concern/Outcome 覆盖度
5. **Rufus 问答能力测试**：页面能否回答关键问题
6. **用户行为信号诊断**：评分、评论量、差评集中点
7. **竞品差异化可提取性**：与竞品的可比较性
8. **改进优先级方案**：P0/P1/P2 动作清单
9. **优化后文案**：标题、Bullet、Q&A、Backend Search Terms
10. **图片卖点与 A+ 方案**：主图、辅图、场景图、A+ 模块

### 文件输出

所有结果保存在：

```text
~/Amazon-Listing-checker/OutPut/<ASIN>/
```

典型文件：
- `feishu_clean_report.md`：完整报告
- `section1_2.md`：产品概览 + 算法评分卡
- `section7_8.md`：竞品差异化 + 改进优先级
- `section9.md`：优化后文案
- `section10.md`：图片卖点与 A+ 方案

## 常见场景

### 场景 1：快速诊断

```text
分析 B0XXXXXXX1，告诉我主要问题
```

### 场景 2：完整审计

```text
请基于真实证据，帮我做 B0XXXXXXX1 的 COSMO + Rufus 审计，不要猜测，缺失字段标注未获取到
```

### 场景 3：只要文案

```text
分析 B0XXXXXXX1，只给我优化后的标题、Bullet、Q&A 和 Backend Search Terms
```

### 场景 4：只要图片方案

```text
分析 B0XXXXXXX1，只给我图片卖点和 A+ 方案
```

## 注意事项

### 证据优先原则

- 缺失字段写"未获取到"
- 不猜测、不伪造数据
- 区分三层证据：页面事实 / 用户反馈 / 运营建议

### 问题分类驱动

先判断问题类型：
- 曝光问题：核心词错、属性缺
- 点击问题：标题/主图不吸引
- 转化问题：决策信息缺失
- 预期错配：买前承诺与买后体验不一致

### 优先级体系

- **P0**：纠错（误购/退货/差评/合规风险）
- **P1**：补齐（明显提升 CTR/CVR）
- **P2**：强化/美化（视觉增强/表达打磨）

## 故障排查

### MCP 连接问题

检查 MCP 状态：

```bash
claude mcp list
```

应该看到 `sorftime` 和 `sif-mcp`。

### 数据缺失问题

如果报告中出现大量"未获取到"：
1. 检查 sorftime MCP 配置
2. 检查 sif-mcp 配置
3. 确认 ASIN 和站点正确
4. 检查 MCP token 是否过期

### 输出目录问题

确认目录存在：

```bash
ls -la ~/Amazon-Listing-checker/OutPut/
```

如果不存在，手动创建：

```bash
mkdir -p ~/Amazon-Listing-checker/OutPut
```

## 高级用法

### 批量分析

```text
分析以下 ASIN：B0XXXXXXX1、B0CXYZ123、B0DABC456，分别输出报告
```

### 竞品对比

```text
对比分析 B0XXXXXXX1 和竞品 B0CXYZ123，找出差异化机会
```

### 指定站点

```text
分析 B0XXXXXXX1，站点 UK
```
