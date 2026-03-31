#!/usr/bin/env python3
"""
补全历史velocity数据
从coin_change历史数据中计算并生成velocity数据
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))

def load_coin_change_data(date_str):
    """加载指定日期的coin_change数据"""
    data_file = Path(f'/home/user/webapp/data/coin_change_tracker/coin_change_{date_str}.jsonl')
    
    if not data_file.exists():
        print(f"❌ 数据文件不存在: {data_file}")
        return []
    
    records = []
    with open(data_file, 'r') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line.strip()))
    
    return records

def calculate_velocity(records):
    """计算5分钟涨速"""
    velocity_records = []
    
    for i in range(len(records)):
        current = records[i]
        current_total_change = current.get('total_change', 0)
        current_time = current.get('beijing_time', '')
        current_timestamp = current.get('timestamp', 0)
        
        # 查找5分钟前的数据（向前查找5-7分钟内的数据）
        total_change_5min_ago = None
        
        for j in range(max(0, i-7), max(0, i-3)):
            if j < len(records):
                prev = records[j]
                prev_time = prev.get('beijing_time', '')
                
                # 计算时间差（分钟）
                if current_time and prev_time:
                    try:
                        current_dt = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
                        prev_dt = datetime.strptime(prev_time, '%Y-%m-%d %H:%M:%S')
                        time_diff = (current_dt - prev_dt).total_seconds() / 60
                        
                        # 如果时间差在4-6分钟之间，认为是5分钟前
                        if 4 <= time_diff <= 6:
                            total_change_5min_ago = prev.get('total_change', 0)
                            break
                    except:
                        pass
        
        # 如果找不到5分钟前的数据，跳过
        if total_change_5min_ago is None:
            continue
        
        # 计算涨速
        velocity_5min = round(current_total_change - total_change_5min_ago, 2)
        
        velocity_record = {
            'timestamp': current_timestamp,
            'beijing_time': current_time,
            'velocity_5min': velocity_5min,
            'current_total_change': round(current_total_change, 2),
            'total_change_5min_ago': round(total_change_5min_ago, 2)
        }
        
        velocity_records.append(velocity_record)
    
    return velocity_records

def save_velocity_data(velocity_records, date_str):
    """保存velocity数据"""
    output_file = Path(f'/home/user/webapp/data/coin_change_tracker/velocity_{date_str}.jsonl')
    
    with open(output_file, 'w') as f:
        for record in velocity_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"✅ 保存了 {len(velocity_records)} 条velocity记录到: {output_file}")

def main():
    # 补全今天的数据
    today = datetime.now(BEIJING_TZ).strftime('%Y%m%d')
    
    print(f"📊 开始补全 {today} 的velocity数据...")
    
    # 加载coin_change数据
    records = load_coin_change_data(today)
    print(f"📥 加载了 {len(records)} 条coin_change记录")
    
    if not records:
        print("❌ 没有找到数据，退出")
        return
    
    # 计算velocity
    velocity_records = calculate_velocity(records)
    print(f"⚡ 计算了 {len(velocity_records)} 条velocity记录")
    
    if not velocity_records:
        print("❌ 没有生成velocity数据，退出")
        return
    
    # 显示样本
    if velocity_records:
        print("\n📋 样本数据（前3条）:")
        for i, record in enumerate(velocity_records[:3]):
            print(f"  {i+1}. {record['beijing_time']} | velocity: {record['velocity_5min']:+.2f}% | current: {record['current_total_change']:.2f}% | 5min ago: {record['total_change_5min_ago']:.2f}%")
        
        print("\n📋 样本数据（最后3条）:")
        for i, record in enumerate(velocity_records[-3:]):
            print(f"  {i+1}. {record['beijing_time']} | velocity: {record['velocity_5min']:+.2f}% | current: {record['current_total_change']:.2f}% | 5min ago: {record['total_change_5min_ago']:.2f}%")
    
    # 保存
    save_velocity_data(velocity_records, today)
    
    print("\n✅ 补全完成！")

if __name__ == '__main__':
    main()
