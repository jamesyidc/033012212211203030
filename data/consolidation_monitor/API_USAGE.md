# 横盘监控 API 使用文档

## 概述

横盘监控系统通过监控 BTC 和 ETH 永续合约 5 分钟 K 线的涨跌幅，当绝对值 ≤0.05% 连续出现 ≥3 次时发送 Telegram 告警。

所有数据按日期存储在 JSONL 文件中，格式为：`consolidation_{SYMBOL}_{YYYYMMDD}.jsonl`

---

## API 端点

### 1. 获取实时状态

**端点**: `GET /api/consolidation-monitor/status`

**描述**: 获取 BTC 和 ETH 的最新横盘监控状态，包括最近的记录和连续横盘次数。

**参数**: 无

**响应示例**:
```json
{
  "success": true,
  "data": {
    "BTC": {
      "timestamp": 1774414500000,
      "datetime": "2026-03-25 12:55:00",
      "change_percent": 0.0025423644979078665,
      "change_percent_display": "+0.254%",
      "price": 70940.8,
      "is_consolidation": false,
      "consecutive_count": 0,
      "recent_records": [
        {
          "timestamp": 1774413900000,
          "datetime": "2026-03-25 12:45:00",
          "change_percent": -0.0003929672989011462,
          "is_consolidation": true
        }
      ]
    },
    "ETH": {
      "timestamp": 1774414500000,
      "datetime": "2026-03-25 12:55:00",
      "change_percent": 0.0015,
      "change_percent_display": "+0.150%",
      "price": 3245.67,
      "is_consolidation": false,
      "consecutive_count": 0,
      "recent_records": []
    }
  },
  "update_time": "2026-03-25 13:00:27"
}
```

---

### 2. 查询可用日期列表

**端点**: `GET /api/consolidation-monitor/dates`

**描述**: 查询指定币种有哪些日期的历史数据可用。

**参数**:
- `symbol` (可选): 币种代码，默认 `BTC-USDT-SWAP`
  - 可选值: `BTC-USDT-SWAP`, `ETH-USDT-SWAP`

**示例请求**:
```bash
curl "http://localhost:9002/api/consolidation-monitor/dates?symbol=BTC-USDT-SWAP"
```

**响应示例**:
```json
{
  "success": true,
  "symbol": "BTC-USDT-SWAP",
  "count": 3,
  "dates": [
    {
      "date": "20260325",
      "formatted": "2026-03-25",
      "file": "consolidation_BTC_USDT_SWAP_20260325.jsonl"
    },
    {
      "date": "20260324",
      "formatted": "2026-03-24",
      "file": "consolidation_BTC_USDT_SWAP_20260324.jsonl"
    },
    {
      "date": "20260323",
      "formatted": "2026-03-23",
      "file": "consolidation_BTC_USDT_SWAP_20260323.jsonl"
    }
  ]
}
```

---

### 3. 查询历史数据

**端点**: `GET /api/consolidation-monitor/history`

**描述**: 查询指定币种和日期的横盘监控历史记录。

**参数**:
- `symbol` (可选): 币种代码，默认 `BTC-USDT-SWAP`
- `date` (可选): 日期，格式 `YYYYMMDD`，默认今天
- `limit` (可选): 返回最近 N 条记录

**示例请求**:
```bash
# 查询今天所有记录
curl "http://localhost:9002/api/consolidation-monitor/history?symbol=BTC-USDT-SWAP"

# 查询指定日期的最近 10 条记录
curl "http://localhost:9002/api/consolidation-monitor/history?symbol=BTC-USDT-SWAP&date=20260324&limit=10"
```

**响应示例**:
```json
{
  "success": true,
  "symbol": "BTC-USDT-SWAP",
  "date": "20260325",
  "count": 3,
  "records": [
    {
      "timestamp": 1774413900000,
      "datetime": "2026-03-25 12:45:00",
      "symbol": "BTC-USDT-SWAP",
      "change_percent": -0.0003929672989011462,
      "change_percent_display": "-0.039%",
      "price": 70716.0,
      "is_consolidation": true,
      "consecutive_count": 1,
      "recorded_at": "2026-03-25 12:50:20"
    },
    {
      "timestamp": 1774414200000,
      "datetime": "2026-03-25 12:50:00",
      "symbol": "BTC-USDT-SWAP",
      "change_percent": 0.0006349341026075313,
      "change_percent_display": "+0.063%",
      "price": 70760.9,
      "is_consolidation": false,
      "consecutive_count": 0,
      "recorded_at": "2026-03-25 12:55:24"
    }
  ]
}
```

---

### 4. 查询统计分析数据

**端点**: `GET /api/consolidation-monitor/stats`

**描述**: 获取指定币种和日期的横盘监控统计分析数据，包括横盘比例、告警时刻、价格范围等。

**参数**:
- `symbol` (可选): 币种代码，默认 `BTC-USDT-SWAP`
- `date` (可选): 日期，格式 `YYYYMMDD`，默认今天

