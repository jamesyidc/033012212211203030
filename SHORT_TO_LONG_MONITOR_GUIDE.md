# 空转多触发价监控系统 - 完整说明文档

## 📋 问题分析

### 用户反馈
```
空转多触发价
30.00%
0:30后最低:
0.00%
+30触发:
30.00%
出现在 00:30:59   空转多
这个也没有接到tg消息
```

### 问题原因
1. **前端显示存在**：币价变化追踪页面已经计算并显示"空转多触发价"
2. **后端监控缺失**：没有对应的监控器发送TG通知
3. **时机错过**：监控器启动时间（14:27）远晚于信号触发时间（01:59）

---

## ✅ 解决方案

### 新建监控器：`short_to_long_trigger_monitor.py`

#### 📊 监控逻辑
```
1. 获取今日正数占比历史数据
2. 筛选出0:30之后的所有数据
3. 找到最低正数占比值及其时间
4. 计算触发价 = 最低值 + 30%
5. 监控当前正数占比是否达到触发价
6. 达到后发送TG通知（3次），标记已触发
7. 每天0:00自动重置状态
```

#### 🔢 计算示例（今日实际数据）
```
0:30后最低正数占比: 0.00%
出现时间: 00:30:59
触发价 = 0.00% + 30% = 30.00%

实际触发:
时间: 01:59:07
正数占比: 30.53% (≥ 30.00%)
```

---

## 🚀 部署信息

### PM2进程
```bash
# 进程名称
short-to-long-monitor

# 启动命令
pm2 start source_code/short_to_long_trigger_monitor.py \
  --name "short-to-long-monitor" \
  --interpreter python3

# 查看状态
pm2 status short-to-long-monitor

# 查看日志
pm2 logs short-to-long-monitor --lines 50
```

### 文件位置
- **监控脚本**：`/home/user/webapp/source_code/short_to_long_trigger_monitor.py`
- **状态文件**：`/home/user/webapp/data/short_to_long_monitor/state.json`
- **报警历史**：`/home/user/webapp/data/short_to_long_monitor/alert_history.json`

### 配置参数
```python
CHECK_INTERVAL = 60  # 检查间隔：60秒
TRIGGER_OFFSET = 30.0  # 触发偏移：最低值+30%
REPEAT_COUNT = 3  # TG消息重复次数
API_URL = "http://localhost:9002/api/coin-change-tracker/positive-ratio-history"
TG_BOT_TOKEN = "8437045462:AAFePnwdC21cqeWhZISMQHGGgjmroVqE2H0"
TG_CHAT_ID = "-1003227444260"
```

---

## 📊 监控日志示例

### 启动日志
```
2026-03-19 14:35:46 - INFO - 🚀 空转多触发价监控系统启动
2026-03-19 14:35:46 - INFO - ⚙️  配置参数:
2026-03-19 14:35:46 - INFO -    - 触发规则: 0:30后最低值 + 30.0%
2026-03-19 14:35:46 - INFO -    - 检查间隔: 60秒
2026-03-19 14:35:46 - INFO -    - Telegram消息重复次数: 3次
2026-03-19 14:35:46 - INFO -    - Telegram Bot: ✅ 已配置
```

### 检测到信号
```
2026-03-19 14:35:46 - INFO - 🆕 新的一天，重置监控状态: 20260319
2026-03-19 14:35:46 - INFO - ✅ 获取历史数据成功: 1047条记录
2026-03-19 14:35:46 - INFO - 📊 空转多触发价计算: 最低0.00% (在00:30:59) + 30 = 30.00%
2026-03-19 14:35:46 - INFO - 📊 当前正数占比: 55.68% | 触发价: 30.00% | 已触发: False
2026-03-19 14:35:46 - WARNING - 🔥 检测到空转多信号！触发价: 30.00%, 实际: 30.53%, 时间: 01:59:07
2026-03-19 14:35:47 - INFO - ✅ Telegram消息发送成功 (1/3)
2026-03-19 14:35:48 - INFO - ✅ Telegram消息发送成功 (2/3)
2026-03-19 14:35:50 - INFO - ✅ Telegram消息发送成功 (3/3)
2026-03-19 14:35:50 - INFO - 💾 报警记录已保存
```

---

## 📱 Telegram通知内容

### 消息格式
```
🟢 空转多信号触发！

━━━━━━━━━━━━━━━━━━
📊 触发详情
━━━━━━━━━━━━━━━━━━

📉 0:30后最低正数占比: 0.00% (出现在 00:30:59)
⚡ 空转多触发价: 30.00% (最低+30%)
📈 实际触发正数占比: 30.53%
⏰ 触发时间: 01:59:07

━━━━━━━━━━━━━━━━━━

💡 操作建议: 逢低做多

📊 当前数据:
  • 当前正数占比: 55.68%
  • 数据日期: 20260319
  • 检查时间: 2026-03-19 14:35:46
```

### 发送规则
- ✅ 发送3次（间隔1秒）
- ✅ 每天只触发一次（触发后标记为已触发）
- ✅ 次日0:00自动重置状态

---

## 🔄 状态管理

### 状态文件结构
```json
{
  "last_date": "20260319",
  "min_ratio_after_0030": 0.0,
  "min_time": "00:30:59",
  "trigger_ratio": 30.0,
  "triggered": true,
  "trigger_time": "01:59:07"
}
```

### 状态重置
- **触发条件**：每天00:00检测到日期变化
- **重置内容**：
  - `min_ratio_after_0030` → `null`
  - `trigger_ratio` → `null`
  - `triggered` → `false`
  - `trigger_time` → `null`

