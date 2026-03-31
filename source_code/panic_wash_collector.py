#!/usr/bin/env python3
"""
Panic Wash Index Collector - 恐慌洗盘指数采集器
从 btc126.com 采集真实的爆仓数据
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
DATA_DIR = Path('/home/user/webapp/data/panic_jsonl')
DATA_DIR.mkdir(parents=True, exist_ok=True)

BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# BTC126 API配置
BTC126_API_URL = 'https://api.btc126.com/bicoin.php'

# 主要监控币种
SYMBOLS = ['BTC', 'ETH', 'BNB', 'XRP', 'SOL']


def get_btc126_liquidation_data():
    """从btc126获取真实的爆仓数据"""
    try:
        # 添加时间戳避免缓存
        timestamp = int(time.time() * 1000)
        url = f"{BTC126_API_URL}?from=24hbaocang&t={timestamp}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://history.btc126.com/baocang/'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data.get('code') == 0 and data.get('data'):
            liquidation_info = data['data']
            
            # 提取关键数据
            liquidation_data = {
                'liquidation_1h': round(liquidation_info.get('totalBlastUsd1h', 0) / 10000, 2),  # 转换为万美元
                'liquidation_24h': round(liquidation_info.get('totalBlastUsd24h', 0) / 10000, 2),  # 转换为万美元
                'liquidation_count_24h': round(liquidation_info.get('totalBlastNum24h', 0) / 10000, 2),  # 转换为万人
                'update_time': liquidation_info.get('updateTime', 0)
            }
            
            print(f"[BTC126] 1h爆仓: {liquidation_data['liquidation_1h']}万$")
            print(f"[BTC126] 24h爆仓: {liquidation_data['liquidation_24h']}万$")
            print(f"[BTC126] 24h爆仓人数: {liquidation_data['liquidation_count_24h']}万人")
            
            return liquidation_data
        else:
            print(f"[错误] BTC126 API返回错误: {data}")
            return None
            
    except Exception as e:
        print(f"[错误] 获取BTC126爆仓数据失败: {e}")
        return None


def get_btc126_open_interest():
    """从btc126获取全网持仓量数据"""
    try:
        timestamp = int(time.time() * 1000)
        url = f"{BTC126_API_URL}?from=realhold&t={timestamp}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://history.btc126.com/baocang/'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data.get('code') == 0 and data.get('data'):
            hold_data_list = data['data']
            
            # 找到全网总计的数据
            for item in hold_data_list:
                if '全网总计' in item.get('exchange', '') or 'Net total' in item.get('exchangeOtherName', ''):
                    total_amount = item.get('amount', 0)
                    open_interest_yi = round(total_amount / 100000000, 2)  # 转换为亿美元
                    print(f"[BTC126] 全网持仓: {open_interest_yi}亿$")
                    return open_interest_yi
            
            # 如果没找到全网总计，累加所有交易所
            total_open_interest = sum(item.get('amount', 0) for item in hold_data_list)
            open_interest_yi = round(total_open_interest / 100000000, 2)
            print(f"[BTC126] 全网持仓: {open_interest_yi}亿$")
            return open_interest_yi
        else:
            return 0
            
    except Exception as e:
        print(f"[错误] 获取BTC126持仓数据失败: {e}")
        return 0


def get_market_data():
    """获取市场数据"""
    market_data = {}
    
    try:
        for symbol in SYMBOLS:
            try:
                url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}-USDT"
                response = requests.get(url, timeout=5)
                data = response.json()
                
                if data.get('code') == '0' and data.get('data'):
                    ticker = data['data'][0]
                    
                    market_data[symbol] = {
                        'last': float(ticker.get('last', 0)),
                        'open24h': float(ticker.get('open24h', 0)),
                        'high24h': float(ticker.get('high24h', 0)),
                        'low24h': float(ticker.get('low24h', 0)),
                        'vol24h': float(ticker.get('vol24h', 0)),
                        'change_pct': 0
                    }
                    
                    # 计算涨跌幅
                    if market_data[symbol]['open24h'] > 0:
                        change = ((market_data[symbol]['last'] - market_data[symbol]['open24h']) 
                                 / market_data[symbol]['open24h']) * 100
                        market_data[symbol]['change_pct'] = round(change, 2)
                    
                    print(f"[价格] {symbol}: {market_data[symbol]['last']} ({market_data[symbol]['change_pct']}%)")
                    
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[错误] {symbol} 获取失败: {e}")
                continue
        
        return market_data
        
    except Exception as e:
        print(f"[错误] 获取市场数据失败: {e}")
        return {}


def calculate_panic_index(market_data):
    """计算恐慌洗盘指数"""
    if not market_data:
        return 0
    
    try:
        # 简单算法：基于价格变化和波动率
        total_change = sum(data['change_pct'] for data in market_data.values())
        
        # 计算波动率（高低价差百分比）
        volatility = 0
        for data in market_data.values():
            if data['low24h'] > 0:
                vol = ((data['high24h'] - data['low24h']) / data['low24h']) * 100
                volatility += vol
        
        avg_volatility = volatility / len(market_data) if market_data else 0
        
        # 恐慌指数 = 负向变化 + 高波动率
        # 负值越大，波动越大，恐慌指数越高
        panic_index = 0
        
        if total_change < 0:
            panic_index = abs(total_change) + (avg_volatility * 0.3)
        else:
            # 即使上涨，高波动也可能表示恐慌
            panic_index = avg_volatility * 0.2
        
        return round(panic_index, 2)
        
    except Exception as e:
        print(f"[错误] 计算恐慌指数失败: {e}")
        return 0


def calculate_liquidation_data(market_data):
    """计算爆仓相关数据（估算）"""
    if not market_data:
        return {
            'liquidation_1h': 0,
            'liquidation_24h': 0,
            'liquidation_count_24h': 0,
            'open_interest': 0
        }
    
    try:
        # 基于交易量和价格波动估算爆仓金额
        total_vol_24h = sum(data['vol24h'] * data['last'] for data in market_data.values())
        
        # 计算平均波动率
        avg_volatility = 0
        for data in market_data.values():
            if data['low24h'] > 0:
                vol = ((data['high24h'] - data['low24h']) / data['low24h']) * 100
                avg_volatility += vol
        avg_volatility = avg_volatility / len(market_data) if market_data else 0
        
        # 估算爆仓金额（基于交易量的一定比例）
        # 波动率越大，爆仓比例越高
        liquidation_ratio = avg_volatility * 0.002  # 0.2% per 1% volatility
        liquidation_24h = total_vol_24h * liquidation_ratio / 10000  # 转换为万美元
        liquidation_1h = liquidation_24h / 24
        
        # 估算爆仓人数（假设平均每人爆仓金额为1000美元）
        liquidation_count_24h = (liquidation_24h * 10000) / 1000
        
        # 估算全网持仓量（通常是24h交易量的2-3倍）
        open_interest = total_vol_24h * 2.5 / 100000000  # 转换为亿美元
        
        return {
            'liquidation_1h': round(liquidation_1h, 2),
            'liquidation_24h': round(liquidation_24h, 2),
            'liquidation_count_24h': round(liquidation_count_24h, 2),
            'open_interest': round(open_interest, 2)
        }
        
    except Exception as e:
        print(f"[错误] 计算爆仓数据失败: {e}")
        return {
            'liquidation_1h': 0,
            'liquidation_24h': 0,
            'liquidation_count_24h': 0,
            'open_interest': 0
        }


def save_to_jsonl(fear_greed_index, market_data, liquidation_data):
    """保存数据到JSONL"""
    jsonl_file = DATA_DIR / 'panic_wash_index.jsonl'
    
    try:
        now = datetime.now(BEIJING_TZ)
        
        # 添加全网持仓量
        if 'open_interest' not in liquidation_data:
            liquidation_data['open_interest'] = 0
        
        # 数据验证：检查异常值
        liquidation_count_24h = liquidation_data.get('liquidation_count_24h', 0)
        if liquidation_count_24h > 100:  # 如果爆仓人数>100万人，数据异常
            print(f"[警告] 检测到异常数据，爆仓人数={liquidation_count_24h}万人，跳过本次保存")
            return
        
        record = {
            'timestamp': int(time.time() * 1000),
            'beijing_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'panic_index': fear_greed_index,  # 恐惧贪婪指数 = 24h爆仓人数(万人) / 全网持仓(亿$)
            'market_data': market_data,
            'liquidation_data': liquidation_data,
            'level': 'high' if fear_greed_index > 0.15 else 'medium' if fear_greed_index > 0.08 else 'low',
            'data_source': 'btc126.com'
        }
        
        # 追加写入
        with open(jsonl_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        print(f"[保存] 恐惧贪婪指数: {fear_greed_index} (级别: {record['level']})")
        print(f"[爆仓] 1h: {liquidation_data['liquidation_1h']}万$ | 24h: {liquidation_data['liquidation_24h']}万$")
        print(f"[数据] 24h爆仓人数: {liquidation_data['liquidation_count_24h']}万人 | 全网持仓: {liquidation_data['open_interest']}亿$")
        print(f"[公式] 恐惧贪婪指数 = {liquidation_data['liquidation_count_24h']}万人 / {liquidation_data['open_interest']}亿$ = {fear_greed_index}")
        print(f"[来源] btc126.com 真实数据")
        
    except Exception as e:
        print(f"[错误] 保存JSONL失败: {e}")


def main():
    """主循环"""
    print("=" * 60)
    print("恐慌洗盘指数采集器启动")
    print("数据来源: https://history.btc126.com/baocang/")
    print("=" * 60)
    
    while True:
        try:
            now = datetime.now(BEIJING_TZ)
            print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] 开始采集恐慌指数...")
            
            # 获取市场数据（用于计算恐慌指数）
            market_data = get_market_data()
            
            # 获取真实的爆仓数据
            liquidation_data = get_btc126_liquidation_data()
            
            # 获取全网持仓量
            open_interest = get_btc126_open_interest()
            
            if market_data and liquidation_data:
                # 添加持仓量到爆仓数据
                liquidation_data['open_interest'] = open_interest
                
                # 计算恐惧贪婪指数
                # 公式: 恐惧贪婪指数 = 24H爆仓人数(万人) / 全网总计(亿$)
                liquidation_count_24h = liquidation_data.get('liquidation_count_24h', 0)
                if open_interest > 0 and liquidation_count_24h > 0:
                    fear_greed_index = round(liquidation_count_24h / open_interest, 2)
                else:
                    fear_greed_index = 0
                
                print(f"[计算] 恐惧贪婪指数 = {liquidation_count_24h}万人 / {open_interest}亿$ = {fear_greed_index}")
                
                # 保存到JSONL
                save_to_jsonl(fear_greed_index, market_data, liquidation_data)
            else:
                print("[警告] 数据获取不完整，跳过本次采集")
            
            # 每3分钟采集一次
            print(f"[等待] 下次采集: 3分钟后")
            time.sleep(180)
            
        except KeyboardInterrupt:
            print("\n[退出] 采集器已停止")
            break
        except Exception as e:
            print(f"[错误] 采集失败: {e}")
            time.sleep(60)


if __name__ == '__main__':
    main()
