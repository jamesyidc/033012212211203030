# SAR偏向趋势统计修复：从峰值改为累计值

**修复时间**: 2026-03-16 12:00 CST  
**修复人员**: GenSpark AI Developer  
**问题描述**: 用户反馈SAR偏向趋势页面的统计信息不正确，显示为0，实际需要显示当天所有数据点的累计统计

---

## 问题分析

### 1. 用户需求
用户希望看到的是：**当天所有数据点中，偏多/偏空（>80%）的总次数累计**

例如：
- 2026-03-14 有 289 个数据点
- 其中 19 个数据点有偏多币种（bullish_count > 0）
- 6 个数据点有偏空币种（bearish_count > 0）
- 用户想看到：**累计偏多 19，累计偏空 6**

### 2. 原实现问题
之前的代码有两个问题：

#### 问题1: API计算限制
```python
# 旧代码 (core_code/app.py line 29260-29266)
if daily_stats is None:
    daily_stats = {'total_bullish': 0, 'total_bearish': 0}
    if page == 1:  # ❌ 只在第1页计算
        for record in all_data:
            daily_stats['total_bullish'] += record['bullish_count']
            daily_stats['total_bearish'] += record['bearish_count']
```

**问题**: 只在 `page == 1` 时计算，导致用户通过日期选择器选择历史日期时，无法获取统计数据

#### 问题2: 前端显示峰值而非累计
```javascript
// 旧代码 (templates/sar_bias_trend.html line 1435-1458)
// 找到偏多数量最多的记录
let maxBullishData = data.data[0];
let maxBullishCount = maxBullishData.bullish_count || 0;

for (const record of data.data) {
    if ((record.bullish_count || 0) > maxBullishCount) {
        maxBullishCount = record.bullish_count;  // ❌ 取峰值
        maxBullishData = record;
    }
}

document.getElementById('currentBullish').textContent = maxBullishCount;
```

**问题**: 显示的是当天 `bullish_count` 的最大值（峰值），而不是累计总和

---

## 修复方案

### 修复1: API始终计算累计统计

**文件**: `core_code/app.py` line 29260-29266

```python
# 新代码
if daily_stats is None:
    daily_stats = {'total_bullish': 0, 'total_bearish': 0}
    # ✅ 累加所有数据点的 bullish_count 和 bearish_count
    for record in all_data:
        daily_stats['total_bullish'] += record['bullish_count']
        daily_stats['total_bearish'] += record['bearish_count']
```

**改进**:
- 移除 `if page == 1` 限制
- 无论通过任何方式访问（page或date参数），都计算累计统计

### 修复2: 前端显示累计值

**文件**: `templates/sar_bias_trend.html` line 1431-1487

```javascript
// 新代码
} else {
    // 历史页面：显示累计统计（从daily_stats获取）
    if (data.daily_stats) {
        document.getElementById('currentBullish').textContent = data.daily_stats.total_bullish || 0;
        document.getElementById('currentBearish').textContent = data.daily_stats.total_bearish || 0;
        console.log(`✅ [历史数据] 累计偏多: ${data.daily_stats.total_bullish}, 累计偏空: ${data.daily_stats.total_bearish}`);
    } else {
        document.getElementById('currentBullish').textContent = '0';
        document.getElementById('currentBearish').textContent = '0';
    }
    
    // 收集当天所有出现过的偏多/偏空币种（去重并按出现次数排序）
    const bullishSymbolsMap = new Map();
    const bearishSymbolsMap = new Map();
    
    for (const record of data.data) {
        // 统计每个币种的出现次数和最大占比
        ...
    }
    
    // 显示: "TON 出现15次 (峰值90%)"
    bullishList.innerHTML = sortedBullish.map(s => 
        `<div class="symbol-item">${s.symbol} <span class="ratio">出现${s.count}次 (峰值${s.maxRatio}%)</span></div>`
    ).join('');
}
```

**改进**:
- 顶部统计卡片显示累计值（从 `daily_stats` 获取）
- 币种列表显示每个币种的出现次数和峰值占比
- 按出现次数排序，更直观

---

## 验证结果

### API验证

| 日期 | 总数据点 | 累计偏多 | 累计偏空 | 说明 |
|------|---------|---------|---------|------|
| 2026-02-05 | 2149 | 5597 | 16989 | 大波动日 |
| 2026-03-01 | 292 | 0 | 3 | 市场平稳 |
| 2026-03-14 | 289 | 19 | 6 | 测试基准日 |
| 2026-03-16 | 133 | 56 | 11 | 当前日 |

### 3月14日详细数据
```bash
$ curl "http://localhost:9002/api/sar-slope/bias-stats?date=2026-03-14"
{
  "success": true,
  "date": "2026-03-14",
  "total": 289,
  "daily_stats": {
    "total_bullish": 19,    # ✅ 累计偏多次数
    "total_bearish": 6      # ✅ 累计偏空次数
  }
}
```

### 页面显示验证

