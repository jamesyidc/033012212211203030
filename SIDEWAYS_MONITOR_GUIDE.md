# 横盘变盘监控功能说明

## 功能概述

实时监控BTC和ETH永续合约的5分钟K线涨跌幅，当连续3根或以上K线的涨跌幅绝对值 ≤ 0.05% 时，自动发送Telegram告警提示"要变盘了"。

## 功能特性

### 监控对象
- BTC-USDT-SWAP（BTC永续合约）
- ETH-USDT-SWAP（ETH永续合约）

### 监控周期
- 5分钟K线
- 每60秒检查一次

### 判断逻辑
1. 计算每根K线涨跌幅：`(收盘价 - 开盘价) / 开盘价 * 100`
2. 取绝对值：`|涨跌幅|`
3. 判断横盘：`|涨跌幅| ≤ 0.05%`
4. 连续计数：
   - 横盘：count++
   - 不横盘：count重置为0
5. 触发告警：count ≥ 3

### 告警控制
- 同一波横盘最多30分钟告警一次
- 避免频繁告警打扰

## 技术架构

### 后台监控
**脚本**: `sideways_monitor.py`
**PM2进程**: `sideways-monitor`

**主要功能**：
- 从OKX API获取5分钟K线数据
- 计算涨跌幅并判断是否横盘
- 维护连续计数状态
- 发送Telegram告警
- 记录历史数据到JSONL

**状态管理**：
- 状态文件：`data/sideways_monitor/sideways_state.json`
- 包含：consecutive_count（连续次数）、last_alert_time（上次告警时间）、recent_candles（最近10根K线）

### 后台API

#### 1. 获取当前状态
```bash
GET /api/sideways-monitor/status
```

**返回示例**：
```json
{
  "success": true,
  "BTC": {
    "consecutive_count": 2,
    "last_alert_time": null,
    "latest_candle": {
      "timestamp": 1774413600000,
      "datetime": "2026-03-25 12:40:00",
      "change_pct": 0.012158,
      "abs_change_pct": 0.012158
    },
    "threshold": 0.05
  },
  "ETH": {
    "consecutive_count": 2,
    "last_alert_time": null,
    "latest_candle": {
      "timestamp": 1774413600000,
      "datetime": "2026-03-25 12:40:00",
      "change_pct": -0.010649,
      "abs_change_pct": 0.010649
    },
    "threshold": 0.05
  },
  "min_consecutive": 3
}
```

#### 2. 查询历史数据
```bash
GET /api/sideways-monitor/history?symbol=BTC-USDT-SWAP&date=20260325&limit=20
```

**参数**：
- `symbol`: BTC-USDT-SWAP 或 ETH-USDT-SWAP
- `date`: 日期（YYYYMMDD格式，可选，默认今天）
- `limit`: 返回记录数（可选，默认全部）

**返回示例**：
```json
{
  "success": true,
  "symbol": "BTC-USDT-SWAP",
  "date": "20260325",
  "count": 20,
  "records": [
    {
      "timestamp": 1774413600000,
      "datetime": "2026-03-25 12:35:00",
      "symbol": "BTC-USDT-SWAP",
      "change_pct": -0.01,
      "abs_change_pct": 0.01,
      "consecutive_count": 1,
      "is_sideways": true,
      "threshold": 0.05,
      "recorded_at": "2026-03-25 12:44:25"
    }
  ]
}
```

### 数据存储

**目录**: `data/sideways_monitor/`

**文件格式**:
- `sideways_BTC_USDT_SWAP_YYYYMMDD.jsonl` - BTC每日数据
- `sideways_ETH_USDT_SWAP_YYYYMMDD.jsonl` - ETH每日数据
- `sideways_state.json` - 当前状态

**数据字段**:
- `timestamp`: 时间戳（毫秒）
- `datetime`: 北京时间字符串
- `symbol`: 交易对
- `change_pct`: 涨跌幅（%）
- `abs_change_pct`: 涨跌幅绝对值（%）
- `consecutive_count`: 当前连续次数
- `is_sideways`: 是否横盘（boolean）
- `threshold`: 判断阈值（0.05）
- `recorded_at`: 记录时间

## Telegram告警

