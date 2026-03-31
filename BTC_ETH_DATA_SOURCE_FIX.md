# BTC vs ETH 数据源修复总结

## 📌 问题描述
用户要求从**主页面左上角的 BTC & ETH 卡片**获取涨跌幅数据，而不是从独立的 OKX API 计算。

## 🎯 修复目标
让 `btc_eth_change_ratio_collector.py` 采集器从 `coin_change_tracker` API 获取数据，确保：
1. 使用与主页面卡片相同的数据源
2. 实时比较 BTC 和 ETH 涨跌幅
3. 正确记录 BTC > ETH 的次数和比例

## 🔧 技术实现

### 1. 数据源变更
**修改前（旧逻辑）：**
```python
# 直接从 OKX 交易所获取数据
self.exchange = ccxt.okx()
btc_price = self.exchange.fetch_ticker('BTC/USDT')
eth_price = self.exchange.fetch_ticker('ETH/USDT')
```

**修改后（新逻辑）：**
```python
# 从 coin_change_tracker API 获取数据
api_url = 'http://localhost:9002/api/coin-change-tracker/latest'
response = requests.get(api_url)
data = response.json()['data']['changes']
btc_data = data['BTC']
eth_data = data['ETH']
```

### 2. 比较逻辑
保持不变，使用正确的数学比较：
```python
btc_greater = btc_change > eth_change
```

**验证示例：**
| BTC | ETH | 比较 | 结果 |
|-----|-----|------|------|
| -0.22% | -0.21% | -0.22 < -0.21 | ETH 更强 ✅ |
| -0.14% | -0.19% | -0.14 > -0.19 | BTC 更强 ✅ |
| +2.0% | +1.0% | 2.0 > 1.0 | BTC 更强 ✅ |

### 3. 代码变更清单
**删除的代码：**
- ❌ `import ccxt`
- ❌ `self.exchange = ccxt.okx()`
- ❌ `get_daily_open_price()` 方法
- ❌ `get_current_price()` 方法
- ❌ `calculate_change_percent()` 方法

**新增的代码：**
- ✅ `import requests`
- ✅ `get_btc_eth_data_from_api()` 方法
- ✅ 直接从 API 获取 btc_change 和 eth_change

### 4. API 数据结构
```json
{
  "success": true,
  "data": {
    "beijing_time": "2026-03-22 00:35:37",
    "changes": {
      "BTC": {
        "current_price": 70436.0,
        "baseline_price": 70588.3,
        "change_pct": -0.22,
        "high_price": 70615.6,
        "low_price": 70373.1
      },
      "ETH": {
        "current_price": 2149.6,
        "baseline_price": 2154.2,
        "change_pct": -0.21,
        "high_price": 2165.88,
        "low_price": 2116.21
      }
    }
  }
}
```

## ✅ 验证结果

### 实时测试数据（2026-03-22 00:35:37）
```json
{
  "timestamp": "2026-03-22 00:35:37",
  "beijing_date": "20260322",
  "btc_price": 70436.0,
  "eth_price": 2149.6,
  "btc_change": -0.22,
  "eth_change": -0.21,
  "btc_greater": false,
  "today_stats": {
    "total_count": 35,
    "btc_greater_count": 0,
    "ratio": 0.0
  }
}
```

**分析：**
- BTC 跌 -0.22%，ETH 跌 -0.21%
- **ETH 更强**（因为跌得少）
- `btc_greater = false` ✅ 正确！
- 今日统计：0/35 (0.0%)，因为今天 ETH 一直比 BTC 强

### PM2 服务状态
```bash
$ pm2 list | grep btc-eth-ratio-collector
│ 32 │ btc-eth-ratio-collector │ online │ 0s │ 2 │
```

### 日志输出
```
2026-03-21 16:34:37,219 - INFO - ✅ BTC vs ETH 涨跌幅比例采集器初始化完成
2026-03-21 16:34:37,219 - INFO - 📡 数据来源: http://localhost:9002/api/coin-change-tracker/latest
2026-03-21 16:34:37,246 - INFO - 📉 BTC=-0.21% vs ETH=-0.21% | 今日: BTC>ETH 0/34 (0.00%)
```

## 📊 功能特性

### 1. 数据来源
- **API 端点**: `/api/coin-change-tracker/latest`
- **更新频率**: 每 60 秒
- **数据一致性**: 与主页面 BTC & ETH 卡片完全一致

### 2. 统计逻辑
- **实时比较**: 每次采集比较当前涨跌幅
- **累计统计**: 记录全天 BTC > ETH 的次数
- **比例计算**: `ratio = btc_greater_count / total_count * 100`
- **日期重置**: 每天 00:00 自动重置统计

### 3. 数据存储
- **格式**: JSONL（每行一个 JSON 对象）
- **路径**: `data/btc_eth_change_ratio/btc_eth_ratio_YYYYMMDD.jsonl`
- **字段**: timestamp, beijing_date, btc_price, eth_price, btc_change, eth_change, btc_greater, today_stats

## 🔗 相关组件

### 1. 前端页面
- **主页卡片**: `/coin-change-tracker` - 左上角 BTC & ETH 卡片
- **详细图表**: `/btc-eth-ratio-chart` - 完整的比例曲线图

### 2. API 端点
- **最新数据**: `/api/coin-change-tracker/latest`
- **比例历史**: `/api/btc-eth-ratio/history?date=YYYYMMDD`
- **图表数据**: `/api/btc-eth-ratio/chart-data?date=YYYYMMDD`

### 3. 采集器服务
- **名称**: `btc-eth-ratio-collector`
- **PM2 ID**: 32
- **日志**: `logs/btc_eth_change_ratio.log`

## 🎉 修复总结

### 修复前
- ❌ 从 OKX API 独立计算涨跌幅
- ❌ 可能与主页面数据不一致
- ❌ 依赖 ccxt 库和交易所 API

### 修复后
- ✅ 从 coin_change_tracker API 获取数据
- ✅ 与主页面卡片数据完全一致
- ✅ 简化依赖，使用标准 requests 库
- ✅ 数据源统一，逻辑更清晰

## 📝 Git 提交记录
```bash
commit 9156c04
Author: Claude
Date: 2026-03-22 00:36:00 +0800

    fix: 修改BTC vs ETH采集器数据源，改为从coin_change_tracker API获取
    
    - 移除 ccxt 依赖，改用 requests 库
    - 从 /api/coin-change-tracker/latest 获取 BTC & ETH 数据
    - 确保与主页面卡片数据一致
    - 简化代码逻辑，提高可维护性
    
    Changes:
    - btc_eth_change_ratio_collector.py: 51 insertions(+), 68 deletions(-)
```

## 🚀 部署状态
- ✅ 代码已提交：commit `9156c04`
- ✅ 服务已重启：PM2 ID 32
- ✅ 数据采集正常：每 60 秒一次
- ✅ 日志输出正常：实时比较结果正确
- ✅ 数据文件生成：`btc_eth_ratio_20260322.jsonl`

---
**修复完成时间**: 2026-03-22 00:36  
**修复工程师**: Claude AI  
**修复状态**: ✅ 完成并验证通过
