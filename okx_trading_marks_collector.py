#!/usr/bin/env python3
"""
OKX Trading Marks Collector - OKX日涨跌幅数据采集器
采集OKX各币种的24小时涨跌幅数据
"""
import sys
sys.path.insert(0, '/home/user/webapp/source_code')

import json
import time
import requests
from datetime import datetime
from pathlib import Path
import pytz

# 配置
DATA_DIR = Path('/home/user/webapp/data/okx_trading_jsonl')
DATA_DIR.mkdir(parents=True, exist_ok=True)

BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 交易对列表
SYMBOLS = [
    'BTC', 'ETH', 'BNB', 'XRP', 'DOGE', 
    'SOL', 'DOT', 'MATIC', 'LTC', 'LINK',
    'HBAR', 'TAO', 'CFX', 'TRX', 'TON',
    'NEAR', 'LDO', 'CRO', 'ETC', 'XLM',
    'BCH', 'UNI', 'SUI', 'FIL', 'STX',
    'CRV', 'AAVE', 'APT'
]


def get_okx_day_change():
    """从OKX获取24小时涨跌幅数据"""
    results = []
    
    try:
        for symbol in SYMBOLS:
            try:
                url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}-USDT"
                response = requests.get(url, timeout=5)
                data = response.json()
                
                if data.get('code') == '0' and data.get('data'):
                    ticker = data['data'][0]
                    
                    # 提取数据
                    record = {
                        'symbol': symbol,
                        'last_price': float(ticker.get('last', 0)),
                        'open_24h': float(ticker.get('open24h', 0)),
                        'high_24h': float(ticker.get('high24h', 0)),
                        'low_24h': float(ticker.get('low24h', 0)),
                        'vol_24h': float(ticker.get('vol24h', 0)),
                        'vol_ccy_24h': float(ticker.get('volCcy24h', 0)),
                        'change_24h': float(ticker.get('open24h', 0)) - float(ticker.get('last', 0)) if ticker.get('open24h') and ticker.get('last') else 0,
                        'change_pct_24h': float(ticker.get('last', 0)) / float(ticker.get('open24h', 1)) - 1 if ticker.get('open24h') and float(ticker.get('open24h', 0)) != 0 else 0
                    }
                    
                    # 计算正确的涨跌幅百分比
                    if record['open_24h'] > 0:
                        record['change_pct_24h'] = ((record['last_price'] - record['open_24h']) / record['open_24h']) * 100
                    else:
                        record['change_pct_24h'] = 0
                    
                    results.append(record)
                    print(f"[数据] {symbol}: {record['last_price']} ({record['change_pct_24h']:.2f}%)")
                    
                else:
                    print(f"[警告] {symbol} 数据获取失败")
                
                time.sleep(0.1)  # 避免请求过快
                
            except Exception as e:
                print(f"[错误] {symbol} 处理失败: {e}")
                continue
        
        return results
        
    except Exception as e:
        print(f"[错误] 获取OKX数据失败: {e}")
        return []


def save_to_jsonl(records):
    """保存数据到JSONL"""
    if not records:
        return
    
    jsonl_file = DATA_DIR / 'okx_day_change.jsonl'
    
    try:
        now = datetime.now(BEIJING_TZ)
        
        # 构建记录
        data_record = {
            'timestamp': int(time.time() * 1000),
            'beijing_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'data': records,
            'count': len(records)
        }
        
        # 追加写入
        with open(jsonl_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data_record, ensure_ascii=False) + '\n')
        
        print(f"[保存] 数据已写入 {jsonl_file}, 币种数: {len(records)}")
        
    except Exception as e:
        print(f"[错误] 保存JSONL失败: {e}")


def main():
    """主循环"""
    print("=" * 60)
    print("OKX日涨跌幅数据采集器启动")
    print("=" * 60)
    
    while True:
        try:
            now = datetime.now(BEIJING_TZ)
            print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] 开始采集OKX数据...")
            
            # 获取数据
            records = get_okx_day_change()
            
            if records:
                # 保存到JSONL
                save_to_jsonl(records)
                
                # 计算总涨跌幅
                total_change = sum(r['change_pct_24h'] for r in records)
                avg_change = total_change / len(records) if records else 0
                
                print(f"[统计] 总涨跌幅: {total_change:.2f}%, 平均: {avg_change:.2f}%")
            
            # 每5分钟采集一次
            print(f"[等待] 下次采集: 5分钟后")
            time.sleep(300)
            
        except KeyboardInterrupt:
            print("\n[退出] 采集器已停止")
            break
        except Exception as e:
            print(f"[错误] 采集失败: {e}")
            time.sleep(60)


if __name__ == '__main__':
    main()
