# 横盘监控卡片 - 功能使用指南

## 📋 功能概览

横盘监控卡片现已全面升级，新增三大核心功能：
1. ✅ **可伸缩面板** - 一键收起/展开，节省页面空间
2. ✅ **今日触发记录** - 实时显示当天所有告警触发
3. ✅ **历史数据查询** - 查询任意日期的横盘数据

---

## 🎯 功能 1: 可伸缩面板

### 使用方法
- 点击右上角的 **"收起"/"展开"** 按钮
- 按钮图标会自动切换（↑ ↔ ↓）
- 面板状态会自动保存，刷新页面后保持

### 应用场景
- 页面空间不足时，临时收起面板
- 专注查看其他数据时，减少干扰
- 手机端查看时，优化显示空间

### 技术细节
```javascript
// 状态保存到 localStorage
localStorage.setItem('consolidationPanelCollapsed', 'true/false')

// 平滑动画过渡
transition: max-height 0.3s ease-in-out
```

---

## 📊 功能 2: 今日触发记录

### 显示内容
- **触发次数统计** - 当天连续≥3次的总触发次数
- **详细记录列表**：
  - 币种标识（BTC/ETH 图标）
  - 触发时间（北京时间）
  - 涨跌幅（带颜色编码）
  - 当时价格
  - 连续横盘次数

### 颜色编码
| 元素 | 颜色 | 含义 |
|------|------|------|
| BTC 记录 | 橙色渐变 | 比特币触发 |
| ETH 记录 | 紫色渐变 | 以太坊触发 |
| 正涨跌幅 | 红色 | 价格上涨 |
| 负涨跌幅 | 绿色 | 价格下跌 |

### 数据更新
- 页面加载时自动获取
- 每 **60 秒** 自动刷新
- 点击 **"刷新"** 按钮手动更新

### 示例显示
```
今日触发记录（连续≥3次）        5 次

🟠 BTC - 2026-03-25 14:35:00
   涨跌: +0.032% | 价格: $71,250
   连续次数: 4

🟣 ETH - 2026-03-25 14:20:00
   涨跌: -0.045% | 价格: $2,165
   连续次数: 3
```

### API 调用逻辑
```javascript
// 获取今日 BTC 数据
GET /api/consolidation-monitor/history?symbol=BTC-USDT-SWAP&date=20260325

// 筛选连续≥3次的记录
triggers = records.filter(r => r.consecutive_count >= 3)

// 按时间倒序排列
triggers.sort((a, b) => b.timestamp - a.timestamp)
```

---

## 🔍 功能 3: 历史数据查询

### 查询参数
1. **币种选择**
   - BTC 永续合约
   - ETH 永续合约

2. **日期选择**
   - 日期选择器（默认今天）
   - 格式：YYYY-MM-DD

3. **快捷按钮**
   - **"查询"** - 执行查询
   - **"今日数据"** - 一键查看今天的数据

### 数据表格

#### 表头
| 时间 | 涨跌幅 | 价格 | 横盘状态 | 连续次数 |
|------|--------|------|----------|----------|

#### 记录样式
- **普通记录** - 白色背景
- **触发记录（≥3次）** - 红色左边框 + 浅红背景

#### 连续次数颜色
- **≥3 次** - 🔴 红色粗体大号
- **≥2 次** - 🟠 橙色粗体
- **≥1 次** - 🟡 黄色
- **0 次** - ⚪ 灰色

### 统计信息
查询结果顶部显示：
```
BTC - 2026-03-25 - 共 288 条记录    触发告警: 12 次
```

### 使用步骤

#### 步骤 1：选择币种
```
下拉菜单选择：
┌─────────────────────┐
│ BTC永续合约 ▼      │
│ ETH永续合约        │
└─────────────────────┘
```

#### 步骤 2：选择日期
```
日期选择器：
┌─────────────────────┐
│ 2026-03-25 📅      │
└─────────────────────┘
```

#### 步骤 3：点击查询
```
┌───────┐  ┌───────────┐
│ 🔍 查询 │  │ 📅 今日数据 │
└───────┘  └───────────┘
```

#### 步骤 4：查看结果
表格自动展开，显示查询结果：
- 最多显示 **当天所有记录**
- 表格最大高度 **384px**（约16行）
- 超出部分支持 **垂直滚动**

### 查询示例

