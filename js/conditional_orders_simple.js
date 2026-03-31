/**
 * 27币涨跌幅条件单管理 - 简化版
 * 固定两个条件单：做空和做多
 */

let shortOrderData = null;
let longOrderData = null;

// 加载条件单数据
async function loadConditionalOrders() {
    const accountId = getCurrentAccountId();
    if (!accountId) {
        console.log('❌ 未选择账户');
        return;
    }
    
    try {
        console.log('📊 加载条件单数据...');
        const response = await fetch(`/api/okx-trading/coin-change-conditional-orders/${accountId}`);
        const data = await response.json();
        
        if (data.success) {
            // 分离做空和做多条件单
            shortOrderData = data.orders.find(o => o.order_type === 'open_short');
            longOrderData = data.orders.find(o => o.order_type === 'open_long');
            
            // 更新UI
            updateShortOrderUI();
            updateLongOrderUI();
            
            console.log('✅ 条件单数据已加载');
        } else {
            console.error('❌ 加载失败:', data.message);
        }
    } catch (error) {
        console.error('❌ 加载条件单失败:', error);
    }
}

// 更新做空条件单UI
function updateShortOrderUI() {
    if (shortOrderData) {
        // 设置启用状态
        document.getElementById('shortOrderEnabled').checked = shortOrderData.enabled;
        
        // 设置触发值
        document.getElementById('shortTriggerValue').value = shortOrderData.trigger_value || 50;
        
        // 设置目标策略
        document.getElementById('shortTargetStrategy').value = shortOrderData.target_strategy_code || '';
        
        // 更新状态徽章
        const statusBadge = document.getElementById('shortOrderStatusBadge');
        if (shortOrderData.enabled) {
            statusBadge.textContent = '✅ 已启用';
            statusBadge.style.background = '#10b981';
        } else {
            statusBadge.textContent = '⚪ 未启用';
            statusBadge.style.background = '#9ca3af';
        }
        
        // 更新触发权限显示
        updateShortTriggerStatus();
    } else {
        // 默认值
        document.getElementById('shortOrderEnabled').checked = false;
        document.getElementById('shortTriggerValue').value = 50;
        document.getElementById('shortTargetStrategy').value = '';
        document.getElementById('shortOrderStatusBadge').textContent = '⚪ 未启用';
        document.getElementById('shortOrderStatusBadge').style.background = '#9ca3af';
    }
}

// 更新做多条件单UI
function updateLongOrderUI() {
    if (longOrderData) {
        // 设置启用状态
        document.getElementById('longOrderEnabled').checked = longOrderData.enabled;
        
        // 设置触发值
        document.getElementById('longTriggerValue').value = longOrderData.trigger_value || -30;
        
        // 设置目标策略
        document.getElementById('longTargetStrategy').value = longOrderData.target_strategy_code || '';
        
        // 更新状态徽章
        const statusBadge = document.getElementById('longOrderStatusBadge');
        if (longOrderData.enabled) {
            statusBadge.textContent = '✅ 已启用';
            statusBadge.style.background = '#10b981';
        } else {
            statusBadge.textContent = '⚪ 未启用';
            statusBadge.style.background = '#9ca3af';
        }
        
        // 更新触发权限显示
        updateLongTriggerStatus();
    } else {
        // 默认值
        document.getElementById('longOrderEnabled').checked = false;
        document.getElementById('longTriggerValue').value = -30;
        document.getElementById('longTargetStrategy').value = '';
        document.getElementById('longOrderStatusBadge').textContent = '⚪ 未启用';
        document.getElementById('longOrderStatusBadge').style.background = '#9ca3af';
    }
}

// 更新做空触发状态
function updateShortTriggerStatus() {
    const permissionDiv = document.getElementById('shortTriggerPermission');
    const triggeredDiv = document.getElementById('shortTriggeredInfo');
    const timeSpan = document.getElementById('shortLastTriggeredTime');
    
    if (!shortOrderData) {
        permissionDiv.style.display = 'none';
        triggeredDiv.style.display = 'none';
        return;
    }
    
    if (shortOrderData.allow_trigger) {
        permissionDiv.style.display = 'block';
        triggeredDiv.style.display = 'none';
    } else {
        permissionDiv.style.display = 'none';
        triggeredDiv.style.display = 'block';
        if (shortOrderData.last_triggered_at) {
            timeSpan.textContent = `最后触发: ${shortOrderData.last_triggered_at}`;
        }
    }
}

// 更新做多触发状态
function updateLongTriggerStatus() {
    const permissionDiv = document.getElementById('longTriggerPermission');
    const triggeredDiv = document.getElementById('longTriggeredInfo');
    const timeSpan = document.getElementById('longLastTriggeredTime');
    
    if (!longOrderData) {
        permissionDiv.style.display = 'none';
        triggeredDiv.style.display = 'none';
        return;
    }
    
    if (longOrderData.allow_trigger) {
        permissionDiv.style.display = 'block';
        triggeredDiv.style.display = 'none';
    } else {
        permissionDiv.style.display = 'none';
        triggeredDiv.style.display = 'block';
        if (longOrderData.last_triggered_at) {
            timeSpan.textContent = `最后触发: ${longOrderData.last_triggered_at}`;
        }
    }
}

