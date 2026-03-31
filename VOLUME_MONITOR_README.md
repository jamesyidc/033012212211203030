# BTC & ETH 5分钟成交量监控系统

## 功能概述

监控 OKX 上 BTC-USDT-SWAP 和 ETH-USDT-SWAP 的 5 分钟成交量，当成交量超过设定阈值时通过 Telegram 发送通知。

## 访问页面

https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/coin-change-tracker

在页面中找到"BTC & ETH 5分钟成交量监控"区域。

## 功能特性

1. **实时监控**：每5分钟获取一次最新的K线成交量数据
2. **可配置阈值**：可在页面上随时调整 BTC 和 ETH 的成交量阈值
3. **Telegram 通知**：成交量超过阈值时自动发送 Telegram 告警
4. **防重复通知**：同一个5分钟K线周期只发送一次通知
5. **历史数据记录**：所有数据保存到 JSONL 文件供后续分析
6. **启用/禁用开关**：可随时启用或禁用某个币种的监控
7. **历史数据查询**：可按日期和币种查询历史成交量数据（新增）
   - 支持 BTC 和 ETH 的历史数据查询
   - 按日期筛选，最多显示 288 条记录（24小时）
   - 表格展示：时间、成交量(M)、成交量(币)、价格、状态
   - 超阈值记录自动高亮显示

## 默认配置

- **BTC-USDT-SWAP**: 阈值 100M USDT（1亿 USDT）
- **ETH-USDT-SWAP**: 阈值 50M USDT（5000万 USDT）

**注意**：单位为 **M**（百万 USDT），与 OKX 页面显示一致。

## 使用步骤

### 1. 在页面上配置

访问 `/coin-change-tracker` 页面，找到成交量监控区域：

1. 调整阈值：在输入框中输入新的阈值（单位：M USDT，1M = 100万 USDT）
2. 启用/禁用：勾选或取消勾选"启用监控"复选框
3. 刷新数据：点击"刷新数据"按钮查看最新成交量（单位：M USDT）

### 2. 配置 Telegram（可选）

如果需要接收 Telegram 通知，请设置环境变量：

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

然后重启监控服务：

```bash
pm2 restart btc-eth-volume-monitor
```

### 3. 查看监控状态

```bash
# 查看服务状态
pm2 status btc-eth-volume-monitor

# 查看日志
pm2 logs btc-eth-volume-monitor --lines 50
```

## 数据文件位置

- **配置文件**: `/home/user/webapp/data/volume_monitor/volume_thresholds.json`
- **状态文件**: `/home/user/webapp/data/volume_monitor/volume_state.json`
- **历史数据**: `/home/user/webapp/data/volume_monitor/volume_*_YYYYMMDD.jsonl`

## API 接口

### 1. 获取成交量状态

```
GET /api/volume-monitor/status
```

返回示例：

```json
{
    "success": true,
    "BTC": {
        "timestamp": 1774001100000,
        "volume_usdt": 1219750.25,
        "volume_base": 1733.25,
        "threshold": 100000000,
        "enabled": true
    },
    "ETH": {
        "timestamp": 1774001100000,
        "volume_usdt": 1320450.75,
        "volume_base": 6171.43,
        "threshold": 50000000,
        "enabled": true
    }
}
```

**说明**：
- `volume_usdt`: 成交量（USDT），前端显示时除以 1,000,000 得到 M 单位
- `threshold`: 阈值（USDT），前端显示时除以 1,000,000 得到 M 单位
- 示例：1219750.25 / 1000000 = **1.22 M USDT**

### 2. 更新阈值配置

```
POST /api/volume-monitor/config
Content-Type: application/json

{
    "symbol": "BTC-USDT-SWAP",
    "threshold": 15000000000
}
```

### 3. 启用/禁用监控

```
POST /api/volume-monitor/toggle
Content-Type: application/json

{
    "symbol": "ETH-USDT-SWAP",
    "enabled": false
}
```