---

## 🔍 监控流程图

```
┌──────────────────────────────────────────────┐
│  short_to_long_trigger_monitor.py           │
│  (PM2进程, 每60秒执行一次)                  │
└──────────────────────────────────────────────┘
           │
           ├─> 1. 检查日期是否变化
           │    • 是 → 重置状态
           │    • 否 → 继续
           │
           ├─> 2. 获取今日正数占比历史
           │    GET /api/coin-change-tracker/positive-ratio-history?date=YYYYMMDD
           │
           ├─> 3. 筛选0:30之后的数据
           │    • 过滤 time >= "00:30:00"
           │
           ├─> 4. 找到最低正数占比
           │    min_ratio = min(data_after_0030, key=lambda x: x['positive_ratio'])
           │
           ├─> 5. 计算触发价
           │    trigger_ratio = min_ratio + 30.0
           │
           ├─> 6. 检查是否达到触发条件
           │    • current_ratio >= trigger_ratio
           │    • AND !triggered
           │
           └─> 7. 发送Telegram通知（3次）
                • 保存报警记录
                • 标记已触发
```

---

## 🛠️ 故障排查

### 监控器未运行
```bash
# 检查进程状态
pm2 status short-to-long-monitor

# 如果显示stopped，重启
pm2 restart short-to-long-monitor

# 查看错误日志
pm2 logs short-to-long-monitor --lines 100 --err
```

### 未收到TG通知
1. **检查监控器日志**：
   ```bash
   pm2 logs short-to-long-monitor | grep "Telegram消息"
   ```

2. **验证Telegram配置**：
   ```bash
   # 手动测试发送
   curl -X POST "https://api.telegram.org/bot8437045462:AAFePnwdC21cqeWhZISMQHGGgjmroVqE2H0/sendMessage" \
     -d "chat_id=-1003227444260" \
     -d "text=测试消息"
   ```

3. **检查触发状态**：
   ```bash
   cat /home/user/webapp/data/short_to_long_monitor/state.json
   ```

### 触发价计算异常
```bash
# 检查0:30后数据量
curl -s "http://localhost:9002/api/coin-change-tracker/positive-ratio-history?date=$(date +%Y%m%d)" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)['data']
after_0030 = [r for r in data if r['time'] >= '00:30:00']
print(f'0:30后数据: {len(after_0030)}条')
if after_0030:
    min_r = min(after_0030, key=lambda x: x['positive_ratio'])
    print(f'最低值: {min_r[\"positive_ratio\"]}% 在 {min_r[\"time\"]}')
    print(f'触发价: {min_r[\"positive_ratio\"] + 30}%')
"
```

---

## 📈 与其他监控器的区别

### 1. positive-ratio-monitor（正数占比多空转换）
- **阈值**：动态计算（当日最高值 - 20%）
- **触发**：从多方转空方 或 从空方转多方
- **示例**：86.4% - 20% = 66.4%，跌破66.4%时触发

### 2. short-to-long-monitor（空转多触发价）
- **阈值**：0:30后最低值 + 30%
- **触发**：从0:30后最低点反弹30%
- **示例**：0.00% + 30% = 30.00%，达到30.00%时触发

### 3. market-sentiment-collector（市场情绪）
- **指标**：RSI变化与币价变化对比
- **触发**：见顶/见底信号
- **频率**：每15分钟

---

## 📝 今日实际触发记录

```json
{
  "date": "20260319",
  "trigger_time": "01:59:07",
  "min_ratio": 0.0,
  "min_time": "00:30:59",
  "trigger_ratio": 30.0,
  "actual_ratio": 30.53,
  "current_ratio": 55.68,
  "check_time": "2026-03-19 14:35:46"
}
```

**说明**：
- 最低点出现在 **00:30:59**，正数占比 **0.00%**
- 触发价为 **30.00%**
- 实际在 **01:59:07** 达到 **30.53%** 触发
- 监控器在 **14:35:46** 启动后立即检测到历史触发记录并补发通知

---

## 🎯 后续优化建议

1. **实时触发**：
   - 当前：每60秒检查一次
   - 优化：使用WebSocket实时推送

2. **多级预警**：
   - 预警1：达到最低值+20%
   - 预警2：达到最低值+25%
   - 触发：达到最低值+30%

3. **可配置阈值**：
   - 允许用户自定义偏移量（当前固定30%）
   - 支持多个触发点

4. **历史分析**：
   - 统计历史触发成功率
   - 分析最佳入场时机

---

## 📞 技术支持

### 监控器管理
```bash
# 查看所有监控器
pm2 list

# 重启所有监控器
pm2 restart all

# 查看总体日志
pm2 logs --lines 50

# 监控特定进程
pm2 monit
```

### 数据查询
```bash
# 查看状态文件
cat /home/user/webapp/data/short_to_long_monitor/state.json | python3 -m json.tool

# 查看报警历史
cat /home/user/webapp/data/short_to_long_monitor/alert_history.json | python3 -m json.tool

# 查看今日正数占比趋势
curl -s "http://localhost:9002/api/coin-change-tracker/positive-ratio-history?date=$(date +%Y%m%d)" | \
  python3 -m json.tool | head -50
```

---

**最后更新**：2026-03-19 14:40 (北京时间)
**监控器状态**：✅ 已启动并正常运行
**今日触发**：✅ 成功检测并发送TG通知（3次）