// 切换做空条件单启用状态
async function toggleShortOrder(enabled) {
    await saveShortOrderSettings();
}

// 切换做多条件单启用状态
async function toggleLongOrder(enabled) {
    await saveLongOrderSettings();
}

// 保存做空条件单设置
async function saveShortOrderSettings() {
    const accountId = getCurrentAccountId();
    if (!accountId) {
        alert('请先选择账户');
        return;
    }
    
    const enabled = document.getElementById('shortOrderEnabled').checked;
    const triggerValue = parseFloat(document.getElementById('shortTriggerValue').value);
    const targetStrategy = document.getElementById('shortTargetStrategy').value;
    
    if (isNaN(triggerValue)) {
        alert('请输入有效的触发值');
        return;
    }
    
    if (enabled && !targetStrategy) {
        alert('启用条件单时必须选择目标策略');
        document.getElementById('shortOrderEnabled').checked = false;
        return;
    }
    
    try {
        const payload = {
            enabled: enabled,
            order_type: 'open_short',
            trigger_condition: 'above',
            trigger_value: triggerValue,
            target_strategy_code: targetStrategy
        };
        
        if (shortOrderData && shortOrderData.id) {
            payload.id = shortOrderData.id;
        }
        
        console.log('💾 保存做空条件单:', payload);
        const response = await fetch(`/api/okx-trading/coin-change-conditional-orders/${accountId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ 做空条件单已保存');
            shortOrderData = data.order;
            updateShortOrderUI();
        } else {
            throw new Error(data.message || '保存失败');
        }
    } catch (error) {
        console.error('❌ 保存做空条件单失败:', error);
        alert('保存失败: ' + error.message);
        // 恢复UI状态
        updateShortOrderUI();
    }
}

// 保存做多条件单设置
async function saveLongOrderSettings() {
    const accountId = getCurrentAccountId();
    if (!accountId) {
        alert('请先选择账户');
        return;
    }
    
    const enabled = document.getElementById('longOrderEnabled').checked;
    const triggerValue = parseFloat(document.getElementById('longTriggerValue').value);
    const targetStrategy = document.getElementById('longTargetStrategy').value;
    
    if (isNaN(triggerValue)) {
        alert('请输入有效的触发值');
        return;
    }
    
    if (enabled && !targetStrategy) {
        alert('启用条件单时必须选择目标策略');
        document.getElementById('longOrderEnabled').checked = false;
        return;
    }
    
    try {
        const payload = {
            enabled: enabled,
            order_type: 'open_long',
            trigger_condition: 'below',
            trigger_value: triggerValue,
            target_strategy_code: targetStrategy
        };
        
        if (longOrderData && longOrderData.id) {
            payload.id = longOrderData.id;
        }
        
        console.log('💾 保存做多条件单:', payload);
        const response = await fetch(`/api/okx-trading/coin-change-conditional-orders/${accountId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ 做多条件单已保存');
            longOrderData = data.order;
            updateLongOrderUI();
        } else {
            throw new Error(data.message || '保存失败');
        }
    } catch (error) {
        console.error('❌ 保存做多条件单失败:', error);
        alert('保存失败: ' + error.message);
        // 恢复UI状态
        updateLongOrderUI();
    }
}

// 重置做空触发状态
async function resetShortTrigger() {
    if (!shortOrderData || !shortOrderData.id) {
        alert('条件单不存在');
        return;
    }
    
    if (!confirm('确定要重置做空条件单的触发状态吗？重置后将可以再次触发。')) {
        return;
    }
    
    const accountId = getCurrentAccountId();
    if (!accountId) return;
    
    try {
        const response = await fetch(`/api/okx-trading/coin-change-conditional-orders/${accountId}/${shortOrderData.id}/reset-trigger`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ 做空条件单触发状态已重置');
            await loadConditionalOrders();
        } else {
            throw new Error(data.message || '重置失败');
        }
    } catch (error) {
        console.error('❌ 重置触发状态失败:', error);
        alert('重置失败: ' + error.message);
    }
}

// 重置做多触发状态
async function resetLongTrigger() {
    if (!longOrderData || !longOrderData.id) {
        alert('条件单不存在');
        return;
    }
    
    if (!confirm('确定要重置做多条件单的触发状态吗？重置后将可以再次触发。')) {
        return;
    }
    
    const accountId = getCurrentAccountId();
    if (!accountId) return;
    
    try {
        const response = await fetch(`/api/okx-trading/coin-change-conditional-orders/${accountId}/${longOrderData.id}/reset-trigger`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ 做多条件单触发状态已重置');
            await loadConditionalOrders();
        } else {
            throw new Error(data.message || '重置失败');
        }
    } catch (error) {
        console.error('❌ 重置触发状态失败:', error);
        alert('重置失败: ' + error.message);
    }
}
