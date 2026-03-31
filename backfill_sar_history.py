#!/usr/bin/env python3
"""
SAR 历史数据回填脚本
从 OKX API 获取历史 K 线数据，重新计算 SAR 指标
回填 2026-02-11 至 2026-03-16 的数据
"""
import sys
sys.path.insert(0, '/home/user/webapp/source_code')

import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
import pytz
import numpy as np

# 配置
DATA_DIR = Path('/home/user/webapp/data/sar_jsonl')
DATA_DIR.mkdir(parents=True, exist_ok=True)

BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 交易对列表
SYMBOLS = [
    'AAVE', 'APT', 'BCH', 'BNB', 'BTC', 'CFX', 'CRO', 'CRV', 
    'DOGE', 'DOT', 'ETC', 'ETH', 'FIL', 'HBAR', 'LDO', 'LINK', 
    'LTC', 'NEAR', 'OKB', 'SOL', 'STX', 'SUI', 'TAO', 'TON', 
    'TRX', 'UNI', 'XLM', 'XRP', 'ADA'
]

# SAR参数
SAR_AF_START = 0.02
SAR_AF_INCREMENT = 0.02
SAR_AF_MAX = 0.2

# 回填时间范围
START_DATE = datetime(2026, 2, 11, tzinfo=BEIJING_TZ)
END_DATE = datetime(2026, 3, 17, tzinfo=BEIJING_TZ)

print(f"回填时间范围: {START_DATE} 至 {END_DATE}")
print(f"币种数量: {len(SYMBOLS)}")
print("=" * 60)

def calculate_sar(high, low, close, af_start=0.02, af_increment=0.02, af_max=0.2):
    """计算SAR指标"""
    length = len(high)
    sar = np.zeros(length)
    trend = np.zeros(length)
    ep = np.zeros(length)
    af = np.zeros(length)
    
    sar[0] = low[0]
    trend[0] = 1
    ep[0] = high[0]
    af[0] = af_start
    
    for i in range(1, length):
        sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
        
        if trend[i-1] == 1:
            if low[i] < sar[i]:
                trend[i] = -1
                sar[i] = ep[i-1]
                ep[i] = low[i]
                af[i] = af_start
            else:
                trend[i] = 1
                if high[i] > ep[i-1]:
                    ep[i] = high[i]
                    af[i] = min(af[i-1] + af_increment, af_max)
                else:
                    ep[i] = ep[i-1]
                    af[i] = af[i-1]
                sar[i] = min(sar[i], low[i-1])
                if i > 1:
                    sar[i] = min(sar[i], low[i-2])
        else:
            if high[i] > sar[i]:
                trend[i] = 1
                sar[i] = ep[i-1]
                ep[i] = high[i]
                af[i] = af_start
            else:
                trend[i] = -1
                if low[i] < ep[i-1]:
                    ep[i] = low[i]
                    af[i] = min(af[i-1] + af_increment, af_max)
                else:
                    ep[i] = ep[i-1]
                    af[i] = af[i-1]
                sar[i] = max(sar[i], high[i-1])
                if i > 1:
                    sar[i] = max(sar[i], high[i-2])
    
    return sar, trend, ep, af

def get_historical_klines(symbol, start_ts, end_ts):
    """获取历史K线数据"""
    all_klines = []
    current_ts = end_ts
    
    while current_ts > start_ts:
        try:
            # 使用永续合约
            url = f"https://www.okx.com/api/v5/market/history-candles?instId={symbol}-USDT-SWAP&bar=1m&limit=100&before={int(current_ts * 1000)}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get('code') != '0' or not data.get('data'):
                # 尝试现货
                url = f"https://www.okx.com/api/v5/market/history-candles?instId={symbol}-USDT&bar=1m&limit=100&before={int(current_ts * 1000)}"
                response = requests.get(url, timeout=10)
                data = response.json()
            
            if data.get('code') == '0' and data.get('data'):
                klines = data['data']
                all_klines.extend(klines)
                
                # 更新时间戳
                if klines:
                    current_ts = float(klines[-1][0]) / 1000
                else:
                    break
                    
                time.sleep(0.2)  # 避免请求过快
            else:
                print(f"  [警告] {symbol}: API返回错误")
                break
                
        except Exception as e:
            print(f"  [错误] {symbol}: {e}")
            break
    
    return all_klines

# 主程序
total_symbols = len(SYMBOLS)
for idx, symbol in enumerate(SYMBOLS, 1):
    print(f"[{idx}/{total_symbols}] 处理 {symbol}...")
    
    try:
        # 获取历史数据
        start_ts = START_DATE.timestamp()
        end_ts = END_DATE.timestamp()
        
        klines = get_historical_klines(symbol, start_ts, end_ts)
        
        if not klines:
            print(f"  [跳过] {symbol}: 无数据")
            continue
        
        # 反转（API返回的是倒序）
        klines.reverse()
        
        # 提取OHLC
        timestamps = [float(k[0]) / 1000 for k in klines]
        opens = np.array([float(k[1]) for k in klines])
        highs = np.array([float(k[2]) for k in klines])
        lows = np.array([float(k[3]) for k in klines])
        closes = np.array([float(k[4]) for k in klines])
        volumes = [float(k[5]) for k in klines]
        
        # 计算SAR
        sar, trend, ep, af = calculate_sar(highs, lows, closes, SAR_AF_START, SAR_AF_INCREMENT, SAR_AF_MAX)
        
        # 写入文件
        jsonl_file = DATA_DIR / f'{symbol}.jsonl'
        new_records = []
        
        for i in range(len(timestamps)):
            timestamp = timestamps[i]
            beijing_time = datetime.fromtimestamp(timestamp, tz=BEIJING_TZ)
            
            # 只保存在时间范围内的
            if beijing_time < START_DATE or beijing_time > END_DATE:
                continue
            
            record = {
                'symbol': symbol,
                'beijing_time': beijing_time.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp': timestamp,
                'close': float(closes[i]),
                'sar': float(sar[i]),
                'trend': int(trend[i]),
                'ep': float(ep[i]),
                'af': float(af[i]),
                'bias': round(((closes[i] - sar[i]) / closes[i]) * 100, 2)
            }
            new_records.append(record)
        
        # 追加到文件
        with open(jsonl_file, 'a', encoding='utf-8') as f:
            for record in new_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        print(f"  [完成] {symbol}: 新增 {len(new_records)} 条记录")
        
    except Exception as e:
        print(f"  [错误] {symbol}: {e}")
        continue

print("=" * 60)
print("回填完成！")