### 告警触发条件
- 连续3根或以上K线涨跌幅 ≤ 0.05%
- 距离上次告警 ≥ 30分钟

### 告警消息格式
```
🚨 横盘变盘告警

📊 币种: BTC
⏱️ 周期: 5分钟
📈 连续次数: 3 根K线
📉 涨跌幅阈值: ≤ 0.05%

最近K线数据:
  2026-03-25 09:50:00 +0.03%
  2026-03-25 09:55:00 +0.04%
  2026-03-25 10:00:00 -0.03%

⚠️ 注意：可能即将变盘！
```

## 使用示例

### 检查后台进程状态
```bash
pm2 list | grep sideways-monitor
# 应显示: online 状态
```

### 查看实时日志
```bash
pm2 logs sideways-monitor --lines 50
```

### 测试API
```bash
# 查看当前状态
curl http://localhost:9002/api/sideways-monitor/status | jq

# 查看今日历史
curl "http://localhost:9002/api/sideways-monitor/history?symbol=BTC-USDT-SWAP" | jq
```

### 手动启动/重启
```bash
# 启动
pm2 start sideways_monitor.py --name sideways-monitor --interpreter python3

# 重启
pm2 restart sideways-monitor

# 停止
pm2 stop sideways-monitor

# 查看日志
pm2 logs sideways-monitor
```

## 配置调整

如需修改监控参数，编辑 `sideways_monitor.py`：

```python
# 涨跌幅阈值（%）
THRESHOLD = 0.05  # 可改为 0.03, 0.08 等

# 最少连续次数
MIN_CONSECUTIVE = 3  # 可改为 2, 4, 5 等

# 检查间隔（秒）
CHECK_INTERVAL = 60  # 可改为 30, 120 等

# 告警间隔（秒）
# 代码中设置为 1800 秒（30分钟）
# 搜索: (now - last_alert_dt).total_seconds() < 1800
```

修改后重启进程：
```bash
pm2 restart sideways-monitor
```

## 故障排查

### 问题1: 进程未运行
```bash
pm2 list | grep sideways-monitor
# 如果显示 stopped 或 errored，查看日志：
pm2 logs sideways-monitor --err --lines 50
```

### 问题2: API无响应
```bash
# 检查Flask是否运行
pm2 list | grep flask-app

# 测试API端点
curl http://localhost:9002/api/sideways-monitor/status
```

### 问题3: 无数据记录
```bash
# 检查数据目录
ls -lh data/sideways_monitor/

# 查看最新记录
tail -5 data/sideways_monitor/sideways_BTC_USDT_SWAP_$(date +%Y%m%d).jsonl
```

### 问题4: Telegram未收到告警
1. 检查Telegram配置：
   ```bash
   echo $TELEGRAM_BOT_TOKEN
   echo $TELEGRAM_CHAT_ID
   ```
2. 查看日志确认是否触发告警：
   ```bash
   pm2 logs sideways-monitor | grep "告警触发"
   ```
3. 手动测试Telegram发送：
   ```bash
   curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
     -d chat_id=$TELEGRAM_CHAT_ID \
     -d text="测试消息"
   ```

## 性能优化

### 内存占用
- 每个进程约30MB
- 保留最近10根K线数据
- 每日JSONL文件约100-200KB

### CPU使用
- 平均 <1%
- 每60秒执行一次检查
- API调用延迟 <2秒

### 网络流量
- 每分钟请求OKX API 2次（BTC+ETH）
- 每次响应约 1-2 KB
- 月流量约 80-160 MB

## 未来扩展

可能的功能增强：
1. 支持更多币种（增加到配置文件）
2. 可配置阈值（通过API动态调整）
3. 前端UI展示实时状态
4. 历史数据可视化图表
5. 多维度横盘判断（加入成交量、波动率等指标）
6. 告警级别分层（3次=提醒，5次=警告，10次=紧急）

## 相关链接

- 后台脚本：`sideways_monitor.py`
- API端点：`core_code/app.py` (搜索 "sideways-monitor")
- 数据目录：`data/sideways_monitor/`
- PM2配置：已保存在 `~/.pm2/dump.pm2`

## 联系与支持

如有问题或建议，请查看项目文档或联系开发团队。
