# 横盘监控数据说明

## 数据目录结构

```
data/consolidation_monitor/
├── consolidation_BTC_USDT_SWAP_YYYYMMDD.jsonl  # BTC每日数据
├── consolidation_ETH_USDT_SWAP_YYYYMMDD.jsonl  # ETH每日数据
├── consolidation_config.json                    # 监控配置
├── consolidation_state.json                     # 运行状态
└── README.md                                    # 说明文档
```

## 数据格式

### JSONL文件格式
每行一条JSON记录，包含以下字段：

```json
{
  "timestamp": 1774413900000,
  "datetime": "2026-03-25 12:45:00",
  "symbol": "BTC-USDT-SWAP",
  "change_percent": -0.000392967,
  "change_percent_display": "-0.039%",
  "price": 70716.0,
  "is_consolidation": true,
  "consecutive_count": 1,
  "recorded_at": "2026-03-25 12:50:20"
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| timestamp | int | K线时间戳（毫秒） |
| datetime | string | 北京时间（YYYY-MM-DD HH:MM:SS） |
| symbol | string | 交易对（BTC-USDT-SWAP/ETH-USDT-SWAP） |
| change_percent | float | 涨跌幅（小数，如0.001=0.1%） |
| change_percent_display | string | 涨跌幅显示（如"+0.100%"） |
| price | float | K线收盘价 |
| is_consolidation | boolean | 是否横盘（\|涨跌幅\|≤0.05%） |
| consecutive_count | int | 当前连续横盘次数 |
| recorded_at | string | 数据记录时间 |

## 数据读取示例

### Python读取

```python
import json
from pathlib import Path
from datetime import datetime

def read_consolidation_data(symbol='BTC-USDT-SWAP', date='20260325'):
    """读取指定币种和日期的横盘数据"""
    data_file = Path(f'data/consolidation_monitor/consolidation_{symbol}_{date}.jsonl')
    
    if not data_file.exists():
        return []
    
    records = []
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    
    return records

# 使用示例
records = read_consolidation_data('BTC-USDT-SWAP', '20260325')
print(f"共{len(records)}条记录")

# 统计横盘次数
consolidation_count = sum(1 for r in records if r['is_consolidation'])
print(f"横盘记录：{consolidation_count}条")

# 查找连续横盘≥3的时刻
alerts = [r for r in records if r['consecutive_count'] >= 3]
print(f"触发告警：{len(alerts)}次")
```

### Flask API读取

```python
@app.route('/api/consolidation-monitor/history')
def get_history():
    symbol = request.args.get('symbol', 'BTC-USDT-SWAP')
    date = request.args.get('date', datetime.now().strftime('%Y%m%d'))
    
    records = read_consolidation_data(symbol, date)
    
    return jsonify({
        'success': True,
        'symbol': symbol,
        'date': date,
        'count': len(records),
        'records': records
    })
```

### JavaScript前端读取

```javascript
async function loadConsolidationHistory(symbol, date) {
    const response = await fetch(
        `/api/consolidation-monitor/history?symbol=${symbol}&date=${date}`
    );
    const data = await response.json();
    
    if (data.success) {
        console.log(`${symbol} ${date}: ${data.count}条记录`);
        return data.records;
    }
    return [];
}

// 使用示例
const records = await loadConsolidationHistory('BTC-USDT-SWAP', '20260325');
```

## 数据分析示例

### 1. 统计每日横盘频率

```python
def analyze_daily_consolidation(records):
    """分析每日横盘情况"""
    total = len(records)
    consolidation = sum(1 for r in records if r['is_consolidation'])
    
    return {
        'total_records': total,
        'consolidation_count': consolidation,
        'consolidation_ratio': consolidation / total if total > 0 else 0,
        'max_consecutive': max((r['consecutive_count'] for r in records), default=0)
    }
```

### 2. 查找告警时刻

```python
def find_alert_moments(records, min_consecutive=3):
    """查找触发告警的时刻"""
    alerts = []
    
    for i, record in enumerate(records):
        if record['consecutive_count'] >= min_consecutive:
            # 检查是否刚达到阈值
            if i == 0 or records[i-1]['consecutive_count'] < min_consecutive:
                alerts.append(record)
    
    return alerts
