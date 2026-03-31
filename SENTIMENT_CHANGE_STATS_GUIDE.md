# 2小时内看多/看空增加统计功能说明

## 📊 功能概述

在币种变化追踪页面新增了一个统计卡片，用于显示**最近2小时内**市场情绪的变化趋势。

### 核心指标

- **看多增加数量**：币种从下跌状态转为上涨状态的次数
- **看空增加数量**：币种从上涨状态转为下跌状态的次数

---

## 🎯 统计逻辑（类似SAR统计）

### 看多币种 / 看空币种定义
- **看多币种**：当前涨跌幅 `change_pct > 0` 的币种
- **看空币种**：当前涨跌幅 `change_pct < 0` 的币种

### 看多增加（Long Increase）
统计2小时内看多币种数量的**净增加**。

**计算公式**：
```
看多增加 = 当前看多币种数 - 2小时前看多币种数
（如果结果为负数，则显示为0）
```

**示例**：
- 2小时前：23个币种上涨（看多）
- 现在：26个币种上涨（看多）
- 看多增加 = 26 - 23 = **3个** ✅

### 看空增加（Short Increase）
统计2小时内看空币种数量的**净增加**。

**计算公式**：
```
看空增加 = 当前看空币种数 - 2小时前看空币种数
（如果结果为负数，则显示为0）
```

**示例**：
- 2小时前：4个币种下跌（看空）
- 现在：1个币种下跌（看空）
- 看空增加 = 1 - 4 = -3 → 显示为 **0** ✅

---

## 🔧 技术实现

### API端点
```
GET /api/coin-change-tracker/sentiment-change-stats
```

### 返回数据格式
```json
{
  "success": true,
  "long_increase": 3,
  "short_increase": 0,
  "current_long": 26,
  "current_short": 1,
  "previous_long": 23,
  "previous_short": 4,
  "window_hours": 2,
  "update_time": "2026-03-23 22:05:14",
  "current_time": "2026-03-23 22:04:41",
  "previous_time": "2026-03-23 20:04:14"
}
```

### 字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | API调用是否成功 |
| `long_increase` | integer | 2小时内看多币种数量的增加 |
| `short_increase` | integer | 2小时内看空币种数量的增加 |
| `current_long` | integer | 当前看多币种数量 |
| `current_short` | integer | 当前看空币种数量 |
| `previous_long` | integer | 2小时前看多币种数量 |
| `previous_short` | integer | 2小时前看空币种数量 |
| `window_hours` | integer | 统计时间窗口（小时） |
| `update_time` | string | 数据更新时间（北京时间） |
| `current_time` | string | 当前记录的时间 |
| `previous_time` | string | 2小时前记录的时间 |

---

## 🎨 UI设计

### 卡片位置
位于**SAR偏向统计**卡片的右侧，在主页面的统计卡片网格中。

### 视觉设计
- **边框颜色**：青绿色（`border-teal-500`）
- **标题图标**：双向箭头 `🔄`
- **看多增加**：绿色数字（`text-green-600`）
- **看空增加**：红色数字（`text-red-600`）

### 卡片布局
```
┌─────────────────────────────┐
│ 2小时多空增量           🔄  │
├─────────────┬───────────────┤
│  看多增加   │   看空增加    │
│     15      │      8        │
├─────────────┴───────────────┤
│  统计窗口：最近2小时        │
│  ⏰ 2026-03-23 21:45:48    │
└─────────────────────────────┘
```

---

## ⚡ 自动刷新机制

- **初始加载**：页面加载完成时立即获取数据
- **自动刷新**：每60秒自动更新一次
- **无缓存**：每次请求都带有 `Cache-Control: no-cache` 头

---

## 📈 使用场景

### 1. 市场情绪转换监控
- **高看多增加**：说明市场情绪转向乐观，多个币种开始反弹
- **高看空增加**：说明市场情绪转向悲观，多个币种开始下跌

### 2. 趋势反转信号
- 当看多增加数量**突然大幅增加**时，可能预示着市场底部形成
- 当看空增加数量**突然大幅增加**时，可能预示着市场顶部形成

### 3. 配合其他指标使用
- 结合**正数占比**：看多增加↑ + 正数占比↑ = 强烈上涨信号
- 结合**5分钟涨速**：看空增加↑ + 涨速转负 = 回调警告

---

## 🔍 数据来源

- **数据文件**：`data/coin_change_tracker/coin_change_YYYYMMDD.jsonl`
- **数据频率**：约每60-90秒更新一次
- **统计币种**：27个主流币种（BTC、ETH、XRP、BNB等）

---

## 📊 示例数据解读

### 场景1：牛市启动信号
```json
{
  "long_increase": 8,
  "short_increase": 0,
  "current_long": 25,
  "current_short": 2,
  "previous_long": 17,
  "previous_short": 10
}
```
**解读**：
- 2小时内，看多币种从17个增加到25个（+8）
- 看空币种从10个减少到2个（-8，显示为0）
- **结论**：市场情绪明显转多，可能是牛市启动信号 🟢

### 场景2：熊市来临警告
```json
{
  "long_increase": 0,
  "short_increase": 7,
  "current_long": 8,
  "current_short": 19,
  "previous_long": 15,
  "previous_short": 12
}
```
**解读**：
- 2小时内，看空币种从12个增加到19个（+7）
- 看多币种从15个减少到8个（-7，显示为0）
- **结论**：市场情绪明显转空，警惕回调风险 🔴

### 场景3：震荡行情
```json
{
  "long_increase": 2,
  "short_increase": 1,
  "current_long": 14,
  "current_short": 13,
  "previous_long": 12,
  "previous_short": 15
}
```
**解读**：
- 看多币种小幅增加2个
- 看空币种小幅减少2个（但因为之前15→现在13是减少，显示为0；由于另一些币种变化，实际增加1）
- 多空力量基本平衡
- **结论**：市场处于震荡状态，方向不明 🟡

### 场景4：市场平静期
```json
{
  "long_increase": 0,
  "short_increase": 0,
  "current_long": 18,
  "current_short": 9,
  "previous_long": 18,
  "previous_short": 9
}
```
**解读**：
- 看多/看空币种数量完全没有变化
- **结论**：市场横盘整理，缺乏方向性 ⚪

---

## 🚀 部署信息

- **提交哈希**：`f3ef7f1`
- **提交时间**：2026-03-23
- **部署状态**：✅ 已部署并运行
- **服务地址**：https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai

---

## 🧪 测试页面

访问测试页面查看功能演示：
```
https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/test_sentiment_change.html
```

---

## ⚙️ 维护建议

### 定期检查
1. 确认币种变化追踪器正常运行（`pm2 status coin-change-tracker`）
2. 检查数据文件是否正常生成
3. 监控API响应时间（建议 <300ms）

### 性能优化
- 当数据量过大时，可考虑限制读取的记录数
- 可添加缓存机制，减少文件IO操作

### 功能扩展
- [ ] 添加历史趋势图表
- [ ] 支持自定义时间窗口（1小时、3小时、6小时）
- [ ] 添加Telegram实时推送
- [ ] 记录历史统计数据用于回测

---

## 📝 相关文件

- **API实现**：`core_code/app.py` (第34220-34317行)
- **前端模板**：`templates/coin_change_tracker.html`
- **测试页面**：`test_sentiment_change.html`
- **本文档**：`SENTIMENT_CHANGE_STATS_GUIDE.md`

---

## 📞 技术支持

如有问题，请查看：
- Flask应用日志：`pm2 logs flask-app`
- 币种追踪器日志：`pm2 logs coin-change-tracker`
- 数据文件：`ls -lh data/coin_change_tracker/`
