#!/usr/bin/env python3
"""
Dashboard JSONL Manager - Dashboard数据管理器
"""
import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/home/user/webapp/source_code')

def manage_dashboard_jsonl():
    """管理Dashboard JSONL数据"""
    print(f"[{datetime.now()}] Dashboard JSONL Manager 启动...")
    
    data_dir = Path('/home/user/webapp/data/dashboard_jsonl')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    while True:
        try:
            print(f"[{datetime.now()}] 正在管理Dashboard数据...")
            time.sleep(60)
            
        except Exception as e:
            print(f"[{datetime.now()}] 管理失败: {e}")
            time.sleep(10)

if __name__ == '__main__':
    manage_dashboard_jsonl()
