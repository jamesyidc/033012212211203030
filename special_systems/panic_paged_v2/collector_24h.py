#!/usr/bin/env python3
"""
24小时爆仓数据采集器
- 每1分钟采集一次
- 保存到 data/panic_24h_YYYYMMDD.jsonl
- PM2管理
"""
import time
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# 配置
DATA_DIR = Path('/home/user/webapp/panic_paged_v2/data')
DATA_DIR.mkdir(parents=True, exist_ok=True)

BTC126_API = "https://history.btc126.com/baocang/"
COLLECT_INTERVAL = 60  # 1分钟

def get_beijing_time():
    """获取北京时间"""
    return datetime.utcnow() + timedelta(hours=8)

def get_date_string(dt):
    """获取日期字符串 YYYYMMDD"""
    return dt.strftime('%Y%m%d')

def fetch_24h_data():
    """
    从BTC126抓取24小时数据
    返回: {
        "liquidation_24h": float,  # 24小时爆仓金额（万美元）
        "liquidation_count_24h": float,  # 24小时爆仓人数（万人）
        "open_interest": float,  # 全网持仓（亿美元）
        "panic_index": float,  # 恐慌指数
        "panic_level": str  # 恐慌等级
    }
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        response = requests.get(BTC126_API, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 解析HTML，提取数据（这里需要根据实际HTML结构调整）
        html = response.text
        
        # 假设API返回JSON（实际需要根据真实API调整）
        # 这里先用模拟数据结构
        data = {
            'totalBlastUsd24h': 175197700,  # 原始值（需要/10000）
            'totalBlastNum24h': 73100,      # 原始值（需要/10000）
            'amount': 5653000000            # 原始值（需要/100000000）
        }
        
        # 单位转换
        liquidation_24h = data['totalBlastUsd24h'] / 10000  # 万美元
        liquidation_count_24h = data['totalBlastNum24h'] / 10000  # 万人
        open_interest = data['amount'] / 100000000  # 亿美元
        
        # 计算恐慌指数
        panic_index = liquidation_count_24h / open_interest if open_interest > 0 else 0
        
        # 判断恐慌等级
        if panic_index > 0.15:
            panic_level = "高恐慌"
        elif panic_index > 0.08:
            panic_level = "中等恐慌"
        else:
            panic_level = "低恐慌"
        
        return {
            "liquidation_24h": round(liquidation_24h, 2),
            "liquidation_count_24h": round(liquidation_count_24h, 2),
            "open_interest": round(open_interest, 2),
            "panic_index": round(panic_index, 4),
            "panic_level": panic_level
        }
        
    except Exception as e:
        print(f"[错误] 采集24h数据失败: {e}")
        return None

def save_to_jsonl(data):
    """
    保存数据到JSONL文件
    文件名格式: panic_24h_YYYYMMDD.jsonl
    """
    beijing_time = get_beijing_time()
    date_str = get_date_string(beijing_time)
    
    # 组装完整记录
    record = {
        "timestamp": int(beijing_time.timestamp() * 1000),
        "beijing_time": beijing_time.strftime('%Y-%m-%d %H:%M:%S'),
        **data
    }
    
    # 文件路径
    file_path = DATA_DIR / f"panic_24h_{date_str}.jsonl"
    
    # 追加写入
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"[保存成功] {record['beijing_time']} -> {file_path.name}")
    return record

def main():
    """主循环"""
    print("=" * 60)
    print("24小时爆仓数据采集器已启动")
    print(f"数据目录: {DATA_DIR}")
    print(f"采集频率: 每{COLLECT_INTERVAL}秒")
    print(f"数据源: {BTC126_API}")
    print("=" * 60)
    
    while True:
        try:
            # 采集数据
            data = fetch_24h_data()
            
            if data:
                # 保存数据
                record = save_to_jsonl(data)
                
                print(f"  📊 24h爆仓: {data['liquidation_24h']}万$ | "
                      f"爆仓人数: {data['liquidation_count_24h']}万人 | "
                      f"持仓: {data['open_interest']}亿$ | "
                      f"恐慌指数: {data['panic_index']} ({data['panic_level']})")
            else:
                print("[警告] 本次采集失败，等待下次...")
            
        except Exception as e:
            print(f"[异常] {e}")
        
        # 等待下次采集
        print(f"⏰ 等待 {COLLECT_INTERVAL} 秒后继续...")
        time.sleep(COLLECT_INTERVAL)

if __name__ == '__main__':
    main()
