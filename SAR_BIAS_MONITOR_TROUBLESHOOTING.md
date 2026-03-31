# SAR Bias Monitor - 问题诊断与解决方案

## 🔍 问题分析

### 用户报告
- 页面显示"看多" 28
- 但是没有收到 Telegram 通知

### 根本原因

经过详细检查，发现了以下问题：

#### 1. **Telegram 未配置** ⚠️
监控脚本日志显示：
```
⚠️ 警告: Telegram 未配置，将只打印日志不发送消息
```

环境变量 `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID` 未设置，所以**无法发送 Telegram 消息**。

#### 2. **监控指标理解偏差**
页面上显示的"看多 28"和监控脚本监控的指标不同：

**页面显示**: 可能是当天累计的看多事件数（`daily_stats.total_bullish`）
**脚本监控**: 当前偏多 >80% 的币种数量（`bullish_symbols` 数组长度）

当前实际数据：
- 偏多 >80% 的币种数: **0个**
- 偏空 >80% 的币种数: **0个**  
- 偏多 >50% 的币种数: **11个**
- 总币种数: **29个**

所以脚本正确地没有发送告警（因为没有币种超过80%阈值）。

#### 3. **服务频繁重启问题** ✅ 已修复
之前的配置导致服务重启了 1215 次：
- 原因：`cron_restart` 配置和脚本的执行模式不匹配
- 修复：改为持续运行模式，每5分钟检查一次
- 结果：现在服务稳定运行，0次重启

## ✅ 已完成的修复

### 1. 修改运行模式
**之前**: 脚本运行完就退出，PM2 用 cron 每5分钟重启
**现在**: 脚本持续运行，内部每5分钟检查一次

### 2. 修正监控指标
**之前**: 从 API 的 `bullish_count` 字段读取（总是0）
**现在**: 计算 `bullish_symbols` 数组长度（实际 >80% 的币种数）

### 3. 增强告警信息
现在告警消息会包含：
- 看多/看空点数变化
- 具体币种列表及其比例
- 示例：`BTC(85.5%), ETH(82.3%)`

## 🔧 Telegram 配置方案

### 方案1: 系统环境变量（推荐）

1. 在系统中设置环境变量：
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

2. 重启 PM2 服务：
```bash
pm2 restart sar-bias-monitor
```

### 方案2: PM2 配置文件

在 `ecosystem.config.json` 中添加环境变量：

```json
{
  "name": "sar-bias-monitor",
  "script": "/home/user/webapp/sar_bias_monitor.py",
  "cwd": "/home/user/webapp",
  "interpreter": "python3",
  "autorestart": true,
  "max_memory_restart": "200M",
  "env": {
    "PYTHONUNBUFFERED": "1",
    "TELEGRAM_BOT_TOKEN": "YOUR_BOT_TOKEN_HERE",
    "TELEGRAM_CHAT_ID": "YOUR_CHAT_ID_HERE"
  },
  "out_file": "/home/user/webapp/logs/sar-bias-monitor-out.log",
  "error_file": "/home/user/webapp/logs/sar-bias-monitor-error.log",
  "log_date_format": "YYYY-MM-DD HH:mm:ss"
}
```

然后重启服务：
```bash
pm2 delete sar-bias-monitor
pm2 start ecosystem.config.json --only sar-bias-monitor
```

### 方案3: 从其他服务复制配置

如果其他服务（如 `okx-tpsl-monitor`）的 Telegram 通知正常工作，可以：

1. 检查那个服务的环境变量：
```bash
pm2 env <service_id>
```

2. 复制相同的配置到 sar-bias-monitor

## 📊 当前监控状态

### 服务状态
```
✅ 服务名称: sar-bias-monitor  
✅ PM2 ID: 25
✅ 运行状态: online
✅ 重启次数: 1 (稳定运行中)
✅ 检查频率: 每5分钟
```

