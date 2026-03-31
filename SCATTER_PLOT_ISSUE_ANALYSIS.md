# 币种变动追踪器散点图数据缺失问题分析

**问题时间**: 2026-03-17 04:00  
**影响范围**: 币种变动追踪器当天数据的散点图不显示

---

## 🔍 问题描述

用户反馈截图显示：
- ✅ **有数据**：顶部显示"24小时盈亏: -0.87"，底部有"10分钟上涨占比"柱状图
- ❌ **无散点图**：趋势图上应该显示27个币种的涨跌幅散点，但只看到主线条和几个标记点
- ❌ **当天数据丢失**：图表上显示的是昨天（03-16）的数据，而不是今天（03-17）的数据

---

## 🕵️ 根本原因

### 1. API使用了lite模式，删除了散点图数据

**代码位置**: `templates/coin_change_tracker.html` 第8046行

**问题代码**:
```javascript
let url = `/api/coin-change-tracker/history?lite=true&date=${currentDate}&_t=${Date.now()}`;
```

**影响**:
- `lite=true` 导致API只返回汇总数据（total_change, up_ratio等）
- **删除了`changes`字段**，该字段包含27个币种的详细涨跌幅数据
- 散点图渲染需要`changes`字段，没有这个字段就无法显示每个币种的点

**API代码** (`core_code/app.py` 第25056-25067行):
```python
if lite and 'changes' in record:
    # 只保留统计信息，移除详细的27币数据
    record_lite = {
        'timestamp': record.get('timestamp'),
        'beijing_time': record.get('beijing_time'),
        'total_change': record.get('total_change'),
        'cumulative_pct': record.get('cumulative_pct'),
        'up_ratio': record.get('up_ratio'),
        'up_coins': record.get('up_coins'),
        'down_coins': record.get('down_coins')
    }
    records.append(record_lite)
```

### 2. 散点图渲染代码缺失

**检查发现**: 
- 趋势图的series数组中**只有主线条**（27币涨跌幅之和）
- **没有为每个币种生成scatter系列**的代码
- 这个功能可能在之前的某次修改中被删除或从未实现

---

## ✅ 已修复内容

### 修复1: 改用完整模式API

**修改位置**: `templates/coin_change_tracker.html` 第8046行

**修复代码**:
```javascript
let url = `/api/coin-change-tracker/history?lite=false&date=${currentDate}&_t=${Date.now()}`;
```

**效果**:
- API现在返回完整的`changes`字段
- 包含27个币种的详细数据：current_price, baseline_price, change_pct等

**验证**:
```bash
curl "http://localhost:9002/api/coin-change-tracker/history?lite=false&date=2026-03-17"
# 返回：27个币种的完整数据
```

### 数据文件验证

**文件存在**: `data/coin_change_tracker/coin_change_20260317.jsonl`
- ✅ 文件大小: 12K
- ✅ 数据条数: 9条（截至04:05）
- ✅ 包含完整的27币种changes字段

**示例数据**:
```json
{
  "timestamp": 1773690951899,
  "beijing_time": "2026-03-17 03:55:42",
  "total_change": 37.73,
  "changes": {
    "BTC": {"current_price": 73890.3, "baseline_price": 73240.8, "change_pct": 0.89},
    "ETH": {"current_price": 2329.96, "baseline_price": 2272.38, "change_pct": 2.53},
    "XRP": {"current_price": 1.5228, "baseline_price": 1.4923, "change_pct": 2.04},
    ... // 共27个币种
  }
}
```

---

## ⚠️ 待修复内容

### 待修复: 添加散点图渲染代码

**需要添加**: 为每个币种生成scatter系列的代码

**理想位置**: 主趋势图setOption之后，在交易标记代码同级

**实现思路**:
```javascript
// 遍历historyData，为每个币种收集数据点
const coinSeriesMap = {};  // {coinName: [[time_index, change_pct], ...]}

historyData.forEach((record, recordIndex) => {
    if (!record.changes) return;
    
    Object.entries(record.changes).forEach(([symbol, data]) => {
        if (data.error) return;
        
        const coinName = symbol.replace('-USDT-SWAP', '');
        if (!coinSeriesMap[coinName]) {
            coinSeriesMap[coinName] = [];
        }
        
        coinSeriesMap[coinName].push([recordIndex, data.change_pct]);
    });
});

// 为每个币种生成scatter系列
const coinScatterSeries = Object.entries(coinSeriesMap).map(([coinName, dataPoints]) => ({
    id: `coin-scatter-${coinName}`,
    name: coinName,
    type: 'scatter',
    yAxisIndex: 0,
    data: dataPoints,
    symbolSize: 6,
    itemStyle: { opacity: 0.6 }
}));

// 添加到图表
trendChart.setOption({
    series: coinScatterSeries
}, {notMerge: false});
```

---

## 📦 备份恢复需求

用户提到备份文件: `webapp_backup_20260317_1.tar.gz`
- **文件大小**: 267.89 MB
- **备份时间**: 2026-03-17 03:21:35

### 恢复内容

1. **恢复改错的代码**
   - 可能是散点图相关的代码被误删
   - 或者lite模式的修改破坏了功能

2. **恢复今天丢失的数据**
   - 检查backup中的data/coin_change_tracker/coin_change_20260317.jsonl
   - 对比当前文件，看是否有数据丢失
   - 如果backup中数据更完整，则恢复

### 恢复步骤

```bash
# 1. 解压备份文件到临时目录
mkdir -p /tmp/backup_restore
tar -xzf webapp_backup_20260317_1.tar.gz -C /tmp/backup_restore

# 2. 对比lite模式修改
diff /tmp/backup_restore/webapp/templates/coin_change_tracker.html \
     /home/user/webapp/templates/coin_change_tracker.html | grep -A 5 -B 5 "lite"

# 3. 对比数据文件
diff /tmp/backup_restore/webapp/data/coin_change_tracker/coin_change_20260317.jsonl \
     /home/user/webapp/data/coin_change_tracker/coin_change_20260317.jsonl

# 4. 恢复散点图代码（如果backup中有）
# grep -A 50 "币种散点\|coin.*scatter" /tmp/backup_restore/webapp/templates/coin_change_tracker.html

# 5. 恢复数据文件（如果backup数据更完整）
# cp /tmp/backup_restore/webapp/data/coin_change_tracker/coin_change_20260317.jsonl \
#    /home/user/webapp/data/coin_change_tracker/
```

---

## 📝 Git提交记录

**已提交修复**:
- Commit: `b8947dc`
- 消息: "fix: 修复币种变动追踪器散点图数据缺失问题"
- 修改: `lite=true` → `lite=false`

---

## 🔗 相关链接

- **验证页面**: https://9002-izdl7i89gq7ib3tbi6fq1-82b888ba.sandbox.novita.ai/coin-change-tracker
- **API测试**: http://localhost:9002/api/coin-change-tracker/history?lite=false&date=2026-03-17

---

## 💡 下一步

**等待用户操作**:
1. 上传备份文件 `webapp_backup_20260317_1.tar.gz` 到服务器
2. 或提供备份文件的访问链接

**自动化修复**:
1. 添加散点图渲染代码
2. 测试验证散点图显示
3. 提交完整修复

---

**修复完成时间**: 待定  
**当前状态**: ⏸️ 等待备份文件恢复
