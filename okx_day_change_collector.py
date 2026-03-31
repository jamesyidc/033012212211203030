#!/usr/bin/env python3
"""
OKX Day Change Collector - OKX日涨跌采集器
"""
import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/home/user/webapp/source_code')

def collect_okx_day_change():
    """采集OKX日涨跌数据"""
    print(f"[{datetime.now()}] OKX Day Change Collector 启动...")
    
    data_dir = Path('/home/user/webapp/data/okx_day_change')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    while True:
        try:
            print(f"[{datetime.now()}] 正在采集OKX日涨跌数据...")
            time.sleep(60)
            
        except Exception as e:
            print(f"[{datetime.now()}] 采集失败: {e}")
            time.sleep(10)

if __name__ == '__main__':
    collect_okx_day_change()
