#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
币种涨跌预判监控器 - 测试脚本
手动测试分析逻辑（不受时间限制）
"""

import sys
import os
sys.path.insert(0, '/home/user/webapp')

from monitors.coin_change_prediction_monitor import (
    fetch_coin_change_data,
    analyze_bar_colors,
    determine_market_signal,
    send_telegram_message
)
from datetime import datetime

def test_analysis():
    """测试分析功能"""
    print("="*60)
    print("🧪 币种涨跌预判监控器 - 测试模式")
    print("="*60)
    
    # 获取数据
    print("\n1️⃣ 获取最新数据...")
    data = fetch_coin_change_data()
    if not data:
        print("❌ 无法获取数据")
        return
    
    print(f"✅ 数据获取成功，币种数量: {len(data.get('coins', []))}")
    
    # 分析柱状图颜色
    print("\n2️⃣ 分析柱状图颜色...")
    color_counts = analyze_bar_colors(data)
    if not color_counts:
        print("❌ 数据解析失败")
        return
    
    print(f"\n📊 柱状图颜色统计:")
    print(f"  🟢 绿色柱子: {color_counts['green']}个 (上涨占比 > 55%)")
    print(f"  🔴 红色柱子: {color_counts['red']}个 (上涨占比 < 45%)")
    print(f"  🟡 黄色柱子: {color_counts['yellow']}个 (45% ≤ 上涨占比 ≤ 55%)")
    
    # 判断市场信号
    print("\n3️⃣ 判断市场信号...")
    signal, description = determine_market_signal(color_counts)
    
    print(f"\n🎯 市场信号: {signal}")
    print(f"📝 说明: {description}")
    
    # 显示详细币种信息（前10个）
    print("\n4️⃣ 详细币种信息 (前10个):")
    for i, coin in enumerate(data.get('coins', [])[:10], 1):
        symbol = coin.get('symbol', 'Unknown')
        up_ratio = coin.get('up_ratio_10m', 0)
        
        if up_ratio > 55:
            color = "🟢"
        elif up_ratio < 45:
            color = "🔴"
        else:
            color = "🟡"
        
        print(f"  {i}. {color} {symbol}: {up_ratio:.2f}%")
    
    # 构建测试消息
    now = datetime.now()
    message = f"""
<b>🧪 测试 - 币种走势预判 - {now.strftime('%Y-%m-%d %H:%M')}</b>

<b>📊 柱状图颜色统计:</b>
🟢 绿色: {color_counts['green']}个 (上涨占比 > 55%)
🔴 红色: {color_counts['red']}个 (上涨占比 < 45%)
🟡 黄色: {color_counts['yellow']}个 (45% ≤ 占比 ≤ 55%)

<b>🎯 预判信号: {signal}</b>
{description}

<b>📖 分析规则:</b>
• 情况1: 有绿+有红+无黄 → 低吸机会
• 情况2: 有绿+有红+有黄 → 等待新低
• 情况3: 只有红色 → 做空信号
• 情况4: 全部绿色 → 诱多不参与

⏰ 这是测试消息
📈 数据来源: 10分钟上涨占比
"""
    
    # 询问是否发送TG消息
    print("\n5️⃣ 发送Telegram测试消息?")
    response = input("输入 'yes' 发送消息，其他键跳过: ").strip().lower()
    
    if response == 'yes':
        print("\n📤 发送Telegram消息...")
        success = send_telegram_message(message.strip())
        if success:
            print("✅ 消息发送成功")
        else:
            print("❌ 消息发送失败")
    else:
        print("\n⏭️ 跳过消息发送")
        print("\n📋 预览消息内容:")
        print(message)
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)

if __name__ == "__main__":
    test_analysis()
