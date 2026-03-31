#!/usr/bin/env python3
"""
BTC & ETH 横盘监控 - 5分钟涨跌幅绝对值≤0.05%连续次数监控
当连续出现3次及以上时，发送Telegram告警：要变盘了
"""
import os
import sys
import time
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque

# 北京时间工具函数
def get_beijing_now():
    """获取当前北京时间"""
    return datetime.now() + timedelta(hours=8)

def get_beijing_now_str():
    """获取当前北京时间字符串"""
    return get_beijing_now().strftime('%Y-%m-%d %H:%M:%S')

# Telegram 配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8437045462:AAFePnwdC21cqeWhZISMQHGGgjmroVqE2H0')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1003227444260')

# 数据目录
DATA_DIR = Path('/home/user/webapp/data/consolidation_monitor')
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 配置文件
CONFIG_FILE = DATA_DIR / 'consolidation_config.json'
STATE_FILE = DATA_DIR / 'consolidation_state.json'

# 默认配置
DEFAULT_CONFIG = {
    'BTC-USDT-SWAP': {
        'enabled': True,
        'threshold': 0.0005,  # 0.05%
        'min_consecutive': 3,  # 最少连续次数
        'name': 'BTC永续合约'
    },
    'ETH-USDT-SWAP': {
        'enabled': True,
        'threshold': 0.0005,  # 0.05%
        'min_consecutive': 3,  # 最少连续次数
        'name': 'ETH永续合约'
    }
}

