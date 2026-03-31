# ABC开仓系统策略保存功能

## 功能时间
2026-03-17 03:35 CST

## 问题描述
用户反馈：ABC开仓系统的策略无法保存，报错 `'dict' object has no attribute 'append'`。同时需要：
1. 添加做多/做空方向选择
2. 策略保存到对应日期的对应账户的jsonl文件

## 根本原因
1. **数据结构不匹配**：旧的策略文件是dict格式（按账户分组），但代码期望list格式，导致 `.append()` 方法失败
2. **缺少方向字段**：没有做多/做空的选择
3. **文件格式不合理**：所有策略保存到同一个JSON文件，不便于按日期和账户管理

## 新功能设计

### 1. 做多/做空方向选择

#### 前端UI
每个账户卡片添加方向选择按钮：
```html
<!-- 做多/做空选择 -->
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
    <div style="font-size: 0.85em; color: #667eea; font-weight: bold;">📊 交易方向</div>
    <div style="display: flex; gap: 5px;">
        <button onclick="setDirection('B', 'long')" id="dir_long_B" class="direction-btn direction-active">
            做多 ↗
        </button>
        <button onclick="setDirection('B', 'short')" id="dir_short_B" class="direction-btn">
            做空 ↘
        </button>
    </div>
</div>
```

#### JavaScript逻辑
```javascript
// 存储每个账户的当前方向（默认做多）
const accountDirections = {
    'A': 'long',
    'B': 'long',
    'C': 'long',
    'D': 'long'
};

// 设置交易方向
function setDirection(accId, direction) {
    accountDirections[accId] = direction;
    // 更新按钮样式（选中的按钮高亮）
    // ...
}
```

### 2. 策略保存到jsonl文件

#### 文件路径规则
```
data/abc_position/strategies/abc_strategy_{账户}_{日期}.jsonl
```

示例：
- `abc_strategy_A_20260317.jsonl` - 主账户2026-03-17的策略
- `abc_strategy_B_20260317.jsonl` - POIT账户2026-03-17的策略
- `abc_strategy_C_20260317.jsonl` - fangfang12账户2026-03-17的策略
- `abc_strategy_D_20260317.jsonl` - dadanini账户2026-03-17的策略

#### 文件格式（JSONL）
每行一个JSON记录：
```json
{"timestamp": "2026-03-17 03:29:48", "account": "B", "direction": "long", "strategy": ["前8", "BTC50"], "mode": "multi"}
{"timestamp": "2026-03-17 03:30:06", "account": "A", "direction": "short", "strategy": "后8", "mode": "single"}
```

### 3. API端点改进

#### POST /abc-position/api/strategies
**保存策略到jsonl文件**

请求参数：
```json
{
  "account": "B",
  "direction": "long",      // 'long' 或 'short'
  "strategy": ["前8", "BTC50"],  // 单选为字符串，多选为数组
  "mode": "multi"           // 'single' 或 'multi'
}
```

响应：
```json
{
  "success": true,
  "message": "策略已保存到 abc_strategy_B_20260317.jsonl",
  "record": {
    "timestamp": "2026-03-17 03:29:48",
    "account": "B",
    "direction": "long",
    "strategy": ["前8", "BTC50"],
    "mode": "multi"
  }
}
```

#### GET /abc-position/api/strategies
**读取策略记录**

查询参数：
- `account`（可选）：指定账户（A/B/C/D）
- `date`（可选）：指定日期（YYYYMMDD格式，默认今天）

示例：
```bash
# 获取POIT账户今天的策略
curl "http://localhost:9002/abc-position/api/strategies?account=B"

# 获取所有账户今天的策略
curl "http://localhost:9002/abc-position/api/strategies"

# 获取主账户2026-03-16的策略
curl "http://localhost:9002/abc-position/api/strategies?account=A&date=20260316"
```

响应（单账户）：
```json
{
  "success": true,
  "account": "B",
  "date": "20260317",
  "data": [
    {
      "timestamp": "2026-03-17 03:29:48",
      "account": "B",
      "direction": "long",
      "strategy": ["前8", "BTC50"],
      "mode": "multi"
    }
  ]
}
```

响应（所有账户）：
```json
{
  "success": true,
  "date": "20260317",
  "data": {
    "A": [...],
    "B": [...],
    "C": [...],
    "D": [...]
  }
}
```

#### DELETE /abc-position/api/strategies
**删除策略文件**

请求参数：
```json
{
  "account": "B",
  "date": "20260317"  // 可选，默认今天
}
```

响应：
```json
{
  "success": true,
  "message": "账户B的策略已删除"
}
```

### 4. 前端改进

