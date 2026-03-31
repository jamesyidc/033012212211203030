#!/usr/bin/env python3
"""
Price Comparison Collector - 价格对比采集器
"""
import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/home/user/webapp/source_code')

def collect_price_comparison():
    """采集价格对比数据"""
    print(f"[{datetime.now()}] Price Comparison Collector 启动...")
    
    data_dir = Path('/home/user/webapp/data/price_comparison')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    while True:
        try:
            print(f"[{datetime.now()}] 正在采集价格对比数据...")
            time.sleep(60)
            
        except Exception as e:
            print(f"[{datetime.now()}] 采集失败: {e}")
            time.sleep(10)

if __name__ == '__main__':
    collect_price_comparison()
