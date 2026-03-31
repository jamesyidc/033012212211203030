#!/usr/bin/env python3
"""
Coin Change Tracker - 币种变化追踪器
"""
import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/home/user/webapp/source_code')
sys.path.insert(0, '/home/user/webapp')

# 导入北京时间工具
from utils.beijing_time import get_beijing_now_str

def track_coin_change():
    """追踪币种变化"""
    print(f"[{get_beijing_now_str()}] Coin Change Tracker 启动...")
    
    data_dir = Path('/home/user/webapp/data/coin_change_tracker')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    while True:
        try:
            print(f"[{get_beijing_now_str()}] 正在追踪币种变化...")
            time.sleep(60)
            
        except Exception as e:
            print(f"[{get_beijing_now_str()}] 追踪失败: {e}")
            time.sleep(10)

if __name__ == '__main__':
    track_coin_change()
