#!/usr/bin/env python3
"""
当日数据补齐脚本 - Backfill Today's Data
用于重新部署后，补齐部署期间缺失的1-2小时数据
"""
import sys
sys.path.insert(0, '/home/user/webapp/source_code')

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import pytz
import numpy as np
import time

# 配置
DATA_DIR = Path('/home/user/webapp/data/coin_change_tracker')
BASELINE_DIR = DATA_DIR
DATA_DIR.mkdir(parents=True, exist_ok=True)

BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 27个追踪的币种
SYMBOLS = [
    'BTC', 'ETH', 'BNB', 'XRP', 'DOGE', 
    'SOL', 'DOT', 'MATIC', 'LTC', 'LINK',
    'HBAR', 'TAO', 'CFX', 'TRX', 'TON',
    'NEAR', 'LDO', 'CRO', 'ETC', 'XLM',
    'BCH', 'UNI', 'SUI', 'FIL', 'STX',
    'CRV', 'AAVE', 'APT'
]


def calculate_rsi(prices, period=14):
    """计算RSI指标"""
    if len(prices) < period + 1:
        return None
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)


def get_baseline_prices(date_str):
    """获取基线价格"""
    baseline_file = BASELINE_DIR / f"baseline_{date_str}.json"
    
    if baseline_file.exists():
        with open(baseline_file, 'r') as f:
            data = json.load(f)
            return data
    return None


def get_kline_data(symbol, start_time_ms, end_time_ms):
    """
    获取指定时间范围的1分钟K线数据
    :param symbol: 币种符号
    :param start_time_ms: 开始时间戳(毫秒)
    :param end_time_ms: 结束时间戳(毫秒)
    :return: K线数据列表
    """
    try:
        # OKX API - 1分钟K线
        url = f"https://www.okx.com/api/v5/market/history-candles"
        params = {
            'instId': f'{symbol}-USDT-SWAP',
            'bar': '1m',
            'after': str(start_time_ms),
            'before': str(end_time_ms),
            'limit': 300  # 最多300根K线(5小时)
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # 如果永续合约失败，尝试现货
        if data.get('code') != '0' or not data.get('data'):
            params['instId'] = f'{symbol}-USDT'
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
        
        if data.get('code') == '0' and data.get('data'):
            # K线格式: [时间戳, 开盘价, 最高价, 最低价, 收盘价, 成交量, ...]
            # OKX返回的数据是从新到旧，需要反转
            candles = data['data']
            return list(reversed(candles))
        else:
            print(f"  ⚠️  {symbol} K线获取失败")
            return None
            
    except Exception as e:
        print(f"  ❌ {symbol} 获取K线失败: {e}")
        return None


def get_5min_candles_for_rsi(symbol, limit=20):
    """获取5分钟K线用于计算RSI"""
    try:
        url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}-USDT-SWAP&bar=5m&limit={limit}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data.get('code') != '0' or not data.get('data'):
            url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}-USDT&bar=5m&limit={limit}"
            response = requests.get(url, timeout=5)
            data = response.json()
        
        if data.get('code') == '0' and data.get('data'):
            candles = data['data']
            close_prices = [float(candle[4]) for candle in reversed(candles)]
            return close_prices
        else:
            return None
            
    except Exception as e:
        print(f"  ❌ {symbol} RSI数据获取失败: {e}")
        return None


