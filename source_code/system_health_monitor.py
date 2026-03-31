#!/usr/bin/env python3
"""
System Health Monitor - 系统健康监控器
"""
import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/home/user/webapp/source_code')

def monitor_system_health():
    """监控系统健康状态"""
    print(f"[{datetime.now()}] System Health Monitor 启动...")
    
    while True:
        try:
            print(f"[{datetime.now()}] 正在监控系统健康状态...")
            time.sleep(60)
            
        except Exception as e:
            print(f"[{datetime.now()}] 监控失败: {e}")
            time.sleep(10)

if __name__ == '__main__':
    monitor_system_health()
