#!/usr/bin/env python3
"""
分析2月份行情预判统计
统计各种预判信号的出现次数和准确率
"""

import json
import os
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# 数据目录
DATA_DIR = Path("/home/user/webapp/data/daily_predictions")

def analyze_february_predictions():
    """分析2月份的预判数据"""
    print("=" * 80)
    print("📊 2月份行情预判统计分析（0-2点分析）")
    print("=" * 80)
    print()
    
    # 统计各种信号的数量
    signal_counts = defaultdict(int)
    color_distribution = {
        'green': [],
        'red': [],
        'yellow': [],
        'blank': []
    }
    
    predictions = []
    
    # 遍历2月份的所有预判文件
    for day in range(1, 25):  # 2月1日-24日
        date_str = f"2026-02-{day:02d}"
        file_path = DATA_DIR / f"prediction_{date_str}.json"
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                signal = data.get('signal', '')
                color_counts = data.get('color_counts', {})
                
                # 统计信号
                if signal:
                    signal_counts[signal] += 1
                
                # 统计颜色
                for color in ['green', 'red', 'yellow', 'blank']:
                    count = color_counts.get(color, 0)
                    color_distribution[color].append(count)
                
                predictions.append({
                    'date': date_str,
                    'signal': signal,
                    'description': data.get('description', ''),
                    'color_counts': color_counts
                })
    
    total_days = len(predictions)
    
    print(f"📅 统计周期：2026年2月1日 - 2月24日")
    print(f"📊 有效预判天数：{total_days} 天")
    print()
    
    # 输出信号分布统计
    print("🎯 预判信号分布统计：")
    print("-" * 80)
    
    # 按数量排序
    sorted_signals = sorted(signal_counts.items(), key=lambda x: x[1], reverse=True)
    
    for signal, count in sorted_signals:
        percentage = (count / total_days * 100) if total_days > 0 else 0
        
        # 根据信号类型选择emoji
        emoji_map = {
            '等待新低': '⚠️',
            '做空': '🔴',
            '观望': '⚪',
            '低吸': '🟢',
            '诱空试盘抄底': '💰',
            '诱多不参与': '🚫',
            '空头强控盘': '⬛'
        }
        emoji = emoji_map.get(signal, '❓')
        
        bar_length = int(count / total_days * 40)
        bar = '█' * bar_length
        
        print(f"{emoji} {signal:12s}: {count:2d} 天 ({percentage:5.1f}%) {bar}")
    
    print("-" * 80)
    print()
    
    # 输出颜色统计
    print("🎨 柱状图颜色分布统计（平均值）：")
    print("-" * 80)
    
    for color, values in color_distribution.items():
        if values:
            avg = sum(values) / len(values)
            total_count = sum(values)
            
            color_names = {
                'green': '🟢 绿色柱子',
                'red': '🔴 红色柱子',
                'yellow': '🟡 黄色柱子',
                'blank': '⚪ 空白柱子'
            }
            
            print(f"{color_names[color]}: 平均 {avg:.1f} 根/天, 总计 {total_count:3d} 根")
    
    print("-" * 80)
    print()
    
    # 输出每日详细预判
    print("📆 每日预判详情：")
    print("=" * 80)
    
    for pred in predictions:
        date = pred['date']
        signal = pred['signal']
        counts = pred['color_counts']
        
        # 格式化颜色计数
        green = counts.get('green', 0)
        red = counts.get('red', 0)
        yellow = counts.get('yellow', 0)
        blank = counts.get('blank', 0)
        
        emoji_map = {
            '等待新低': '⚠️',
            '做空': '🔴',
            '观望': '⚪',
            '低吸': '🟢',
            '诱空试盘抄底': '💰',
            '诱多不参与': '🚫',
            '空头强控盘': '⬛'
        }
        emoji = emoji_map.get(signal, '❓')
        
        print(f"\n📅 {date}")
        print(f"   {emoji} 预判: {signal}")
        print(f"   🟢:{green:2d} | 🔴:{red:2d} | 🟡:{yellow:2d} | ⚪:{blank:2d}")
        print(f"   说明: {pred['description']}")
    
    print()
    print("=" * 80)
    
    # 保存统计结果
    output_file = "/home/user/webapp/data/daily_predictions/predictions_summary.json"
    summary = {
        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'period': '2026-02-01 to 2026-02-24',
        'total_days': total_days,
        'signal_distribution': dict(signal_counts),
        'color_statistics': {
            'green': {
                'total': sum(color_distribution['green']),
                'average': sum(color_distribution['green']) / len(color_distribution['green']) if color_distribution['green'] else 0
            },
            'red': {
                'total': sum(color_distribution['red']),
                'average': sum(color_distribution['red']) / len(color_distribution['red']) if color_distribution['red'] else 0
            },
            'yellow': {
                'total': sum(color_distribution['yellow']),
                'average': sum(color_distribution['yellow']) / len(color_distribution['yellow']) if color_distribution['yellow'] else 0
            },
            'blank': {
                'total': sum(color_distribution['blank']),
                'average': sum(color_distribution['blank']) / len(color_distribution['blank']) if color_distribution['blank'] else 0
            }
        },
        'daily_predictions': predictions
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"📁 详细统计结果已保存到: {output_file}")
    print()

if __name__ == '__main__':
    analyze_february_predictions()
