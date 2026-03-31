# 每日凌晨2点预判自动生成 - 问题修复报告

## 📋 问题描述

用户反馈：**每天凌晨2点的预判都需要手动修复**

## 🔍 问题根因分析

### 现状调查
1. **缺少自动化任务**
   - ❌ 没有定时任务（crontab为空）
   - ❌ `coin_change_prediction_monitor.py` 只是空壳，无实际功能
   - ❌ `regenerate_all_predictions.py` 是手动批量重新生成历史数据的工具

2. **数据采集正常**
   - ✅ `coin_change_tracker_collector.py` 正常采集0-2点数据
   - ✅ 数据文件 `coin_change_20260321.jsonl` 存在且内容完整

3. **API和前端正常**
   - ✅ API路由 `/api/coin-change-tracker/daily-prediction` 工作正常
   - ✅ 前端能正确显示预判数据（如果文件存在）

### 根本原因
**缺少自动化调度任务在凌晨2点后生成当天的预判文件**

每天凌晨2点后，虽然0-2点的数据已经采集完成，但没有程序自动读取这些数据、分析并生成预判文件，导致需要人工运行 `regenerate_all_predictions.py` 来手动生成。

## ✅ 解决方案

### 新增自动生成器：`daily_prediction_generator.py`

#### 核心功能
1. **智能时间窗口**
   - 仅在凌晨 **02:00-03:00** 时间窗口生成预判
   - 每5分钟检查一次
   - 避免在其他时段重复生成

2. **防重复机制**
   - 检查今日预判文件是否已存在
   - 如已存在则跳过，避免覆盖

3. **数据分析逻辑**
   ```
   读取0-2点数据 → 按10分钟分组 → 计算上涨占比 → 判断颜色（绿/红/黄）
   → 根据规则判断信号（低吸/做空/观望等） → 生成预判文件
   ```

4. **信号判断规则**
   - **空头强控盘**：全部空白（0涨幅）
   - **诱多不参与**：全部绿色
   - **做空**：只有红色或红色+空白
   - **低吸**：有绿≥3根+红，无黄或黄≤1根
   - **等待新低**：有绿有红，黄≥2根
   - **观望**：其他混合情况

5. **文件格式**
   ```json
   {
     "date": "2026-03-21",
     "timestamp": "2026-03-21 02:00:00",
     "analysis_time": "02:00:00",
     "color_counts": {
       "green": 1,
       "red": 11,
       "yellow": 0,
       "blank": 0,
       "blank_ratio": 0.0
     },
     "signal": "观望",
     "description": "⚪ 柱状图混合分布，建议观望",
     "is_final": true,
     "is_temp": false
   }
   ```

#### PM2部署
```bash
# 服务名称
daily-prediction-generator

# 进程ID
33

# 状态
✅ online

# 日志文件
~/.pm2/logs/daily-prediction-generator-out.log
~/.pm2/logs/daily-prediction-generator-error.log
/home/user/webapp/logs/daily_prediction_generator.log
```

#### 数据存储
```
目录：data/daily_predictions/
格式：prediction_YYYYMMDD.jsonl
示例：prediction_20260321.jsonl
```

## 🧪 测试验证

### 实时测试（2026-03-21 02:07）
```bash
# 1. 检查服务状态
pm2 list | grep daily-prediction
✅ id 33 | daily-prediction-generator | online | uptime 0s

# 2. 查看日志
pm2 logs daily-prediction-generator --lines 20
✅ 当前北京时间: 2026-03-21 02:07:06
✅ 开始生成今日预判...
✅ 找到 96 条0-2点数据记录
✅ 生成预判: 2026-03-21 - 绿1 红11 黄0 空0 - 观望
✅ 预判文件已保存: data/daily_predictions/prediction_20260321.jsonl
✅ 🎉 成功生成今日预判: 2026-03-21 - 观望

# 3. 验证文件生成
ls -la data/daily_predictions/prediction_20260321.jsonl
✅ -rw-r--r-- 1 user user 289 Mar 20 18:07

# 4. 测试API
curl "http://localhost:9002/api/coin-change-tracker/daily-prediction?date=2026-03-21"
✅ {
  "success": true,
  "source": "final",
  "data": {
    "signal": "观望",
    "color_counts": {"green": 1, "red": 11, "yellow": 0, "blank": 0},
    ...
  }
}

# 5. 验证前端显示
# 浏览器控制台日志：
✅ 成功获取日期 2026-03-21 的预判数据: 观望
✅ 📊 已加载日期预判数据: 2026-03-21 观望
✅ 🎯 预测卡片更新: {date: 2026-03-21, signal: 观望, green: 1, red: 11, yellow: 0}
```

## 📊 运行流程图

```
00:00 - 02:00  | 数据采集阶段
               | coin_change_tracker_collector.py 
               | 每分钟采集27个币种的涨跌幅数据
               ↓
02:00 - 03:00  | 预判生成窗口
               | daily_prediction_generator.py 每5分钟检查
               ↓
               | 读取0-2点数据（约100+条记录）
               ↓
               | 按10分钟分组，计算平均上涨占比
               ↓
               | 判断每个时间段颜色（绿/红/黄/空）
               ↓
               | 根据颜色组合判断交易信号
               ↓
               | 生成 prediction_YYYYMMDD.jsonl
               ↓
03:00+         | 全天使用固定预判文件
               | API返回 "source": "final"
               | 前端显示预判结果
```

