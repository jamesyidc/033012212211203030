#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有账户的API配置
验证每个账户是否能正常连接OKX API
"""

import json
import hmac
import base64
from datetime import datetime, timezone
import requests
from pathlib import Path

# 读取账户配置
config_path = Path('/home/user/webapp/config/okx_accounts.json')

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

accounts = config.get('accounts', [])

print("=" * 60)
print("🔍 测试所有OKX账户API配置")
print("=" * 60)
print(f"\n总账户数: {len(accounts)}\n")

for i, account in enumerate(accounts, 1):
    account_id = account.get('id', '')
    account_name = account.get('name', '')
    api_key = account.get('apiKey', '')
    api_secret = account.get('apiSecret', '')
    passphrase = account.get('passphrase', '')
    
    print(f"{i}. 账户: {account_name} ({account_id})")
    print(f"   API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else ''}")
    print(f"   API Secret: {'✅ 已配置' if api_secret else '❌ 未配置'}")
    print(f"   Passphrase: {'✅ 已配置' if passphrase else '❌ 未配置'}")
    
    if not api_key or not api_secret or not passphrase:
        print(f"   ⚠️  凭证不完整，跳过测试\n")
        continue
    
    # 测试API连接
    try:
        base_url = 'https://www.okx.com'
        path = '/api/v5/account/balance'
        
        timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        message = timestamp + 'GET' + path
        mac = hmac.new(
            bytes(api_secret, encoding='utf8'),
            bytes(message, encoding='utf-8'),
            digestmod='sha256'
        )
        signature = base64.b64encode(mac.digest()).decode()
        
        headers = {
            'OK-ACCESS-KEY': api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': passphrase,
        }
        
        response = requests.get(base_url + path, headers=headers, timeout=10)
        result = response.json()
        
        if result.get('code') == '0':
            balance_data = result.get('data', [])
            if balance_data and balance_data[0]:
                total_eq = float(balance_data[0].get('totalEq', 0))
                print(f"   ✅ API连接成功")
                print(f"   💰 账户总权益: {total_eq:.2f} USDT")
        else:
            error_msg = result.get('msg', '未知错误')
            print(f"   ❌ API连接失败: {error_msg}")
            print(f"      错误代码: {result.get('code', 'N/A')}")
    
    except Exception as e:
        print(f"   ❌ API测试异常: {e}")
    
    print()

print("=" * 60)
print("✅ 测试完成")
print("=" * 60)
