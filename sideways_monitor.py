#!/usr/bin/env python3
"""
横盘监控 - BTC & ETH 5分钟K线涨跌幅监控
当连续3根或以上K线涨跌幅绝对值 ≤ 0.05% 时，发送Telegram告警
"""
import os
import sys
import time
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque

# 北京时间工具
def get_beijing_now():
    return datetime.now() + timedelta(hours=8)

def get_beijing_now_str():
    return get_beijing_now().strftime('%Y-%m-%d %H:%M:%S')

# Telegram配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8437045462:AAFePnwdC21cqeWhZISMQHGGgjmroVqE2H0')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1003227444260')

# 数据目录
DATA_DIR = Path('/home/user/webapp/data/sideways_monitor')
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 配置
THRESHOLD = 0.05  # 0.05% 涨跌幅阈值
MIN_CONSECUTIVE = 3  # 最少连续次数
CHECK_INTERVAL = 60  # 检查间隔（秒）

# 状态文件
STATE_FILE = DATA_DIR / 'sideways_state.json'

def load_state():
    """加载状态"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'BTC-USDT-SWAP': {
            'consecutive_count': 0,
            'last_alert_time': None,
            'recent_candles': []
        },
        'ETH-USDT-SWAP': {
            'consecutive_count': 0,
            'last_alert_time': None,
            'recent_candles': []
        }
    }

def save_state(state):
    """保存状态"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def get_5min_candle(symbol):
    """获取最新的已完成5分钟K线
    
    返回: (timestamp, open, high, low, close, volume, change_pct)
    """
    try:
        url = "https://www.okx.com/api/v5/market/candles"
        params = {
            'instId': symbol,
            'bar': '5m',
            'limit': '2'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data['code'] == '0' and data['data']:
            # 检查第一根K线是否已完成
            latest_candle = data['data'][0]
            is_confirmed = latest_candle[8] == '1'
            
            if is_confirmed:
                candle = latest_candle
            elif len(data['data']) >= 2:
                candle = data['data'][1]
            else:
                return None
            
            # 解析K线数据
            timestamp = int(candle[0])
            open_price = float(candle[1])
            high_price = float(candle[2])
            low_price = float(candle[3])
            close_price = float(candle[4])
            volume = float(candle[7])
            
            # 计算涨跌幅
            change_pct = ((close_price - open_price) / open_price) * 100
            
            return {
                'timestamp': timestamp,
                'datetime': datetime.fromtimestamp(timestamp/1000 + 8*3600).strftime('%Y-%m-%d %H:%M:%S'),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume,
                'change_pct': change_pct,
                'abs_change_pct': abs(change_pct)
            }
        
        return None
        
    except Exception as e:
        print(f"[{get_beijing_now_str()}] 获取 {symbol} K线数据失败: {e}")
        return None

def send_telegram_alert(symbol, consecutive_count, recent_candles):
    """发送Telegram告警"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[{get_beijing_now_str()}] Telegram配置未设置，跳过发送")
        return False
    
    try:
        coin_name = 'BTC' if 'BTC' in symbol else 'ETH'
        
        # 构建K线列表文本
        candle_text = ""
        for c in recent_candles[-consecutive_count:]:
            candle_text += f"\n  {c['datetime']} {c['change_pct']:+.2f}%"
        
        message = f"""🚨 <b>横盘变盘告警</b>

📊 币种: <b>{coin_name}</b>
⏱️ 周期: 5分钟
📈 连续次数: <b>{consecutive_count} 根K线</b>
📉 涨跌幅阈值: ≤ 0.05%

<b>最近K线数据</b>:{candle_text}

⚠️ <b>注意：可能即将变盘！</b>"""

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"[{get_beijing_now_str()}] ✅ Telegram告警发送成功: {coin_name} 连续{consecutive_count}次横盘")
            return True
        else:
            print(f"[{get_beijing_now_str()}] ❌ Telegram告警发送失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"[{get_beijing_now_str()}] Telegram告警发送异常: {e}")
        return False

def record_sideways_data(symbol, candle_data, consecutive_count, is_sideways):
    """记录横盘数据"""
    try:
        beijing_date = get_beijing_now().strftime('%Y%m%d')
        jsonl_file = DATA_DIR / f'sideways_{symbol.replace("-", "_")}_{beijing_date}.jsonl'
        
        record = {
            'timestamp': candle_data['timestamp'],
            'datetime': candle_data['datetime'],
            'symbol': symbol,
            'change_pct': candle_data['change_pct'],
            'abs_change_pct': candle_data['abs_change_pct'],
            'consecutive_count': consecutive_count,
            'is_sideways': is_sideways,
            'threshold': THRESHOLD,
            'recorded_at': get_beijing_now_str()
        }
        
        with open(jsonl_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        status = "横盘" if is_sideways else "波动"
        print(f"[{get_beijing_now_str()}] ✅ 记录 {symbol}: {candle_data['datetime']} 涨跌: {candle_data['change_pct']:+.2f}% ({status}, 连续{consecutive_count}次)")
            
    except Exception as e:
        print(f"[{get_beijing_now_str()}] 记录数据失败: {e}")

def check_sideways(symbol, state):
    """检查横盘状态"""
    candle = get_5min_candle(symbol)
    if not candle:
        return
    
    symbol_state = state[symbol]
    
    # 检查是否是新K线（避免重复处理）
    if symbol_state['recent_candles']:
        last_timestamp = symbol_state['recent_candles'][-1]['timestamp']
        if candle['timestamp'] == last_timestamp:
            # 同一根K线，不处理
            return
    
    # 判断是否横盘（涨跌幅绝对值 ≤ 阈值）
    is_sideways = candle['abs_change_pct'] <= THRESHOLD
    
    # 更新连续计数
    if is_sideways:
        symbol_state['consecutive_count'] += 1
    else:
        symbol_state['consecutive_count'] = 0
    
    # 添加到最近K线列表（保留最近10根）
    symbol_state['recent_candles'].append(candle)
    if len(symbol_state['recent_candles']) > 10:
        symbol_state['recent_candles'].pop(0)
    
    # 记录数据
    record_sideways_data(symbol, candle, symbol_state['consecutive_count'], is_sideways)
    
    # 检查是否需要告警
    if symbol_state['consecutive_count'] >= MIN_CONSECUTIVE:
        # 检查距离上次告警是否超过30分钟（避免频繁告警）
        last_alert = symbol_state['last_alert_time']
        now = get_beijing_now()
        
        should_alert = True
        if last_alert:
            last_alert_dt = datetime.fromisoformat(last_alert)
            if (now - last_alert_dt).total_seconds() < 1800:  # 30分钟
                should_alert = False
        
        if should_alert:
            coin_name = 'BTC' if 'BTC' in symbol else 'ETH'
            print(f"[{get_beijing_now_str()}] 🚨 {coin_name} 横盘告警触发: 连续{symbol_state['consecutive_count']}次")
            
            if send_telegram_alert(symbol, symbol_state['consecutive_count'], symbol_state['recent_candles']):
                symbol_state['last_alert_time'] = now.isoformat()
                # 重置计数，避免同一波横盘多次告警
                symbol_state['consecutive_count'] = 0
    
    # 保存状态
    save_state(state)

def monitor_loop():
    """主监控循环"""
    print(f"[{get_beijing_now_str()}] 横盘监控启动...")
    print(f"[{get_beijing_now_str()}] 涨跌幅阈值: {THRESHOLD}%")
    print(f"[{get_beijing_now_str()}] 最少连续次数: {MIN_CONSECUTIVE}")
    print(f"[{get_beijing_now_str()}] 数据目录: {DATA_DIR}")
    
    state = load_state()
    
    while True:
        try:
            print(f"\n[{get_beijing_now_str()}] === 开始检查横盘状态 ===")
            
            # 检查BTC
            check_sideways('BTC-USDT-SWAP', state)
            time.sleep(2)
            
            # 检查ETH
            check_sideways('ETH-USDT-SWAP', state)
            
            print(f"[{get_beijing_now_str()}] BTC连续: {state['BTC-USDT-SWAP']['consecutive_count']} | ETH连续: {state['ETH-USDT-SWAP']['consecutive_count']}")
            
        except Exception as e:
            print(f"[{get_beijing_now_str()}] 监控异常: {e}")
            import traceback
            traceback.print_exc()
        
        # 等待下次检查
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    monitor_loop()