```

### 3. 计算横盘持续时间

```python
def calculate_consolidation_duration(records):
    """计算横盘持续时间"""
    durations = []
    current_duration = 0
    
    for record in records:
        if record['is_consolidation']:
            current_duration += 1
        else:
            if current_duration > 0:
                durations.append(current_duration)
            current_duration = 0
    
    if current_duration > 0:
        durations.append(current_duration)
    
    return {
        'max_duration': max(durations) if durations else 0,
        'avg_duration': sum(durations) / len(durations) if durations else 0,
        'total_periods': len(durations)
    }
```

## 配置文件

### consolidation_config.json

```json
{
  "BTC-USDT-SWAP": {
    "enabled": true,
    "threshold": 0.0005,
    "min_consecutive": 3,
    "name": "BTC永续合约"
  },
  "ETH-USDT-SWAP": {
    "enabled": true,
    "threshold": 0.0005,
    "min_consecutive": 3,
    "name": "ETH永续合约"
  }
}
```

### 配置说明

| 字段 | 说明 | 默认值 |
|------|------|--------|
| enabled | 是否启用监控 | true |
| threshold | 横盘阈值（小数） | 0.0005 (0.05%) |
| min_consecutive | 最小连续次数 | 3 |
| name | 显示名称 | - |

## 数据查询API

### 1. 获取最新状态
```
GET /api/consolidation-monitor/status
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "BTC": {
      "timestamp": 1774413900000,
      "datetime": "2026-03-25 12:45:00",
      "change_percent": -0.000393,
      "consecutive_count": 1,
      "is_consolidation": true
    }
  },
  "update_time": "2026-03-25 12:50:20"
}
```

### 2. 查询历史数据
```
GET /api/consolidation-monitor/history?symbol=BTC-USDT-SWAP&date=20260325&limit=100
```

**参数说明**：
- `symbol`: 交易对（BTC-USDT-SWAP/ETH-USDT-SWAP）
- `date`: 日期（YYYYMMDD格式，可选）
- `limit`: 返回记录数（可选）

**响应示例**：
```json
{
  "success": true,
  "symbol": "BTC-USDT-SWAP",
  "date": "20260325",
  "count": 24,
  "records": [...]
}
```

## 监控规则

### 横盘判断
```python
is_consolidation = abs(change_percent) <= 0.0005  # 0.05%
```

### 连续统计
从最新K线向前计数，遇到非横盘立即中断：
```python
consecutive = 0
for record in reversed(records):
    if record['is_consolidation']:
        consecutive += 1
    else:
        break
```

### 告警触发
只在刚达到阈值时发送一次：
```python
if consecutive >= min_consecutive:
    if previous_consecutive < min_consecutive:
        send_alert()
```

## 注意事项

1. **时区**：所有datetime字段均为北京时间（UTC+8）
2. **K线周期**：5分钟K线（每5分钟一条记录）
3. **数据完整性**：只记录已完成的K线，避免数据不准确
4. **重复记录**：脚本会自动去重，同一时间戳只记录一次
5. **文件命名**：文件名包含日期，便于按日期查询

## 数据备份建议

1. **每日备份**：建议每天备份前一天的数据
2. **压缩存储**：可以用gzip压缩旧数据节省空间
3. **长期归档**：超过30天的数据可移至归档目录

```bash
# 压缩旧数据
gzip data/consolidation_monitor/consolidation_*_20260301.jsonl

# 移至归档
mkdir -p data/consolidation_monitor/archive/202603
mv data/consolidation_monitor/consolidation_*_202603*.jsonl.gz \
   data/consolidation_monitor/archive/202603/
```

## 故障排查

### 数据缺失
检查PM2进程状态：
```bash
pm2 list | grep consolidation-monitor
pm2 logs consolidation-monitor --lines 50
```

### 数据异常
验证数据格式：
```bash
# 检查JSON格式
cat consolidation_BTC_USDT_SWAP_20260325.jsonl | jq .

# 统计记录数
wc -l consolidation_BTC_USDT_SWAP_20260325.jsonl
```

### 配置问题
检查配置文件：
```bash
cat consolidation_config.json | jq .
```