**示例请求**:
```bash
# 查询今天的统计
curl "http://localhost:9002/api/consolidation-monitor/stats?symbol=BTC-USDT-SWAP"

# 查询指定日期的统计
curl "http://localhost:9002/api/consolidation-monitor/stats?symbol=BTC-USDT-SWAP&date=20260324"
```

**响应示例**:
```json
{
  "success": true,
  "symbol": "BTC-USDT-SWAP",
  "date": "20260325",
  "stats": {
    "total_count": 288,
    "consolidation_count": 96,
    "consolidation_ratio": 33.33,
    "max_consecutive": 5,
    "alert_count": 2,
    "avg_change_percent": 0.119,
    "price_range": {
      "min": 70500.0,
      "max": 71200.0,
      "diff": 700.0
    },
    "time_range": {
      "first": "2026-03-25 00:00:00",
      "last": "2026-03-25 23:55:00"
    }
  },
  "alert_moments": [
    {
      "timestamp": 1774380000000,
      "datetime": "2026-03-25 03:25:00",
      "consecutive_count": 3,
      "change_percent_display": "+0.048%"
    },
    {
      "timestamp": 1774392000000,
      "datetime": "2026-03-25 08:45:00",
      "consecutive_count": 4,
      "change_percent_display": "-0.032%"
    }
  ]
}
```

**字段说明**:
- `total_count`: 总记录数
- `consolidation_count`: 横盘记录数（涨跌幅绝对值 ≤0.05%）
- `consolidation_ratio`: 横盘比例（%）
- `max_consecutive`: 最大连续横盘次数
- `alert_count`: 告警次数（连续 ≥3 次的时刻数）
- `avg_change_percent`: 平均涨跌幅绝对值（%）
- `price_range`: 价格范围
- `time_range`: 时间范围
- `alert_moments`: 所有告警时刻的详细信息

---

## 数据文件格式

### JSONL 文件命名

```
consolidation_{SYMBOL}_{YYYYMMDD}.jsonl
```

示例:
- `consolidation_BTC_USDT_SWAP_20260325.jsonl`
- `consolidation_ETH_USDT_SWAP_20260325.jsonl`

### 记录字段说明

每行一个 JSON 对象，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | number | 时间戳（毫秒） |
| `datetime` | string | 北京时间（YYYY-MM-DD HH:MM:SS） |
| `symbol` | string | 币种代码 |
| `change_percent` | number | 涨跌幅（小数形式，如 0.0005 表示 0.05%） |
| `change_percent_display` | string | 涨跌幅显示（如 "+0.050%"） |
| `price` | number | 收盘价 |
| `is_consolidation` | boolean | 是否为横盘（绝对值 ≤0.05%） |
| `consecutive_count` | number | 当前连续横盘次数 |
| `recorded_at` | string | 记录时间（北京时间） |

---

## Python 示例代码

### 1. 读取指定日期的数据

```python
import json
from pathlib import Path

def read_consolidation_data(symbol, date):
    """读取横盘监控数据"""
    data_dir = Path('/home/user/webapp/data/consolidation_monitor')
    symbol_normalized = symbol.replace('-', '_')
    jsonl_file = data_dir / f'consolidation_{symbol_normalized}_{date}.jsonl'
    
    records = []
    if jsonl_file.exists():
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    
    return records

# 使用示例
records = read_consolidation_data('BTC-USDT-SWAP', '20260325')
print(f"总记录数: {len(records)}")

# 统计横盘记录
consolidation_records = [r for r in records if r['is_consolidation']]
print(f"横盘记录数: {len(consolidation_records)}")
```

### 2. 查找告警时刻

```python
def find_alert_moments(records, min_consecutive=3):
    """查找所有告警时刻（连续≥min_consecutive次）"""
    alert_moments = []
    
    for i, rec in enumerate(records):
        consecutive = rec.get('consecutive_count', 0)
        if consecutive >= min_consecutive:
            # 检查是否是刚达到阈值的时刻
            if i == 0 or records[i-1].get('consecutive_count', 0) < min_consecutive:
                alert_moments.append({
                    'datetime': rec['datetime'],
                    'consecutive_count': consecutive,
                    'change_percent_display': rec['change_percent_display']
                })
    
    return alert_moments

# 使用示例
alerts = find_alert_moments(records)
print(f"告警次数: {len(alerts)}")
for alert in alerts:
    print(f"  {alert['datetime']}: 连续{alert['consecutive_count']}次横盘")
```

### 3. 统计分析

```python
def analyze_consolidation_stats(records):
    """统计分析横盘数据"""
    if not records:
        return None
    
    total_count = len(records)
    consolidation_count = sum(1 for r in records if r['is_consolidation'])
    max_consecutive = max((r.get('consecutive_count', 0) for r in records), default=0)
    
    prices = [r['price'] for r in records]
    changes = [abs(r['change_percent']) for r in records]
    
    return {
        'total_count': total_count,
        'consolidation_count': consolidation_count,
        'consolidation_ratio': round(consolidation_count / total_count * 100, 2),
        'max_consecutive': max_consecutive,
        'avg_change_percent': round(sum(changes) / len(changes) * 100, 3),
        'price_range': {
            'min': min(prices),
            'max': max(prices),
            'diff': max(prices) - min(prices)
        }
    }

# 使用示例
stats = analyze_consolidation_stats(records)
print(f"横盘比例: {stats['consolidation_ratio']}%")
print(f"最大连续: {stats['max_consecutive']}次")
```