#### 示例 1：查看昨天的 BTC 数据
```bash
1. 选择：BTC永续合约
2. 日期：2026-03-24
3. 点击：查询
```

#### 示例 2：快速查看今日 ETH
```bash
1. 选择：ETH永续合约
2. 点击：今日数据
```

#### 示例 3：查看特定日期的触发情况
```bash
1. 选择：BTC永续合约
2. 日期：2026-03-20
3. 点击：查询
4. 查看红色边框的记录（连续≥3次）
```

---

## 🎨 UI/UX 设计亮点

### 1. 视觉层次
```
横盘监控标题
└─ 实时状态卡片（BTC/ETH）
   └─ 今日触发记录（紫色边框）
      └─ 历史数据查询（靛蓝边框）
```

### 2. 颜色方案
- **主色调** - 紫色/靛蓝渐变（横盘监控主题）
- **强调色** - 红色（告警/触发）
- **辅助色** - 橙色（BTC）、紫色（ETH）
- **状态色** - 绿色（上涨）、红色（下跌）

### 3. 交互反馈
- ✅ 按钮悬停 - 颜色加深
- ✅ 表格行悬停 - 背景变灰
- ✅ 加载状态 - 图标旋转动画
- ✅ 触发记录 - 渐变背景 + 阴影效果

### 4. 响应式设计
- 表格支持横向滚动（小屏幕）
- 查询面板网格布局自适应
- 触发记录卡片自动换行

---

## 📡 API 端点

### 1. 实时状态
```http
GET /api/consolidation-monitor/status
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "BTC": {
      "change_percent": 0.00032,
      "change_percent_display": "+0.032%",
      "consecutive_count": 1,
      "datetime": "2026-03-25 14:35:00",
      "is_consolidation": true,
      "price": 71250.5
    },
    "ETH": { ... }
  },
  "update_time": "2026-03-25 14:35:00"
}
```

### 2. 历史数据
```http
GET /api/consolidation-monitor/history?symbol=BTC-USDT-SWAP&date=20260325&limit=100
```

**参数**：
- `symbol` - 币种（BTC-USDT-SWAP / ETH-USDT-SWAP）
- `date` - 日期（YYYYMMDD 格式，默认今天）
- `limit` - 返回记录数（可选，默认全部）

**响应示例**：
```json
{
  "success": true,
  "symbol": "BTC-USDT-SWAP",
  "date": "20260325",
  "count": 5,
  "records": [
    {
      "timestamp": 1774415100000,
      "datetime": "2026-03-25 13:05:00",
      "symbol": "BTC-USDT-SWAP",
      "change_percent": 0.00321,
      "change_percent_display": "+0.321%",
      "price": 71180.6,
      "is_consolidation": false,
      "consecutive_count": 0,
      "recorded_at": "2026-03-25 13:10:33"
    }
  ]
}
```

---

## 💡 使用技巧

### 技巧 1：监控变盘信号
定期查看今日触发记录：
- 触发次数突然增多 → 可能即将变盘
- 连续多次触发 → 市场波动性降低

### 技巧 2：分析历史模式
查询历史数据，寻找规律：
1. 查看过去一周的每日触发次数
2. 统计触发最多的时间段（如早盘/午盘/晚盘）
3. 对比 BTC vs ETH 的横盘频率

### 技巧 3：组合其他指标
横盘监控 + 成交量监控 + SAR 偏向：
- 横盘 + 低成交量 → 等待突破方向
- 横盘 + 高成交量 → 可能酝酿大行情
- 横盘结束后 SAR 翻转 → 趋势可能改变

### 技巧 4：设置观察时段
在特定时间段重点关注：
- 美股开盘前后（21:30）
- 亚洲交易时段（09:00-15:00）
- 周末市场波动降低时段

---

## 🔧 技术实现

### 前端架构
```javascript
// 页面加载时初始化
window.addEventListener('DOMContentLoaded', () => {
  loadConsolidationData();        // 加载实时状态
  loadTodayTriggers();            // 加载今日触发
  initConsolidationDatePicker();  // 初始化日期选择器
  
  // 自动刷新
  setInterval(loadConsolidationData, 60000);
  setInterval(loadTodayTriggers, 60000);
});
```

### 数据流程
```
OKX API (5分钟K线)
    ↓
consolidation_monitor.py (后台监控)
    ↓
JSONL 文件（按日期存储）
    ↓
Flask API (/api/consolidation-monitor/*)
    ↓
前端 JavaScript (fetch)
    ↓
DOM 更新（实时显示）
```

