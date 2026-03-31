#!/usr/bin/env python3
"""
Telegram配置测试脚本
"""
import os
import requests

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

print("=" * 60)
print("Telegram配置测试")
print("=" * 60)
print()

if not TELEGRAM_BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN 未设置")
    print("请在 .env 文件中配置：")
    print("  TELEGRAM_BOT_TOKEN=your_bot_token_here")
    exit(1)

if not TELEGRAM_CHAT_ID:
    print("❌ TELEGRAM_CHAT_ID 未设置")
    print("请在 .env 文件中配置：")
    print("  TELEGRAM_CHAT_ID=your_chat_id_here")
    exit(1)

print(f"✓ BOT_TOKEN: {TELEGRAM_BOT_TOKEN[:10]}...{TELEGRAM_BOT_TOKEN[-5:]}")
print(f"✓ CHAT_ID: {TELEGRAM_CHAT_ID}")
print()
print("正在发送测试消息...")
print()

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
message = (
    "🧪 <b>Telegram配置测试</b>\n\n"
    "这是一条测试消息，如果你看到了，说明配置成功！✅\n\n"
    "接下来，OKX止盈止损监控服务将通过此通道发送平仓通知。\n\n"
    f"测试时间: {os.popen('date').read().strip()}"
)
payload = {
    'chat_id': TELEGRAM_CHAT_ID,
    'text': message,
    'parse_mode': 'HTML'
}

try:
    response = requests.post(url, json=payload, timeout=10)
    if response.status_code == 200:
        print("✅ Telegram配置正确，测试消息已发送！")
        print()
        print("请检查你的Telegram，应该会收到测试消息。")
        print()
        print("如果收到了消息，说明配置成功！")
        print("现在可以启动监控服务：")
        print("  pm2 start okx-tpsl-monitor")
    else:
        print(f"❌ 发送失败: HTTP {response.status_code}")
        print()
        print("响应内容：")
        print(response.text)
        print()
        if response.status_code == 401:
            print("可能的原因：Bot Token无效")
            print("解决方案：检查.env中的TELEGRAM_BOT_TOKEN是否正确")
        elif response.status_code == 400:
            print("可能的原因：Chat ID无效或Bot未被用户启动")
            print("解决方案：")
            print("  1. 在Telegram中搜索你的Bot")
            print("  2. 点击Start或发送任意消息")
            print("  3. 确认TELEGRAM_CHAT_ID是正确的数字")
except Exception as e:
    print(f"❌ 异常: {e}")
    print()
    print("可能的原因：网络问题或配置错误")