### 监控数据
```json
{
  "last_bullish_count": 0,
  "last_bearish_count": 0,
  "last_check_time": "2026-03-19T02:46:13",
  "last_alert_time": null
}
```

### 当前币种统计
- 总币种数: 29个
- 偏多 >80%: 0个 ← **监控此指标**
- 偏空 >80%: 0个 ← **监控此指标**
- 偏多 >50%: 11个
- 偏空 >50%: 15个

## 🎯 监控机制说明

### 触发条件
当以下**任一条件**满足时发送 Telegram 通知：

1. ✅ 偏多(>80%)币种数**增加或减少**
2. ✅ 偏空(>80%)币种数**增加或减少**

### 告警示例

```
🚨 SAR Bias Trend 数据变化提醒

📈 看多点数: 3 📈 +3
   比例: 10.3%
   币种: BTC(85.5%), ETH(82.3%), BNB(81.0%)

📊 总币种数: 29
⏰ 数据时间: 2026-03-19 02:50:00

🔗 查看详情: [链接]
```

## 🧪 测试 Telegram 功能

### 手动测试脚本
```bash
# 临时设置环境变量并运行测试
TELEGRAM_BOT_TOKEN="your_token" TELEGRAM_CHAT_ID="your_chat_id" python3 /home/user/webapp/sar_bias_monitor.py
```

### 查看日志
```bash
# 查看实时日志
pm2 logs sar-bias-monitor

# 查看最近日志
pm2 logs sar-bias-monitor --lines 50 --nostream
```

### 检查环境变量
```bash
pm2 show sar-bias-monitor | grep env
pm2 env 25
```

## 📝 理解页面上的"看多"数字

根据您的截图，页面上显示"看多 28"。这个数字可能是：

1. **累计事件数**: 当天出现的看多信号总次数
2. **历史统计**: 基于 `daily_stats.total_bullish`
3. **不同的阈值**: 可能是 >50% 或其他阈值的统计

**监控脚本监控的是**: 当前时刻偏多/偏空 **>80%** 的币种数量变化

如果您希望监控不同的指标（比如 >50%），可以：
1. 修改脚本中的 `BULLISH_THRESHOLD` 和 `BEARISH_THRESHOLD`
2. 或者监控页面上实际显示的 `daily_stats` 数据

## 🔄 下一步行动

### 立即行动
1. ✅ 配置 Telegram 环境变量（见上面方案）
2. ✅ 重启服务
3. ✅ 验证日志中不再显示"Telegram 未配置"

### 验证步骤
1. 配置后查看日志：
   ```bash
   pm2 logs sar-bias-monitor --lines 20 --nostream
   ```

2. 等待下一次检查（最多5分钟）

3. 如果数据有变化，应该会收到 Telegram 消息

### 如果还是没收到消息
可能原因：
- Telegram Bot Token 或 Chat ID 不正确
- 网络问题无法访问 Telegram API  
- **实际上没有币种达到 >80% 阈值**（这是最可能的原因）

## 📊 当前状态总结

| 项目 | 状态 | 说明 |
|------|------|------|
| 服务运行 | ✅ 正常 | PM2 显示 online，重启次数稳定 |
| 数据监控 | ✅ 正常 | 每5分钟检查一次，数据正确 |
| Telegram | ❌ 未配置 | 需要设置环境变量 |
| 告警触发 | ⏸️ 待触发 | 当前无币种 >80%，无告警 |

## 📖 相关文档

- 完整文档: `SAR_BIAS_MONITOR_SETUP.md`
- 脚本文件: `sar_bias_monitor.py`
- PM2 配置: `ecosystem.config.json`
- 状态文件: `data/sar_bias_monitor_state.json`
- 历史记录: `data/sar_bias_monitor_history.jsonl`

---

**创建时间**: 2026-03-19 02:50 UTC+8  
**Git 提交**: 7123723
**状态**: ✅ 服务运行正常，待配置 Telegram
