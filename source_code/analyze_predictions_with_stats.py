#!/usr/bin/env python3
"""
分析2月份行情预判统计，并计算每天的最低点、最高点、最高涨幅
按预测信号分组显示相同信号的日期及其统计数据
"""

import json
import os
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# 数据目录
PREDICTIONS_DIR = Path("/home/user/webapp/data/daily_predictions")
TRACKER_DIR = Path("/home/user/webapp/data/coin_change_tracker")

def load_daily_data(date_str):
    """加载某一天的coin_change数据"""
    file_path = TRACKER_DIR / f"coin_change_{date_str.replace('-', '')}.jsonl"
    
    if not file_path.exists():
        return None
    
    data_points = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data_points.append(json.loads(line))
        return data_points
    except Exception as e:
        print(f"❌ 读取数据文件失败 {file_path}: {e}")
        return None

def calculate_daily_stats(data_points):
    """
    计算当天的最低点、最高点、最高涨幅
    返回: {
        'lowest': 最低点 (total_change),
        'highest': 最高点 (total_change),
        'max_increase': 最高涨幅 (从最低到最高)
    }
    """
    if not data_points:
        return None
    
    total_changes = [point.get('total_change', 0) for point in data_points]
    
    if not total_changes:
        return None
    
    lowest = min(total_changes)
    highest = max(total_changes)
    
    # 计算最高涨幅（从最低点到最高点）
    max_increase = highest - lowest
    
    return {
        'lowest': round(lowest, 2),
        'highest': round(highest, 2),
        'max_increase': round(max_increase, 2)
    }

def analyze_predictions_with_stats():
    """分析2月份的预判数据，并附加每日统计数据"""
    print("=" * 80)
    print("📊 2月份行情预判统计分析（含当日最低点、最高点、最高涨幅）")
    print("=" * 80)
    print()
    
    # 按信号分组
    signal_groups = defaultdict(list)
    
    # 遍历2月份的所有预判文件（动态获取到今天）
    from datetime import date
    today = date.today()
    # 如果是2月份，统计到今天；否则统计到2月29日
    if today.month == 2 and today.year == 2026:
        last_day = today.day
    else:
        last_day = 29  # 2026年2月有29天（闰年）
    
    for day in range(1, last_day + 1):  # 2月1日到最后一天
        date_str = f"2026-02-{day:02d}"
        prediction_file = PREDICTIONS_DIR / f"prediction_{date_str}.json"
        
        if not prediction_file.exists():
            continue
        
        # 读取预测数据
        with open(prediction_file, 'r', encoding='utf-8') as f:
            prediction = json.load(f)
        
        signal = prediction.get('signal', '未知')
        
        # 读取当天的交易数据
        daily_data = load_daily_data(date_str)
        
        if daily_data:
            stats = calculate_daily_stats(daily_data)
        else:
            stats = {
                'lowest': 0,
                'highest': 0,
                'max_increase': 0
            }
        
        # 组合数据
        day_info = {
            'date': date_str,
            'signal': signal,
            'color_counts': prediction.get('color_counts', {}),
            'description': prediction.get('description', ''),
            'stats': stats
        }
        
        signal_groups[signal].append(day_info)
    
    # 统计信号分布
    print("🎯 预判信号分布统计：")
    print("-" * 80)
    
    # 信号emoji映射
    emoji_map = {
        '等待新低': '⚠️',
        '做空': '🔴',
        '观望': '⚪',
        '低吸': '🟢',
        '诱空试盘抄底': '💰',
        '诱多不参与': '🚫',
        '空头强控盘': '⬛'
    }
    
    total_days = sum(len(days) for days in signal_groups.values())
    
    # 按天数排序
    sorted_signals = sorted(signal_groups.items(), key=lambda x: len(x[1]), reverse=True)
    
    for signal, days in sorted_signals:
        count = len(days)
        percentage = (count / total_days * 100) if total_days > 0 else 0
        emoji = emoji_map.get(signal, '❓')
        bar_length = int(count / total_days * 40)
        bar = '█' * bar_length
        
        print(f"{emoji} {signal:12s}: {count:2d} 天 ({percentage:5.1f}%) {bar}")
    
    print("-" * 80)
    print()
    
    # 按信号分组显示详细数据
    print("📆 按预判信号分组显示日期及统计数据：")
    print("=" * 80)
    
    for signal, days in sorted_signals:
        emoji = emoji_map.get(signal, '❓')
        print(f"\n{emoji} 【{signal}】 ({len(days)} 天)")
        print("-" * 80)
        
        # 按日期排序
        days.sort(key=lambda x: x['date'])
        
        for day_info in days:
            date = day_info['date']
            stats = day_info['stats']
            counts = day_info['color_counts']
            
            green = counts.get('green', 0)
            red = counts.get('red', 0)
            yellow = counts.get('yellow', 0)
            blank = counts.get('blank', 0)
            
            print(f"\n  📅 {date}")
            print(f"     柱状图: 🟢×{green:2d} 🔴×{red:2d} 🟡×{yellow:2d} ⚪×{blank:2d}")
            
            if stats:
                print(f"     📉 最低点: {stats['lowest']:8.2f}%")
                print(f"     📈 最高点: {stats['highest']:8.2f}%")
                print(f"     📊 最高涨幅: {stats['max_increase']:8.2f}%")
            else:
                print(f"     ⚠️  无数据")
            
            print(f"     💡 {day_info['description']}")
        
        print()
    
    print("=" * 80)
    
    # 保存统计结果
    output_file = PREDICTIONS_DIR / "predictions_with_stats.json"
    
    # 动态计算period（使用实际统计到的最后一天）
    period_end = f"2026-02-{last_day:02d}"
    
    summary = {
        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'period': f'2026-02-01 to {period_end}',
        'total_days': total_days,
        'signal_groups': {
            signal: [
                {
                    'date': day['date'],
                    'color_counts': day['color_counts'],
                    'stats': day['stats'],
                    'description': day['description']
                }
                for day in days
            ]
            for signal, days in signal_groups.items()
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 详细统计结果已保存到: {output_file}")
    print()

if __name__ == '__main__':
    analyze_predictions_with_stats()
