#!/usr/bin/env python3
"""
Panic V3 数据采集器
采集频率: 每1分钟
数据来源: https://history.btc126.com/baocang/
数据存储: 按日期存储JSONL文件 (data/panic_YYYYMMDD.jsonl)
"""

import json
import time
import requests
from datetime import datetime
from pathlib import Path
import pytz

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 数据目录
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

# API配置
BTC126_API_BASE = 'https://api.btc126.com/bicoin.php'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://history.btc126.com/baocang/'
}


def get_btc126_data():
    """
    从BTC126获取实时数据
    
    返回:
    {
        'liquidation_1h': float,        # 1小时爆仓金额 (万美元)
        'liquidation_24h': float,       # 24小时爆仓金额 (万美元)
        'liquidation_count_24h': float, # 24小时爆仓人数 (万人)
        'open_interest': float,         # 全网持仓 (亿美元)
        'panic_index': float,           # 恐慌清洗指数
        'panic_level': str,             # 恐慌级别
        'timestamp': int,               # 时间戳 (毫秒)
        'beijing_time': str             # 北京时间
    }
    """
    try:
        # 1. 获取爆仓数据
        ts = int(time.time() * 1000)
        resp1 = requests.get(
            f'{BTC126_API_BASE}?from=24hbaocang&t={ts}',
            headers=HEADERS,
            timeout=10
        )
        resp1.raise_for_status()
        liquidation_data = resp1.json()
        
        if liquidation_data.get('code') != 0:
            print(f"[错误] 爆仓数据API返回错误: {liquidation_data}")
            return None
        
        # 2. 获取全网持仓数据
        resp2 = requests.get(
            f'{BTC126_API_BASE}?from=realhold&t={ts}',
            headers=HEADERS,
            timeout=10
        )
        resp2.raise_for_status()
        open_interest_data = resp2.json()
        
        if open_interest_data.get('code') != 0:
            print(f"[错误] 持仓数据API返回错误: {open_interest_data}")
            return None
        
        # 3. 提取数据
        liq_data = liquidation_data.get('data', {})
        liquidation_1h = round(liq_data.get('totalBlastUsd1h', 0) / 10000, 2)
        liquidation_24h = round(liq_data.get('totalBlastUsd24h', 0) / 10000, 2)
        liquidation_count_24h = round(liq_data.get('totalBlastNum24h', 0) / 10000, 2)
        
        # 4. 找到全网持仓
        open_interest = 0
        for item in open_interest_data.get('data', []):
            exchange = item.get('exchange', '')
            exchange_other = item.get('exchangeOtherName', '')
            if '全网总计' in exchange or 'Net total' in exchange_other:
                open_interest = round(item.get('amount', 0) / 100000000, 2)
                break
        
        # 5. 数据验证
        if liquidation_count_24h > 100:  # 超过100万人明显异常
            print(f"[警告] 检测到异常数据，爆仓人数: {liquidation_count_24h}万人，跳过")
            return None
        
        if open_interest <= 0 or open_interest > 200:  # 持仓异常
            print(f"[警告] 检测到异常持仓: {open_interest}亿美元，跳过")
            return None
        
        # 6. 计算恐慌清洗指数
        if open_interest > 0 and liquidation_count_24h > 0:
            panic_index = round(liquidation_count_24h / open_interest, 4)
        else:
            panic_index = 0
        
        # 7. 确定恐慌级别
        if panic_index > 0.15:
            panic_level = '高恐慌'
        elif panic_index > 0.08:
            panic_level = '中等恐慌'
        else:
            panic_level = '低恐慌'
        
        # 8. 组装返回数据
        now = datetime.now(BEIJING_TZ)
        result = {
            'liquidation_1h': liquidation_1h,
            'liquidation_24h': liquidation_24h,
            'liquidation_count_24h': liquidation_count_24h,
            'open_interest': open_interest,
            'panic_index': panic_index,
            'panic_level': panic_level,
            'timestamp': int(now.timestamp() * 1000),
            'beijing_time': now.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"[采集成功] {result['beijing_time']} | "
              f"1h爆仓: {liquidation_1h}万$ | "
              f"24h爆仓: {liquidation_24h}万$ | "
              f"爆仓人数: {liquidation_count_24h}万人 | "
              f"全网持仓: {open_interest}亿$ | "
              f"恐慌指数: {panic_index} ({panic_level})")
        
        return result
        
    except Exception as e:
        print(f"[错误] 采集数据失败: {e}")
        return None


def save_data(data):
    """
    保存数据到JSONL文件（按日期分文件）
    
    文件名格式: panic_YYYYMMDD.jsonl
    """
    if not data:
        return False
    
    try:
        # 生成文件名
        date_str = datetime.now(BEIJING_TZ).strftime('%Y%m%d')
        file_path = DATA_DIR / f'panic_{date_str}.jsonl'
        
        # 追加写入
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        print(f"[保存成功] 数据已保存到: {file_path}")
        return True
        
    except Exception as e:
        print(f"[错误] 保存数据失败: {e}")
        return False


def collect_once():
    """执行一次采集"""
    print("\n" + "="*80)
    print(f"[开始采集] {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    data = get_btc126_data()
    if data:
        save_data(data)
    else:
        print("[失败] 本次采集未获取到有效数据")


def main():
    """主循环：每1分钟采集一次"""
    print("\n" + "#"*80)
    print("# Panic V3 数据采集器")
    print("# 采集频率: 每1分钟")
    print("# 数据来源: https://history.btc126.com/baocang/")
    print("# 存储路径:", DATA_DIR.absolute())
    print("#"*80 + "\n")
    
    while True:
        try:
            collect_once()
            
            # 等待60秒（1分钟）
            print(f"\n[等待] 下次采集将在60秒后开始...")
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\n\n[退出] 采集器已停止")
            break
        except Exception as e:
            print(f"\n[错误] 发生异常: {e}")
            print("[重试] 60秒后重试...")
            time.sleep(60)


if __name__ == '__main__':
    main()