---

## JavaScript 前端调用示例

### 1. 获取实时状态

```javascript
async function loadConsolidationStatus() {
    try {
        const response = await fetch('/api/consolidation-monitor/status');
        const data = await response.json();
        
        if (data.success) {
            console.log('BTC 状态:', data.data.BTC);
            console.log('ETH 状态:', data.data.ETH);
            
            // 更新 UI
            updateConsolidationUI(data.data);
        }
    } catch (error) {
        console.error('加载横盘状态失败:', error);
    }
}

// 每 60 秒刷新一次
setInterval(loadConsolidationStatus, 60000);
```

### 2. 查询历史数据

```javascript
async function loadConsolidationHistory(symbol, date) {
    try {
        const url = `/api/consolidation-monitor/history?symbol=${symbol}&date=${date}`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            console.log(`${symbol} ${date} 记录数: ${data.count}`);
            return data.records;
        }
    } catch (error) {
        console.error('加载历史数据失败:', error);
        return [];
    }
}

// 使用示例
const records = await loadConsolidationHistory('BTC-USDT-SWAP', '20260325');
```

### 3. 查询统计数据

```javascript
async function loadConsolidationStats(symbol, date) {
    try {
        const url = `/api/consolidation-monitor/stats?symbol=${symbol}&date=${date}`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            console.log('统计数据:', data.stats);
            console.log('告警时刻:', data.alert_moments);
            
            // 显示统计图表
            displayStatsChart(data.stats);
        }
    } catch (error) {
        console.error('加载统计数据失败:', error);
    }
}
```

---

## 告警机制

### 触发条件

1. **横盘判定**: 5 分钟 K 线涨跌幅绝对值 ≤ 0.05%
2. **连续次数**: 连续出现 ≥ 3 次
3. **告警时机**: 刚达到连续 3 次时发送一次（避免重复）

### Telegram 消息格式

```
🔔 横盘变盘告警

📊 BTC永续合约
⚠️ 5分钟涨跌幅连续3次≤0.05%

要变盘了！

📈 最近5次记录：
• 12:40: +0.048% ($70,650.00)
• 12:45: -0.039% ($70,716.00)
• 12:50: +0.032% ($70,738.50)
```

---

## 监控进程管理

### 查看监控状态

```bash
pm2 status consolidation-monitor
```

### 查看监控日志

```bash
pm2 logs consolidation-monitor --lines 50
```

### 重启监控

```bash
pm2 restart consolidation-monitor
```

---

## 故障排查

### 1. 检查数据文件是否生成

```bash
ls -lh /home/user/webapp/data/consolidation_monitor/*.jsonl
```

### 2. 查看最新记录

```bash
tail -5 /home/user/webapp/data/consolidation_monitor/consolidation_BTC_USDT_SWAP_$(date +%Y%m%d).jsonl
```

### 3. 验证 JSON 格式

```bash
jq . /home/user/webapp/data/consolidation_monitor/consolidation_BTC_USDT_SWAP_20260325.jsonl
```

### 4. 测试 API

```bash
# 测试状态接口
curl "http://localhost:9002/api/consolidation-monitor/status" | jq .

# 测试历史数据接口
curl "http://localhost:9002/api/consolidation-monitor/history?symbol=BTC-USDT-SWAP&limit=5" | jq .

# 测试统计接口
curl "http://localhost:9002/api/consolidation-monitor/stats?symbol=BTC-USDT-SWAP" | jq .
```

---

## 数据归档建议

### 定期归档历史数据

```bash
#!/bin/bash
# 归档 30 天前的数据

cd /home/user/webapp/data/consolidation_monitor

# 创建归档目录
mkdir -p archive/$(date -d '30 days ago' +%Y%m)

# 查找并移动旧文件
find . -maxdepth 1 -name "consolidation_*_$(date -d '30 days ago' +%Y%m)*.jsonl" \
  -exec gzip {} \; \
  -exec mv {}.gz archive/$(date -d '30 days ago' +%Y%m)/ \;
```

---

## 总结

横盘监控系统已实现：

✅ **实时监控**: 每 60 秒检查一次 5 分钟 K 线  
✅ **按日期存储**: JSONL 格式，方便查询和分析  
✅ **完整 API**: 状态、历史、统计、日期列表  
✅ **Telegram 告警**: 连续 ≥3 次自动发送  
✅ **数据分析**: 横盘比例、最大连续次数、告警时刻等  

所有数据都保存在 `/home/user/webapp/data/consolidation_monitor/` 目录下，按日期和币种分别存储，方便后续调用和分析。
