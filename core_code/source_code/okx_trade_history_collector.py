#!/usr/bin/env python3
"""
OKX Trade History Collector - OKX交易历史采集器
实时采集主账户的成交历史并写入JSONL
"""
import sys
sys.path.insert(0, '/home/user/webapp/source_code')

import json
import time
import hmac
import hashlib
import base64
import requests
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# 配置
DATA_DIR = Path('/home/user/webapp/data/okx_trading_history')
DATA_DIR.mkdir(parents=True, exist_ok=True)

BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 主账户API配置
API_KEY = 'd6b272da-b59e-4ca3-97bd-663102f981b3'
API_SECRET = '5D76ACDE6D74CF07842661385E12C61E'
PASSPHRASE = 'Tencent@123'

# OKX API配置
API_BASE = 'https://www.okx.com'
COLLECT_INTERVAL = 5 * 60  # 5分钟采集一次


def okx_signature(timestamp, method, request_path, body=''):
    """生成OKX API签名"""
    message = timestamp + method + request_path + body
    mac = hmac.new(
        bytes(API_SECRET, encoding='utf8'),
        bytes(message, encoding='utf-8'),
        digestmod=hashlib.sha256
    )
    return base64.b64encode(mac.digest()).decode()


def get_okx_fills(inst_type='SWAP', limit=100):
    """获取最近的成交记录"""
    try:
        timestamp = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
        method = 'GET'
        request_path = f'/api/v5/trade/fills?instType={inst_type}&limit={limit}'
        
        headers = {
            'OK-ACCESS-KEY': API_KEY,
            'OK-ACCESS-SIGN': okx_signature(timestamp, method, request_path),
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': PASSPHRASE,
            'Content-Type': 'application/json'
        }
        
        url = API_BASE + request_path
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data.get('code') == '0' and data.get('data'):
            return data['data']
        else:
            print(f'[错误] OKX API返回: {data}')
            return []
            
    except Exception as e:
        print(f'[错误] 获取成交记录失败: {e}')
        return []


def save_trades_to_jsonl(trades):
    """保存交易到JSONL文件（按日期分文件）"""
    if not trades:
        return 0
    
    # 按日期分组
    trades_by_date = {}
    
    for trade in trades:
        # fillTime是时间戳（毫秒）
        fill_time_ms = int(trade.get('fillTime', 0))
        if fill_time_ms == 0:
            continue
        
        # 转换为北京时间
        fill_dt = datetime.fromtimestamp(fill_time_ms / 1000, tz=BEIJING_TZ)
        date_str = fill_dt.strftime('%Y%m%d')
        
        # 添加可读的时间字段
        trade['fillTime_str'] = fill_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        if date_str not in trades_by_date:
            trades_by_date[date_str] = []
        
        trades_by_date[date_str].append(trade)
    
    # 保存到对应日期的文件
    total_saved = 0
    
    for date_str, date_trades in trades_by_date.items():
        file_path = DATA_DIR / f'okx_trades_{date_str}.jsonl'
        
        # 读取已有的交易ID
        existing_ids = set()
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            existing_trade = json.loads(line)
                            trade_id = existing_trade.get('tradeId', '')
                            if trade_id:
                                existing_ids.add(trade_id)
                        except:
                            continue
        
        # 只写入新的交易
        new_trades = [t for t in date_trades if t.get('tradeId') not in existing_ids]
        
        if new_trades:
            with open(file_path, 'a', encoding='utf-8') as f:
                for trade in new_trades:
                    f.write(json.dumps(trade, ensure_ascii=False) + '\n')
            
            total_saved += len(new_trades)
            print(f'[保存] {date_str}: 新增 {len(new_trades)} 笔交易')
    
    return total_saved


def main():
    """主循环"""
    print('=' * 60)
    print('OKX交易历史采集器启动')
    print(f'数据目录: {DATA_DIR}')
    print(f'采集间隔: {COLLECT_INTERVAL}秒')
    print('=' * 60)
    print()
    
    while True:
        try:
            now = datetime.now(BEIJING_TZ)
            print(f'[{now.strftime("%Y-%m-%d %H:%M:%S")}] 开始采集交易历史...')
            
            # 获取永续合约的成交记录
            fills_swap = get_okx_fills(inst_type='SWAP', limit=100)
            print(f'[SWAP] 获取到 {len(fills_swap)} 笔成交')
            
            # 获取现货的成交记录
            fills_spot = get_okx_fills(inst_type='SPOT', limit=100)
            print(f'[SPOT] 获取到 {len(fills_spot)} 笔成交')
            
            # 合并并保存
            all_fills = fills_swap + fills_spot
            saved_count = save_trades_to_jsonl(all_fills)
            
            print(f'[完成] 共保存 {saved_count} 笔新交易')
            print(f'[等待] 下次采集: {COLLECT_INTERVAL}秒后')
            print()
            
            time.sleep(COLLECT_INTERVAL)
            
        except KeyboardInterrupt:
            print('\n[停止] 采集器已停止')
            break
        except Exception as e:
            print(f'[错误] 采集失败: {e}')
            time.sleep(60)  # 出错后等待1分钟再试


if __name__ == '__main__':
    main()