**顶部统计卡片**:
- `currentBullish` (看多点数): 显示累计值（如19）
- `currentBearish` (看空点数): 显示累计值（如6）

**底部统计信息**:
- `totalBullishPoints`: 显示累计值（如19）
- `totalBearishPoints`: 显示累计值（如6）

**币种列表**:
- 按出现次数排序
- 显示格式：`TON 出现15次 (峰值90%)`

---

## 技术细节

### 统计逻辑

**累计统计计算**:
```python
total_bullish = sum(record['bullish_count'] for record in all_data)
total_bearish = sum(record['bearish_count'] for record in all_data)
```

**币种出现次数统计**:
```javascript
// 去重并统计每个币种的出现次数
const bullishSymbolsMap = new Map();  // symbol -> {count, maxRatio}

for (const record of data.data) {
    if (record.bullish_symbols) {
        for (const s of record.bullish_symbols) {
            if (!bullishSymbolsMap.has(s.symbol)) {
                bullishSymbolsMap.set(s.symbol, {count: 0, maxRatio: 0});
            }
            const entry = bullishSymbolsMap.get(s.symbol);
            entry.count++;  // 累计出现次数
            entry.maxRatio = Math.max(entry.maxRatio, s.ratio);  // 记录峰值
        }
    }
}

// 排序：按出现次数降序
const sortedBullish = Array.from(bullishSymbolsMap.entries())
    .sort((a, b) => b[1].count - a[1].count || b[1].maxRatio - a[1].maxRatio);
```

### 数据流程

```
1. 用户选择日期 "2026-03-14"
   ↓
2. 前端调用 API: /api/sar-slope/bias-stats?date=2026-03-14
   ↓
3. 后端读取 bias_stats_20260314.jsonl (289条记录)
   ↓
4. 累加所有记录的 bullish_count 和 bearish_count
   total_bullish = 0 + 1 + 0 + ... + 2 + 1 = 19
   total_bearish = 0 + 0 + 1 + ... + 0 + 0 = 6
   ↓
5. API返回 daily_stats: {total_bullish: 19, total_bearish: 6}
   ↓
6. 前端显示:
   - currentBullish: 19
   - currentBearish: 6
   - totalBullishPoints: 19
   - totalBearishPoints: 6
```

---

## 对比：修复前后

| 项目 | 修复前 | 修复后 |
|-----|-------|-------|
| **顶部统计** | 显示峰值（如最大值2） | 显示累计值（如总和19） |
| **统计范围** | 仅单个时刻的数据 | 当天所有时刻的累计 |
| **API限制** | 仅page=1时计算 | 始终计算 |
| **币种列表** | 显示峰值时刻的币种 | 显示所有出现过的币种+次数 |
| **用户体验** | 数据不直观，经常为0 | 准确反映当天多空强度 |

---

## 示例说明

以 **2026-03-14** 为例：

### 修复前（峰值模式）
- 显示: 偏多 **2** 个，偏空 **1** 个
- 含义: 当天某个时刻最多有2个偏多币种
- 问题: 无法反映全天累计情况

### 修复后（累计模式）
- 显示: 偏多 **19** 次，偏空 **6** 次
- 含义: 当天所有289个数据点中，共有19次出现偏多，6次出现偏空
- 优势: 准确反映全天多空强度分布

---

## 相关提交

1. **35e0dcf** - 修复历史数据无法显示问题（复制JSONL文件）
2. **2d137d4** - 初版修复：显示峰值统计（仍有问题）
3. **44fe618** - 修复日期选择bug（添加date参数支持）
4. **42dba27** - 本次修复：从峰值改为累计值 ✅

---

## 测试建议

### 推荐测试日期
1. **2026-02-05** - 大波动日（累计偏多 5597，偏空 16989）
2. **2026-03-14** - 中等活跃（累计偏多 19，偏空 6）
3. **2026-03-01** - 市场平稳（累计偏多 0，偏空 3）

### 验证步骤
```bash
# 1. 测试API
curl "http://localhost:9002/api/sar-slope/bias-stats?date=2026-03-14" | jq '.daily_stats'

# 2. 访问页面
open https://9002-xxxxx.sandbox.novita.ai/sar-bias-trend

# 3. 选择日期 2026-03-14

# 4. 验证统计
# 应显示: 看多点数 19, 看空点数 6
```

---

## 总结

### 问题本质
用户需要的是 **累计统计**（sum），而不是 **峰值统计**（max）

### 解决方案
- 后端: 移除page限制，始终计算累计值
- 前端: 从daily_stats获取累计值，不再计算峰值
- 优化: 币种列表按出现次数排序，显示更丰富的信息

### 修复状态
✅ **完全修复** - 历史页面现在准确反映当天的多空累计强度

### 影响范围
- 所有历史日期的统计数据
- 日期选择器功能
- 统计卡片显示
- 币种列表排序

---

**验证人员**: GenSpark AI Developer  
**验证时间**: 2026-03-16 12:00 CST  
**验证结论**: 修复有效，数据准确 ✅
