#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查止损计算逻辑
查看-3 USDT止损对应的实际亏损
"""

import json
import os

def check_current_positions():
    """检查当前持仓"""
    print("="*80)
    print("🔍 止损计算分析")
    print("="*80)
    
    # 从配置文件读取账户信息
    config_file = 'config/okx_accounts.json'
    if not os.path.exists(config_file):
        print("❌ 配置文件不存在")
        return
    
    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    accounts = data.get('accounts', [])
    main_account = None
    for acc in accounts:
        if acc.get('id') == 'account_main':
            main_account = acc
            break
    
    if not main_account:
        print("❌ 未找到主账户")
        return
    
    print(f"\n📊 主账户信息:")
    print(f"   ID: {main_account.get('id')}")
    print(f"   名称: {main_account.get('name')}")
    print(f"   API Key: {main_account.get('apiKey')[:20]}...")
    
    print("\n" + "="*80)
    print("💡 止损逻辑说明")
    print("="*80)
    
    print("""
止损触发条件：
- 止损开关：已开启 ✅
- 止损阈值：-3 USDT（您的设置）
- 未实现盈亏：当前所有持仓的总未实现盈亏
- 触发条件：未实现盈亏 <= -3 USDT

示例场景：
┌────────────────────────────────────────────────────────────┐
│  币种  │ 方向 │ 数量  │ 开仓价 │ 当前价 │ 未实现盈亏 │
├────────────────────────────────────────────────────────────┤
│  BTC   │ 多   │ 0.01  │ 50000  │ 49700  │  -3.00 USDT│  ← 触发
│  ETH   │ 多   │ 0.5   │ 3000   │ 2994   │  -3.00 USDT│  ← 触发
│  BTC   │ 多   │ 0.01  │ 50000  │ 49500  │  -5.00 USDT│  ← 触发
│  BTC   │ 多   │ 0.01  │ 50000  │ 49800  │  -2.00 USDT│  ✅ 不触发
└────────────────────────────────────────────────────────────┘

⚠️  重要说明：
1. 止损阈值 -3 USDT 表示：当所有持仓的总未实现盈亏 ≤ -3 USDT 时触发
2. 这是【所有持仓的总亏损】，不是单个持仓
3. 触发后会【一键平掉所有4个账户的所有持仓】
4. 每次触发后有5分钟冷却时间，防止重复触发

实际亏损计算公式：
- 多单：未实现盈亏 = (当前价 - 开仓均价) × 持仓数量
- 空单：未实现盈亏 = (开仓均价 - 当前价) × 持仓数量
- 总未实现盈亏 = Σ(所有持仓的未实现盈亏)

💰 -3 USDT 止损意味着什么？
- 如果您有1个BTC多单（0.01 BTC），价格下跌 300 USDT 就会触发
  (0.01 × 300 = -3 USDT)
- 如果您有10个币种各持仓相当，每个亏 0.3 USDT 就会触发
  (10 × -0.3 = -3 USDT)
- 如果您的总资金是 300 USDT，-3 USDT = 1% 亏损
- 如果您的总资金是 30 USDT，-3 USDT = 10% 亏损

建议：
✅ 保守型：-10 USDT（约3-5%资金）
✅ 平衡型：-30 USDT（约10%资金，默认值）
✅ 激进型：-50 USDT（约15-20%资金）
⚠️  极度激进：-3 USDT（可能频繁触发）

""")
    
    print("="*80)
    print("🎯 前端止损逻辑代码位置")
    print("="*80)
    print("""
文件：templates/okx_trading.html
关键代码段：

1. 止损阈值输入框（第3797行）：
   <input type="number" id="stopLossThreshold" value="-30" step="1" max="-1">
   
2. 止损检查逻辑（第5070-5081行）：
   const stopLossThreshold = parseFloat(document.getElementById('stopLossThreshold').value);
   if (unrealizedPnl <= stopLossThreshold) {
       showStopLossAlert(unrealizedPnl, stopLossThreshold);
   }

3. 止损触发执行（第5114-5138行）：
   async function showStopLossAlert(currentPnl, threshold) {
       // 关闭止损开关
       // 调用 closeAllAccountsPositions() 平掉所有账户
       // 发送Telegram通知（3次）
       // 发送浏览器通知
   }
""")
    
    print("="*80)
    print("📝 查看您的当前设置")
    print("="*80)
    print("""
请在浏览器中：
1. 打开 OKX交易页面
2. 找到「止盈止损监控」区域
3. 查看「止损阈值」输入框的值
4. 如果是 -3，说明非常敏感，建议改为 -30 或更大
""")

if __name__ == "__main__":
    check_current_positions()
