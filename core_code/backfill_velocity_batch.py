#!/usr/bin/env python3
"""
批量补全历史velocity数据
从coin_change历史数据中计算并生成velocity数据
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))

def load_coin_change_data(date_str):
    """加载指定日期的coin_change数据"""
    data_file = Path(f'/home/user/webapp/data/coin_change_tracker/coin_change_{date_str}.jsonl')
    
    if not data_file.exists():
        return None, f"数据文件不存在: {data_file}"
    
    records = []
    with open(data_file, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line.strip()))
                except:
                    pass
    
    return records, None

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
    
    return output_file

def process_date(date_str):
    """处理单个日期"""
    print(f"\n{'='*60}")
    print(f"📅 处理日期: {date_str}")
    print(f"{'='*60}")
    
    # 检查velocity文件是否已存在
    velocity_file = Path(f'/home/user/webapp/data/coin_change_tracker/velocity_{date_str}.jsonl')
    if velocity_file.exists():
        existing_count = sum(1 for _ in open(velocity_file))
        print(f"⚠️  velocity文件已存在，包含 {existing_count} 条记录")
        response = input(f"是否覆盖？(y/n，默认n): ").strip().lower()
        if response != 'y':
            print(f"⏭️  跳过 {date_str}")
            return False
    
    # 加载coin_change数据
    records, error = load_coin_change_data(date_str)
    if error:
        print(f"❌ {error}")
        return False
    
    if not records:
        print(f"❌ 没有找到数据")
        return False
    
    print(f"📥 加载了 {len(records)} 条coin_change记录")
    
    # 计算velocity
    velocity_records = calculate_velocity(records)
    print(f"⚡ 计算了 {len(velocity_records)} 条velocity记录")
    
    if not velocity_records:
        print(f"❌ 没有生成velocity数据")
        return False
    
    # 显示样本
    print(f"\n📋 样本数据（前3条）:")
    for i, record in enumerate(velocity_records[:3]):
        print(f"  {i+1}. {record['beijing_time']} | velocity: {record['velocity_5min']:+.2f}%")
    
    print(f"\n📋 样本数据（最后3条）:")
    for i, record in enumerate(velocity_records[-3:]):
        print(f"  {i+1}. {record['beijing_time']} | velocity: {record['velocity_5min']:+.2f}%")
    
    # 保存
    output_file = save_velocity_data(velocity_records, date_str)
    print(f"\n✅ 保存了 {len(velocity_records)} 条记录到: {output_file}")
    
    return True

def main():
    # 获取所有需要处理的日期
    data_dir = Path('/home/user/webapp/data/coin_change_tracker')
    
    # 查找所有2月和3月的coin_change文件
    coin_change_files = sorted(data_dir.glob('coin_change_202602*.jsonl'))
    coin_change_files.extend(sorted(data_dir.glob('coin_change_202603*.jsonl')))
    
    if not coin_change_files:
        print("❌ 没有找到数据文件")
        return
    
    # 提取日期
    dates = []
    for file in coin_change_files:
        date_str = file.stem.replace('coin_change_', '')
        dates.append(date_str)
    
    print(f"\n🔍 找到 {len(dates)} 个日期需要处理")
    print(f"📅 日期范围: {dates[0]} 到 {dates[-1]}")
    
    # 询问是否批量处理
    print(f"\n选择处理模式:")
    print(f"  1. 全部处理（{len(dates)}个日期）")
    print(f"  2. 只处理缺失的velocity文件")
    print(f"  3. 手动选择日期")
    
    choice = input(f"\n请选择 (1/2/3，默认2): ").strip() or '2'
    
    if choice == '1':
        # 全部处理
        dates_to_process = dates
    elif choice == '2':
        # 只处理缺失的
        dates_to_process = []
        for date_str in dates:
            velocity_file = Path(f'/home/user/webapp/data/coin_change_tracker/velocity_{date_str}.jsonl')
            if not velocity_file.exists():
                dates_to_process.append(date_str)
        print(f"\n📊 发现 {len(dates_to_process)} 个日期缺少velocity文件")
    else:
        # 手动选择
        print(f"\n可用日期列表:")
        for i, date_str in enumerate(dates, 1):
            velocity_file = Path(f'/home/user/webapp/data/coin_change_tracker/velocity_{date_str}.jsonl')
            status = "✅" if velocity_file.exists() else "❌"
            print(f"  {i}. {date_str} {status}")
        
        selected = input(f"\n请输入要处理的日期序号（逗号分隔，如: 1,3,5）: ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in selected.split(',')]
            dates_to_process = [dates[i] for i in indices if 0 <= i < len(dates)]
        except:
            print("❌ 输入格式错误")
            return
    
    if not dates_to_process:
        print("\n⚠️  没有需要处理的日期")
        return
    
    print(f"\n📊 将处理 {len(dates_to_process)} 个日期")
    print(f"{'='*60}")
    
    # 批量处理
    success_count = 0
    fail_count = 0
    
    for date_str in dates_to_process:
        try:
            if process_date(date_str):
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"❌ 处理 {date_str} 时出错: {e}")
            fail_count += 1
    
    # 总结
    print(f"\n{'='*60}")
    print(f"📊 处理完成！")
    print(f"✅ 成功: {success_count} 个")
    print(f"❌ 失败: {fail_count} 个")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
