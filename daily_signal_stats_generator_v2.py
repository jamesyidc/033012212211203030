#!/usr/bin/env python3
"""
Daily Signal Stats Generator V2 - 从JSONL文件直接生成统计
不依赖数据库，直接从 price_position_*.jsonl 读取数据

功能：
1. 从 price_position_YYYYMMDD.jsonl 读取原始数据
2. 为每个时间点计算24h和2h内的信号统计
3. 生成 signal_stats_sell/buy_YYYYMMDD.jsonl

使用方法：
1. 生成今天的数据: python3 daily_signal_stats_generator_v2.py
2. 生成指定日期: python3 daily_signal_stats_generator_v2.py 2026-02-17
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
import pytz
from collections import defaultdict

# 配置
BASE_DIR = Path(__file__).parent.parent
SOURCE_DIR = BASE_DIR / 'data' / 'price_position'
OUTPUT_DIR = BASE_DIR / 'data' / 'signal_stats'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_beijing_time():
    """获取北京时间"""
    beijing_tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(beijing_tz)

def load_jsonl_data(date_str):
    """
    加载指定日期及前一天的JSONL数据（用于24h窗口计算）
    
    Returns:
        list: 所有记录，按时间排序
    """
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    prev_date = date_obj - timedelta(days=1)
    
    all_records = []
    
    # 加载前一天的数据（用于24h窗口）
    prev_file_str = prev_date.strftime('%Y%m%d')
    prev_file = SOURCE_DIR / f'price_position_{prev_file_str}.jsonl'
    if prev_file.exists():
        with open(prev_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    all_records.append(record)
                except:
                    continue
        print(f"✓ 加载前一天数据: {prev_file.name} ({len([r for r in all_records])}条)")
    
    # 加载目标日期的数据
    curr_file_str = date_obj.strftime('%Y%m%d')
    curr_file = SOURCE_DIR / f'price_position_{curr_file_str}.jsonl'
    if not curr_file.exists():
        print(f"⚠️  文件不存在: {curr_file}")
        return []
    
    current_day_count = 0
    with open(curr_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                all_records.append(record)
                current_day_count += 1
            except:
                continue
    
    print(f"✓ 加载目标日期数据: {curr_file.name} ({current_day_count}条)")
    
    # 按时间排序
    all_records.sort(key=lambda x: x['snapshot_time'])
    
    return all_records

def calculate_signal_counts_from_records(records, target_time_str, window_hours):
    """
    从记录列表中计算指定时间点之前N小时内的信号统计
    
    Args:
        records: 所有记录列表
        target_time_str: 目标时间（字符串格式 'YYYY-MM-DD HH:MM:SS'）
        window_hours: 窗口大小（小时）
    
    Returns:
        tuple: (sell_count, buy_count)
    """
    target_time = datetime.strptime(target_time_str, '%Y-%m-%d %H:%M:%S')
    window_start = target_time - timedelta(hours=window_hours)
    
    sell_count = 0
    buy_count = 0
    
    for record in records:
        record_time_str = record['snapshot_time']
        record_time = datetime.strptime(record_time_str, '%Y-%m-%d %H:%M:%S')
        
        # 只统计窗口内的数据
        if record_time <= window_start or record_time > target_time:
            continue
        
        # 检查信号类型
        summary = record.get('summary', {})
        signal_type = summary.get('signal_type', '')
        signal_triggered = summary.get('signal_triggered', 0)
        
        if signal_triggered == 1:
            if signal_type == '逃顶信号':
                sell_count += 1
            elif signal_type == '抄底信号':
                buy_count += 1
    
    return sell_count, buy_count

def generate_daily_stats_v2(date_str):
    """
    从JSONL文件生成指定日期的完整统计数据
    
    Args:
        date_str: 日期字符串，格式 YYYY-MM-DD
    """
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    date_file_str = date_obj.strftime('%Y%m%d')
    
    print(f"\n{'='*60}")
    print(f"生成 {date_str} 的信号统计数据 (V2 - 从JSONL读取)")
    print(f"{'='*60}")
    
    # 加载数据
    all_records = load_jsonl_data(date_str)
    if not all_records:
        print("⚠️  没有可用数据")
        return
    
    print(f"✓ 总共加载 {len(all_records)} 条记录")
    
    # 准备输出文件
    sell_file = OUTPUT_DIR / f'signal_stats_sell_{date_file_str}.jsonl'
    buy_file = OUTPUT_DIR / f'signal_stats_buy_{date_file_str}.jsonl'
    
    # 判断是否是今天
    beijing_time = get_beijing_time()
    today_str = beijing_time.strftime('%Y-%m-%d')
    is_today = (date_str == today_str)
    
    # 生成时间点（每3分钟）
    time_points = []
    current_time = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 如果是今天，只生成到当前时间；如果是历史日期，生成全天24小时
    if is_today:
        # 只生成到当前时间，向下取整到3分钟
        end_time = beijing_time.replace(tzinfo=None)
        # 向下取整到3分钟边界
        minutes = (end_time.minute // 3) * 3
        end_time = end_time.replace(minute=minutes, second=0, microsecond=0)
        print(f"⚠️  今天的数据，只生成到当前时间: {end_time.strftime('%H:%M:%S')}")
    else:
        # 历史日期，生成全天数据
        end_time = current_time + timedelta(days=1)
    
    while current_time < end_time:
        time_points.append(current_time)
        current_time += timedelta(minutes=3)
    
    print(f"✓ 生成 {len(time_points)} 个时间点")
    
    # 写入数据
    with open(sell_file, 'w', encoding='utf-8') as f_sell, \
         open(buy_file, 'w', encoding='utf-8') as f_buy:
        
        for i, time_point in enumerate(time_points):
            time_str = time_point.strftime('%Y-%m-%d %H:%M:%S')
            
            # 计算24h和2h统计
            sell_24h, buy_24h = calculate_signal_counts_from_records(all_records, time_str, 24)
            sell_2h, buy_2h = calculate_signal_counts_from_records(all_records, time_str, 2)
            
            # 逃顶信号记录
            sell_entry = {
                'time': time_str,
                'sell_24h': sell_24h,
                'sell_2h': sell_2h
            }
            
            # 抄底信号记录
            buy_entry = {
                'time': time_str,
                'buy_24h': buy_24h,
                'buy_2h': buy_2h
            }
            
            f_sell.write(json.dumps(sell_entry, ensure_ascii=False) + '\n')
            f_buy.write(json.dumps(buy_entry, ensure_ascii=False) + '\n')
            
            if (i + 1) % 100 == 0:
                print(f"  已生成 {i+1}/{len(time_points)} 个数据点...")
    
    print(f"✅ 完成！生成 {len(time_points)} 条记录")
    print(f"  逃顶统计: {sell_file}")
    print(f"  抄底统计: {buy_file}")

def main():
    """主函数"""
    if len(sys.argv) == 1:
        # 没有参数，生成今天的数据
        beijing_time = get_beijing_time()
        date_str = beijing_time.strftime('%Y-%m-%d')
        generate_daily_stats_v2(date_str)
    elif len(sys.argv) == 2:
        # 一个参数，生成指定日期
        date_str = sys.argv[1]
        generate_daily_stats_v2(date_str)
    else:
        print("用法:")
        print("  python3 daily_signal_stats_generator_v2.py           # 生成今天的数据")
        print("  python3 daily_signal_stats_generator_v2.py 2026-02-17  # 生成指定日期")

if __name__ == '__main__':
    main()
