# 横盘监控数据使用指南

## 数据存储格式

### 文件位置
```
data/consolidation_monitor/
├── consolidation_BTC_USDT_SWAP_YYYYMMDD.jsonl  # BTC每日数据
├── consolidation_ETH_USDT_SWAP_YYYYMMDD.jsonl  # ETH每日数据
├── consolidation_config.json                    # 配置文件
└── consolidation_state.json                     # 运行状态
```

### 数据格式 (JSONL)
每一行是一条JSON记录，包含以下字段：

```json
{
  "timestamp": 1774413900000,                    // Unix时间戳（毫秒）
  "datetime": "2026-03-25 12:45:00",             // 北京时间
  "symbol": "BTC-USDT-SWAP",                     // 交易对
  "change_percent": -0.0003929672989011462,      // 涨跌幅（小数形式）
  "change_percent_display": "-0.039%",           // 涨跌幅（显示格式）
  "price": 70716.0,                              // 收盘价
  "is_consolidation": true,                      // 是否横盘（|涨跌幅|≤0.05%）
  "consecutive_count": 1,                        // 当前连续横盘次数
  "recorded_at": "2026-03-25 12:50:20"          // 记录时间
}
```

## API调用方式

### 1. 获取最新状态
**端点**: `GET /api/consolidation-monitor/status`

**请求示例**:
```bash
curl http://localhost:9002/api/consolidation-monitor/status
```

**返回示例**:
```json
{
  "success": true,
  "data": {
    "BTC": {
      "timestamp": 1774413900000,
      "datetime": "2026-03-25 12:45:00",
      "change_percent": -0.0003929672989011462,
      "change_percent_display": "-0.039%",
      "price": 70716.0,
      "is_consolidation": true,
      "consecutive_count": 1,
      "recent_records": [...]                    // 最近5条记录
    },
    "ETH": {
      // 类似BTC的数据结构
    }
  },
  "update_time": "2026-03-25 12:50:20"
}
```

### 2. 查询历史数据
**端点**: `GET /api/consolidation-monitor/history`

**参数**:
- `symbol`: 交易对（`BTC-USDT-SWAP` 或 `ETH-USDT-SWAP`）
- `date`: 日期（`YYYYMMDD`格式，默认今天）
- `limit`: 返回条数（可选，不指定则返回全部）

**请求示例**:
```bash
# 查询BTC今天的所有数据
curl "http://localhost:9002/api/consolidation-monitor/history?symbol=BTC-USDT-SWAP"

# 查询ETH指定日期的数据
curl "http://localhost:9002/api/consolidation-monitor/history?symbol=ETH-USDT-SWAP&date=20260325"

# 查询BTC最近10条记录
curl "http://localhost:9002/api/consolidation-monitor/history?symbol=BTC-USDT-SWAP&limit=10"
```

**返回示例**:
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
      "change_percent": -0.0003929672989011462,
      "change_percent_display": "-0.039%",
      "price": 70716.0,
      "is_consolidation": true,
      "consecutive_count": 1,
      "recorded_at": "2026-03-25 12:50:20",
      "symbol": "BTC-USDT-SWAP"
    },
    // ... 更多记录
  ]
}
```

## Python代码示例

### 读取JSONL文件
```python
import json
from pathlib import Path
from datetime import datetime, timedelta

def read_consolidation_data(symbol='BTC-USDT-SWAP', date=None):
    """
    读取横盘监控数据
    
    Args:
        symbol: 交易对 (BTC-USDT-SWAP 或 ETH-USDT-SWAP)
        date: 日期 (YYYYMMDD格式，默认今天)
    
    Returns:
        list: 数据记录列表
    """
    if date is None:
        # 默认今天（北京时间）
        date = (datetime.now() + timedelta(hours=8)).strftime('%Y%m%d')
    
    # 构建文件路径
    data_dir = Path('/home/user/webapp/data/consolidation_monitor')
    file_path = data_dir / f'consolidation_{symbol.replace("-", "_")}_{date}.jsonl'
    
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return []
    
    # 读取所有记录
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    record = json.loads(line)
                    records.append(record)
                except Exception as e:
                    print(f"解析JSON失败: {e}")
                    continue
    
    return records

