#!/usr/bin/env python3
"""
分析0-2点的10分钟上涨占比柱状图统计
统计2月份每天0:00-2:00之间12根柱子的绿/红/黄/灰分布
"""

import json
import os
from datetime import datetime
from collections import defaultdict

# 数据目录
DATA_DIR = "/home/user/webapp/data/coin_change_tracker"

def calculate_up_ratio(changes_dict):
    """计算上涨占比"""
    if not changes_dict:
        return 0.0
    
    up_count = sum(1 for coin, data in changes_dict.items() 
                   if isinstance(data, dict) and data.get('change_pct', 0) > 0)
    total = len(changes_dict)
    return (up_count / total * 100) if total > 0 else 0.0

def classify_bar_color(up_ratio):
    """
    根据上涨占比分类柱子颜色
    - 绿色：上涨占比 > 55%
    - 红色：上涨占比 < 45% 且 > 0
    - 黄色：45% <= 上涨占比 <= 55%
    - 空白：上涨占比 = 0%
    """
    if up_ratio == 0:
        return 'blank'
    elif up_ratio > 55:
        return 'green'
    elif up_ratio >= 45:
        return 'yellow'
    else:
        return 'red'

def analyze_day_file(year, month, day):
    """分析某一天的0-2点数据"""
    date_str = f"{year}{month:02d}{day:02d}"
    file_path = os.path.join(DATA_DIR, f"coin_change_{date_str}.jsonl")
    
    if not os.path.exists(file_path):
        return None
    
    # 按10分钟分组
    groups = defaultdict(lambda: {'sum': 0, 'count': 0})
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                time_str = data.get('beijing_time', '').split(' ')[-1]  # HH:MM:SS
                
                if not time_str:
                    continue
                
                # 解析时间
                hours, minutes, seconds = map(int, time_str.split(':'))
                
                # 只统计0-2点的数据
                if hours >= 2:
                    continue
                
                total_minutes = hours * 60 + minutes
                group_index = total_minutes // 10  # 10分钟一组
                
                # 计算上涨占比
                changes = data.get('changes', {})
                up_ratio = calculate_up_ratio(changes)
                
                groups[group_index]['sum'] += up_ratio
                groups[group_index]['count'] += 1
                
            except Exception as e:
                continue
    
    # 计算每个10分钟区间的平均上涨占比
    bar_data = []
    for i in range(12):  # 0-2点共12个10分钟区间
        if i in groups and groups[i]['count'] > 0:
            avg_ratio = groups[i]['sum'] / groups[i]['count']
            color = classify_bar_color(avg_ratio)
            bar_data.append({
                'interval': f"{i*10//60:02d}:{i*10%60:02d}-{(i+1)*10//60:02d}:{(i+1)*10%60:02d}",
                'up_ratio': round(avg_ratio, 2),
                'color': color,
                'samples': groups[i]['count']
            })
        else:
            bar_data.append({
                'interval': f"{i*10//60:02d}:{i*10%60:02d}-{(i+1)*10//60:02d}:{(i+1)*10%60:02d}",
                'up_ratio': 0,
                'color': 'blank',
                'samples': 0
            })
    
    return bar_data

def analyze_february():
    """分析2月份所有数据"""
    print("=" * 80)
    print("📊 2月份0-2点上涨占比柱状图统计分析")
    print("=" * 80)
    print()
    
    # 统计所有天的颜色分布
    color_stats = defaultdict(int)
    day_results = []
    
    for day in range(1, 25):  # 2月1日-24日
        date_str = f"2026{2:02d}{day:02d}"
        bars = analyze_day_file(2026, 2, day)
        
        if bars:
            day_color_count = {'green': 0, 'red': 0, 'yellow': 0, 'blank': 0}
            
            for bar in bars:
                color = bar['color']
                color_stats[color] += 1
                day_color_count[color] += 1
            
            day_results.append({
                'date': date_str,
                'bars': bars,
                'color_count': day_color_count
            })
    
    # 输出总体统计
    total_bars = sum(color_stats.values())
    if total_bars == 0:
        print("⚠️  没有找到0-2点的数据，可能数据采集时间不包含0-2点区间")
        return
    
    print(f"📅 统计周期：2026年2月1日 - 2月24日")
    print(f"📊 总柱子数：{total_bars} 根（{len(day_results)}天 × 12根）")
    print()
    
    print("🎨 颜色分布统计：")
    print("-" * 80)
    print(f"🟢 绿色柱子（上涨>55%） : {color_stats['green']:3d} 根 ({color_stats['green']/total_bars*100:5.1f}%)")
    print(f"🔴 红色柱子（上涨<45%） : {color_stats['red']:3d} 根 ({color_stats['red']/total_bars*100:5.1f}%)")
    print(f"🟡 黄色柱子（45-55%）   : {color_stats['yellow']:3d} 根 ({color_stats['yellow']/total_bars*100:5.1f}%)")
    print(f"⚪ 空白柱子（上涨=0%）  : {color_stats['blank']:3d} 根 ({color_stats['blank']/total_bars*100:5.1f}%)")
    if color_stats['no_data'] > 0:
        print(f"⬛ 无数据柱子         : {color_stats['no_data']:3d} 根 ({color_stats['no_data']/total_bars*100:5.1f}%)")
    print("-" * 80)
    print()
    
    # 输出每天的详细统计
    print("📆 每日详细统计：")
    print("=" * 80)
    
    for result in day_results:
        date = result['date']
        date_formatted = f"{date[0:4]}-{date[4:6]}-{date[6:8]}"
        counts = result['color_count']
        
        print(f"\n📅 {date_formatted}")
        print(f"   🟢 绿: {counts['green']:2d} | 🔴 红: {counts['red']:2d} | 🟡 黄: {counts['yellow']:2d} | ⚪ 空白: {counts['blank']:2d}")
        
        # 显示每个柱子的详细数据
        for bar in result['bars']:
            color_emoji = {
                'green': '🟢',
                'red': '🔴',
                'yellow': '🟡',
                'blank': '⚪'
            }
            emoji = color_emoji.get(bar['color'], '❓')
            
            if bar['samples'] > 0:
                print(f"   {emoji} {bar['interval']}: {bar['up_ratio']:5.1f}% (样本数:{bar['samples']:2d})")
            else:
                print(f"   {emoji} {bar['interval']}: 无数据")
    
    print()
    print("=" * 80)
    
    # 保存统计结果到JSON
    output_file = "/home/user/webapp/data/coin_change_tracker/0_2am_bars_analysis.json"
    summary = {
        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'period': '2026-02-01 to 2026-02-24',
        'total_days': len(day_results),
        'total_bars': total_bars,
        'color_distribution': {
            'green': {
                'count': color_stats['green'],
                'percentage': round(color_stats['green']/total_bars*100, 2),
                'description': '上涨>55%'
            },
            'red': {
                'count': color_stats['red'],
                'percentage': round(color_stats['red']/total_bars*100, 2),
                'description': '上涨<45%'
            },
            'yellow': {
                'count': color_stats['yellow'],
                'percentage': round(color_stats['yellow']/total_bars*100, 2),
                'description': '45%≤上涨≤55%'
            },
            'blank': {
                'count': color_stats['blank'],
                'percentage': round(color_stats['blank']/total_bars*100, 2),
                'description': '上涨=0%'
            }
        },
        'daily_results': day_results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"📁 详细统计结果已保存到: {output_file}")
    print()

if __name__ == '__main__':
    analyze_february()
