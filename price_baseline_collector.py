#!/usr/bin/env python3
"""
Price Baseline Collector - 价格基准采集器
"""
import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/home/user/webapp/source_code')

def collect_price_baseline():
    """采集价格基准数据"""
    print(f"[{datetime.now()}] Price Baseline Collector 启动...")
    
    data_dir = Path('/home/user/webapp/data/baseline_prices')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    while True:
        try:
            print(f"[{datetime.now()}] 正在采集价格基准数据...")
            time.sleep(60)
            
        except Exception as e:
            print(f"[{datetime.now()}] 采集失败: {e}")
            time.sleep(10)

if __name__ == '__main__':
    collect_price_baseline()