# 使用示例
btc_data = read_consolidation_data('BTC-USDT-SWAP', '20260325')
print(f"读取到 {len(btc_data)} 条BTC数据")

for record in btc_data:
    print(f"{record['datetime']}: {record['change_percent_display']} "
          f"(横盘: {record['is_consolidation']}, 连续: {record['consecutive_count']})")
```

### 统计分析示例
```python
def analyze_consolidation(records):
    """
    分析横盘数据
    
    Args:
        records: 数据记录列表
    
    Returns:
        dict: 统计结果
    """
    if not records:
        return {}
    
    # 统计横盘和波动的次数
    consolidation_count = sum(1 for r in records if r['is_consolidation'])
    volatility_count = len(records) - consolidation_count
    
    # 找出最大连续横盘次数
    max_consecutive = max(r['consecutive_count'] for r in records)
    
    # 统计触发告警的次数（连续≥3）
    alert_times = sum(1 for r in records if r['consecutive_count'] >= 3)
    
    # 计算平均涨跌幅
    avg_change = sum(abs(r['change_percent']) for r in records) / len(records)
    
    return {
        'total_records': len(records),
        'consolidation_count': consolidation_count,
        'volatility_count': volatility_count,
        'consolidation_ratio': consolidation_count / len(records) * 100,
        'max_consecutive': max_consecutive,
        'alert_times': alert_times,
        'avg_change_percent': avg_change * 100
    }

# 使用示例
btc_data = read_consolidation_data('BTC-USDT-SWAP')
stats = analyze_consolidation(btc_data)

print(f"总记录数: {stats['total_records']}")
print(f"横盘次数: {stats['consolidation_count']} ({stats['consolidation_ratio']:.1f}%)")
print(f"波动次数: {stats['volatility_count']}")
print(f"最大连续横盘: {stats['max_consecutive']}次")
print(f"触发告警次数: {stats['alert_times']}次")
print(f"平均涨跌幅: {stats['avg_change_percent']:.3f}%")
```

### 查询特定时间段的横盘记录
```python
from datetime import datetime

def filter_consolidation_records(records, start_time=None, end_time=None, min_consecutive=3):
    """
    筛选满足条件的横盘记录
    
    Args:
        records: 数据记录列表
        start_time: 开始时间 (格式: "HH:MM")
        end_time: 结束时间 (格式: "HH:MM")
        min_consecutive: 最小连续次数
    
    Returns:
        list: 筛选后的记录
    """
    filtered = []
    
    for record in records:
        # 检查连续次数
        if record['consecutive_count'] < min_consecutive:
            continue
        
        # 检查时间范围
        if start_time or end_time:
            time_str = record['datetime'].split()[1][:5]  # 提取HH:MM
            
            if start_time and time_str < start_time:
                continue
            if end_time and time_str > end_time:
                continue
        
        filtered.append(record)
    
    return filtered

# 使用示例：查询9:00-12:00之间连续≥3次的横盘记录
btc_data = read_consolidation_data('BTC-USDT-SWAP')
morning_alerts = filter_consolidation_records(
    btc_data, 
    start_time="09:00", 
    end_time="12:00",
    min_consecutive=3
)

print(f"上午9-12点触发告警 {len(morning_alerts)} 次:")
for record in morning_alerts:
    print(f"  {record['datetime']}: 连续{record['consecutive_count']}次横盘")
```

## JavaScript代码示例

### 前端调用API
```javascript
// 获取最新状态
async function getConsolidationStatus() {
    try {
        const response = await fetch('/api/consolidation-monitor/status');
        const data = await response.json();
        
        if (data.success) {
            console.log('BTC连续横盘次数:', data.data.BTC.consecutive_count);
            console.log('ETH连续横盘次数:', data.data.ETH.consecutive_count);
            return data.data;
        }
    } catch (error) {
        console.error('获取横盘状态失败:', error);
    }
}

