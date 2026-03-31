#!/usr/bin/env python3
"""
将panic_daily目录的历史数据导入到panic_wash_index.jsonl
"""
import json
import os
from datetime import datetime
from pathlib import Path

# 数据源目录
SOURCE_DIR = 'data/panic_daily'
# 目标文件
TARGET_FILE = 'data/panic_jsonl/panic_wash_index.jsonl'

def load_existing_data():
    """加载现有数据"""
    if not os.path.exists(TARGET_FILE):
        return {}
    
    existing = {}
    with open(TARGET_FILE, 'r') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                # 使用北京时间作为key去重
                beijing_time = data.get('beijing_time')
                if beijing_time:
                    existing[beijing_time] = data
            except:
                pass
    
    return existing

def convert_to_jsonl_format(record):
    """转换数据格式"""
    # 从panic_daily格式转换为panic_wash_index格式
    try:
        timestamp_str = record.get('timestamp')
        data_obj = record.get('data', {})
        beijing_time = data_obj.get('record_time')
        
        # 将ISO格式时间戳转换为毫秒级时间戳
        timestamp_ms = 0
        if timestamp_str:
            try:
                from dateutil.parser import parse
                dt = parse(timestamp_str)
                timestamp_ms = int(dt.timestamp() * 1000)
            except:
                # 如果解析失败，尝试从beijing_time解析
                if beijing_time:
                    try:
                        dt = datetime.strptime(beijing_time, '%Y-%m-%d %H:%M:%S')
                        timestamp_ms = int(dt.timestamp() * 1000)
                    except:
                        pass
        
        # 构建liquidation_data
        liquidation_data = {
            'liquidation_1h': data_obj.get('hour_1_amount', 0),
            'liquidation_24h': data_obj.get('hour_24_amount', 0),
            'liquidation_count_24h': data_obj.get('hour_24_people', 0),
            'open_interest': data_obj.get('total_position', 0)
        }
        
        # 构建完整记录
        jsonl_record = {
            'timestamp': timestamp_ms,
            'beijing_time': beijing_time,
            'panic_index': data_obj.get('panic_index', 0),
            'liquidation_data': liquidation_data,
            'level': 'medium'  # 默认值
        }
        
        return jsonl_record
    except Exception as e:
        print(f"转换错误: {e}, record: {record.get('timestamp', 'N/A')}")
        return None

def import_from_file(file_path, existing_data):
    """从单个文件导入数据"""
    new_records = []
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    data_obj = record.get('data', {})
                    beijing_time = data_obj.get('record_time')
                    
                    # 跳过已存在的数据
                    if beijing_time in existing_data:
                        continue
                    
                    # 转换格式
                    jsonl_record = convert_to_jsonl_format(record)
                    if jsonl_record and jsonl_record['beijing_time']:
                        new_records.append(jsonl_record)
                        existing_data[beijing_time] = jsonl_record
                        
                except Exception as e:
                    continue
    except Exception as e:
        print(f"读取文件错误 {file_path}: {e}")
    
    return new_records

def main():
    print("="*60)
    print("导入历史数据到 panic_wash_index.jsonl")
    print("="*60)
    
    # 1. 加载现有数据
    print("\n1️⃣ 加载现有数据...")
    existing_data = load_existing_data()
    print(f"   现有记录数: {len(existing_data)}")
    
    # 2. 扫描panic_daily目录
    print("\n2️⃣ 扫描历史数据文件...")
    source_files = sorted(Path(SOURCE_DIR).glob('panic_202602*.jsonl'))
    print(f"   找到 {len(source_files)} 个文件")
    
    # 3. 导入数据
    print("\n3️⃣ 导入数据...")
    total_new = 0
    for file_path in source_files:
        date = file_path.stem.replace('panic_', '')
        new_records = import_from_file(file_path, existing_data)
        if new_records:
            print(f"   {date}: 导入 {len(new_records)} 条新记录")
            total_new += len(new_records)
    
    # 4. 排序并写入文件
    print("\n4️⃣ 排序并保存...")
    all_records = sorted(existing_data.values(), key=lambda x: x['beijing_time'])
    
    # 备份原文件
    if os.path.exists(TARGET_FILE):
        backup_file = f"{TARGET_FILE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(TARGET_FILE, backup_file)
        print(f"   ✅ 已备份原文件: {backup_file}")
    
    # 写入新文件
    with open(TARGET_FILE, 'w') as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"   ✅ 已保存 {len(all_records)} 条记录")
    
    # 5. 统计
    print("\n5️⃣ 统计结果")
    print("="*60)
    print(f"原有记录数: {len(existing_data) - total_new}")
    print(f"新增记录数: {total_new}")
    print(f"总记录数: {len(all_records)}")
    
    # 日期分布
    dates = {}
    for record in all_records:
        date = record['beijing_time'].split(' ')[0]
        dates[date] = dates.get(date, 0) + 1
    
    print(f"\n📅 日期分布:")
    for date in sorted(dates.keys()):
        print(f"  {date}: {dates[date]}条")
    
    print("\n✅ 导入完成！")

if __name__ == '__main__':
    main()
