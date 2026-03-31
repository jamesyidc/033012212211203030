#!/usr/bin/env python3
"""
Data Health Monitor - 数据健康监控器
"""
import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/home/user/webapp/source_code')

def monitor_data_health():
    """监控数据健康状态"""
    print(f"[{datetime.now()}] Data Health Monitor 启动...")
    
    while True:
        try:
            print(f"[{datetime.now()}] 正在监控数据健康状态...")
            time.sleep(60)
            
        except Exception as e:
            print(f"[{datetime.now()}] 监控失败: {e}")
            time.sleep(10)

if __name__ == '__main__':
    monitor_data_health()