#### 保存函数修改
```javascript
// 保存单选策略（包含方向）
async function saveStrategySingle(accId) {
    const strategy = document.getElementById(`single_mode_${accId}`).value;
    const direction = accountDirections[accId] || 'long';
    
    await fetch('/abc-position/api/strategies', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            account: accId,
            direction: direction,  // 添加方向
            strategy: strategy,
            mode: 'single'
        })
    });
}

// 保存多选策略（包含方向）
async function saveStrategyMulti(accId) {
    const selectedStrategies = [...];  // 获取选中的策略
    const direction = accountDirections[accId] || 'long';
    
    await fetch('/abc-position/api/strategies', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            account: accId,
            direction: direction,  // 添加方向
            strategy: selectedStrategies,
            mode: 'multi'
        })
    });
}
```

#### 提示信息改进
保存成功后显示方向信息：
- 单选：`POIT: 做多 前8`
- 多选：`POIT: 做空 前8, BTC50`

## 验证测试

### 测试1：保存做多策略（多选）
```bash
curl -X POST "http://localhost:9002/abc-position/api/strategies" \
  -H "Content-Type: application/json" \
  -d '{
    "account": "B",
    "direction": "long",
    "strategy": ["前8", "BTC50"],
    "mode": "multi"
  }'
```

结果：✅ 成功保存到 `data/abc_position/strategies/abc_strategy_B_20260317.jsonl`

文件内容：
```json
{"timestamp": "2026-03-17 03:29:48", "account": "B", "direction": "long", "strategy": ["前8", "BTC50"], "mode": "multi"}
```

### 测试2：保存做空策略（单选）
```bash
curl -X POST "http://localhost:9002/abc-position/api/strategies" \
  -H "Content-Type: application/json" \
  -d '{
    "account": "A",
    "direction": "short",
    "strategy": "后8",
    "mode": "single"
  }'
```

结果：✅ 成功保存到 `data/abc_position/strategies/abc_strategy_A_20260317.jsonl`

文件内容：
```json
{"timestamp": "2026-03-17 03:30:06", "account": "A", "direction": "short", "strategy": "后8", "mode": "single"}
```

### 测试3：读取策略记录
```bash
# 读取POIT账户的策略
curl "http://localhost:9002/abc-position/api/strategies?account=B"
```

返回：
```json
{
  "success": true,
  "account": "B",
  "date": "20260317",
  "data": [
    {
      "timestamp": "2026-03-17 03:29:48",
      "account": "B",
      "direction": "long",
      "strategy": ["前8", "BTC50"],
      "mode": "multi"
    }
  ]
}
```

## 功能特点

### 1. 按日期分离
- 每天的策略独立保存
- 方便历史回溯和分析
- 不会混淆不同日期的策略

### 2. 按账户分离
- 每个账户独立文件
- 避免不同账户策略互相干扰
- 便于单独查询和管理

### 3. JSONL格式
- 追加写入，不需要读取整个文件
- 每行独立的JSON记录
- 便于流式处理和增量分析

### 4. 完整记录
每条策略记录包含：
- `timestamp`: 保存时间（北京时间）
- `account`: 账户ID（A/B/C/D）
- `direction`: 交易方向（long/short）
- `strategy`: 策略内容（单选为字符串，多选为数组）
- `mode`: 选择模式（single/multi）

### 5. 前端体验
- 做多/做空按钮清晰可见
- 选中的方向高亮显示
- 保存成功后提示包含方向信息
- 操作即时响应

## 使用示例

### 场景1：POIT账户做多前8和BTC50
1. 点击POIT卡片上的"做多 ↗"按钮
2. 勾选"前8"和"BTC50"策略
3. 自动保存
4. 提示：`POIT: 做多 前8, BTC50`

### 场景2：主账户做空后8
1. 点击主账户卡片上的"做空 ↘"按钮
2. 切换到单选模式
3. 选择"后8"
4. 自动保存
5. 提示：`主账户: 做空 后8`

### 场景3：查询历史策略
```bash
# 查询昨天的策略
curl "http://localhost:9002/abc-position/api/strategies?account=B&date=20260316"
```

## 相关文件

### 代码文件
- `core_code/app.py` - 后端API（POST/GET/DELETE）
- `templates/abc_position.html` - 前端UI和JavaScript

### 数据文件
- `data/abc_position/strategies/abc_strategy_A_20260317.jsonl`
- `data/abc_position/strategies/abc_strategy_B_20260317.jsonl`
- `data/abc_position/strategies/abc_strategy_C_20260317.jsonl`
- `data/abc_position/strategies/abc_strategy_D_20260317.jsonl`

## Git提交
- `9a5ed12` - 添加ABC开仓系统策略保存功能（支持做多/做空）

## 完成时间
2026-03-17 03:40 CST

---

**✅ 策略保存功能已完成，支持做多/做空方向，数据按账户和日期保存到独立的jsonl文件。**
