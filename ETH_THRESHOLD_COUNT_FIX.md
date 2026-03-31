# ETH超阈值次数统计错误修复报告

## 问题描述

用户报告：ETH在今日（2026-03-23）有两次超过阈值（2:35 和 5:05），但前端界面只显示"今日超过阈值: 1次"。

## 问题分析

### 1. 数据验证

通过检查原始数据文件 `data/volume_monitor/volume_ETH_USDT_SWAP_20260323.jsonl`：

```
Total records: 144
Exceeded records: 2
  2026-03-23 02:35:00: 159.69M > 130M (timestamp: 1774204500000)
  2026-03-23 05:05:00: 345.64M > 130M (timestamp: 1774213500000)
```

确认数据文件中**确实记录了2次超阈值事件**。

### 2. 根因定位

问题出在 `/api/volume-monitor/history` API接口：

**原代码（第34712行）**：
```python
limit = int(request.args.get('limit', 100))  # 返回最近N条记录
```

**原代码（第34739行）**：
```python
# 返回最近的 limit 条记录
records = records[-limit:] if len(records) > limit else records
```

**问题**：
- API默认`limit=100`，只返回最近100条记录
- 今日共144条记录，第一次超阈值(2:35)在第40条左右
- 返回最后100条时，第一次超阈值记录被截掉了
- 前端统计时只能看到1次(5:05)

### 3. API响应对比

**修复前**：
```bash
curl "http://localhost:9002/api/volume-monitor/history?symbol=ETH-USDT-SWAP&date=20260323"
# 返回: 100条记录，1次超阈值
```

**修复后**：
```bash
curl "http://localhost:9002/api/volume-monitor/history?symbol=ETH-USDT-SWAP&date=20260323"
# 返回: 144条记录，2次超阈值
```

## 修复方案

### 代码修改

**文件**: `core_code/app.py` (行 34708-34739)

**修改内容**：

1. **移除默认limit限制**：
```python
# 修改前
limit = int(request.args.get('limit', 100))

# 修改后
limit = request.args.get('limit')  # None表示返回全部
```

2. **条件性应用limit**：
```python
# 修改前
records = records[-limit:] if len(records) > limit else records

# 修改后
if limit is not None:
    limit = int(limit)
    records = records[-limit:] if len(records) > limit else records
```

### 修复逻辑

- **不指定limit参数**：返回全部记录（用于前端统计今日超阈值次数）
- **指定limit参数**：返回最近N条记录（保留向后兼容）

## 测试验证

### 1. API测试

```bash
curl -s "http://localhost:9002/api/volume-monitor/history?symbol=ETH-USDT-SWAP&date=20260323" \
  | python3 -c "import sys,json; data=json.load(sys.stdin); \
  exceeded=[r for r in data['records'] if r.get('exceeded')]; \
  print(f'Total: {len(data[\"records\"])}, Exceeded: {len(exceeded)}')"
```

**结果**：
```
Total: 144, Exceeded: 2
```

### 2. 超阈值记录详情

| 时间 | 成交量 | 阈值 | 超出倍数 |
|------|--------|------|----------|
| 2026-03-23 02:35:00 | 159.69M | 130M | 1.23x |
| 2026-03-23 05:05:00 | 345.64M | 130M | 2.66x |

## 影响范围

- **修复的问题**：ETH和BTC的今日超阈值次数统计现在准确
- **向后兼容**：保留了limit参数支持，不影响其他使用场景
- **性能影响**：单日数据量通常144-288条（每5分钟一条），返回全部记录对性能无明显影响

## 部署状态

- ✅ 代码已修复
- ✅ Flask应用已重启
- ✅ API测试通过
- ✅ 本地提交完成 (commit: 14b1887)
- ⏸️ 等待推送到远程仓库 (需要GitHub认证)

## 前端显示

修复后，前端应正确显示：

```
🔔 ETH 5分钟成交量
💰 当前成交量: 9.11 M
⚠️ 13日M USDT
📊 阈值范围: 130 M USDT
✅ 未达阈值

今日超过阈值: 2 次    (修复前显示: 1 次)
```

## 建议

1. **监控告警**：可以考虑在超过2次阈值时发送Telegram告警
2. **历史统计**：可以添加"本周/本月超阈值次数"统计
3. **阈值调优**：当超阈值次数过于频繁时，考虑调整13日M USDT算法

---

**修复时间**: 2026-03-23  
**修复文件**: `core_code/app.py`  
**提交信息**: "fix: 修复ETH超阈值次数统计错误"
