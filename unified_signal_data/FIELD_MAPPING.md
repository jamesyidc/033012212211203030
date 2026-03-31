# 逃顶信号与支撑压力系统数据映射

## 数据源信息

- **原始数据**: `data/escape_signal_jsonl/escape_signal_stats.jsonl`
- **统一数据**: `data/unified_signal_data/escape_signal_unified.jsonl`
- **记录数**: 47647
- **时间范围**: 2026-01-06 00:33:42 ~ 2026-01-23 22:10:48

## 字段映射表

| 统一格式字段 | 原始字段 | 说明 | 数据类型 |
|-------------|---------|------|---------|
| `timestamp` | `stat_time` | 统计时间戳（北京时间） | string |
| `data_type` | - | 数据类型标识：escape_signal | string |
| `source` | - | 数据来源：sar_slope_analyzer | string |
| `source_url` | - | 数据源URL | string |
| `signal_24h_count` | `signal_24h_count` | 24小时逃顶信号数量 | integer |
| `signal_2h_count` | `signal_2h_count` | 2小时逃顶信号数量 | integer |
| `max_signal_24h` | `max_signal_24h` | 24小时历史最大值 | integer |
| `max_signal_2h` | `max_signal_2h` | 2小时历史最大值 | integer |
| `decline_strength_level` | `decline_strength_level` | 下跌强度等级 | integer |
| `rise_strength_level` | `rise_strength_level` | 上涨强度等级 | integer |
| `signal_type` | - | 信号类型：topping（逃顶） | string |
| `confidence` | - | 信号置信度（0-1） | float |
| `total_coins_monitored` | - | 监控币种总数：27 | integer |
| `created_at` | `created_at` | 创建时间 | string |
| `raw_data` | - | 原始记录备份 | object |

## 与支撑压力系统的集成

### 数据对齐

1. **时间粒度**: 60秒采样（与支撑压力系统一致）
2. **监控币种**: 27个币种（相同）
3. **信号类型**:
   - 支撑压力系统：scenario1/2（抄底）, scenario3/4（逃顶）
   - SAR系统：signal_24h_count（逃顶信号强度）

### 置信度计算

```python
confidence = min(signal_24h_count / 27.0, 1.0)
```

- 0个信号 → 置信度 0%
- 14个信号 → 置信度 ~50%
- 27个信号 → 置信度 100%

### 信号强度分级

- **高强度**: signal_24h_count ≥ 100（历史峰值区域）
- **中强度**: 50 ≤ signal_24h_count < 100（显著信号）
- **低强度**: signal_24h_count < 50（正常波动）

## 使用示例

### Python 读取

```python
import json

with open('data/unified_signal_data/escape_signal_unified.jsonl', 'r') as f:
    for line in f:
        record = json.loads(line)
        print(f"{record['timestamp']}: 24h信号={record['signal_24h_count']}")
```

### API集成建议

```python
# 在支撑压力系统中集成SAR信号
def get_unified_signals(start_time=None, end_time=None):
    # 读取支撑压力信号
    sr_signals = support_resistance_adapter.get_snapshots(limit=None)
    
    # 读取SAR逃顶信号
    sar_signals = load_escape_signals_unified()
    
    # 按时间戳合并
    unified = merge_signals_by_timestamp(sr_signals, sar_signals)
    
    return unified
```

## 数据质量

- ✅ 无缺失值
- ✅ 时间戳连续（60秒间隔）
- ✅ 数值范围合理（0-966）
- ✅ 支持历史回溯（17天历史数据）

## 更新频率

- **采集**: 每60秒一次
- **存储**: 实时写入JSONL
- **API**: 实时查询

## 文件大小

- **当前**: ~11MB（47647条）
- **增长**: ~0.5MB/天
- **建议**: 按月分片存储

---
生成时间: 2026-01-25 03:15:12
