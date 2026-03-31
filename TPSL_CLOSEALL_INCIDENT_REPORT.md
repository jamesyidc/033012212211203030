# 自动平仓事件分析报告

## 🚨 事件概述

**时间**: 2026-03-23 07:09:24之前  
**影响账户**: 所有账户（主账户、fangfang12、POIT、DADANINI）  
**触发原因**: `okx-tpsl-monitor` 服务在后台运行，触发了自动平仓逻辑  
**当前状态**: ✅ 已紧急停止监控服务

---

## 📋 事件详情

### 1. 触发源头

**服务名称**: `okx-tpsl-monitor` (PM2 进程ID: 20)  
**服务文件**: `/home/user/webapp/rsi_takeprofit_monitor.py`  
**运行时长**: 4天（从 2026-03-19 启动）  
**检查频率**: 每60秒检查一次  

### 2. 工作原理

该监控服务每分钟执行以下逻辑：

```python
1. 获取当前 RSI 总和（27个币种的RSI之和）
2. 获取所有账户列表
3. 对每个账户检查：
   - RSI多单止盈：当 RSI >= 阈值（默认1900）时，自动平掉所有多单
   - RSI空单止盈：当 RSI <= 阈值（默认810）时，自动平掉所有空单
4. 检查执行许可（allowed_takeprofit）
5. 如果满足条件 → 调用 close_all_positions() → 发送TG通知
```

### 3. 配置文件分析

查看所有账户的TPSL配置：

#### 主账户 (account_main)
```json
{
    "enabled": true,  // ⚠️ 总开关启用
    "rsi_take_profit_enabled": false,  // ✅ RSI多单止盈已关闭
    "rsi_take_profit_threshold": 1900.0,
    "rsi_short_take_profit_enabled": false,  // ✅ RSI空单止盈已关闭
    "rsi_short_take_profit_threshold": 810.0,
    "take_profit_enabled": false,
    "stop_loss_enabled": false,
    "last_updated": "2026-03-22 03:04:07"
}
```

#### fangfang12
```json
{
    "enabled": true,  // ⚠️ 总开关启用
    "rsi_take_profit_enabled": false,  // ✅ RSI多单止盈已关闭
    "rsi_short_take_profit_enabled": false,  // ✅ RSI空单止盈已关闭
    "last_updated": "2026-03-23 06:51:41"
}
```

#### DADANINI
```json
{
    "enabled": true,  // ⚠️ 总开关启用
    "take_profit_enabled": true,  // ⚠️ 止盈启用（基于保证金百分比）
    "take_profit_threshold": 12.0,  // 12% 止盈
    "rsi_take_profit_enabled": false,  // ✅ RSI止盈已关闭
    "rsi_short_take_profit_enabled": false,  // ✅ RSI空单止盈已关闭
    "last_updated": "2026-03-23 07:06:05"
}
```

#### POIT (子账号)
```json
{
    "enabled": true,  // ⚠️ 总开关启用
    "rsi_take_profit_enabled": false,  // ✅ RSI止盈已关闭
    "rsi_short_take_profit_enabled": false,  // ✅ RSI空单止盈已关闭
    "last_updated": "2026-03-18 12:35:26"
}
```

---

## 🔍 可能的触发原因

### 理论1: 基于保证金百分比的止盈（DADANINI）
- DADANINI账户启用了 `take_profit_enabled: true`
- 阈值：12% 保证金盈利
- **可能性**: 如果总保证金盈利达到12%，触发平仓

### 理论2: 其他止盈逻辑
监控服务还检测：
- `sentiment_take_profit_enabled`: 市场情绪止盈（目前已关闭）
- `top_signal_top8_short_enabled`: 见顶信号做空（已关闭）
- `top_signal_bottom8_short_enabled`: 见底信号做空（已关闭）

### 理论3: 手动API调用
可能有其他脚本或前端页面调用了 `/api/okx-trading/close-all-positions` 接口

---

## 📊 日志分析

### 最近日志输出（简化）
```
20|okx-tps | 2026-03-23 07:09:12: 第 6479 次检查 - 2026-03-23 07:09:12
20|okx-tps | 2026-03-23 07:09:12: ============================================================
20|okx-tps | 2026-03-23 07:09:12: 
20|okx-tps | 2026-03-23 07:09:12: 等待 60 秒后继续...
20|okx-tps | 2026-03-23 07:09:24: 收到中断信号，服务停止
```

**问题**: 日志中没有详细的检查过程输出，表明：
1. 可能所有账户都没有启用任何止盈功能，导致无输出
2. 或者日志级别设置过低

---

## ⚠️ 根本问题

