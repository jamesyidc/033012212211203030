#!/usr/bin/env python3
"""
Backfill Panic Historical Data - 回填恐慌指数历史数据
从btc126.com的30天API回填历史数据
"""
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# 配置
DATA_DIR = Path('/home/user/webapp/data/panic_jsonl')
DATA_DIR.mkdir(parents=True, exist_ok=True)

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
BTC126_API_URL = 'https://api.btc126.com/bicoin.php'
DATA_FILE = DATA_DIR / 'panic_wash_index.jsonl'


def get_30day_history():
    """获取30天历史数据"""
    try:
        timestamp = int(time.time() * 1000)
        url = f"{BTC126_API_URL}?from=30daybaocang&t={timestamp}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://history.btc126.com/baocang/'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data.get('code') == 0 and data.get('data'):
            return data['data']['list']
        return None
    except Exception as e:
        print(f"[错误] 获取30天历史数据失败: {e}")
        return None


def get_okx_market_data(symbol):
    """获取OKX市场数据"""
    try:
        url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}-USDT-SWAP"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data['code'] == '0' and data['data']:
            ticker = data['data'][0]
            return {
                'last': float(ticker['last']),
                'open24h': float(ticker['open24h']),
                'high24h': float(ticker['high24h']),
                'low24h': float(ticker['low24h']),
                'vol24h': float(ticker['vol24h']),
                'change_pct': round((float(ticker['last']) - float(ticker['open24h'])) / float(ticker['open24h']) * 100, 2)
            }
    except:
        pass
    return None


def calculate_panic_index(change_pct_sum, avg_volatility):
    """计算恐慌指数"""
    panic_index = abs(change_pct_sum) + (avg_volatility * 0.5)
    return round(panic_index, 2)


def backfill_historical_data():
    """回填历史数据"""
    print("=" * 60)
    print("开始回填恐慌指数历史数据...")
    print("=" * 60)
    
    # 获取30天历史数据
    history = get_30day_history()
    if not history:
        print("[错误] 无法获取历史数据")
        return
    
    print(f"\n[成功] 获取到 {len(history)} 天的历史数据")
    
    # 读取现有数据，检查哪些日期已存在
    existing_dates = set()
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        date = data.get('beijing_time', '').split()[0]
                        if date:
                            existing_dates.add(date)
                    except:
                        pass
    
    print(f"[信息] 已存在 {len(existing_dates)} 个日期的数据")
    
    # 准备回填的记录
    backfill_records = []
    
    for item in history:
        date_str = item.get('dateStr', '')
        if not date_str:
            continue
        
        # 检查是否已存在
        if date_str in existing_dates:
            print(f"[跳过] {date_str} - 数据已存在")
            continue
        
        # 计算总爆仓金额
        buy_amount = item.get('buyAmount', 0)
        sell_amount = item.get('sellAmount', 0)
        total_24h = buy_amount + sell_amount
        
        # 估算1小时爆仓（24小时的1/24）
        total_1h = total_24h / 24
        
        # 估算爆仓人数（基于金额）
        liquidation_count = total_24h / 10000  # 假设每人平均1万美元
        
        # 为该日期创建一个合理的时间戳（北京时间中午12:00）
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            date_obj = date_obj.replace(hour=12, minute=0, second=0)
            beijing_time = BEIJING_TZ.localize(date_obj)
            timestamp = int(beijing_time.timestamp() * 1000)
        except:
            continue
        
        # 获取该日期的市场数据（使用当前数据作为示例）
        market_data = {}
        for symbol in ['BTC', 'ETH', 'BNB', 'XRP', 'SOL']:
            data = get_okx_market_data(symbol)
            if data:
                market_data[symbol] = data
            time.sleep(0.1)
        
        # 计算恐慌指数
        if market_data:
            total_change = sum(d['change_pct'] for d in market_data.values())
            volatilities = [(d['high24h'] - d['low24h']) / d['low24h'] * 100 for d in market_data.values()]
            avg_volatility = sum(volatilities) / len(volatilities) if volatilities else 0
            panic_index = calculate_panic_index(total_change, avg_volatility)
        else:
            # 如果无法获取市场数据，基于爆仓金额估算恐慌指数
            # 爆仓金额越大，恐慌指数越高
            panic_index = min(100, round(total_24h / 10000000, 2))  # 每1千万美元对应1个指数点
        
        # 创建记录
        record = {
            'timestamp': timestamp,
            'beijing_time': date_obj.strftime('%Y-%m-%d %H:%M:%S'),
            'panic_index': panic_index,
            'market_data': market_data,
            'liquidation_data': {
                'liquidation_1h': round(total_1h / 10000, 2),  # 万美元
                'liquidation_24h': round(total_24h / 10000, 2),  # 万美元
                'liquidation_count_24h': round(liquidation_count / 10000, 2),  # 万人
                'open_interest': 0.0  # 历史数据无法获取持仓量
            },
            'level': 'high' if panic_index > 10 else 'medium' if panic_index > 5 else 'low'
        }
        
        backfill_records.append(record)
        print(f"[准备] {date_str} - 24h爆仓: {record['liquidation_data']['liquidation_24h']}万$, 恐慌指数: {panic_index}")
    
    # 按时间排序
    backfill_records.sort(key=lambda x: x['timestamp'])
    
    # 写入文件
    if backfill_records:
        print(f"\n[写入] 准备写入 {len(backfill_records)} 条历史记录...")
        
        # 读取现有数据
        existing_records = []
        if DATA_FILE.exists():
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            existing_records.append(json.loads(line))
                        except:
                            pass
        
        # 合并并排序
        all_records = existing_records + backfill_records
        all_records.sort(key=lambda x: x.get('timestamp', 0))
        
        # 写入所有记录
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            for record in all_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        print(f"[完成] 成功写入 {len(backfill_records)} 条历史记录")
        print(f"[完成] 数据文件总记录数: {len(all_records)}")
    else:
        print("\n[信息] 没有需要回填的数据")
    
    print("\n" + "=" * 60)
    print("回填完成！")
    print("=" * 60)


if __name__ == '__main__':
    backfill_historical_data()
