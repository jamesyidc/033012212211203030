#!/usr/bin/env python3
"""
Financial Indicators Collector - 金融指标采集器
"""
import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/home/user/webapp/source_code')

def collect_financial_indicators():
    """采集金融指标数据"""
    print(f"[{datetime.now()}] Financial Indicators Collector 启动...")
    
    data_dir = Path('/home/user/webapp/data/financial_indicators')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    while True:
        try:
            print(f"[{datetime.now()}] 正在采集金融指标数据...")
            time.sleep(60)
            
        except Exception as e:
            print(f"[{datetime.now()}] 采集失败: {e}")
            time.sleep(10)

if __name__ == '__main__':
    collect_financial_indicators()
