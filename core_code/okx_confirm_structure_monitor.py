#!/usr/bin/env python3
"""
OKX 确认结构监控服务
- 监控持仓组合的整体涨幅
- 达到阈值时发送Telegram提醒
- 记录每次提醒到JSONL文件
"""

import os
import json
import time
import hmac
import hashlib
import base64
from datetime import datetime, timezone
import requests

# 配置
SETTINGS_DIR = 'data/okx_tpsl_settings'
CHECK_INTERVAL = 10  # 10秒检查一次
TELEGRAM_COOLDOWN = 300  # 5分钟冷却期

# Telegram配置
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# OKX API配置
OKX_API_BASE = "https://www.okx.com"

# 记录最后一次提醒时间
last_alert_times = {}


def send_telegram(message):
    """发送Telegram消息"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ [Telegram] 未配置Bot Token或Chat ID，跳过发送")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print(f"✅ [Telegram] 消息发送成功")
            return True
        else:
            print(f"❌ [Telegram] 发送失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ [Telegram] 发送异常: {e}")
        return False


def generate_signature(timestamp, method, request_path, body, secret_key):
    """生成OKX API签名"""
    message = timestamp + method + request_path + (body or '')
    mac = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    )
    return base64.b64encode(mac.digest()).decode()


def get_account_info(api_key, api_secret, passphrase):
    """获取账户信息（包含总保证金和未实现盈亏）"""
    try:
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        method = 'GET'
        request_path = '/api/v5/account/balance'
        
        signature = generate_signature(timestamp, method, request_path, '', api_secret)
        
        headers = {
            'OK-ACCESS-KEY': api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': passphrase,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(OKX_API_BASE + request_path, headers=headers, timeout=10)
        result = response.json()
        
        if result.get('code') != '0':
            print(f"❌ [OKX API] 获取账户信息失败: {result}")
            return None
        
        # 解析账户数据
        data = result.get('data', [])
        if not data:
            return None
        
        details = data[0].get('details', [])
        total_equity = 0
        total_margin = 0
        total_upl = 0
        
        for item in details:
            equity = float(item.get('eq', 0))
            margin = float(item.get('imr', 0))  # 初始保证金
            upl = float(item.get('upl', 0))
            
            total_equity += equity
            total_margin += margin
            total_upl += upl
        
        return {
            'totalEquity': total_equity,
            'totalMargin': total_margin,
            'unrealizedPnl': total_upl
        }
    
    except Exception as e:
        print(f"❌ [OKX API] 获取账户信息异常: {e}")
        return None


def get_positions(api_key, api_secret, passphrase):
    """获取持仓列表"""
    try:
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        method = 'GET'
        request_path = '/api/v5/account/positions'
        
        signature = generate_signature(timestamp, method, request_path, '', api_secret)
        
        headers = {
            'OK-ACCESS-KEY': api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': passphrase,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(OKX_API_BASE + request_path, headers=headers, timeout=10)
        result = response.json()
        
        if result.get('code') != '0':
            print(f"❌ [OKX API] 获取持仓失败: {result}")
            return []
        
        positions = result.get('data', [])
        # 过滤掉空仓
        return [p for p in positions if float(p.get('pos', 0)) != 0]
    
    except Exception as e:
        print(f"❌ [OKX API] 获取持仓异常: {e}")
        return []


def load_settings(account_id):
    """加载账户的确认结构配置"""
    config_file = os.path.join(SETTINGS_DIR, f"{account_id}_percent_tpsl.jsonl")
    
    if not os.path.exists(config_file):
        return None
    
    try:
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    settings = json.loads(line)
                    return settings
        return None
    except Exception as e:
        print(f"❌ [配置加载] 读取失败: {e}")
        return None


def load_credentials(account_id):
    """加载账户的API凭证"""
    cred_file = os.path.join(SETTINGS_DIR, f"{account_id}_credentials.json")
    
    if not os.path.exists(cred_file):
        return None
    
    try:
        with open(cred_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ [凭证加载] 读取失败: {e}")
        return None


def save_alert_record(account_id, threshold_percent, total_margin, total_pnl, portfolio_gain, position_count):
    """保存提醒记录到JSONL"""
    record_file = os.path.join(SETTINGS_DIR, f"{account_id}_confirm_structure_alerts.jsonl")
    
    record = {
        'account_id': account_id,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'thresholdPercent': threshold_percent,
        'totalMargin': round(total_margin, 2),
        'totalPnl': round(total_pnl, 2),
        'portfolioGain': round(portfolio_gain, 2),
        'positionCount': position_count,
        'alertType': 'confirm_structure',
        'comment': '组合涨幅确认结构提醒'
    }
    
    try:
        with open(record_file, 'a') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        print(f"✅ [记录保存] 已保存到 {record_file}")
        return True
    except Exception as e:
        print(f"❌ [记录保存] 保存失败: {e}")
        return False


def check_confirm_structure(account_id):
    """检查确认结构条件"""
    # 1. 加载配置
    settings = load_settings(account_id)
    if not settings:
        return
    
    # 检查是否启用确认结构
    if not settings.get('confirmStructureEnabled', False):
        return
    
    threshold_percent = settings.get('confirmStructureThreshold', 10.0)
    
    # 2. 加载API凭证
    credentials = load_credentials(account_id)
    if not credentials:
        print(f"⚠️ [确认结构] {account_id} 未配置API凭证")
        return
    
    api_key = credentials.get('apiKey')
    api_secret = credentials.get('apiSecret')
    passphrase = credentials.get('passphrase')
    
    if not all([api_key, api_secret, passphrase]):
        print(f"⚠️ [确认结构] {account_id} API凭证不完整")
        return
    
    # 3. 获取账户信息
    account_info = get_account_info(api_key, api_secret, passphrase)
    if not account_info:
        return
    
    total_margin = account_info['totalMargin']
    total_pnl = account_info['unrealizedPnl']
    
    if total_margin <= 0:
        return
    
    # 4. 计算组合涨幅
    portfolio_gain = (total_pnl / total_margin) * 100
    
    print(f"📊 [确认结构] {account_id} - 保证金: {total_margin:.2f} USDT, 盈亏: {total_pnl:.2f} USDT, 涨幅: {portfolio_gain:.2f}%")
    
    # 5. 检查是否达到阈值
    if portfolio_gain >= threshold_percent:
        # 检查冷却期
        current_time = time.time()
        last_alert_time = last_alert_times.get(account_id, 0)
        
        if current_time - last_alert_time < TELEGRAM_COOLDOWN:
            remaining = int(TELEGRAM_COOLDOWN - (current_time - last_alert_time))
            print(f"⏳ [确认结构] {account_id} 冷却期中，还需等待 {remaining} 秒")
            return
        
        # 获取持仓数量
        positions = get_positions(api_key, api_secret, passphrase)
        position_count = len(positions)
        
        # 发送提醒
        message = f"""🔔 <b>确认结构触发</b> - {account_id}

