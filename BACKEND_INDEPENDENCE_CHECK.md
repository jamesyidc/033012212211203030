# 后台独立运行检查报告

## 概述
本文档验证系统是否完全独立于前端浏览器运行，确保关闭浏览器后所有核心功能依然正常工作。

## 检查日期
2026-03-24

## 后台进程清单（PM2管理）

### 数据采集器 (Collectors)
✅ **coin-change-tracker** - 27币种涨跌幅追踪
✅ **coin-price-tracker** - 币种价格追踪
✅ **crypto-index-collector** - 加密货币指数采集
✅ **okx-day-change-collector** - OKX日内涨跌采集
✅ **panic-wash-collector** - 恐慌/洗盘数据采集
✅ **price-baseline-collector** - 价格基准线采集
✅ **price-comparison-collector** - 价格比较采集
✅ **price-speed-collector** - 价格速度采集
✅ **sar-slope-collector** - SAR斜率采集
✅ **sar-bias-stats-collector** - SAR偏向统计采集
✅ **financial-indicators-collector** - 金融指标采集
✅ **liquidation-1h-collector** - 1小时清算数据采集
✅ **v1v2-collector** - V1/V2阈值数据采集
✅ **btc-eth-ratio-collector** - BTC/ETH比率采集

### 监控器 (Monitors)
✅ **btc-eth-volume-monitor** - **BTC/ETH成交量监控（包含V1/V2双阈值判断、Telegram告警）**
✅ **volume-monitor** - 通用成交量监控
✅ **positive-ratio-monitor** - 正比率监控
✅ **short-to-long-monitor** - 空转多监控
✅ **sar-bias-monitor** - SAR偏向监控
✅ **liquidation-alert-monitor** - 清算告警监控
✅ **data-health-monitor** - 数据健康监控
✅ **system-health-monitor** - 系统健康监控

### 其他后台服务
✅ **abc-position-tracker** - ABC仓位追踪
✅ **daily-prediction-generator** - 每日预测生成
✅ **signal-collector** - 交易信号采集
✅ **backup-manager** - 备份管理
✅ **dashboard-jsonl-manager** - Dashboard数据管理
✅ **gdrive-jsonl-manager** - Google Drive数据管理
✅ **flask-app** - Flask API服务器（端口9002）

## 核心功能独立性验证

### 1. BTC/ETH 成交量监控 ✅
**后台脚本**: `btc_eth_volume_monitor.py`
**PM2进程**: `btc-eth-volume-monitor`

**功能**：
- ✅ 每5分钟从OKX API获取BTC/ETH 5分钟K线数据
- ✅ 双阈值判断（V1高阈值、V2中等阈值）
- ✅ 数据记录到JSONL文件（包含exceeded_level字段）
- ✅ Telegram告警发送（V1发3遍红色，V2发1遍黄色）
- ✅ 避免重复告警（基于时间戳+级别）

**API端点**：
- `/api/volume-monitor/status` - 获取最新成交量状态
- `/api/volume-monitor/config` - 配置阈值
- `/api/volume-monitor/toggle` - 启用/禁用监控
- `/api/volume-monitor/history` - 查询历史数据
- `/api/volume-monitor/daily-stats` - **后台计算V1/V2次数统计**

**前端职责**：
- ✅ 仅展示数据（从API获取）
- ✅ 配置阈值（通过API保存到后台）
- ✅ 每30秒刷新显示（可选，关闭浏览器不影响后台）

### 2. 2小时多空增量统计 ✅
**后台API**: `/api/coin-change-tracker/sentiment-change-stats`
**数据来源**: `data/sar_bias_stats/bias_stats_YYYYMMDD.jsonl`

**功能**：
- ✅ 统计SAR指标的看多/看空点数变化
- ✅ 比较当前2小时窗口和前2小时窗口
- ✅ 计算增量（current - previous）

**前端职责**：
- ✅ 仅展示数据（从API获取）
- ✅ 每60秒刷新一次（可选）

### 3. 今日超过阈值次数统计 ✅（已修复）
**后台API**: `/api/volume-monitor/daily-stats`

**问题**：
- ❌ 之前：前端JavaScript遍历所有记录，计算V1/V2次数
- ✅ 现在：后台API计算，前端仅展示结果