def get_existing_timestamps(date_str):
    """获取当天已有的数据时间戳"""
    coin_file = DATA_DIR / f"coin_change_{date_str}.jsonl"
    existing_timestamps = set()
    
    if coin_file.exists():
        with open(coin_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        ts = record.get('timestamp')
                        if ts:
                            # 转换为datetime对象，只保留到分钟
                            dt = datetime.fromisoformat(ts.replace('+08:00', '')).replace(second=0, microsecond=0)
                            existing_timestamps.add(dt.isoformat())
                    except:
                        continue
    
    return existing_timestamps


def backfill_data(start_datetime, end_datetime):
    """
    补齐指定时间范围的数据
    :param start_datetime: 开始时间 (datetime对象，北京时间)
    :param end_datetime: 结束时间 (datetime对象，北京时间)
    """
    date_str = start_datetime.strftime('%Y%m%d')
    
    print(f"\n{'='*60}")
    print(f"  当日数据补齐 - {date_str}")
    print(f"{'='*60}")
    print(f"  开始时间: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  结束时间: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  时间跨度: {int((end_datetime - start_datetime).total_seconds() / 60)} 分钟")
    print(f"{'='*60}\n")
    
    # 获取基线价格
    print("📊 步骤1: 加载基线价格...")
    baseline_data = get_baseline_prices(date_str)
    if not baseline_data:
        print(f"  ❌ 未找到基线价格文件: baseline_{date_str}.json")
        print(f"  💡 提示: 请先确保基线文件存在")
        return
    
    print(f"  ✅ 基线价格已加载 ({len(baseline_data) - 2} 个币种)")
    
    # 获取已有的时间戳
    print("\n📊 步骤2: 检查已有数据...")
    existing_timestamps = get_existing_timestamps(date_str)
    print(f"  ℹ️  已有 {len(existing_timestamps)} 条记录")
    
    # 转换时间为毫秒时间戳
    start_ms = int(start_datetime.timestamp() * 1000)
    end_ms = int(end_datetime.timestamp() * 1000)
    
    # 为每个币种获取K线数据
    print(f"\n📊 步骤3: 获取 {len(SYMBOLS)} 个币种的K线数据...")
    print("  (每个币种需要1-2秒，请耐心等待...)\n")
    
    symbol_klines = {}
    for i, symbol in enumerate(SYMBOLS, 1):
        print(f"  [{i:2d}/{len(SYMBOLS)}] {symbol:8s} ", end='', flush=True)
        klines = get_kline_data(symbol, start_ms, end_ms)
        if klines:
            symbol_klines[symbol] = klines
            print(f"✅ {len(klines)} 根K线")
        else:
            print(f"⚠️  无数据")
        time.sleep(0.5)  # 避免API限流
    
    if not symbol_klines:
        print("\n  ❌ 所有币种K线获取失败")
        return
    
    print(f"\n  ✅ 成功获取 {len(symbol_klines)}/{len(SYMBOLS)} 个币种的数据")
    
    # 构建时间序列数据
    print("\n📊 步骤4: 构建时间序列数据...")
    
    # 找出所有的时间戳
    all_timestamps = set()
    for klines in symbol_klines.values():
        for candle in klines:
            ts = int(candle[0])  # K线时间戳
            dt = datetime.fromtimestamp(ts / 1000, tz=BEIJING_TZ).replace(second=0, microsecond=0)
            all_timestamps.add(dt)
    
    all_timestamps = sorted(all_timestamps)
    print(f"  ℹ️  共找到 {len(all_timestamps)} 个时间点")
    
    # 过滤出需要补齐的时间点
    timestamps_to_fill = []
    for dt in all_timestamps:
        dt_iso = dt.isoformat().replace('+08:00', '')
        if dt_iso not in existing_timestamps:
            timestamps_to_fill.append(dt)
    
    print(f"  ℹ️  需要补齐 {len(timestamps_to_fill)} 个时间点")
    
    if not timestamps_to_fill:
        print("\n✅ 无需补齐，数据已完整!")
        return
    
    # 准备文件
    coin_file = DATA_DIR / f"coin_change_{date_str}.jsonl"
    rsi_file = DATA_DIR / f"rsi_{date_str}.jsonl"
    
    # 补齐数据
    print("\n📊 步骤5: 写入补齐数据...")
    filled_count = 0
    
    with open(coin_file, 'a') as f_coin, open(rsi_file, 'a') as f_rsi:
        for dt in timestamps_to_fill:
            # 构建币种涨跌数据
            coin_record = {
                'timestamp': dt.isoformat()
            }
            
            # 为每个币种找到对应的价格
            for symbol in SYMBOLS:
                if symbol not in symbol_klines:
                    continue
                
                # 在K线数据中找到最接近的时间点
                target_ts = int(dt.timestamp() * 1000)
                closest_candle = None
                min_diff = float('inf')
                
                for candle in symbol_klines[symbol]:
                    candle_ts = int(candle[0])
                    diff = abs(candle_ts - target_ts)
                    if diff < min_diff:
                        min_diff = diff
                        closest_candle = candle
                
                if closest_candle and min_diff < 60000:  # 1分钟内
                    close_price = float(closest_candle[4])
                    baseline_price = baseline_data.get(symbol)
                    
                    if baseline_price:
                        change_pct = ((close_price - baseline_price) / baseline_price) * 100
                        coin_record[symbol] = round(change_pct, 2)
            
            # 只写入有数据的记录
            if len(coin_record) > 1:  # 除了timestamp还有其他字段
                f_coin.write(json.dumps(coin_record, ensure_ascii=False) + '\n')
                filled_count += 1
                
                # 获取RSI数据
                rsi_record = {
                    'timestamp': dt.isoformat()
                }
                
                for symbol in SYMBOLS:
                    if symbol in coin_record:
                        # 获取5分钟K线计算RSI
                        close_prices = get_5min_candles_for_rsi(symbol, limit=20)
                        if close_prices:
                            rsi = calculate_rsi(close_prices)
                            if rsi is not None:
                                rsi_record[f'{symbol}_rsi'] = rsi
                
                if len(rsi_record) > 1:
                    f_rsi.write(json.dumps(rsi_record, ensure_ascii=False) + '\n')
            
            if filled_count % 10 == 0:
                print(f"  ✓ 已补齐 {filled_count}/{len(timestamps_to_fill)} 条记录")
    
    print(f"\n{'='*60}")
    print(f"  ✅ 补齐完成!")
    print(f"{'='*60}")
    print(f"  新增记录: {filled_count} 条")
    print(f"  涨跌文件: {coin_file}")
    print(f"  RSI文件: {rsi_file}")
    print(f"{'='*60}\n")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  27币追踪系统 - 当日数据补齐工具")
    print("  用途: 补齐重新部署期间缺失的1-2小时数据")
    print("="*60)
    
    # 获取当前北京时间
    now = datetime.now(BEIJING_TZ)
    date_str = now.strftime('%Y%m%d')
    
    print(f"\n当前北京时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标日期: {date_str}")
    
    # 询问用户补齐的时间范围
    print("\n" + "-"*60)
    print("请输入需要补齐的时间范围:")
    print("-"*60)
    
    # 默认补齐最近2小时
    default_start = (now - timedelta(hours=2)).replace(second=0, microsecond=0)
    default_end = now.replace(second=0, microsecond=0)
    
    start_input = input(f"\n开始时间 (格式: HH:MM, 默认 {default_start.strftime('%H:%M')}): ").strip()
    if not start_input:
        start_time = default_start
    else:
        try:
            hour, minute = map(int, start_input.split(':'))
            start_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except:
            print("  ⚠️  时间格式错误，使用默认值")
            start_time = default_start
    
    end_input = input(f"结束时间 (格式: HH:MM, 默认 {default_end.strftime('%H:%M')}): ").strip()
    if not end_input:
        end_time = default_end
    else:
        try:
            hour, minute = map(int, end_input.split(':'))
            end_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except:
            print("  ⚠️  时间格式错误，使用默认值")
            end_time = default_end
    
    # 验证时间范围
    if end_time <= start_time:
        print("\n  ❌ 错误: 结束时间必须晚于开始时间")
        return
    
    duration_minutes = int((end_time - start_time).total_seconds() / 60)
    if duration_minutes > 300:  # 5小时
        print(f"\n  ⚠️  警告: 时间跨度过大 ({duration_minutes} 分钟)")
        confirm = input("  是否继续? (y/N): ").strip().lower()
        if confirm != 'y':
            print("  已取消")
            return
    
    # 开始补齐
    backfill_data(start_time, end_time)


if __name__ == '__main__':
    main()