### 4. 查询历史数据（新增）

```
GET /api/volume-monitor/history?symbol=BTC-USDT-SWAP&date=20260320&limit=100
```

参数：
- `symbol`: BTC-USDT-SWAP 或 ETH-USDT-SWAP
- `date`: 日期（YYYYMMDD 格式，可选，默认今天）
- `limit`: 返回记录数（可选，默认100，最多288）

返回示例：

```json
{
    "success": true,
    "symbol": "BTC-USDT-SWAP",
    "date": "20260320",
    "count": 4,
    "records": [
        {
            "timestamp": 1774000500000,
            "datetime": "2026-03-20 17:55:00",
            "symbol": "BTC-USDT-SWAP",
            "volume": 5668778.17868,
            "price": 70530.9,
            "threshold": 100000000,
            "exceeded": false,
            "recorded_at": "2026-03-20 17:56:10"
        }
    ]
}
```

### 5. 获取可用日期列表（新增）

```
GET /api/volume-monitor/dates?symbol=BTC-USDT-SWAP
```

返回示例：

```json
{
    "success": true,
    "symbol": "BTC-USDT-SWAP",
    "count": 1,
    "dates": [
        {
            "date": "20260320",
            "formatted": "2026-03-20",
            "file": "volume_BTC_USDT_SWAP_20260320.jsonl"
        }
    ]
}
```

## 告警消息格式

当成交量超过阈值时，Telegram 会收到如下格式的消息：

```
🚨 成交量告警

📊 BTC永续合约
⏰ 时间: 2026-03-20 17:55:00
💰 价格: $70,530.90
📈 5分钟成交量: 120.50M
⚠️ 阈值: 100.00M

超过阈值 20.5%
```

## 数据示例

JSONL 文件中的数据格式：

```json
{
    "timestamp": 1774000500000,
    "datetime": "2026-03-20 17:55:00",
    "symbol": "BTC-USDT-SWAP",
    "volume": 5668778178.68,
    "price": 70530.9,
    "threshold": 10000000000,
    "exceeded": false,
    "recorded_at": "2026-03-20 17:56:10"
}
```

## 常见问题

### Q: 如何修改阈值？

A: 直接在页面上的输入框中修改，修改后会自动保存。

### Q: 为什么没有收到 Telegram 通知？

A: 请检查：
1. 环境变量 `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID` 是否设置
2. 监控服务是否正在运行：`pm2 status btc-eth-volume-monitor`
3. 成交量是否确实超过了阈值
4. 查看日志确认：`pm2 logs btc-eth-volume-monitor`

### Q: 如何查看历史数据？

A: 历史数据保存在 `/home/user/webapp/data/volume_monitor/volume_*_YYYYMMDD.jsonl` 文件中，可以使用任何文本编辑器或 Python/Node.js 脚本读取和分析。

### Q: 监控频率可以调整吗？

A: 当前固定为 5 分钟（与OKX的K线周期对齐）。如需调整，请修改 `btc_eth_volume_monitor.py` 中的 `time.sleep(300)` 参数。

## 维护命令

```bash
# 启动监控
pm2 start btc_eth_volume_monitor.py --name btc-eth-volume-monitor --interpreter python3

# 停止监控
pm2 stop btc-eth-volume-monitor

# 重启监控
pm2 restart btc-eth-volume-monitor

# 查看日志
pm2 logs btc-eth-volume-monitor

# 删除监控
pm2 delete btc-eth-volume-monitor
```

## 技术架构

- **后端监控**: Python 脚本 (`btc_eth_volume_monitor.py`)
- **数据采集**: OKX API (`/api/v5/market/candles`)
- **Web API**: Flask (`/api/volume-monitor/*`)
- **前端UI**: 集成在 `/coin-change-tracker` 页面
- **通知系统**: Telegram Bot API
- **数据存储**: JSON 配置文件 + JSONL 历史记录

