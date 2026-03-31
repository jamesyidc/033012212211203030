#!/usr/bin/env python3
"""
10分钟涨速统计采集器
Price Speed 10-Minute Statistics Collector

功能：
1. 获取28种币的实时价格
2. 计算10分钟涨速（与10分钟前价格对比）
3. 统计涨速分布（+4%, +1%, -1%, -3%等区间）
4. 按日期存储为JSONL文件

采集间隔：3分钟（与其他采集器同步）
数据存储：data/price_speed_10m/price_speed_10m_YYYYMMDD.jsonl
"""

import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

import ccxt

# 配置
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data' / 'price_speed_10m'
COLLECT_INTERVAL = 180  # 3分钟

# 创建数据目录
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 28种监控币种
SYMBOLS = [
    'BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'SOL-USDT-SWAP', 'BNB-USDT-SWAP',
    'XRP-USDT-SWAP', 'ADA-USDT-SWAP', 'DOGE-USDT-SWAP', 'TRX-USDT-SWAP',
    'DOT-USDT-SWAP', 'LTC-USDT-SWAP', 'BCH-USDT-SWAP', 'LINK-USDT-SWAP',
    'UNI-USDT-SWAP', 'FIL-USDT-SWAP', 'ETC-USDT-SWAP', 'AAVE-USDT-SWAP',
    'CRV-USDT-SWAP', 'NEAR-USDT-SWAP', 'APT-USDT-SWAP', 'STX-USDT-SWAP',
    'LDO-USDT-SWAP', 'OKB-USDT-SWAP', 'CRO-USDT-SWAP', 'HBAR-USDT-SWAP',
    'TON-USDT-SWAP', 'TAO-USDT-SWAP', 'SUI-USDT-SWAP', 'XLM-USDT-SWAP'
]

def get_okx_exchange():
    """创建OKX交易所实例"""
    return ccxt.okx({
        'enableRateLimit': True,
        'timeout': 30000,
    })

def get_beijing_time():
    """获取北京时间"""
    beijing_tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(beijing_tz)

def calculate_10m_speed(exchange, symbol):
    """
    计算10分钟涨速
    
    返回：
    {
        'symbol': 'BTC',
        'current_price': 50000.0,
        'price_10m_ago': 49500.0,
        'speed_10m': 1.01,  # 百分比
        'category': '+1%'    # 涨速分类
    }
    """
    try:
        # 获取当前价格
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        
        # 获取10分钟K线（1分钟级别，10根）
        klines = exchange.fetch_ohlcv(symbol, '1m', limit=11)
        if len(klines) < 11:
            return None
        
        # 10分钟前的价格（使用11根K线前的收盘价）
        price_10m_ago = klines[0][4]  # 第一根K线的收盘价
        
        # 计算涨速百分比
        if price_10m_ago == 0:
            return None
        
        speed_10m = ((current_price - price_10m_ago) / price_10m_ago) * 100
        
        # 分类涨速（正确区间）
        # +4%: ≥ +4%
        # +1%: +1% ≤ speed < +4%
        # 0%:  -1% < speed < +1%
        # -1%: -3% < speed ≤ -1%
        # -3%: ≤ -3%
        if speed_10m >= 4:
            category = '+4%'
        elif speed_10m >= 1:
            category = '+1%'
        elif speed_10m > -1:
            category = '0%'
        elif speed_10m > -3:
            category = '-1%'
        else:
            category = '-3%'
        
        symbol_name = symbol.replace('-USDT-SWAP', '')
        
        return {
            'symbol': symbol_name,
            'current_price': round(current_price, 6),
            'price_10m_ago': round(price_10m_ago, 6),
            'speed_10m': round(speed_10m, 3),
            'category': category
        }
        
    except Exception as e:
        print(f"  ✗ {symbol} 计算涨速失败: {e}")
        return None

def calculate_daily_counts(existing_data, new_results):
    """
    计算每个币种当天在各涨速区间出现的次数
    
    参数：
    - existing_data: 今天已有的历史数据（不包含当前这次采集）
    - new_results: 当前这次采集的数据
    
    返回：
    {
        'BTC': {'+4%': 0, '+1%': 5, '-1%': 2, '-3%': 0},
        'ETH': {'+4%': 1, '+1%': 3, '-1%': 4, '-3%': 0},
        ...
    }
    """
    daily_counts = {}
    
    # 初始化所有币种的计数器
    for symbol in SYMBOLS:
        coin_name = symbol.replace('-USDT-SWAP', '')
        daily_counts[coin_name] = {
            '+4%': 0,
            '+1%': 0,
            '-1%': 0,
            '-3%': 0
        }
    
    # 统计历史数据中的涨速区间次数（不包含当前这次）
    for entry in existing_data:
        for coin_data in entry.get('coins', []):
            symbol = coin_data.get('symbol')
            category = coin_data.get('category', '0%')
            
            if symbol in daily_counts:
                # 根据category累加对应区间的计数
                if category == '+4%':
                    daily_counts[symbol]['+4%'] += 1
                elif category == '+1%':
                    daily_counts[symbol]['+1%'] += 1
                elif category == '-1%':
                    daily_counts[symbol]['-1%'] += 1
                elif category == '-3%':
                    daily_counts[symbol]['-3%'] += 1
    
    # 累加当前采集的数据
    for coin_data in new_results:
        symbol = coin_data.get('symbol')
        category = coin_data.get('category', '0%')
        
        if symbol in daily_counts:
            if category == '+4%':
                daily_counts[symbol]['+4%'] += 1
            elif category == '+1%':
                daily_counts[symbol]['+1%'] += 1
            elif category == '-1%':
                daily_counts[symbol]['-1%'] += 1
            elif category == '-3%':
                daily_counts[symbol]['-3%'] += 1
    
    return daily_counts

