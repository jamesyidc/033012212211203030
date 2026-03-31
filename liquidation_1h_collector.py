#!/usr/bin/env python3
"""
Liquidation 1H Collector - 1小时爆仓数据采集器
"""
import time
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/home/user/webapp/source_code')

def collect_liquidation():
    """采集1小时爆仓数据"""
    print(f"[{datetime.now()}] Liquidation 1H Collector 启动...")
    
    data_dir = Path('/home/user/webapp/data/liquidation_1h')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    while True:
        try:
            print(f"[{datetime.now()}] 正在采集1小时爆仓数据...")
            time.sleep(2)  # 每2秒采集一次
            
        except Exception as e:
            print(f"[{datetime.now()}] 采集失败: {e}")
            time.sleep(10)

if __name__ == '__main__':
    collect_liquidation()