📊 <b>组合涨幅:</b> {portfolio_gain:.2f}%
🎯 <b>触发阈值:</b> {threshold_percent}%

💰 <b>总保证金:</b> {total_margin:.2f} USDT
💵 <b>未实现盈亏:</b> {total_pnl:.2f} USDT
📦 <b>持仓数量:</b> {position_count} 个

💡 <b>建议:</b> 趋势已确认，可考虑加仓
"""
        
        if send_telegram(message):
            # 更新最后提醒时间
            last_alert_times[account_id] = current_time
            
            # 保存记录
            save_alert_record(account_id, threshold_percent, total_margin, total_pnl, portfolio_gain, position_count)
            
            print(f"✅ [确认结构] {account_id} 提醒已发送")
        else:
            print(f"❌ [确认结构] {account_id} 提醒发送失败")
    else:
        # 如果涨幅低于阈值，重置冷却期（允许再次提醒）
        if account_id in last_alert_times:
            current_time = time.time()
            last_alert_time = last_alert_times[account_id]
            if current_time - last_alert_time >= TELEGRAM_COOLDOWN:
                del last_alert_times[account_id]
                print(f"🔄 [确认结构] {account_id} 冷却期已重置")


def main():
    """主循环"""
    print("=" * 60)
    print("🔔 OKX确认结构监控服务启动")
    print(f"📁 配置目录: {SETTINGS_DIR}")
    print(f"⏱️  检查间隔: {CHECK_INTERVAL}秒")
    print(f"🕐 冷却时间: {TELEGRAM_COOLDOWN}秒")
    print("=" * 60)
    
    # 创建配置目录
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    
    while True:
        try:
            # 获取所有配置文件
            if os.path.exists(SETTINGS_DIR):
                for filename in os.listdir(SETTINGS_DIR):
                    if filename.endswith('_percent_tpsl.jsonl'):
                        account_id = filename.replace('_percent_tpsl.jsonl', '')
                        check_confirm_structure(account_id)
            
            time.sleep(CHECK_INTERVAL)
        
        except KeyboardInterrupt:
            print("\n👋 确认结构监控服务已停止")
            break
        except Exception as e:
            print(f"❌ [主循环] 异常: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