def collect_speed_data():
    """采集所有币种的10分钟涨速"""
    beijing_time = get_beijing_time()
    time_str = beijing_time.strftime('%Y-%m-%d %H:%M:%S')
    date_str = beijing_time.strftime('%Y%m%d')
    
    print(f"\n{'='*60}")
    print(f"开始采集10分钟涨速 - {time_str}")
    print(f"{'='*60}")
    
    exchange = get_okx_exchange()
    
    results = []
    categories_count = {
        '+4%': 0,
        '+1%': 0,
        '0%': 0,
        '-1%': 0,
        '-3%': 0
    }
    
    for symbol in SYMBOLS:
        speed_data = calculate_10m_speed(exchange, symbol)
        if speed_data:
            results.append(speed_data)
            categories_count[speed_data['category']] += 1
            
            # 显示带颜色的涨速
            speed = speed_data['speed_10m']
            if speed >= 4:
                color = '🔴'
            elif speed >= 1:
                color = '🟢'
            elif speed >= -1:
                color = '⚪'
            elif speed >= -3:
                color = '🟡'
            else:
                color = '🔵'
            
            print(f"  {color} {speed_data['symbol']:6s} | "
                  f"当前: ${speed_data['current_price']:>10.6f} | "
                  f"10分钟前: ${speed_data['price_10m_ago']:>10.6f} | "
                  f"涨速: {speed:>6.2f}% | "
                  f"分类: {speed_data['category']}")
        
        time.sleep(0.1)  # 避免频率限制
    
    print(f"\n📊 涨速分布统计:")
    print(f"  🔴 +4%及以上: {categories_count['+4%']} 个")
    print(f"  🟢 +1%~+4%:   {categories_count['+1%']} 个")
    print(f"  ⚪ -1%~+1%:   {categories_count['0%']} 个")
    print(f"  🟡 -1%~-3%:   {categories_count['-1%']} 个")
    print(f"  🔵 -3%及以下: {categories_count['-3%']} 个")
    
    # 读取今天已有的数据以计算累计统计
    file_path = DATA_DIR / f'price_speed_10m_{date_str}.jsonl'
    existing_data = []
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    existing_data.append(json.loads(line))
    
    # 计算每个币种的当日累计次数
    daily_counts = calculate_daily_counts(existing_data, results)
    
    # 保存数据
    entry = {
        'time': time_str,
        'coins': results,
        'statistics': categories_count,
        'total_coins': len(results),
        'daily_counts': daily_counts  # 新增：每个币种的当日统计
    }
    
    save_to_jsonl(entry, date_str)
    
    return entry

def save_to_jsonl(entry, date_str):
    """保存数据到JSONL文件"""
    file_path = DATA_DIR / f'price_speed_10m_{date_str}.jsonl'
    
    try:
        # 读取今天已有的数据
        existing_data = []
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        existing_data.append(json.loads(line))
        
        # 检查是否已有相同时间的数据（去重）
        entry_time = entry['time']
        existing_data = [d for d in existing_data if d['time'] != entry_time]
        
        # 添加新数据（新数据已经包含正确的daily_counts）
        existing_data.append(entry)
        
        # 按时间排序
        existing_data.sort(key=lambda x: x['time'])
        
        # 完整覆盖写入（保留每条记录自己的daily_counts，不要修改历史记录）
        with open(file_path, 'w', encoding='utf-8') as f:
            for data in existing_data:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        print(f"\n✅ 数据已保存: {file_path}")
        print(f"   总计: {len(existing_data)} 条记录")
        
    except Exception as e:
        print(f"\n✗ 保存数据失败: {e}")
        import traceback
        traceback.print_exc()
        
    except Exception as e:
        print(f"\n✗ 保存数据失败: {e}")
        import traceback
        traceback.print_exc()

def backfill_today():
    """回填今天的历史数据（一次性运行）"""
    print("\n🔄 回填今天的10分钟涨速数据...")
    collect_speed_data()
    print("✅ 回填完成")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='10分钟涨速统计采集器')
    parser.add_argument('--backfill', action='store_true',
                       help='回填今天的数据（一次性运行）')
    parser.add_argument('--daemon', action='store_true',
                       help='后台运行模式（持续采集）')
    
    args = parser.parse_args()
    
    if args.backfill:
        backfill_today()
    elif args.daemon:
        print("10分钟涨速采集器启动")
        print(f"数据目录: {DATA_DIR}")
        print(f"采集间隔: {COLLECT_INTERVAL} 秒")
        
        while True:
            try:
                collect_speed_data()
                next_time = get_beijing_time() + timedelta(seconds=COLLECT_INTERVAL)
                print(f"\n下次采集时间: {next_time.strftime('%H:%M:%S')}")
                print("等待中...")
                time.sleep(COLLECT_INTERVAL)
            except KeyboardInterrupt:
                print("\n收到停止信号，退出...")
                break
            except Exception as e:
                print(f"采集出错: {e}")
                import traceback
                traceback.print_exc()
                print(f"等待 {COLLECT_INTERVAL} 秒后重试...")
                time.sleep(COLLECT_INTERVAL)
    else:
        print("单次运行模式 - 采集当前数据")
        collect_speed_data()
        print("\n提示: 使用 --backfill 回填今天数据，使用 --daemon 持续运行")

if __name__ == '__main__':
    main()
