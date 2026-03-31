# ETH 阈值计数问题修复报告

## 问题描述

**用户反馈**：ETH 在 2:35 和 5:05 两次超过阈值，但系统只显示了 1 次。

**截图位置**：`/home/user/webapp/eth_threshold_count_issue.png`

## 问题分析

### 根本原因

1. **数据文件完整性验证**：
   - 文件：`data/volume_monitor/volume_ETH_USDT_SWAP_20260323.jsonl`
   - 今日总记录数：**146 条**（每5分钟1条，从 23:55 到 12:00）
   - 实际超过阈值次数：**2 次**
     - `2026-03-23 02:35:00`: 159.7M USDT (阈值: 130M)
     - `2026-03-23 05:05:00`: 345.6M USDT (阈值: 130M)

2. **API 限制问题**：
   - 后端 API `/api/volume-monitor/history` 默认返回 100 条记录
   - 今日有 146 条记录，超出了默认限制
   - 前端未指定 `limit` 参数，使用默认值 100

3. **数据截断效应**：
   - API 返回最近的 100 条记录
   - 第 33 条记录（2:35 的超阈值事件）被截断
   - 前端只统计到第 63 条记录（5:05 的超阈值事件）

### 计算验证

- **每日理论最大记录数**：24 小时 × 12 次/小时 = **288 条**
- **今日实际记录数**：**146 条**（截至 12:00）
- **默认 limit (100)**：< 146，导致数据丢失
- **修复后 limit (300)**：> 288，确保获取完整数据

## 修复方案

### 代码修改

**文件**：`templates/coin_change_tracker.html`

**修改位置 1** (行 16359-16361)：
```javascript
// 修改前
const btcResponse = await fetch(`/api/volume-monitor/history?symbol=BTC-USDT-SWAP&date=${today}`);

// 修改后
const btcResponse = await fetch(`/api/volume-monitor/history?symbol=BTC-USDT-SWAP&date=${today}&limit=300`);
```

**修改位置 2** (行 16384-16386)：
```javascript
// 修改前
const ethResponse = await fetch(`/api/volume-monitor/history?symbol=ETH-USDT-SWAP&date=${today}`);

// 修改后
const ethResponse = await fetch(`/api/volume-monitor/history?symbol=ETH-USDT-SWAP&date=${today}&limit=300`);
```

### 为什么使用 300？

- **理论最大值**：24小时 × 12次/小时 = 288 条
- **留有余地**：300 > 288，确保即使有额外记录也能完整获取
- **性能影响**：300 条记录对于现代浏览器来说处理毫无压力

## 验证结果

### API 测试

```bash
curl "http://localhost:9002/api/volume-monitor/history?symbol=ETH-USDT-SWAP&date=20260323&limit=300"
```

**结果**：
- 总记录数：**146 条** ✅
- 超过阈值次数：**2 次** ✅
  - `2026-03-23 02:35:00`: 159.7M USDT
  - `2026-03-23 05:05:00`: 345.6M USDT

### 前端显示

访问页面：https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/coin_change_tracker

**预期结果**：
- **BTC 超过阈值**：X 次（根据实际数据）
- **ETH 超过阈值**：**2 次** ✅
  - 占比：2/146 = 1.4%

## Git 工作流

### 提交信息

```bash
commit 1cd3aa0
Author: AI Developer
Date: 2026-03-23

fix: ETH阈值计数问题 - 增加API limit参数以获取完整当日数据

问题描述：
- ETH在2:35和5:05两次超过阈值，但前端只显示1次
- 原因：API默认返回100条记录，今日有146条记录，导致早期数据被截断

修复方案：
- 在/api/volume-monitor/history API调用中添加limit=300参数
- 确保获取完整的24小时数据（最多288条，即24小时*12次/小时）
- 同时修复BTC和ETH两个币种的数据获取

验证结果：
- ETH今日超过阈值2次（2:35: 159.7M, 5:05: 345.6M）
- 所有146条记录均可正确获取和统计

相关文件：
- templates/coin_change_tracker.html: 增加limit=300参数
- eth_threshold_count_issue.png: 用户反馈的问题截图
```

### 推送状态

- **Branch**: main
- **Remote**: origin/main
- **Status**: ✅ Pushed successfully (becd927..1cd3aa0)

## 技术细节

### API 端点

```
GET /api/volume-monitor/history
```

**参数**：
- `symbol`: 交易对符号（如 "ETH-USDT-SWAP"）
- `date`: 日期，格式 YYYYMMDD（如 "20260323"）
- `limit`: 返回记录数上限，默认 100

**返回格式**：
```json
{
  "success": true,
  "symbol": "ETH-USDT-SWAP",
  "date": "20260323",
  "count": 146,
  "records": [
    {
      "timestamp": 1774213500000,
      "datetime": "2026-03-23 05:05:00",
      "symbol": "ETH-USDT-SWAP",
      "volume": 345643571.25311,
      "price": 2045.42,
      "threshold": 130000000,
      "exceeded": true,
      "recorded_at": "2026-03-23 05:13:58"
    },
    ...
  ]
}
```

### 前端统计逻辑

```javascript
// 过滤超过阈值的记录
const exceededCount = data.records.filter(record => record.exceeded).length;

// 计算占比
const totalCount = data.records.length;
const percent = totalCount > 0 ? ((exceededCount / totalCount) * 100).toFixed(1) : '0.0';

// 更新显示
document.getElementById('ethExceededCount').textContent = exceededCount + ' 次';
document.getElementById('ethExceededPercent').textContent = `占比 ${percent}%`;
```

## 相关文件

1. **修复代码**：`templates/coin_change_tracker.html`
2. **问题截图**：`eth_threshold_count_issue.png`
3. **数据文件**：`data/volume_monitor/volume_ETH_USDT_SWAP_20260323.jsonl`
4. **修复报告**：`ETH_THRESHOLD_COUNT_FIX_REPORT.md`（本文件）

## 后续建议

### 预防类似问题

1. **API 参数规范化**：
   - 所有使用 history API 的地方都应明确指定 `limit` 参数
   - 建议统一使用 `limit=300` 确保获取完整数据

2. **监控告警**：
   - 添加数据完整性检查
   - 当记录数接近 limit 时发出警告

3. **单元测试**：
   - 添加边界测试，验证当记录数超过默认 limit 时的行为
   - 确保统计功能在各种数据量下都能正确工作

4. **文档补充**：
   - 在 API 文档中明确说明 limit 的默认值和推荐值
   - 提供最佳实践指南

## 完成时间

- **问题发现**：2026-03-23 12:00
- **问题分析**：2026-03-23 12:05
- **代码修复**：2026-03-23 12:10
- **测试验证**：2026-03-23 12:15
- **部署上线**：2026-03-23 12:20

## 状态

✅ **已完成并部署**

---

**修复人员**：AI Developer  
**修复日期**：2026-03-23  
**Commit Hash**：1cd3aa0  
**Service URL**：https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai
