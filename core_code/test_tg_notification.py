#!/usr/bin/env python3
"""测试Telegram通知功能"""
import sys
from pathlib import Path

BASE_DIR = Path('/home/user/webapp')
sys.path.insert(0, str(BASE_DIR / 'config'))

try:
    from telegram_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    print(f"✅ TG配置已加载")
    print(f"   BOT_TOKEN: {'已设置' if TELEGRAM_BOT_TOKEN else '未设置'}")
    print(f"   CHAT_ID: {'已设置' if TELEGRAM_CHAT_ID else '未设置'}")
except ImportError as e:
    print(f"❌ 无法加载TG配置: {e}")
    sys.exit(1)

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("\n⚠️  Telegram配置未完成，无法发送通知")
    print("请在 config/telegram_config.py 中配置:")
    print("  TELEGRAM_BOT_TOKEN = 'your_bot_token'")
    print("  TELEGRAM_CHAT_ID = 'your_chat_id'")
    sys.exit(0)

# 测试发送
import requests
import time

test_message = "🧪 <b>测试通知</b>\n\n这是一条测试消息，用于验证Telegram通知功能。"
url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'

print(f"\n📤 正在发送测试通知...")
try:
    response = requests.post(url, json={
        'chat_id': TELEGRAM_CHAT_ID,
        'text': test_message,
        'parse_mode': 'HTML'
    }, timeout=10)
    
    if response.status_code == 200:
        print(f"✅ 测试通知发送成功！")
        print(f"   请检查您的Telegram是否收到消息")
    else:
        print(f"❌ 发送失败: {response.status_code}")
        print(f"   响应: {response.text}")
except Exception as e:
    print(f"❌ 发送异常: {e}")
