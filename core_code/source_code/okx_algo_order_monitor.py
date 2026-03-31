#!/usr/bin/env python3
"""
OKX算法订单监控 - 检测止盈止损触发并发送Telegram通知
"""

import json
import os
import sys
import time
import hmac
import base64
import requests
from datetime import datetime, timezone
from pathlib import Path

# 配置
WEBAPP_DIR = Path(__file__).resolve().parent.parent
ACCOUNTS_CONFIG_DIR = WEBAPP_DIR / 'data' / 'okx_auto_strategy'
OKX_BASE_URL = 'https://www.okx.com'
CHECK_INTERVAL = 30  # 每30秒检查一次

# Telegram配置
TG_CONFIG_PATH = WEBAPP_DIR / 'config' / 'configs' / 'telegram_config.json'

def load_telegram_config():
    """加载Telegram配置"""
    try:
        if TG_CONFIG_PATH.exists():
            with open(TG_CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('bot_token'), config.get('chat_id')
    except Exception as e:
        print(f"⚠️  加载Telegram配置失败: {e}")
    return None, None

BOT_TOKEN, CHAT_ID = load_telegram_config()
TELEGRAM_ENABLED = bool(BOT_TOKEN and CHAT_ID)

def send_telegram(message):
    """发送Telegram通知"""
    if not TELEGRAM_ENABLED:
        print("[Telegram] 未配置，跳过通知")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("[Telegram] ✅ 通知发送成功")
            return True
        else:
            print(f"[Telegram] ❌ 通知发送失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"[Telegram] ❌ 通知异常: {e}")
        return False

def load_account_credentials(account_id):
    """加载账户API凭证"""
    config_file = ACCOUNTS_CONFIG_DIR / f'{account_id}.json'
    if not config_file.exists():
        return None
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            api_key = config.get('apiKey', '')
            secret_key = config.get('apiSecret', '')
            passphrase = config.get('passphrase', '')
            
            # 检查API凭证是否完整
            if not api_key or not secret_key or not passphrase:
                return None
            
            return {
                'api_key': api_key,
                'secret_key': secret_key,
                'passphrase': passphrase,
                'account_name': config.get('account_name', account_id)
            }
    except Exception as e:
        print(f"⚠️  加载 {account_id} 凭证失败: {e}")
    return None

def get_algo_orders(credentials):
    """获取算法订单列表（包括已触发和待触发的）"""
    try:
        # 获取待触发的算法订单
        path = '/api/v5/trade/orders-algo-pending?ordType=conditional'
        timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        message = timestamp + 'GET' + path
        
        mac = hmac.new(
            bytes(credentials['secret_key'], encoding='utf8'),
            bytes(message, encoding='utf-8'),
            digestmod='sha256'
        )
        signature = base64.b64encode(mac.digest()).decode()
        
        headers = {
            'OK-ACCESS-KEY': credentials['api_key'],
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': credentials['passphrase'],
            'Content-Type': 'application/json'
        }
        
        response = requests.get(OKX_BASE_URL + path, headers=headers, timeout=10)
        result = response.json()
        
        if result.get('code') == '0':
            return result.get('data', [])
        else:
            print(f"⚠️  获取算法订单失败: {result.get('msg', '未知错误')}")
            return []
            
    except Exception as e:
        print(f"⚠️  获取算法订单异常: {e}")
        return []

def get_algo_history(credentials, inst_id=None):
    """获取最近的算法订单历史（已触发/已取消）"""
    try:
        # 必须提供state参数
        path = '/api/v5/trade/orders-algo-history?ordType=conditional&state=effective'
        if inst_id:
            path += f'&instId={inst_id}'
        
        timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        message = timestamp + 'GET' + path
        
        mac = hmac.new(
            bytes(credentials['secret_key'], encoding='utf8'),
            bytes(message, encoding='utf-8'),
            digestmod='sha256'
        )
        signature = base64.b64encode(mac.digest()).decode()
        
        headers = {
            'OK-ACCESS-KEY': credentials['api_key'],
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': credentials['passphrase'],
            'Content-Type': 'application/json'
        }
        
        response = requests.get(OKX_BASE_URL + path, headers=headers, timeout=10)
        result = response.json()
        
        if result.get('code') == '0':
            return result.get('data', [])
        else:
            print(f"⚠️  获取算法订单历史失败: {result.get('msg', '未知错误')}")
            return []
            
    except Exception as e:
        print(f"⚠️  获取算法订单历史异常: {e}")
        return []

def check_triggered_orders(account_id, credentials):
    """检查是否有算法订单触发"""
    # 获取最近的历史记录，查找已触发的订单
    history_orders = get_algo_history(credentials)
    
    # 过滤出最近5分钟内触发的订单
    now = datetime.now(timezone.utc)
    triggered_orders = []
    
    for order in history_orders:
        # 状态: effective(已生效), canceled(已取消), order_failed(失败)
        state = order.get('state', '')
        if state == 'effective':  # 已触发（止盈止损已成交）
            # 检查触发时间
            trigger_time_str = order.get('triggerTime', '')
            if trigger_time_str:
                try:
                    trigger_time = datetime.fromtimestamp(int(trigger_time_str) / 1000, tz=timezone.utc)
                    time_diff = (now - trigger_time).total_seconds()
                    
                    # 只通知最近5分钟内触发的订单
                    if time_diff < 300:  # 5分钟 = 300秒
                        triggered_orders.append(order)
                except:
                    pass
    
    return triggered_orders

def send_tpsl_notification(account_name, order):
    """发送止盈止损触发通知"""
    inst_id = order.get('instId', 'Unknown')
    pos_side = order.get('posSide', '')
    tp_trigger_px = order.get('tpTriggerPx', '')
    sl_trigger_px = order.get('slTriggerPx', '')
    sz = order.get('sz', '0')
    trigger_time = order.get('triggerTime', '')
    
    # 判断是止盈还是止损
    if tp_trigger_px:
        action_type = 'take_profit'
        emoji = '✅'
        action_text = 'OKX止盈触发'
        trigger_price = float(tp_trigger_px)
    elif sl_trigger_px:
        action_type = 'stop_loss'
        emoji = '⛔'
        action_text = 'OKX止损触发'
        trigger_price = float(sl_trigger_px)
    else:
        return  # 既不是止盈也不是止损，跳过
    
    side_name = '多单' if pos_side == 'long' else '空单'
    
    # 格式化触发时间
    if trigger_time:
        try:
            trigger_dt = datetime.fromtimestamp(int(trigger_time) / 1000)
            trigger_time_str = trigger_dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            trigger_time_str = trigger_time
    else:
        trigger_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    message = f"""
{emoji} <b>{action_text}</b>

📊 <b>账户:</b> {account_name}
💰 <b>交易对:</b> {inst_id}
📈 <b>方向:</b> {side_name}
💵 <b>触发价:</b> {trigger_price:.4f}
📏 <b>数量:</b> {sz}
⏰ <b>触发时间:</b> {trigger_time_str}

🎯 <b>状态:</b> 已成交
"""
    
    send_telegram(message)

# 存储已通知的订单ID，避免重复通知
notified_orders = set()

def monitor_loop():
    """主监控循环"""
    print("🚀 OKX算法订单监控启动...")
    
    # 加载所有账户配置
    account_ids = []
    if ACCOUNTS_CONFIG_DIR.exists():
        for file in ACCOUNTS_CONFIG_DIR.glob('*.json'):
            account_id = file.stem
            account_ids.append(account_id)
    
    print(f"📋 发现 {len(account_ids)} 个账户: {account_ids}")
    
    while True:
        try:
            for account_id in account_ids:
                credentials = load_account_credentials(account_id)
                if not credentials:
                    continue
                
                # 检查触发的订单
                triggered_orders = check_triggered_orders(account_id, credentials)
                
                for order in triggered_orders:
                    algo_id = order.get('algoId', '')
                    
                    # 避免重复通知
                    if algo_id in notified_orders:
                        continue
                    
                    # 发送通知
                    account_name = credentials.get('account_name', account_id)
                    send_tpsl_notification(account_name, order)
                    
                    # 记录已通知
                    notified_orders.add(algo_id)
                    print(f"✅ 已通知 {account_name} - {order.get('instId')} 算法订单触发")
            
            # 定期清理已通知列表（保留最近1000条）
            if len(notified_orders) > 1000:
                notified_orders.clear()
            
            # 等待下一次检查
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n⏹️  监控已停止")
            break
        except Exception as e:
            print(f"❌ 监控异常: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    if not TELEGRAM_ENABLED:
        print("⚠️  Telegram未配置，请先配置 telegram_config.json")
        print("继续运行，但不会发送通知...")
    
    monitor_loop()
