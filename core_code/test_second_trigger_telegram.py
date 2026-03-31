#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试二级触发 Telegram 消息发送
"""

import requests
from datetime import datetime

# Telegram配置
TG_BOT_TOKEN = "8437045462:AAFePnwdC21cqeWhZISMQHGGgjmroVqE2H0"
TG_CHAT_ID = "-1003227444260"

def send_telegram_message(message):
    """发送Telegram消息"""
    bot_token = TG_BOT_TOKEN
    chat_id = TG_CHAT_ID
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Telegram消息发送成功")
            return True
        else:
            print(f"❌ Telegram消息发送失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 发送Telegram消息异常: {e}")
        return False

# 测试消息
now = datetime.now()
bar_details = [
    {'color': 'green', 'up_ratio': 88.9, 'time': '02:10'},
    {'color': 'green', 'up_ratio': 74.1, 'time': '02:20'},
    {'color': 'green', 'up_ratio': 88.9, 'time': '02:30'}
]

color_emojis = []
for detail in bar_details:
    emoji = {
        'green': '🟢',
        'red': '🔴',
        'yellow': '🟡',
        'blank': '⚪'
    }.get(detail['color'], '⚪')
    color_emojis.append(emoji)

message = f"""
🔔 <b>【低吸】二级触发通知</b> 🔔

📅 日期: {now.strftime('%Y-%m-%d')}
⏰ 时间: {now.strftime('%H:%M')} (北京时间)

━━━━━━━━━━━━━━━━━━━━

📊 <b>今日预判: 低吸</b>

🔍 <b>2点后前三根柱子:</b>
{color_emojis[0]} 2:10 - 上涨占比 {bar_details[0]['up_ratio']:.1f}%
{color_emojis[1]} 2:20 - 上涨占比 {bar_details[1]['up_ratio']:.1f}%
{color_emojis[2]} 2:30 - 上涨占比 {bar_details[2]['up_ratio']:.1f}%

━━━━━━━━━━━━━━━━━━━━

✅ <b>二级触发: 已触发</b>
💡 <b>操作建议: 🚀 立即做多</b>

🟢🟢🟢 2点之后三根全绿，直接做多！

━━━━━━━━━━━━━━━━━━━━

💬 <b>说明:</b>
二级触发【立即做多】：2点后连续三根绿色柱子，市场上涨趋势明确。

⚠️ <b>风险提示:</b> 请结合实际市场情况谨慎决策
"""

print("📱 发送测试消息...")
print()
print(message)
print()
print("=" * 60)

send_telegram_message(message.strip())