## 🎯 技术要点

### 1. 北京时间处理
```python
def get_beijing_time():
    from datetime import timezone, timedelta
    utc_now = datetime.now(timezone.utc)
    beijing_tz = timezone(timedelta(hours=8))
    return utc_now.astimezone(beijing_tz)
```

### 2. 时间窗口控制
```python
if current_hour < 2 or current_hour >= 3:
    logger.info(f"当前时间 {current_hour}:xx 不在生成时间窗口（02:00-03:00），跳过")
    return False
```

### 3. 防重复生成
```python
pred_file = f'data/daily_predictions/prediction_{date_file}.jsonl'
if os.path.exists(pred_file):
    logger.info(f"今日预判已存在: {pred_file}，跳过生成")
    return False
```

### 4. 数据分组统计
```python
# 按10分钟分组
interval = 10
grouped = defaultdict(lambda: {'ratios': []})
for record in records:
    total_minutes = hour * 60 + minute
    group_index = total_minutes // interval
    grouped[group_index]['ratios'].append(up_ratio)
```

### 5. 信号判断逻辑
```python
# 核心判断规则（按优先级）
if blank > 0 and green == 0 and red == 0 and yellow == 0:
    signal = "空头强控盘"
elif green > 0 and red == 0 and yellow == 0 and blank == 0:
    signal = "诱多不参与"
elif red > 0 and green == 0 and yellow == 0:
    signal = "做空"
elif green >= 3 and red > 0 and yellow == 0:
    signal = "低吸"
elif green > 0 and red > 0 and yellow >= 2:
    signal = "等待新低"
# ... 更多规则
```

## 📈 预期效果

### 之前（需要手动修复）
```
02:00  数据采集完成
       ↓
       ❌ 无预判文件
       ↓
用户访问网站  →  ⚠️ 提示"暂无预判数据"
       ↓
用户手动运行  →  python3 regenerate_all_predictions.py
       ↓
       ✅ 预判文件生成
```

### 现在（全自动）
```
02:00  数据采集完成
       ↓
02:00-02:05  自动检测并生成预判
       ↓
       ✅ 预判文件已就绪
       ↓
用户访问网站  →  ✅ 正常显示预判结果
```

## 🔧 维护指南

### 日常监控
```bash
# 查看服务状态
pm2 list | grep daily-prediction

# 查看今日日志
pm2 logs daily-prediction-generator --lines 50

# 查看详细日志文件
tail -f logs/daily_prediction_generator.log
```

### 手动触发（如需）
```bash
# 如果某天自动生成失败，可手动运行
python3 daily_prediction_generator.py

# 或者使用批量重新生成工具
python3 regenerate_all_predictions.py
```

### 故障排查
1. **预判文件未生成**
   - 检查服务是否运行：`pm2 list`
   - 查看错误日志：`pm2 logs daily-prediction-generator --err`
   - 检查数据文件是否存在：`ls data/coin_change_tracker/coin_change_YYYYMMDD.jsonl`

2. **生成了错误的预判**
   - 查看日志确认数据范围
   - 检查0-2点数据是否完整
   - 手动重新生成：`python3 regenerate_all_predictions.py`

3. **服务意外停止**
   - PM2自动重启
   - 查看崩溃日志：`~/.pm2/logs/daily-prediction-generator-error.log`

## 📝 相关文件

| 文件 | 说明 |
|-----|------|
| `daily_prediction_generator.py` | ⭐ 新增：每日自动生成器 |
| `coin_change_prediction_monitor.py` | 旧文件（空壳），可考虑删除 |
| `regenerate_all_predictions.py` | 批量重新生成历史数据工具 |
| `core_code/app.py` | API路由：`/api/coin-change-tracker/daily-prediction` |
| `templates/coin_change_tracker.html` | 前端页面：预判卡片显示 |

## 🎉 总结

### 问题
❌ 每天凌晨2点预判需要手动修复

### 根因
❌ 缺少自动化任务在凌晨2点后生成预判文件

### 解决
✅ 创建 `daily_prediction_generator.py` 自动生成器
✅ PM2托管，开机自启，故障自动重启
✅ 智能时间窗口（02:00-03:00）
✅ 防重复生成机制
✅ 详细日志记录

### 效果
🎉 **完全自动化，无需人工干预**
- 每天凌晨2点后自动生成预判
- 前端页面立即可用
- 用户体验流畅

### 部署信息
- **Git Commit**: 8ddf145
- **PM2服务**: daily-prediction-generator (id 33)
- **运行状态**: ✅ Online
- **测试日期**: 2026-03-21 02:07
- **测试结果**: ✅ 通过

---

## 💡 建议

1. **监控告警**（可选）
   - 每天上午检查昨晚是否成功生成预判
   - 可设置告警通知（邮件/企业微信等）

2. **备份策略**（可选）
   - 定期备份 `data/daily_predictions/` 目录
   - 保留历史预判数据用于回溯分析

3. **性能优化**（未来）
   - 如数据量增大，可考虑数据库存储
   - 添加缓存层提升API响应速度

---

**修复完成时间**: 2026-03-21 02:07 (UTC+8)  
**修复人员**: AI Assistant  
**验证状态**: ✅ 已验证通过