def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def load_state():
    """加载状态"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)
            # 将列表转换回deque
            for symbol in state:
                if 'history' in state[symbol]:
                    state[symbol]['history'] = deque(state[symbol]['history'], maxlen=20)
            return state
    return {}

def save_state(state):
    """保存状态"""
    # 将deque转换为列表用于JSON序列化
    state_copy = {}
    for symbol in state:
        state_copy[symbol] = state[symbol].copy()
        if 'history' in state_copy[symbol]:
            state_copy[symbol]['history'] = list(state_copy[symbol]['history'])
    
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state_copy, f, indent=2, ensure_ascii=False)

def get_5min_candle(symbol):
    """
    获取指定币种的最新已完成5分钟K线数据
    返回: (timestamp, change_percent, close_price) 或 None
    """
    try:
        url = f"https://www.okx.com/api/v5/market/candles"
        params = {
            'instId': symbol,
            'bar': '5m',
            'limit': '2'  # 获取最近2根K线
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data['code'] == '0' and data['data']:
            # 检查第一根K线是否已完成
            if len(data['data']) >= 1:
                latest_candle = data['data'][0]
                is_confirmed = latest_candle[8] == '1'
                
                # 如果最新K线已确认，使用它
                if is_confirmed:
                    candle = latest_candle
                # 否则使用上一根已完成的K线
                elif len(data['data']) >= 2:
                    candle = data['data'][1]
                else:
                    return None
                
                # OKX K线数据格式: [ts, o, h, l, c, vol, volCcy, volCcyQuote, confirm]
                timestamp = int(candle[0])
                open_price = float(candle[1])
                close_price = float(candle[4])
                
                # 计算涨跌幅（小数形式，如0.01表示1%）
                change_percent = (close_price - open_price) / open_price if open_price != 0 else 0
                
                return timestamp, change_percent, close_price
        
        return None
        
    except Exception as e:
        print(f"[{get_beijing_now_str()}] 获取 {symbol} K线数据失败: {e}")
        return None

def send_telegram_alert(symbol, config_name, consecutive_count, records):
    """发送 Telegram 横盘告警"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[{get_beijing_now_str()}] Telegram 配置未设置，跳过发送")
        return False
    
    try:
        # 构建消息
        message = f"""🔔 <b>横盘变盘告警</b>

📊 <b>{config_name}</b>
⚠️ 5分钟涨跌幅连续{consecutive_count}次≤0.05%

<b>要变盘了！</b>

📈 最近{len(records)}次记录："""
        
        for record in records[-5:]:  # 只显示最近5条
            time_str = record['time']
            change = record['change_percent'] * 100
            price = record['price']
            
            # 判断K线颜色：涨为绿色，跌为红色（国际标准配色）
            if change > 0:
                color_emoji = "🟩"  # 绿色方块 - 上涨
                color_text = "绿色"
            elif change < 0:
                color_emoji = "🟥"  # 红色方块 - 下跌
                color_text = "红色"
            else:
                color_emoji = "⬜"  # 白色方块 - 平盘
                color_text = "平盘"
            
            message += f"\n• {time_str}: {change:+.3f}% {color_emoji} ({color_text}) - ${price:,.2f}"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"[{get_beijing_now_str()}] ✅ Telegram 告警发送成功: {config_name} - 连续{consecutive_count}次横盘")
            return True
        else:
            print(f"[{get_beijing_now_str()}] ❌ Telegram 告警发送失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"[{get_beijing_now_str()}] 发送 Telegram 告警异常: {e}")
        return False

def check_consolidation(symbol, config, state):
    """检查横盘情况并发送告警"""
    if not config.get('enabled', False):
        return
    
    result = get_5min_candle(symbol)
    if not result:
        return
    
    timestamp, change_percent, price = result
    config_name = config['name']
    threshold = config.get('threshold', 0.0005)  # 默认0.05%
    min_consecutive = config.get('min_consecutive', 3)
    
    # 初始化状态
    if symbol not in state:
        state[symbol] = {
            'history': deque(maxlen=20),  # 保留最近20条记录
            'last_alert_timestamp': 0,  # 上次告警的时间戳
            'consecutive_count': 0  # 当前连续次数
        }
    
    symbol_state = state[symbol]
    
    # 检查是否已经记录过这个时间戳
    if symbol_state['history'] and symbol_state['history'][-1]['timestamp'] == timestamp:
        return  # 已经处理过这条数据
    
    # 转换时间戳为北京时间
    dt = datetime.fromtimestamp(timestamp / 1000)
    beijing_time = dt + timedelta(hours=8)
    time_str = beijing_time.strftime('%H:%M')
    
    # 判断是否满足横盘条件（绝对值≤阈值）
    abs_change = abs(change_percent)
    is_consolidation = abs_change <= threshold
    
    # 记录数据
    record = {
        'timestamp': timestamp,
        'time': time_str,
        'change_percent': change_percent,
        'price': price,
        'is_consolidation': is_consolidation
    }
    symbol_state['history'].append(record)
    
    # 计算连续横盘次数
    consecutive = 0
    for rec in reversed(list(symbol_state['history'])):
        if rec['is_consolidation']:
            consecutive += 1
        else:
            break
    
    symbol_state['consecutive_count'] = consecutive
    
    # 记录到JSONL
    record_consolidation_data(symbol, timestamp, change_percent, price, is_consolidation, consecutive)
    
    # 判断是否需要告警
    if consecutive >= min_consecutive:
        # 检查是否已经为这个连续序列发送过告警（避免重复）
        # 只在刚达到阈值时发送一次
        if len(symbol_state['history']) >= min_consecutive:
            # 检查前一条记录的连续次数
            if len(symbol_state['history']) >= min_consecutive + 1:
                # 找到倒数第min_consecutive+1条记录
                idx = -(min_consecutive + 1)
                if idx >= -len(symbol_state['history']):
                    prev_records = list(symbol_state['history'])[:idx]
                    prev_consecutive = 0
                    for rec in reversed(prev_records):
                        if rec['is_consolidation']:
                            prev_consecutive += 1
                        else:
                            break
                    
                    # 只在刚从min_consecutive-1变成min_consecutive时告警
                    if prev_consecutive < min_consecutive:
                        print(f"[{get_beijing_now_str()}] 🔔 {config_name} 横盘连续{consecutive}次！发送告警...")
                        send_telegram_alert(symbol, config_name, consecutive, list(symbol_state['history']))
            else:
                # 首次达到阈值
                print(f"[{get_beijing_now_str()}] 🔔 {config_name} 横盘连续{consecutive}次！发送告警...")
                send_telegram_alert(symbol, config_name, consecutive, list(symbol_state['history']))
    
    # 保存状态
    save_state(state)
    
    # 打印当前状态
    status_icon = "📊" if is_consolidation else "📈"
    print(f"[{get_beijing_now_str()}] {status_icon} {config_name} {time_str}: {change_percent*100:+.3f}% (连续横盘: {consecutive}次)")

def record_consolidation_data(symbol, timestamp, change_percent, price, is_consolidation, consecutive_count):
    """记录横盘数据到 JSONL"""
    try:
        beijing_date = get_beijing_now().strftime('%Y%m%d')
        jsonl_file = DATA_DIR / f'consolidation_{symbol.replace("-", "_")}_{beijing_date}.jsonl'
        
        # 检查是否已经记录过这个时间戳
        recorded_timestamps = set()
        if jsonl_file.exists():
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        recorded_timestamps.add(data.get('timestamp'))
                    except:
                        pass
        
        if timestamp in recorded_timestamps:
            return
        
        dt = datetime.fromtimestamp(timestamp / 1000)
        beijing_time = dt + timedelta(hours=8)
        
        record = {
            'timestamp': timestamp,
            'datetime': beijing_time.strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': symbol,
            'change_percent': change_percent,
            'change_percent_display': f"{change_percent*100:+.3f}%",
            'price': price,
            'is_consolidation': is_consolidation,
            'consecutive_count': consecutive_count,
            'recorded_at': get_beijing_now_str()
        }
        
        with open(jsonl_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        status = "横盘" if is_consolidation else "波动"
        print(f"[{get_beijing_now_str()}] ✅ 记录 {symbol} 数据: {record['datetime']} 涨跌{change_percent*100:+.3f}% ({status}, 连续{consecutive_count})")
            
    except Exception as e:
        print(f"[{get_beijing_now_str()}] 记录横盘数据失败: {e}")

def monitor_loop():
    """主监控循环"""
    print(f"[{get_beijing_now_str()}] BTC & ETH 横盘监控启动...")
    print(f"[{get_beijing_now_str()}] 数据目录: {DATA_DIR}")
    print(f"[{get_beijing_now_str()}] 监控条件: 5分钟涨跌幅绝对值≤0.05%，连续≥3次")
    print(f"[{get_beijing_now_str()}] Telegram Bot: {'已配置' if TELEGRAM_BOT_TOKEN else '未配置'}")
    
    config = load_config()
    state = load_state()
    
    while True:
        try:
            # 检查 BTC
            if 'BTC-USDT-SWAP' in config:
                check_consolidation('BTC-USDT-SWAP', config['BTC-USDT-SWAP'], state)
            
            # 检查 ETH
            if 'ETH-USDT-SWAP' in config:
                check_consolidation('ETH-USDT-SWAP', config['ETH-USDT-SWAP'], state)
            
            # 每60秒检查一次（5分钟K线，提前检查确保及时获取新数据）
            time.sleep(60)
            
        except KeyboardInterrupt:
            print(f"\n[{get_beijing_now_str()}] 收到停止信号，保存状态并退出...")
            save_state(state)
            break
        except Exception as e:
            print(f"[{get_beijing_now_str()}] 监控循环异常: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(60)

if __name__ == '__main__':
    monitor_loop()
