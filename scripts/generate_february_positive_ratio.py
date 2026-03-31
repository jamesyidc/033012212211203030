#!/usr/bin/env python3
"""
批量生成2月份所有日期的正数占比历史数据
从coin_change JSONL文件计算每个时间点的累计正数占比
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta

def calculate_positive_ratio_history(input_file, target_date):
    """
    计算指定日期的正数占比历史数据
    
    Args:
        input_file: coin_change JSONL文件路径
        target_date: 目标日期字符串 YYYY-MM-DD
    
    Returns:
        list: 正数占比历史数据列表
    """
    ratio_data = []
    positive_count = 0
    total_count = 0
    
    with open(input_file, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            
            record = json.loads(line.strip())
            total_change = record.get('cumulative_pct', 0) or record.get('total_change', 0)
            
            # 提取完整时间戳
            timestamp = record.get('beijing_time') or record.get('time', '')
            
            # 🔥 过滤：只保留指定日期的数据
            if ' ' in timestamp:
                record_date = timestamp.split()[0]  # "2026-02-15 15:30:00" -> "2026-02-15"
                # 如果记录日期不是目标日期，跳过
                if record_date != target_date:
                    continue
                time_only = timestamp.split()[1]  # "15:30:00"
            else:
                time_only = timestamp
            
            # 累计统计
            total_count += 1
            if total_change > 0:
                positive_count += 1
            
            # 计算到当前时间点的累计正数占比
            current_ratio = (positive_count / total_count) * 100 if total_count > 0 else 0
            
            ratio_data.append({
                'time': time_only,
                'total_change': round(total_change, 2),
                'is_positive': total_change > 0,
                'positive_ratio': round(current_ratio, 2),
                'positive_count': positive_count,
                'total_count': total_count
            })
    
    return ratio_data


def process_february_dates():
    """处理2月份所有日期"""
    base_dir = Path('/home/user/webapp/data')
    input_dir = base_dir / 'coin_change_tracker'
    output_dir = base_dir / 'positive_ratio_stats'
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 2月份日期范围：2026-02-01 到 2026-02-28
    start_date = datetime(2026, 2, 1)
    end_date = datetime(2026, 2, 28)
    
    results = []
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        date_file_str = current_date.strftime('%Y%m%d')
        
        # 输入文件
        input_file = input_dir / f'coin_change_{date_file_str}.jsonl'
        
        # 输出文件
        output_file = output_dir / f'positive_ratio_{date_file_str}.jsonl'
        
        if not input_file.exists():
            print(f'⚠️  跳过 {date_str}: 输入文件不存在')
            results.append({
                'date': date_str,
                'status': 'skip',
                'reason': 'input_file_not_found'
            })
            current_date += timedelta(days=1)
            continue
        
        try:
            print(f'🔄 处理 {date_str}...')
            
            # 计算正数占比历史
            ratio_data = calculate_positive_ratio_history(input_file, date_str)
            
            if len(ratio_data) == 0:
                print(f'⚠️  {date_str}: 没有数据（可能被日期过滤掉）')
                results.append({
                    'date': date_str,
                    'status': 'no_data',
                    'count': 0
                })
                current_date += timedelta(days=1)
                continue
            
            # 写入输出文件
            with open(output_file, 'w') as f:
                for item in ratio_data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
            # 计算文件大小
            file_size = output_file.stat().st_size
            
            print(f'✅ {date_str}: {len(ratio_data)} 条记录, 文件大小: {file_size / 1024:.1f} KB')
            
            results.append({
                'date': date_str,
                'status': 'success',
                'count': len(ratio_data),
                'file_size': file_size,
                'first_time': ratio_data[0]['time'],
                'last_time': ratio_data[-1]['time'],
                'final_positive_ratio': ratio_data[-1]['positive_ratio']
            })
            
        except Exception as e:
            print(f'❌ {date_str}: 处理失败 - {e}')
            results.append({
                'date': date_str,
                'status': 'error',
                'error': str(e)
            })
        
        current_date += timedelta(days=1)
    
    return results


def main():
    print('=' * 60)
    print('开始批量生成2月份正数占比历史数据')
    print('=' * 60)
    print()
    
    results = process_february_dates()
    
    print()
    print('=' * 60)
    print('处理完成，统计结果：')
    print('=' * 60)
    print()
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    skip_count = sum(1 for r in results if r['status'] == 'skip')
    no_data_count = sum(1 for r in results if r['status'] == 'no_data')
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    print(f'总计: {len(results)} 天')
    print(f'✅ 成功: {success_count} 天')
    print(f'⚠️  跳过: {skip_count} 天')
    print(f'⚠️  无数据: {no_data_count} 天')
    print(f'❌ 错误: {error_count} 天')
    print()
    
    if success_count > 0:
        print('成功处理的日期详情：')
        print('-' * 60)
        for r in results:
            if r['status'] == 'success':
                print(f"{r['date']}: {r['count']:4d} 条记录, "
                      f"{r['first_time']} ~ {r['last_time']}, "
                      f"最终正数占比: {r['final_positive_ratio']:5.1f}%")
    
    print()
    print('=' * 60)


if __name__ == '__main__':
    main()
