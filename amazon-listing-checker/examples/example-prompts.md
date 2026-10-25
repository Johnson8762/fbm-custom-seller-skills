# 示例提示词

## 基础分析

### 最简单的调用

```text
分析 B0XXXXXXX1
```

### 证据优先分析

```text
请基于真实证据，分析 B0XXXXXXX1
```

### 指定站点

```text
请基于真实证据，分析 B0XXXXXXX1，站点 US
```

## 完整审计

### COSMO + Rufus 审计

```text
请基于真实证据，帮我做 B0XXXXXXX1 的 COSMO + Rufus 审计，不要猜测，缺失字段标注未获取到
```

### 完整 10 板块报告

```text
请基于真实证据，分析 B0XXXXXXX1，输出完整 10 板块 COSMO + Rufus 报告，并给我优化后的标题、5条 Bullet、Backend Search Terms、6条 Q&A、图片卖点和 A+ 方案，结果保存到 OutPut 目录
```

## 局部交付

### 只要文案

```text
分析 B0XXXXXXX1，只给我优化后的标题、5条 Bullet、Backend Search Terms 和 6条 Q&A
```

### 只要图片方案

```text
分析 B0XXXXXXX1，只给我图片卖点和 A+ 方案
```

### 只要问题诊断

```text
分析 B0XXXXXXX1，告诉我当前主要问题和改进优先级
```

## 高级场景

### 竞品对比

```text
对比分析 B0XXXXXXX1 和竞品 B0CXYZ123，找出差异化机会和改进方向
```

### 批量分析

```text
分析以下 ASIN：B0XXXXXXX1、B0CXYZ123、B0DABC456，分别输出完整报告到 OutPut 目录
```

### 多站点分析

```text
分析 B0XXXXXXX1 在 US、UK、DE 三个站点的表现差异
```

### 指定问题类型

```text
分析 B0XXXXXXX1，重点诊断曝光问题和语义检索盲区
```

### 指定改写重点

```text
分析 B0XXXXXXX1，重点优化标题和 Bullet，提升 Rufus 适配度
```

## 补充证据场景

### 提供评论证据

```text
分析 B0XXXXXXX1，我注意到评论中频繁提到"电池续航短"和"连接不稳定"，请重点诊断这两个问题
```

### 提供竞品信息

```text
分析 B0XXXXXXX1，主要竞品是 B0CXYZ123 和 B0DABC456，请对比差异化表达
```

### 提供旧文案

```text
分析 B0XXXXXXX1，当前标题是"Wireless Earbuds Bluetooth 5.0"，请基于 COSMO + Rufus 规则优化
```

## 特殊需求

### 合规检查

```text
分析 B0XXXXXXX1，重点检查是否有合规风险（绝对化宣传、品牌侵权、医疗疗效等）
```

### 语义盲区诊断

```text
分析 B0XXXXXXX1，重点诊断语义检索盲区和隐式查询解析能力
```

### Rufus 问答测试

```text
分析 B0XXXXXXX1，测试页面能否回答以下问题：
1. 这个产品适合什么人？
2. 和竞品有什么区别？
3. 需要注意什么？
4. 不适合什么情况？
```

### 图片卖点优化

```text
分析 B0XXXXXXX1，重点优化图片卖点，给出主图、6张辅图、3个场景图和 A+ 方案
```

## 输出控制

### 保存到本地

```text
分析 B0XXXXXXX1，结果保存到 OutPut 目录
```

### 分段输出

```text
分析 B0XXXXXXX1，先输出产品概览和算法评分卡（section1_2），再输出优化后文案（section9）
```

### 简洁模式

```text
分析 B0XXXXXXX1，只给核心结论和动作清单，不要详细解释
```

### 详细模式

```text
分析 B0XXXXXXX1，输出完整诊断过程、证据链和改进逻辑
```

## 组合场景

### 完整工作流

```text
请基于真实证据，分析 B0XXXXXXX1（站点 US），执行以下步骤：
1. 获取产品、评论、竞品、广告数据
2. 判断问题类型（曝光/点击/转化/预期错配）
3. 输出 7 维评分和 10 板块报告
4. 给出 P0/P1/P2 优先级动作清单
5. 输出优化后的标题、Bullet、Q&A、Backend Search Terms
6. 输出图片卖点和 A+ 方案
7. 结果保存到 OutPut/B0XXXXXXX1/ 目录
```

### 快速迭代

```text
分析 B0XXXXXXX1，快速诊断主要问题，给出 Top 3 改进建议
```

### 深度审计

```text
分析 B0XXXXXXX1，深度审计 COSMO 节点覆盖度、Rufus 因果链完整度、语义检索盲区，输出完整证据链和改进方案
```
