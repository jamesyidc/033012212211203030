# SAR Bias Trend 监控系统

## 📋 功能说明

监控 SAR Bias Trend 页面的看多/看空点数变化，当数据有增加时自动发送 Telegram 通知。

## 🎯 监控指标

- **看多点数** (Bullish Count): 偏多 >80% 的币种数量
- **看空点数** (Bearish Count): 偏空 >80% 的币种数量

## ✅ 部署状态

### 服务信息
- **服务名称**: sar-bias-monitor
- **PM2 ID**: 24
- **运行状态**: ✅ Online
- **检查频率**: 每5分钟自动运行一次 (cron: */5 * * * *)
- **脚本路径**: /home/user/webapp/sar_bias_monitor.py

### 数据存储
- **状态文件**: data/sar_bias_monitor_state.json
- **历史记录**: data/sar_bias_monitor_history.jsonl

## 🔔 告警机制

### 触发条件
当以下任一条件满足时发送 Telegram 通知：
1. 看多点数发生变化（增加或减少）
2. 看空点数发生变化（增加或减少）

### 告警内容
消息包含以下信息：
- 📈 看多点数变化（显示增减量）
- 📉 看空点数变化（显示增减量）
- 📊 看多/看空比例
- ⚠️ 偏多/偏空警告（当比例 >80%）
- 📊 总币种数
- ⏰ 数据时间戳
- 🔗 查看详情链接

### 消息格式示例
```
🚨 SAR Bias Trend 数据变化提醒

📈 看多点数: 25 📈 +5
   比例: 83.3% ⚠️ 偏多

📉 看空点数: 3 📉 -2
   比例: 10.0%

📊 总币种数: 30
⏰ 数据时间: 2026-03-18 20:15:30

🔗 查看详情: https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/sar-bias-trend
```

## 🔧 Telegram 配置

### 环境变量
需要设置以下环境变量：
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### 当前状态
⚠️ **Telegram 未配置** - 监控正常运行，但不会发送消息，只记录日志

### 配置步骤
1. 从 BotFather 获取 Bot Token
2. 获取您的 Chat ID
3. 设置环境变量（可以在 PM2 配置中添加）
4. 重启服务: `pm2 restart sar-bias-monitor`

## 📊 监控数据

### 当前状态
```json
{
  "last_bullish_count": 0,
  "last_bearish_count": 0,
  "last_check_time": "2026-03-18T20:09:06",
  "last_alert_time": null
}
```

### API 端点
- **数据源**: http://localhost:9002/api/sar-slope/bias-ratios
- **监控页面**: https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/sar-bias-trend

## 🚀 使用指南

### 查看服务状态
```bash
pm2 list | grep sar-bias-monitor
```

### 查看实时日志
```bash
pm2 logs sar-bias-monitor
```

### 查看最近日志
```bash
pm2 logs sar-bias-monitor --lines 50 --nostream
```

### 手动运行测试
```bash
python3 /home/user/webapp/sar_bias_monitor.py
```

### 重启服务
```bash
pm2 restart sar-bias-monitor
```

### 停止服务
```bash
pm2 stop sar-bias-monitor
```

### 查看状态文件
```bash
cat data/sar_bias_monitor_state.json
```

### 查看历史记录
```bash
tail -20 data/sar_bias_monitor_history.jsonl
```

## 📈 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    SAR Bias Monitor                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │   每5分钟自动运行（PM2）      │
              └─────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │  获取 API 数据               │
              │  /api/sar-slope/bias-ratios  │
              └─────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │  对比上次数据                │
              │  (state.json)                │
              └─────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    │               │
                有变化            无变化
                    │               │
                    ▼               ▼
        ┌───────────────────┐   ┌──────────┐
        │  构建告警消息       │   │  记录状态 │
        │  发送 Telegram      │   │  退出     │
        │  保存历史记录       │   └──────────┘
        │  更新状态文件       │
        └───────────────────┘
```

## 🧪 测试场景

### 场景1：首次启动
- 状态：初始化状态文件
- 行为：记录当前数据，不发送告警

### 场景2：数据增加
- 条件：看多点数从 0 → 25
- 行为：发送 Telegram 告警，显示 📈 +25

### 场景3：数据减少
- 条件：看空点数从 10 → 3
- 行为：发送 Telegram 告警，显示 📉 -7

### 场景4：无变化
- 条件：数据与上次相同
- 行为：只记录状态，不发送告警

### 场景5：偏多警告
- 条件：看多点数占比 >80%
- 行为：告警消息中显示 ⚠️ 偏多

## 📝 日志说明

### 正常日志
```
🚀 SAR Bias Monitor 启动
监控阈值: 看多 >80%, 看空 >80%
API: http://localhost:9002/api/sar-slope/bias-ratios
状态文件: /home/user/webapp/data/sar_bias_monitor_state.json
历史文件: /home/user/webapp/data/sar_bias_monitor_history.jsonl

============================================================
🔍 SAR Bias Monitor - 2026-03-18 20:09:06
============================================================

📊 当前数据:
   看多点数: 0 (上次: 0)
   看空点数: 0 (上次: 0)
   总币种数: 0
   数据时间: 2026-03-18 20:09:02

✅ 数据无变化，无需告警

✅ 监控执行完成
```

### 告警日志
```
📤 准备发送告警:
🚨 SAR Bias Trend 数据变化提醒

📈 看多点数: 25 📈 +25
   比例: 83.3% ⚠️ 偏多

📊 总币种数: 30
⏰ 数据时间: 2026-03-18 20:15:30

✅ [Telegram] 消息发送成功
✅ 告警发送成功
```

## 🔍 故障排查

### 问题1：服务未运行
```bash
# 检查服务状态
pm2 list | grep sar-bias-monitor

# 如果未运行，启动服务
pm2 start ecosystem.config.json --only sar-bias-monitor
```

### 问题2：Telegram 消息未发送
- 检查环境变量是否配置
- 查看日志中是否有 "未配置Bot Token或Chat ID"
- 验证 Bot Token 和 Chat ID 的有效性

### 问题3：API 请求失败
- 检查 Flask 应用是否运行
- 验证 API 端点是否可访问
- 查看错误日志: `pm2 logs sar-bias-monitor --err`

### 问题4：数据始终为0
- SAR Bias Stats 数据采集器可能未运行
- 检查: `pm2 list | grep sar-bias-stats-collector`
- 检查数据文件是否存在和更新

## 📅 维护计划

### 日常维护
- 定期查看日志确认运行正常
- 检查历史记录文件大小（可定期清理）

### 优化建议
1. 配置 Telegram 环境变量以启用通知
2. 根据实际需求调整检查频率（当前5分钟）
3. 调整偏多/偏空阈值（当前80%）
4. 添加更多数据分析维度

## 🎉 部署完成

- ✅ 脚本已创建: `sar_bias_monitor.py`
- ✅ PM2 配置已更新: `ecosystem.config.json`
- ✅ 服务已启动: `sar-bias-monitor` (ID: 24)
- ✅ 每5分钟自动检查
- ✅ 状态文件已初始化
- ⚠️ Telegram 待配置（可选）

## 🔗 相关链接

- **监控页面**: https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/sar-bias-trend
- **API 端点**: http://localhost:9002/api/sar-slope/bias-ratios
- **脚本文件**: /home/user/webapp/sar_bias_monitor.py
- **PM2 配置**: /home/user/webapp/ecosystem.config.json

---

**创建时间**: 2026-03-19 04:10 UTC+8
**状态**: ✅ 已部署并运行