**API返回**：
```json
{
  "v1_count": 0,
  "v2_count": 2,
  "total_exceeded": 2,
  "total_records": 262,
  "threshold_v1": 300000000,
  "threshold_v2_min": 130000000,
  "threshold_v2_max": 299000000
}
```

### 4. 27币涨跌幅追踪 ✅
**后台脚本**: `core_code/source_code/coin_change_tracker_collector.py`
**PM2进程**: `coin-change-tracker`
**数据文件**: `data/coin_change_tracker/coin_change_YYYYMMDD.jsonl`

**功能**：
- ✅ 实时采集27个币种的价格和涨跌幅
- ✅ 计算cumulative_change、up_ratio等指标
- ✅ 记录RSI、velocity等数据

### 5. SAR偏向统计 ✅
**后台脚本**: `core_code/source_code/sar_bias_stats_collector.py`
**PM2进程**: `sar-bias-stats-collector`

**功能**：
- ✅ 统计看多/看空币种数量
- ✅ 生成每日汇总（daily_stats）

### 6. 每日预测生成 ✅
**后台脚本**: `core_code/source_code/daily_prediction_generator.py`
**PM2进程**: `daily-prediction-generator`

**功能**：
- ✅ 基于历史数据生成每日涨跌预测
- ✅ 统计绿/红/黄/空白次数

## 前端JavaScript角色定位

### 仅用于UI展示的函数
- `loadVolumeData()` - 加载并展示成交量数据
- `loadSARBiasStats()` - 加载并展示SAR统计
- `loadDailyPrediction()` - 加载并展示每日预测
- `loadSentimentChangeStats()` - 加载并展示2小时多空增量
- `loadExceededCountStats()` - 加载并展示今日超过阈值次数

### UI辅助函数（非核心逻辑）
- `calculateUpRatioBarData()` - 前端图表数据分组（用于展示）
- `calculateDuration()` - 时间差显示格式化
- 各种折叠/展开/高亮效果

### 配置管理（通过API保存到后台）
- `saveVolumeThreshold()` - 保存阈值配置
- `toggleVolumeMonitor()` - 启用/禁用监控

## 数据流架构

```
OKX API → 后台采集器 → JSONL文件 → Flask API → 前端展示
   ↓           ↓            ↓           ↓
 实时数据   业务逻辑     持久化存储   只读展示
```

## 测试验证

### 测试1: 关闭浏览器后BTC/ETH监控是否运行
```bash
# 检查后台进程
pm2 list | grep btc-eth-volume-monitor
# 状态: online ✅

# 检查日志
pm2 logs btc-eth-volume-monitor --lines 10
# 可见定期采集日志 ✅

# 检查数据文件
ls -lh data/volume_monitor/volume_BTC_USDT_SWAP_20260324.jsonl
# 文件持续更新 ✅
```

### 测试2: 统计API是否正常工作
```bash
curl -s "http://localhost:9002/api/volume-monitor/daily-stats?symbol=BTC-USDT-SWAP" | jq
# 返回: {"v1_count": 0, "v2_count": 0, "success": true} ✅

curl -s "http://localhost:9002/api/volume-monitor/daily-stats?symbol=ETH-USDT-SWAP" | jq
# 返回: {"v1_count": 0, "v2_count": 2, "success": true} ✅
```

### 测试3: Telegram告警是否正常
- ✅ 后台监控检测到V1阈值超过时，自动发送3条红色告警
- ✅ 检测到V2阈值时，自动发送1条黄色告警
- ✅ 不需要浏览器打开

## 结论

✅ **系统完全独立于前端浏览器运行**

所有核心功能（数据采集、阈值判断、统计计算、告警发送）都在后台进程中完成。

前端浏览器只负责：
1. 展示数据（通过API获取）
2. 配置管理（通过API保存到后台）
3. UI交互效果

关闭浏览器后，系统依然：
- ✅ 持续采集数据
- ✅ 实时监控阈值
- ✅ 发送Telegram告警
- ✅ 生成每日统计
- ✅ 记录历史数据

## 改进建议

1. ✅ 已完成：将成交量统计迁移到后台API
2. 建议：定期检查PM2进程健康状态
3. 建议：添加后台服务重启告警
4. 建议：增加数据采集失败的自动重试机制

