#!/usr/bin/env python3
"""
为历史数据添加beijing_time字段
"""

import json
import os
from datetime import datetime

def fix_beijing_time_field(date_str):
    """为指定日期的数据添加beijing_time字段"""
    
    file_path = f"/home/user/webapp/data/coin_change_tracker/coin_change_{date_str}.jsonl"
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    print(f"📝 处理文件: {file_path}")
    
    # 读取所有数据
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                record = json.loads(line.strip())
                records.append(record)
    
    print(f"  原始记录数: {len(records)}")
    
    # 检查是否需要修复
    needs_fix = False
    has_beijing_time = 0
    
    for record in records:
        if 'beijing_time' in record and record['beijing_time']:
            has_beijing_time += 1
        elif 'time' in record and record['time']:
            needs_fix = True
            
    print(f"  已有beijing_time的记录: {has_beijing_time}")
    
    if not needs_fix and has_beijing_time == len(records):
        print(f"  ✅ 数据完整，无需修复")
        return True
    
    # 修复数据
    fixed_count = 0
    for record in records:
        if 'beijing_time' not in record or not record['beijing_time']:
            # 从timestamp或date+time构建beijing_time
            if 'timestamp' in record:
                # 解析timestamp
                timestamp_str = record['timestamp']
                # 移除时区信息
                if '+' in timestamp_str:
                    timestamp_str = timestamp_str.split('+')[0]
                
                try:
                    dt = datetime.fromisoformat(timestamp_str)
                    record['beijing_time'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    fixed_count += 1
                except Exception as e:
                    print(f"    ⚠️ 解析失败: {timestamp_str}, 错误: {e}")
            elif 'date' in record and 'time' in record:
                # 从date和time构建
                date_part = record['date']
                time_part = record['time']
                # 格式化日期 20260209 -> 2026-02-09
                formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                record['beijing_time'] = f"{formatted_date} {time_part}"
                fixed_count += 1
    
    print(f"  修复记录数: {fixed_count}")
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"  ✅ 写入完成")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("🔧 修复历史数据的beijing_time字段")
    print("=" * 60)
    print()
    
    # 需要修复的日期范围
    dates = [
        "20260201", "20260202", "20260203", "20260204", "20260205",
        "20260206", "20260207", "20260208", "20260209", "20260210",
        "20260211", "20260212", "20260213", "20260214", "20260215",
        "20260216", "20260217"
    ]
    
    success_count = 0
    for date_str in dates:
        if fix_beijing_time_field(date_str):
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"✅ 完成！成功处理 {success_count}/{len(dates)} 个文件")
    print("=" * 60)

if __name__ == "__main__":
    main()
