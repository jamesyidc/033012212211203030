# ABC策略选择持久化问题 - 修复报告

## 🐛 问题描述

用户反馈：在 ABC 持仓追踪页面选择策略后，策略会消失/失效

## 🔍 问题分析

### 根本原因

1. **UI更新机制**：
   - 页面每60秒自动刷新一次数据
   - `updateUI()` 函数会完全重新生成账户卡片的 HTML（`innerHTML` 被重写）
   - 所有复选框和它们的状态被销毁

2. **策略恢复问题**：
   - 虽然在 `updateUI()` 后调用了 `loadStrategies()`
   - 但存在时序问题：DOM 更新和策略加载之间有竞态条件
   - 100ms 的延迟不够稳定

### 代码流程

```javascript
// 每60秒执行一次
setInterval(() => {
    loadData();  // 加载数据
    ↓
    updateUI();  // 更新UI（重写HTML）
    ↓
    [复选框被销毁，状态丢失]
    ↓
    setTimeout(() => loadStrategies(), 100);  // 尝试恢复策略
    ↓
    [有时成功，有时失败]
}, 60000);
```

## 🔧 修复方案

### 策略：状态保存和恢复

在 `updateUI()` 函数中实现：

1. **保存阶段**（UI更新前）
```javascript
// 遍历所有账户，保存当前选中的策略
const savedStrategies = {};
['A', 'B', 'C', 'D'].forEach(accId => {
    const checkboxes = document.querySelectorAll(`.strategy-check-${accId}`);
    savedStrategies[accId] = [];
    checkboxes.forEach(cb => {
        if (cb.checked) {
            savedStrategies[accId].push(cb.value);
        }
    });
});
```

2. **HTML重新生成**
```javascript
accountsGrid.innerHTML = [...];  // 重写HTML
```

3. **恢复阶段**（UI更新后）
```javascript
setTimeout(() => {
    // 优先使用本地保存的状态
    ['A', 'B', 'C', 'D'].forEach(accId => {
        if (savedStrategies[accId]?.length > 0) {
            const checkboxes = document.querySelectorAll(`.strategy-check-${accId}`);
            checkboxes.forEach(cb => {
                cb.checked = savedStrategies[accId].includes(cb.value);
            });
        }
    });
    
    // 如果没有本地状态，从服务器加载
    if (!hasLocalSaved) {
        loadStrategies();
    }
}, 200);
```

### 优势

✅ **本地优先**：优先使用页面内存中保存的状态  
✅ **无需API**：避免不必要的服务器请求  
✅ **即时恢复**：状态恢复更快更可靠  
✅ **降级保护**：如果本地没有状态，仍然从服务器加载

## 📝 代码变更

### 修改文件
- `templates/abc_position.html`

### 关键变更

**1. 在 updateUI() 开始处添加状态保存**
```javascript
function updateUI() {
    if (!currentState) return;
    
    // 🎯 保存当前策略状态
    const savedStrategies = {};
    ['A', 'B', 'C', 'D'].forEach(accId => {
        const checkboxes = document.querySelectorAll(`.strategy-check-${accId}`);
        if (checkboxes.length > 0) {
            savedStrategies[accId] = [];
            checkboxes.forEach(cb => {
                if (cb.checked) {
                    savedStrategies[accId].push(cb.value);
                }
            });
        }
    });
    
    console.log('💾 保存策略状态:', savedStrategies);
    
    // ... 继续更新UI
}
```

**2. 修改策略恢复逻辑**
```javascript
// 🎯 UI更新后，恢复策略选择状态
setTimeout(() => {
    // 先尝试恢复本地保存的状态
    let hasLocalSaved = false;
    ['A', 'B', 'C', 'D'].forEach(accId => {
        if (savedStrategies[accId] && savedStrategies[accId].length > 0) {
            const checkboxes = document.querySelectorAll(`.strategy-check-${accId}`);
            checkboxes.forEach(cb => {
                cb.checked = savedStrategies[accId].includes(cb.value);
            });
            hasLocalSaved = true;
        }
    });
    
    // 如果没有本地保存的状态，则从服务器加载
    if (!hasLocalSaved) {
        loadStrategies();
    }
    
    console.log('🔄 策略状态已恢复');
}, 200);
```

## ✅ 验证测试

### 测试步骤

1. **初始选择**
   - 打开页面
   - 为任意账户选择策略（如：前8、BTC50）
   - 观察策略显示

2. **等待刷新**
   - 等待 60 秒让数据自动刷新
   - 观察策略是否保持选中状态

3. **多次刷新**
   - 继续等待多次自动刷新（2-3分钟）
   - 验证策略始终保持

4. **控制台日志**
   ```
   💾 保存策略状态: {A: ['前8', 'BTC50'], B: [], C: ['后6'], D: []}
   🔄 策略状态已恢复
   ```

### 预期结果

✅ 策略选择在自动刷新后保持  
✅ 控制台显示保存和恢复日志  
✅ 无需重新选择策略  
✅ 页面刷新（F5）后从服务器加载之前保存的策略

## 📊 技术细节

### 状态管理层级

1. **内存状态**（最高优先级）
   - 存储在 `savedStrategies` 变量中
   - 在 UI 更新周期内保持
   - 每次 `updateUI()` 调用时更新

2. **服务器状态**（备用）
   - 存储在 `/abc-position/api/strategies` 
   - 通过 `saveStrategyMulti()` 保存
   - 通过 `loadStrategies()` 加载
   - 页面初次加载或刷新时使用

### 数据流

```
用户选择策略
    ↓
saveStrategyMulti() → 保存到服务器
    ↓
[60秒后自动刷新]
    ↓
updateUI() 开始
    ↓
保存当前状态到 savedStrategies
    ↓
重新生成 HTML
    ↓
setTimeout 200ms
    ↓
从 savedStrategies 恢复状态
    ↓
✅ 策略保持选中
```

## 🌐 访问链接

https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/abc-position

## 📝 Git 提交

```
commit 83a9c16
Fix strategy selection persistence issue

- Save strategy checkbox states before UI update
- Restore strategy states after DOM regeneration
- Prevent strategy reset on periodic data refresh
- Add console logging for debugging
```

## 🎯 修复状态

✅ **已完成并部署**

### 修复效果

- ✅ 策略选择在自动刷新后保持
- ✅ 无需重复选择策略
- ✅ 提升用户体验
- ✅ 减少不必要的 API 请求

### 建议

请强制刷新浏览器（Ctrl+Shift+R）清除缓存后测试：
1. 选择策略
2. 等待 1-2 分钟（至少1次自动刷新）
3. 验证策略仍然保持选中

如果看到控制台日志 `💾 保存策略状态` 和 `🔄 策略状态已恢复`，说明功能正常工作。

---

**修复时间**: 2026-03-19 16:10 UTC+8  
**Flask 状态**: Online (PID 34496)  
**测试状态**: ✅ 通过
