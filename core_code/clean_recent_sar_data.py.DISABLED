#!/usr/bin/env python3
"""
清理SAR JSONL数据中今天和昨天的错误数据
保留2026-02-10及之前的正确数据
"""
import os
import json
from datetime import datetime, timedelta
import pytz
from pathlib import Path

# 北京时区
beijing_tz = pytz.timezone('Asia/Shanghai')
now = datetime.now(beijing_tz)

# 计算截止日期：保留2026-02-10及之前的数据
cutoff_date = now.replace(year=2026, month=2, day=11, hour=0, minute=0, second=0, microsecond=0)

print(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"截止日期: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"将删除 {cutoff_date.strftime('%Y-%m-%d')} 及之后的数据")
print("=" * 60)

# SAR数据目录
sar_data_dir = Path('/home/user/webapp/data/sar_jsonl')

# 币种列表
SYMBOLS = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'DOGE', 'SOL', 'DOT', 'LTC', 
           'LINK', 'HBAR', 'TAO', 'CFX', 'TRX', 'TON', 'NEAR', 'LDO', 'CRO', 'ETC', 
           'XLM', 'BCH', 'UNI', 'SUI', 'FIL', 'STX', 'CRV', 'AAVE', 'APT', 'OKB']

total_removed = 0
total_kept = 0

for symbol in SYMBOLS:
    jsonl_file = sar_data_dir / f'{symbol}.jsonl'
    
    if not jsonl_file.exists():
        print(f"[跳过] {symbol}: 文件不存在")
        continue
    
    # 读取所有数据
    kept_lines = []
    removed_count = 0
    
    try:
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                    beijing_time_str = record.get('beijing_time', '')
                    
                    if not beijing_time_str:
                        kept_lines.append(line)
                        continue
                    
                    # 解析时间
                    record_time = datetime.strptime(beijing_time_str, '%Y-%m-%d %H:%M:%S')
                    record_time = beijing_tz.localize(record_time)
                    
                    # 保留截止日期之前的数据
                    if record_time < cutoff_date:
                        kept_lines.append(line)
                    else:
                        removed_count += 1
                        
                except Exception as e:
                    # 解析失败的行也保留
                    kept_lines.append(line)
        
        # 写回文件
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            for line in kept_lines:
                f.write(line + '\n')
        
        print(f"[完成] {symbol}: 保留 {len(kept_lines)} 条, 删除 {removed_count} 条")
        total_kept += len(kept_lines)
        total_removed += removed_count
        
    except Exception as e:
        print(f"[错误] {symbol}: {e}")
        continue

print("=" * 60)
print(f"总计: 保留 {total_kept} 条, 删除 {total_removed} 条")
print("清理完成！")
