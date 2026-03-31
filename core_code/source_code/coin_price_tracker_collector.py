#!/usr/bin/env python3
"""
27币种价格追踪采集器
每30分钟采集一次，记录27个主流币种相对于当天00:00基准价的涨跌幅
"""

import json
import time
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

# 数据目录
DATA_DIR = Path('/home/user/webapp/data/coin_price_tracker')
JSONL_FILE = DATA_DIR / 'coin_prices_30min.jsonl'

# 27个追踪的币种（USDT交易对）
TRACKED_COINS = [
    'BTC', 'ETH', 'XRP', 'BNB', 'SOL', 'LTC', 'DOGE', 'SUI', 'TRX',
    'TON', 'ETC', 'BCH', 'HBAR', 'XLM', 'FIL', 'LINK', 'CRO', 'DOT',
    'UNI', 'NEAR', 'APT', 'CFX', 'CRV', 'STX', 'LDO', 'TAO', 'AAVE'
]

# OKX API base URL
OKX_API_BASE = 'https://www.okx.com/api/v5'


def get_beijing_time():
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)


def get_today_base_date():
    """获取今天的日期字符串（北京时间）"""
    return get_beijing_time().strftime('%Y-%m-%d')


def load_base_prices():
    """
    加载今天的基准价格（00:00价格）
    如果是新的一天，返回None表示需要重新获取基准价
    """
    base_file = DATA_DIR / 'base_prices.json'
    today = get_today_base_date()
    
    if not base_file.exists():
        return None, today
    
    try:
        with open(base_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查日期是否为今天
        if data.get('base_date') == today:
            return data.get('prices', {}), today
        else:
            # 新的一天，需要重新获取基准价
            return None, today
    except:
        return None, today


def save_base_prices(prices, base_date):
    """保存今天的基准价格"""
    base_file = DATA_DIR / 'base_prices.json'
    data = {
        'base_date': base_date,
        'prices': prices,
        'updated_at': get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')
    }
    with open(base_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存今天的基准价格 ({base_date})")


def get_okx_price(symbol):
    """
    从OKX获取币种的当前价格
    symbol: 例如 'BTC-USDT-SWAP'
    """
    try:
        url = f"{OKX_API_BASE}/market/ticker"
        params = {'instId': symbol}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('code') == '0' and data.get('data'):
            return float(data['data'][0]['last'])
        return None
    except Exception as e:
        print(f"❌ 获取 {symbol} 价格失败: {e}")
        return None


def collect_prices():
    """采集27个币种的当前价格"""
    prices = {}
    success_count = 0
    failed_count = 0
    
    for coin in TRACKED_COINS:
        symbol = f"{coin}-USDT-SWAP"
        price = get_okx_price(symbol)
        
        if price:
            prices[coin] = price
            success_count += 1
            print(f"✅ {coin}: ${price}")
        else:
            failed_count += 1
            print(f"❌ {coin}: 获取失败")
        
        # 避免请求过快
        time.sleep(0.1)
    
    return prices, success_count, failed_count


def calculate_changes(current_prices, base_prices):
    """计算涨跌幅"""
    day_changes = {}
    total_change = 0
    valid_count = 0
    
    for coin in TRACKED_COINS:
        if coin in current_prices and coin in base_prices:
            base = base_prices[coin]
            current = current_prices[coin]
            change_pct = ((current - base) / base) * 100
            
            day_changes[coin] = {
                'base_price': round(base, 4) if base < 10 else round(base, 2),
                'current_price': round(current, 4) if current < 10 else round(current, 2),
                'change_pct': round(change_pct, 4)
            }
            
            total_change += change_pct
            valid_count += 1
    
    average_change = total_change / valid_count if valid_count > 0 else 0
    
    return day_changes, total_change, average_change, valid_count


def save_to_jsonl(record):
    """保存记录到JSONL文件"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(JSONL_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def main():
    """主函数 - 采集并保存数据"""
    print(f"\n{'='*60}")
    print(f"🕐 开始采集 - {get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 获取当前时间
    now = get_beijing_time()
    collect_time = now.strftime('%Y-%m-%d %H:%M:%S')
    timestamp = int(now.timestamp())
    base_date = get_today_base_date()
    
    # 加载或初始化基准价格
    base_prices, today = load_base_prices()
    
    # 如果是新的一天或基准价不存在，获取当前价格作为基准价
    if base_prices is None:
        print("📍 获取今天的基准价格...")
        base_prices, success, failed = collect_prices()
        if base_prices:
            save_base_prices(base_prices, today)
        print(f"✅ 基准价格获取完成: {success}成功, {failed}失败\n")
    
    # 获取当前价格
    print("📊 获取当前价格...")
    current_prices, success_count, failed_count = collect_prices()
    
    # 计算涨跌幅
    day_changes, total_change, average_change, valid_count = calculate_changes(
        current_prices, base_prices
    )
    
    # 构建记录
    record = {
        'collect_time': collect_time,
        'timestamp': timestamp,
        'base_date': base_date,
        'day_changes': day_changes,
        'total_change': round(total_change, 3),
        'average_change': round(average_change, 4),
        'total_coins': len(TRACKED_COINS),
        'valid_coins': valid_count,
        'success_count': success_count,
        'failed_count': failed_count
    }
    
    # 保存到文件
    save_to_jsonl(record)
    
    print(f"\n{'='*60}")
    print(f"✅ 采集完成")
    print(f"📊 统计: {valid_count}/{len(TRACKED_COINS)} 有效币种")
    print(f"📈 总涨跌: {total_change:+.2f}%")
    print(f"📊 平均涨跌: {average_change:+.4f}%")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    # 首次启动时先执行一次
    main()
    
    # 每30分钟执行一次
    print("🔄 进入定时采集模式（每30分钟）...")
    while True:
        try:
            time.sleep(30 * 60)  # 30分钟
            main()
        except KeyboardInterrupt:
            print("\n⚠️ 收到退出信号，停止采集")
            break
        except Exception as e:
            print(f"\n❌ 采集异常: {e}")
            print("⏳ 30秒后重试...")
            time.sleep(30)
