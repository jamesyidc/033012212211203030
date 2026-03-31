# 横盘监控 API 查询示例

## 1. 获取今天的所有 BTC 记录

```bash
curl "http://localhost:9002/api/consolidation-monitor/history?symbol=BTC-USDT-SWAP"
```

## 2. 获取今天的最新 10 条 ETH 记录

```bash
curl "http://localhost:9002/api/consolidation-monitor/history?symbol=ETH-USDT-SWAP&limit=10"
```

## 3. 获取指定日期的记录

```bash
# 获取 2026年3月25日 的 BTC 数据
curl "http://localhost:9002/api/consolidation-monitor/history?symbol=BTC-USDT-SWAP&date=20260325"
```

## 4. 获取实时状态

```bash
curl "http://localhost:9002/api/consolidation-monitor/status"
```

## 5. Python 调用示例

```python
import requests
from datetime import datetime

# 获取今天的 BTC 横盘数据
response = requests.get(
    'http://localhost:9002/api/consolidation-monitor/history',
    params={
        'symbol': 'BTC-USDT-SWAP',
        'limit': 50  # 最新50条
    }
)

if response.json()['success']:
    records = response.json()['records']
    
    # 统计连续横盘次数
    max_consecutive = max(r['consecutive_count'] for r in records)
    print(f"今日最大连续横盘次数: {max_consecutive}")
    
    # 筛选横盘记录
    consolidation_records = [r for r in records if r['is_consolidation']]
    print(f"横盘记录数: {len(consolidation_records)}/{len(records)}")
```

## 6. JavaScript 前端调用示例

```javascript
// 加载最新的横盘数据
async function loadConsolidationData() {
    try {
        const response = await fetch('/api/consolidation-monitor/history?symbol=BTC-USDT-SWAP&limit=20');
        const data = await response.json();
        
        if (data.success) {
            console.log(`获取到 ${data.count} 条记录`);
            
            // 显示最新记录
            const latest = data.records[data.records.length - 1];
            console.log(`最新: ${latest.datetime} ${latest.change_percent_display} (连续${latest.consecutive_count}次)`);
        }
    } catch (error) {
        console.error('加载数据失败:', error);
    }
}

// 每60秒刷新一次
setInterval(loadConsolidationData, 60000);
```

## 7. 批量查询多个日期

```bash
# 查询最近3天的数据
for date in 20260323 20260324 20260325; do
    echo "=== $date ==="
    curl "http://localhost:9002/api/consolidation-monitor/history?symbol=BTC-USDT-SWAP&date=$date" | jq '.count'
done
```

## 8. 数据分析示例

```python
import requests
import json
from collections import Counter

def analyze_consolidation_patterns(symbol='BTC-USDT-SWAP', date='20260325'):
    """分析横盘模式"""
    response = requests.get(
        'http://localhost:9002/api/consolidation-monitor/history',
        params={'symbol': symbol, 'date': date}
    )
    
    if not response.json()['success']:
        return
    
    records = response.json()['records']
    
    # 统计
    total = len(records)
    consolidation_count = sum(1 for r in records if r['is_consolidation'])
    max_consecutive = max(r['consecutive_count'] for r in records)
    
    # 横盘时段分布（按小时）
    hours = [r['datetime'].split()[1].split(':')[0] for r in records if r['is_consolidation']]
    hour_dist = Counter(hours)
    
    print(f"=== {symbol} {date} 横盘分析 ===")
    print(f"总记录数: {total}")
    print(f"横盘次数: {consolidation_count} ({consolidation_count/total*100:.1f}%)")
    print(f"最大连续: {max_consecutive}次")
    print(f"\n横盘时段分布:")
    for hour, count in sorted(hour_dist.items()):
        print(f"  {hour}时: {count}次")

# 调用
analyze_consolidation_patterns()
```

## 响应格式

### 成功响应

```json
{
    "success": true,
    "symbol": "BTC-USDT-SWAP",
    "date": "20260325",
    "count": 4,
    "records": [
        {
            "timestamp": 1774414800000,
            "datetime": "2026-03-25 13:00:00",
            "symbol": "BTC-USDT-SWAP",
            "change_percent": 0.00016915,
            "change_percent_display": "+0.017%",
            "price": 70952.9,
            "is_consolidation": true,
            "consecutive_count": 1,
            "recorded_at": "2026-03-25 13:05:30"
        }
    ]
}
```

### 错误响应

```json
{
    "success": false,
    "error": "数据文件不存在: 20260323"
}
```

## 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| timestamp | number | Unix 时间戳（毫秒） |
| datetime | string | 北京时间 (YYYY-MM-DD HH:MM:SS) |
| symbol | string | 交易对符号 |
| change_percent | number | 涨跌幅（小数形式，0.01 = 1%） |
| change_percent_display | string | 涨跌幅显示格式 |
| price | number | 收盘价格 |
| is_consolidation | boolean | 是否横盘（≤0.05%） |
| consecutive_count | number | 当前连续横盘次数 |
| recorded_at | string | 记录时间 |
