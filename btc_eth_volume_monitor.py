#!/usr/bin/env python3
"""
BTC & ETH 5分钟成交量监控
监控 OKX BTC-USDT-SWAP 和 ETH-USDT-SWAP 的 5 分钟成交量
当成交量超过设定阈值时发送 Telegram 通知
"""
import os
import sys
import time
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta

# 北京时间工具函数
def get_beijing_now():
    """获取当前北京时间"""
    return datetime.now() + timedelta(hours=8)

def get_beijing_now_str():
    """获取当前北京时间字符串"""
    return get_beijing_now().strftime('%Y-%m-%d %H:%M:%S')

# Telegram 配置（使用与其他监控相同的配置）
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8437045462:AAFePnwdC21cqeWhZISMQHGGgjmroVqE2H0')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1003227444260')

# 数据目录
DATA_DIR = Path('/home/user/webapp/data/volume_monitor')
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 配置文件（与 API 保持一致）
CONFIG_FILE = DATA_DIR / 'volume_thresholds.json'
STATE_FILE = DATA_DIR / 'volume_state.json'

# 默认配置 (M USDT)
DEFAULT_CONFIG = {
    'BTC-USDT-SWAP': {
        'enabled': True,
        'threshold_v1': 180_000_000,  # 180M USDT - V1阈值（大于此值）
        'threshold_v2_min': 100_000_000,  # 100M USDT - V2最小值
        'threshold_v2_max': 180_000_000,  # 180M USDT - V2最大值（大于min且小于max）
        'name': 'BTC永续合约'
    },
    'ETH-USDT-SWAP': {
        'enabled': True,
        'threshold_v1': 130_000_000,  # 130M USDT - V1阈值（大于此值）
        'threshold_v2_min': 50_000_000,  # 50M USDT - V2最小值
        'threshold_v2_max': 130_000_000,  # 130M USDT - V2最大值（大于min且小于max）
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
            return json.load(f)
    return {}


def save_state(state):
    """保存状态"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def get_5min_candle(symbol):
    """
    获取指定币种的最新**已完成**5分钟K线数据
    返回: (timestamp, volume, close_price) 或 None
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
            # data['data'][0] 是最新的K线（可能未完成）
            # data['data'][1] 是上一根K线（已完成）
            
            # 检查第一根K线是否已完成
            if len(data['data']) >= 1:
                latest_candle = data['data'][0]
                is_confirmed = latest_candle[8] == '1'
                
                # 如果最新K线已确认（完成），使用它
                if is_confirmed:
                    candle = latest_candle
                # 否则使用上一根已完成的K线
                elif len(data['data']) >= 2:
                    candle = data['data'][1]
                else:
                    # 没有已完成的K线数据
                    return None
                
                # OKX K线数据格式: [ts, o, h, l, c, vol, volCcy, volCcyQuote, confirm]
                # ts: 时间戳, vol: 成交量(张), volCcy: 成交量(币), volCcyQuote: 成交量(计价货币USDT)
                timestamp = int(candle[0])
                volume_usdt = float(candle[7])  # 使用 USDT 计价的成交量
                close_price = float(candle[4])
                
                return timestamp, volume_usdt, close_price
        
        return None
        
    except Exception as e:
        print(f"[{get_beijing_now_str()}] 获取 {symbol} K线数据失败: {e}")
        return None


def send_telegram_alert(symbol, config_name, volume, threshold_level, threshold_value, price, timestamp):
    """发送 Telegram 告警
    
    Args:
        symbol: 交易对符号
        config_name: 配置名称
        volume: 成交量
        threshold_level: 阈值级别 ('V1' 或 'V2')
        threshold_value: 阈值数值（对于V2是范围字符串）
        price: 价格
        timestamp: 时间戳
    
    发送规则：
        - V1 高阈值：发送 3 遍（红色高亮，闪烁效果）
        - V2 中等阈值：发送 1 遍（黄色提示）
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[{get_beijing_now_str()}] Telegram 配置未设置，跳过发送")
        return False
    
    try:
        # 转换时间戳为北京时间
        dt = datetime.fromtimestamp(timestamp / 1000)
        beijing_time = dt + timedelta(hours=8)
        time_str = beijing_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 格式化成交量（单位：M）
        volume_m = volume / 1_000_000
        
        # 根据阈值级别生成不同的消息
        if threshold_level == 'V1':
            threshold_m = threshold_value / 1_000_000
            level_emoji = '🔴'
            level_text = 'V1 高阈值'
            threshold_text = f'{threshold_m:.2f}M'
            exceed_percent = ((volume/threshold_value - 1) * 100)
            repeat_count = 3  # V1 发送 3 遍
            message_prefix = '🚨🚨🚨 '  # 三个警报符号
        else:  # V2
            level_emoji = '🟡'
            level_text = 'V2 中等阈值'
            threshold_text = threshold_value  # 已经是格式化的范围字符串
            exceed_percent = 0  # V2不计算超过百分比
            repeat_count = 1  # V2 发送 1 遍
            message_prefix = '⚠️ '  # 单个警告符号
        
        message = f"""{message_prefix}<b>成交量告警 - {level_text}</b>

📊 <b>{config_name}</b>
⏰ 时间: {time_str}
💰 价格: ${price:,.2f}
📈 5分钟成交量: <b>{volume_m:.2f}M</b>
⚠️ 阈值: {threshold_text}"""

        if threshold_level == 'V1' and exceed_percent > 0:
            message += f"\n\n🔥 超过阈值 <b>{exceed_percent:.1f}%</b> 🔥"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        
        # 根据级别发送不同次数
        success_count = 0
        for i in range(repeat_count):
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            try:
                response = requests.post(url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    success_count += 1
                    if repeat_count > 1:
                        print(f"[{get_beijing_now_str()}] Telegram 告警发送成功 ({i+1}/{repeat_count}): {config_name} - {level_text}")
                    else:
                        print(f"[{get_beijing_now_str()}] Telegram 告警发送成功: {config_name} - {level_text}")
                    
                    # V1级别的消息之间间隔1秒，避免被限流
                    if i < repeat_count - 1:
                        time.sleep(1)
                else:
                    print(f"[{get_beijing_now_str()}] Telegram 告警发送失败 ({i+1}/{repeat_count}): {response.text}")
            except Exception as e:
                print(f"[{get_beijing_now_str()}] Telegram 告警发送异常 ({i+1}/{repeat_count}): {e}")
        
        # 只要有一次发送成功就返回True
        if success_count > 0:
            if repeat_count > 1:
                print(f"[{get_beijing_now_str()}] ✅ {level_text} 告警发送完成: 成功 {success_count}/{repeat_count} 次")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"[{get_beijing_now_str()}] 发送 Telegram 告警异常: {e}")
        return False


def check_volume_alert(symbol, config, state):
    """检查成交量并发送告警（支持双阈值）"""
    if not config.get('enabled', False):
        return
    
    result = get_5min_candle(symbol)
    if not result:
        return
    
    timestamp, volume, price = result
    config_name = config['name']
    
    # 获取双阈值配置（兼容旧配置）
    threshold_v1 = config.get('threshold_v1', config.get('threshold', 0))
    threshold_v2_min = config.get('threshold_v2_min', 0)
    threshold_v2_max = config.get('threshold_v2_max', threshold_v1)
    
    # 确定触发的阈值级别
    alert_level = None
    alert_threshold = None
    
    if volume > threshold_v1:
        # V1阈值：大于V1
        alert_level = 'V1'
        alert_threshold = threshold_v1
    elif threshold_v2_min < volume <= threshold_v2_max:
        # V2阈值：大于V2_min且小于等于V2_max
        alert_level = 'V2'
        alert_threshold = f"{threshold_v2_min/1_000_000:.0f}M - {threshold_v2_max/1_000_000:.0f}M"
    
    # 如果触发了告警
    if alert_level:
        # 检查是否已经为这个时间点和级别发送过告警
        state_key = f"{symbol}_{timestamp}_{alert_level}"
        if state_key not in state:
            volume_m = volume / 1_000_000
            print(f"[{get_beijing_now_str()}] {config_name} 触发 {alert_level} 阈值: {volume_m:.2f}M")
            
            # 发送告警
            if send_telegram_alert(symbol, config_name, volume, alert_level, alert_threshold, price, timestamp):
                # 记录已发送
                state[state_key] = {
                    'timestamp': timestamp,
                    'volume': volume,
                    'price': price,
                    'level': alert_level,
                    'alert_time': get_beijing_now_str()
                }
                save_state(state)
    
    # 记录最新数据到 JSONL（包含双阈值信息）
    record_volume_data(symbol, timestamp, volume, price, threshold_v1, threshold_v2_min, threshold_v2_max)


def record_volume_data(symbol, timestamp, volume, price, threshold_v1, threshold_v2_min, threshold_v2_max):
    """记录成交量数据到 JSONL（支持双阈值，避免重复记录同一时间戳）"""
    try:
        beijing_date = get_beijing_now().strftime('%Y%m%d')
        jsonl_file = DATA_DIR / f'volume_{symbol.replace("-", "_")}_{beijing_date}.jsonl'
        
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
        
        # 如果这个时间戳已经记录过，跳过
        if timestamp in recorded_timestamps:
            print(f"[{get_beijing_now_str()}] {symbol} K线 {timestamp} 已记录，跳过")
            return
        
        # 判断触发的阈值级别
        exceeded_level = None
        if volume > threshold_v1:
            exceeded_level = 'V1'
        elif threshold_v2_min < volume <= threshold_v2_max:
            exceeded_level = 'V2'
        
        record = {
            'timestamp': timestamp,
            'datetime': datetime.fromtimestamp(timestamp / 1000 + 8*3600).strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': symbol,
            'volume': volume,
            'price': price,
            'threshold_v1': threshold_v1,
            'threshold_v2_min': threshold_v2_min,
            'threshold_v2_max': threshold_v2_max,
            'exceeded': volume > threshold_v1 or (threshold_v2_min < volume <= threshold_v2_max),
            'exceeded_level': exceeded_level,  # 'V1', 'V2', 或 None
            'recorded_at': get_beijing_now_str()
        }
        
        with open(jsonl_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        level_str = f" ({exceeded_level})" if exceeded_level else ""
        print(f"[{get_beijing_now_str()}] ✅ 记录 {symbol} K线数据: {record['datetime']} 成交量: {volume/1_000_000:.2f}M{level_str}")
            
    except Exception as e:
        print(f"[{get_beijing_now_str()}] 记录成交量数据失败: {e}")


def monitor_loop():
    """主监控循环"""
    print(f"[{get_beijing_now_str()}] BTC & ETH 成交量监控启动...")
    print(f"[{get_beijing_now_str()}] 数据目录: {DATA_DIR}")
    print(f"[{get_beijing_now_str()}] Telegram Bot: {'已配置' if TELEGRAM_BOT_TOKEN else '未配置'}")
    
    while True:
        try:
            config = load_config()
            state = load_state()
            
            # 检查 BTC
            if 'BTC-USDT-SWAP' in config:
                check_volume_alert('BTC-USDT-SWAP', config['BTC-USDT-SWAP'], state)
            
            # 检查 ETH
            if 'ETH-USDT-SWAP' in config:
                check_volume_alert('ETH-USDT-SWAP', config['ETH-USDT-SWAP'], state)
            
            # 每5分钟检查一次（与K线周期对齐）
            time.sleep(300)
            
        except KeyboardInterrupt:
            print(f"\n[{get_beijing_now_str()}] 监控已停止")
            break
        except Exception as e:
            print(f"[{get_beijing_now_str()}] 监控异常: {e}")
            time.sleep(60)


if __name__ == '__main__':
    monitor_loop()
