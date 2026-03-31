#!/usr/bin/env python3
"""
Panic Data Daily Splitter - 恐慌数据按日分割器
将 panic_wash_index.jsonl 中的数据按日期分割到 panic_daily 目录
"""
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import pytz

BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def split_panic_data_by_day():
    """将panic_wash_index.jsonl按日期分割到panic_daily目录"""
    
    source_file = Path('/home/user/webapp/data/panic_jsonl/panic_wash_index.jsonl')
    target_dir = Path('/home/user/webapp/data/panic_daily')
    target_dir.mkdir(parents=True, exist_ok=True)
    
    if not source_file.exists():
        print(f"[错误] 源文件不存在: {source_file}")
        return
    
    print(f"[信息] 开始分割数据: {source_file}")
    
    # 按日期分组数据
    daily_data = defaultdict(list)
    total_records = 0
    
    with open(source_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                total_records += 1
                
                # 获取北京时间
                beijing_time = record.get('beijing_time', '')
                if not beijing_time:
                    # 如果没有beijing_time，从timestamp转换
                    timestamp = record.get('timestamp', 0)
                    if timestamp:
                        dt = datetime.fromtimestamp(timestamp, tz=BEIJING_TZ)
                        beijing_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                
                if beijing_time:
                    # 提取日期 (YYYY-MM-DD -> YYYYMMDD)
                    date_str = beijing_time.split()[0]  # "2026-02-16"
                    date_key = date_str.replace('-', '')  # "20260216"
                    daily_data[date_key].append(line)
                
            except Exception as e:
                print(f"[警告] 解析记录失败: {e}")
                continue
    
    print(f"[信息] 共读取 {total_records} 条记录")
    print(f"[信息] 涉及 {len(daily_data)} 天数据")
    
    # 写入各日期文件
    written_files = []
    for date_key, records in sorted(daily_data.items()):
        target_file = target_dir / f'panic_{date_key}.jsonl'
        
        # 读取已存在的记录（去重）
        existing_records = set()
        if target_file.exists():
            with open(target_file, 'r', encoding='utf-8') as f:
                for line in f:
                    existing_records.add(line.strip())
        
        # 合并新旧记录
        all_records = list(existing_records) + [r for r in records if r not in existing_records]
        new_count = len(all_records) - len(existing_records)
        
        # 写入文件
        with open(target_file, 'w', encoding='utf-8') as f:
            for record in all_records:
                f.write(record + '\n')
        
        written_files.append((date_key, len(all_records), new_count))
        print(f"[完成] {date_key}: {len(all_records)} 条记录 (+{new_count} 新增)")
    
    print(f"\n[总结] 成功分割 {len(written_files)} 个日期文件")
    
    # 显示最近5天的数据
    if written_files:
        print("\n最近的数据文件:")
        for date_key, count, new in sorted(written_files)[-5:]:
            print(f"  📅 {date_key[:4]}-{date_key[4:6]}-{date_key[6:]}: {count} 条记录")

if __name__ == '__main__':
    print("=" * 60)
    print("恐慌数据按日分割器")
    print("=" * 60)
    split_panic_data_by_day()
    print("=" * 60)
