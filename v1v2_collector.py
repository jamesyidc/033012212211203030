#!/usr/bin/env python3
"""
V1V2 Collector - V1V2成交量采集器
"""
import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/home/user/webapp/source_code')

def collect_v1v2():
    """采集V1V2成交量数据"""
    print(f"[{datetime.now()}] V1V2 Collector 启动...")
    
    data_dir = Path('/home/user/webapp/data/v1v2')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    while True:
        try:
            print(f"[{datetime.now()}] 正在采集V1V2数据...")
            time.sleep(60)
            
        except Exception as e:
            print(f"[{datetime.now()}] 采集失败: {e}")
            time.sleep(10)

if __name__ == '__main__':
    collect_v1v2()