// 查询历史数据
async function getConsolidationHistory(symbol, date, limit) {
    try {
        let url = `/api/consolidation-monitor/history?symbol=${symbol}`;
        if (date) url += `&date=${date}`;
        if (limit) url += `&limit=${limit}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            console.log(`查询到 ${data.count} 条记录`);
            return data.records;
        }
    } catch (error) {
        console.error('查询历史数据失败:', error);
    }
}

// 使用示例
getConsolidationStatus().then(status => {
    if (status.BTC.consecutive_count >= 3) {
        alert('BTC横盘连续' + status.BTC.consecutive_count + '次，要变盘了！');
    }
});

// 查询今天所有数据
getConsolidationHistory('BTC-USDT-SWAP').then(records => {
    console.log('今天的横盘记录:', records);
});
```

## 数据字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `timestamp` | number | Unix时间戳（毫秒） | 1774413900000 |
| `datetime` | string | 北京时间（YYYY-MM-DD HH:MM:SS） | "2026-03-25 12:45:00" |
| `symbol` | string | 交易对 | "BTC-USDT-SWAP" |
| `change_percent` | number | 涨跌幅（小数形式，0.01=1%） | -0.000392967 |
| `change_percent_display` | string | 涨跌幅（显示格式） | "-0.039%" |
| `price` | number | 收盘价（USDT） | 70716.0 |
| `is_consolidation` | boolean | 是否横盘（\|涨跌幅\|≤0.05%） | true |
| `consecutive_count` | number | 当前连续横盘次数 | 1 |
| `recorded_at` | string | 记录时间 | "2026-03-25 12:50:20" |

## 常见使用场景

### 1. 回测分析
```python
# 分析某天的横盘情况与后续走势的关系
def backtest_consolidation_signal(date):
    btc_data = read_consolidation_data('BTC-USDT-SWAP', date)
    
    # 找出所有触发告警的时刻
    alerts = [r for r in btc_data if r['consecutive_count'] >= 3]
    
    for alert in alerts:
        alert_time = alert['datetime']
        alert_price = alert['price']
        
        # 查看告警后1小时的价格变化
        # ... 分析代码
        
    return analysis_results
```

### 2. 实时监控
```javascript
// 每分钟检查一次，发现连续横盘≥3次时提醒
setInterval(async () => {
    const status = await getConsolidationStatus();
    
    if (status.BTC.consecutive_count >= 3 || status.ETH.consecutive_count >= 3) {
        showNotification('横盘变盘告警', '要变盘了！');
    }
}, 60000);
```

### 3. 统计报表
```python
# 生成每日横盘统计报表
def generate_daily_report(date):
    btc_data = read_consolidation_data('BTC-USDT-SWAP', date)
    eth_data = read_consolidation_data('ETH-USDT-SWAP', date)
    
    report = {
        'date': date,
        'BTC': analyze_consolidation(btc_data),
        'ETH': analyze_consolidation(eth_data)
    }
    
    return report
```

## 注意事项

1. **数据更新频率**: 每5分钟更新一次（对应5分钟K线）
2. **时区**: 所有时间均为北京时间（UTC+8）
3. **数据保留**: 按日期分文件存储，建议定期备份
4. **并发访问**: JSONL文件支持并发读取，但写入时有锁机制
5. **数据完整性**: 每条记录都包含完整的字段，不会缺失

## 故障排查

### 数据文件不存在
```python
# 检查数据文件是否存在
from pathlib import Path
data_dir = Path('/home/user/webapp/data/consolidation_monitor')
print(list(data_dir.glob('consolidation_*.jsonl')))
```

### API返回错误
```bash
# 检查Flask应用状态
pm2 status flask-app

# 查看Flask日志
pm2 logs flask-app --lines 50
```

### 监控进程未运行
```bash
# 检查监控进程状态
pm2 status consolidation-monitor

# 重启监控进程
pm2 restart consolidation-monitor

# 查看监控日志
pm2 logs consolidation-monitor --lines 50
```

## 联系方式

如有问题，请查看：
- 主配置文件: `data/consolidation_monitor/consolidation_config.json`
- 监控脚本: `consolidation_monitor.py`
- API文档: `core_code/app.py` (搜索 `consolidation-monitor`)
