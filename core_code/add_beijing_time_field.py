#!/usr/bin/env python3
"""
为历史数据添加beijing_time字段
"""

import json
import os
from datetime import datetime

def add_beijing_time_to_file(file_path):
    """为单个文件添加beijing_time字段"""
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    print(f"📁 处理文件: {file_path}")
    
    # 读取所有数据
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                record = json.loads(line.strip())
                records.append(record)
    
    print(f"  读取记录数: {len(records)}")
    
    # 检查是否需要添加beijing_time
    needs_update = False
    updated_count = 0
    
    for record in records:
        # 如果已经有beijing_time，跳过
        if 'beijing_time' in record and record['beijing_time']:
            continue
        
        needs_update = True
        
        # 从timestamp字段构建beijing_time
        if 'timestamp' in record:
            # timestamp可能是字符串或数字
            timestamp = record['timestamp']
            
            if isinstance(timestamp, str):
                # 如果是ISO格式字符串，解析它
                try:
                    # 移除时区信息
                    if '+' in timestamp:
                        timestamp = timestamp.split('+')[0]
                    if 'T' in timestamp:
                        dt = datetime.fromisoformat(timestamp)
                    else:
                        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    record['beijing_time'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    updated_count += 1
                except Exception as e:
                    print(f"  ⚠️ 解析timestamp失败: {timestamp}, 错误: {e}")
            elif isinstance(timestamp, (int, float)):
                # 如果是Unix时间戳（秒或毫秒）
                try:
                    if timestamp > 1e12:  # 毫秒
                        dt = datetime.fromtimestamp(timestamp / 1000)
                    else:  # 秒
                        dt = datetime.fromtimestamp(timestamp)
                    record['beijing_time'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    updated_count += 1
                except Exception as e:
                    print(f"  ⚠️ 解析timestamp失败: {timestamp}, 错误: {e}")
        
        # 如果没有timestamp但有date和time字段
        elif 'date' in record and 'time' in record:
            date_str = record['date']  # 例如: "20260209"
            time_str = record['time']  # 例如: "00:54:00"
            
            try:
                # 格式化为 YYYY-MM-DD HH:MM:SS
                beijing_time = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {time_str}"
                record['beijing_time'] = beijing_time
                updated_count += 1
            except Exception as e:
                print(f"  ⚠️ 构建beijing_time失败: date={date_str}, time={time_str}, 错误: {e}")
    
    if not needs_update:
        print(f"  ✅ 无需更新（所有记录都有beijing_time）")
        return True
    
    # 备份原文件
    backup_path = file_path + '.backup_before_beijing_time'
    if not os.path.exists(backup_path):
        print(f"  💾 创建备份: {backup_path}")
        with open(backup_path, 'w', encoding='utf-8') as f:
            with open(file_path, 'r', encoding='utf-8') as src:
                f.write(src.read())
    
    # 写入更新后的数据
    print(f"  ✍️ 写入更新数据...")
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"  ✅ 更新完成，更新记录数: {updated_count}")
    return True

def main():
    """主函数"""
    data_dir = "/home/user/webapp/data/coin_change_tracker"
    
    # 处理2月1日到2月10日的数据
    dates = [
        "20260201", "20260202", "20260203", "20260204", "20260205",
        "20260206", "20260207", "20260208", "20260209", "20260210"
    ]
    
    print("=" * 80)
    print("📊 批量添加beijing_time字段到历史数据")
    print("=" * 80)
    print()
    
    success_count = 0
    fail_count = 0
    
    for date in dates:
        file_path = os.path.join(data_dir, f"coin_change_{date}.jsonl")
        
        if add_beijing_time_to_file(file_path):
            success_count += 1
        else:
            fail_count += 1
        
        print()
    
    print("=" * 80)
    print(f"✅ 处理完成: 成功 {success_count} 个, 失败 {fail_count} 个")
    print("=" * 80)

if __name__ == "__main__":
    main()
