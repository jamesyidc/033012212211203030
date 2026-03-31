# ABC Position 零值数据问题修复

## 🐛 问题
页面显示"正在加载数据..."，图表无法显示有效数据。

## 🔍 根本原因
数据文件 `abc_position_20260319.jsonl` 包含：
- **前200行**: 零值数据（00:00-03:11），所有账户 `pnl_pct=0, total_cost=0, position_count=0`
- **后154行**: 有效数据（03:11-03:39），实际的持仓和盈亏数据

API 返回所有数据后，图表显示包含大量零值数据，导致有效数据被压缩在很小的区域，用户看不到。

## ✅ 解决方案
在前端过滤零值数据点，只显示至少有一个账户有数据的记录。

### 修改代码
```javascript
// templates/abc_position.html (第 4479-4491 行)

// ❌ 修复前
if (data.success) {
    historyData = data.data;
    
    if (historyData.length === 0) {
        document.getElementById('chartTimeRange').textContent = `📅 ${dateInput.value} - 暂无数据`;
    } else {
        // ...
    }
}

// ✅ 修复后
if (data.success) {
    // 过滤掉所有账户都是零值的数据点
    const rawData = data.data;
    historyData = rawData.filter(record => {
        // 检查是否至少有一个账户有数据
        return Object.values(record.accounts).some(acc => 
            acc.pnl_pct !== 0 || acc.total_cost !== 0 || acc.position_count !== 0
        );
    });
    
    console.log(`📊 原始数据: ${rawData.length} 条, 过滤后: ${historyData.length} 条`);
    
    if (historyData.length === 0) {
        document.getElementById('chartTimeRange').textContent = `📅 ${dateInput.value} - 暂无数据`;
    } else {
        // ...
    }
}
```

## 📊 修复效果
- **修复前**: 354条数据，其中200条零值，图表显示压缩
- **修复后**: 154条有效数据，图表清晰显示盈亏曲线
- **控制台输出**: `📊 原始数据: 354 条, 过滤后: 154 条`

## 📝 数据示例
### 零值数据 (被过滤)
```json
{
  "timestamp": "2026-03-19T00:00:08.051280+08:00",
  "accounts": {
    "A": {"pnl_pct": 0, "total_cost": 0, "position_count": 0},
    "B": {"pnl_pct": 0, "total_cost": 0, "position_count": 0}
  }
}
```

### 有效数据 (保留)
```json
{
  "timestamp": "2026-03-19T03:39:31.611793+08:00",
  "accounts": {
    "A": {"pnl_pct": 3.69, "total_cost": 33.37902, "position_count": 8},
    "B": {"pnl_pct": 3.06, "total_cost": 22.701327, "position_count": 8}
  }
}
```

## 🚀 部署
```bash
cd /home/user/webapp
pm2 restart flask-app
```

## 📅 修复时间
- **问题发现**: 2026-03-19 03:42 Beijing
- **修复完成**: 2026-03-19 03:45 Beijing

## 🔗 Git提交
- Commit: `a7663cf`
- Message: "Filter zero-value data points to show meaningful chart data"

## 🎯 验证
刷新页面后：
1. ✅ 打开浏览器开发者工具 Console
2. ✅ 查看日志: `📊 原始数据: 354 条, 过滤后: 154 条`
3. ✅ 图表显示完整的盈亏曲线
4. ✅ 数据点清晰可见

---
**状态**: ✅ 已修复
**影响**: 所有用户
**优先级**: 高