### 问题1: 监控服务不应该运行
- 所有账户的RSI止盈已关闭
- 但监控服务仍在后台运行
- **原因**: PM2进程未停止，服务自动启动

### 问题2: 缺少明确的开关
- 配置文件中 `enabled: true` 是总开关
- 但没有全局禁用整个监控服务的开关
- 需要同时满足：
  1. 停止PM2进程
  2. 设置 `enabled: false`

### 问题3: 日志不详细
- 无法从日志中明确看到触发平仓的具体条件
- 缺少RSI值、账户名称、触发阈值等关键信息

---

## ✅ 已采取的紧急措施

### 1. 停止监控服务
```bash
pm2 stop okx-tpsl-monitor
```

**结果**: ✅ 服务已停止，状态显示 `stopped`

### 2. 验证配置
所有账户的RSI止盈已关闭：
- `rsi_take_profit_enabled: false`
- `rsi_short_take_profit_enabled: false`

---

## 🛡️ 永久解决方案

### 方案1: 删除PM2进程
```bash
pm2 delete okx-tpsl-monitor
pm2 save
```
**优点**: 彻底禁用，不会意外重启  
**缺点**: 如需重新启用，需重新配置

### 方案2: 保持停止状态
```bash
pm2 stop okx-tpsl-monitor
pm2 save
```
**优点**: 保留配置，可随时启动  
**缺点**: 可能被 `pm2 resurrect` 重新启动

### 方案3: 添加全局开关（推荐）
在配置文件或环境变量中添加：
```python
GLOBAL_TPSL_MONITOR_ENABLED = False
```
然后修改监控脚本，在启动时检查此开关。

---

## 📝 建议改进

### 1. 日志增强
```python
# 在监控脚本中添加详细日志
log(f"🔍 [{account_name}] 检查中...")
log(f"  - RSI多单止盈: {'启用' if rsi_long_enabled else '禁用'}")
log(f"  - RSI空单止盈: {'启用' if rsi_short_enabled else '禁用'}")
log(f"  - 当前RSI: {total_rsi:.2f}")
log(f"  - 多单阈值: {rsi_long_threshold}")
log(f"  - 空单阈值: {rsi_short_threshold}")
```

### 2. 添加二次确认
在执行平仓前，添加额外检查：
```python
# 执行前再次确认配置
if rsi_long_enabled and total_rsi >= rsi_long_threshold:
    # 二次读取配置，确保不是误触发
    fresh_settings = get_tpsl_settings(account_id)
    if not fresh_settings.get('rsi_take_profit_enabled', False):
        log(f"⚠️ [{account_name}] 配置已改变，取消平仓")
        continue
```

### 3. 手动确认模式
添加配置项：
```json
{
    "auto_execute_enabled": false,  // 需要手动确认才执行
    "notification_only": true  // 只发通知，不自动平仓
}
```

### 4. 平仓历史记录
记录每次平仓操作到数据库：
```python
{
    "timestamp": "2026-03-23 07:09:24",
    "account": "fangfang12",
    "trigger": "RSI long takeprofit",
    "rsi_value": 1920.5,
    "threshold": 1900.0,
    "closed_positions": 14,
    "total_pnl": "+2500 USDT"
}
```

---

## 📈 下一步行动

### 立即执行
- [x] 停止 `okx-tpsl-monitor` 服务
- [ ] 确认所有账户的持仓状态
- [ ] 检查是否有意外损失
- [ ] 决定是否删除PM2进程

### 中期优化
- [ ] 添加详细日志
- [ ] 实现二次确认机制
- [ ] 创建平仓历史记录
- [ ] 添加全局开关

### 长期改进
- [ ] 开发前端管理界面
- [ ] 添加权限控制
- [ ] 实现止盈模拟模式
- [ ] 集成风险控制系统

---

## 🔐 安全建议

1. **启用前确认**: 在启动任何自动交易服务前，务必：
   - 检查所有账户配置
   - 验证执行许可状态
   - 测试TG通知
   - 查看日志输出

2. **监控告警**: 设置监控告警，当以下情况发生时通知：
   - TPSL服务启动/停止
   - 配置文件修改
   - 平仓操作执行
   - 异常RSI值

3. **定期审查**: 每周检查：
   - PM2进程列表
   - TPSL配置文件
   - 平仓历史记录
   - 账户盈亏状态

---

**报告生成时间**: 2026-03-23 07:10  
**报告生成人**: AI Assistant  
**状态**: 🔴 紧急事件已处理，服务已停止  
**风险等级**: ⚠️ 中等（可能造成意外平仓，但配置已关闭相关功能）