### 本地存储
```javascript
// 保存面板状态
localStorage.setItem('consolidationPanelCollapsed', 'true/false')

// 读取面板状态
const collapsed = localStorage.getItem('consolidationPanelCollapsed') === 'true'
```

---

## 📊 数据统计

### 实时监控
- **监控频率** - 每 60 秒检查一次
- **数据来源** - OKX 永续合约 5 分钟 K 线
- **判断标准** - |涨跌幅| ≤ 0.05%
- **告警条件** - 连续 ≥ 3 次

### 数据存储
- **存储格式** - JSONL（每行一个 JSON 对象）
- **文件命名** - `consolidation_{SYMBOL}_{YYYYMMDD}.jsonl`
- **存储位置** - `/home/user/webapp/data/consolidation_monitor/`
- **保留时间** - 永久保存（需手动清理）

### 查询性能
- **单日数据量** - 约 288 条记录（24小时 × 12个5分钟）
- **API 响应时间** - < 200ms
- **前端渲染** - 支持数百条记录流畅滚动

---

## 🚀 快速上手

### 1 分钟快速体验

1. **打开页面**
   - 访问：https://9002-iwyspq7c2ufr5cnosf8lb-2e77fc33.sandbox.novita.ai/coin-change-tracker
   - 找到 **"横盘监控"** 卡片

2. **查看实时状态**
   - BTC/ETH 当前涨跌幅
   - 连续横盘次数

3. **查看今日触发**
   - 向下滚动到 **"今日触发记录"**
   - 查看所有触发详情

4. **查询历史数据**
   - 向下滚动到 **"历史数据查询"**
   - 点击 **"今日数据"** 按钮
   - 查看完整数据表格

5. **收起面板**
   - 点击右上角 **"收起"** 按钮
   - 页面空间立即释放

---

## ❓ 常见问题

### Q1：为什么今日触发记录是空的？
**A**: 当天可能还没有出现连续≥3次的横盘情况。横盘触发需要满足：
- 5分钟涨跌幅绝对值 ≤ 0.05%
- 连续出现 3 次及以上

### Q2：历史数据查询显示"暂无数据"？
**A**: 可能原因：
1. 所选日期没有数据（系统未运行）
2. 日期格式错误
3. 文件尚未生成（当天首次运行需等待）

### Q3：如何知道是否发送了 Telegram 告警？
**A**: 
1. 查看 PM2 日志：`pm2 logs consolidation-monitor`
2. 检查 Telegram 聊天记录
3. 查看今日触发记录（有触发 = 已发告警）

### Q4：可以修改横盘阈值吗（0.05%）？
**A**: 可以，编辑配置文件：
```bash
# 编辑配置
vim data/consolidation_monitor/consolidation_config.json

# 修改阈值（示例：改为 0.03%）
"threshold": 0.0003

# 重启监控
pm2 restart consolidation-monitor
```

### Q5：如何导出历史数据？
**A**: 直接访问 JSONL 文件：
```bash
# 查看文件
cat data/consolidation_monitor/consolidation_BTC_USDT_SWAP_20260325.jsonl

# 导出为 CSV（使用 Python）
python3 << EOF
import json
import csv

with open('data/consolidation_monitor/consolidation_BTC_USDT_SWAP_20260325.jsonl', 'r') as f:
    records = [json.loads(line) for line in f]

with open('export.csv', 'w', newline='') as f:
    if records:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
EOF
```

---

## 📈 未来规划

### 计划中的功能
- [ ] 统计图表（横盘频率趋势）
- [ ] 自定义告警阈值（前端配置）
- [ ] 多时间周期支持（1分钟、15分钟）
- [ ] 导出功能（CSV/Excel）
- [ ] 横盘时长统计
- [ ] 触发后价格走势分析

### 欢迎反馈
如有功能建议或 Bug 反馈，请提 Issue！

---

## 📚 相关文档

- [API 查询示例](API_QUERY_EXAMPLES.md)
- [数据存储说明](README.md)
- [横盘监控配置](consolidation_config.json)
- [后端实现代码](../../consolidation_monitor.py)

---

**最后更新**: 2026-03-25  
**版本**: v1.1.0  
**作者**: GenSpark AI Developer
