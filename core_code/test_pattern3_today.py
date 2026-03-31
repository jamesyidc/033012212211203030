#!/usr/bin/env python3
"""测试筑底信号检测 - 今天的数据"""

import json
import sys
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, '/home/user/webapp')

def determine_bar_color(up_ratio):
    """判断柱子颜色"""
    if up_ratio == 0:
        return 'blank'
    elif up_ratio > 55:
        return 'green'
    elif 45 <= up_ratio <= 55:
        return 'yellow'
    else:
        return 'red'

def aggregate_to_10min_bars():
    """将数据聚合为10分钟柱子"""
    jsonl_file = "data/coin_change_tracker/coin_change_20260226.jsonl"
    
    # 读取数据
    data = []
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    
    print(f"✓ 读取到 {len(data)} 条记录")
    
    # 按10分钟聚合
    buckets = {}
    for record in data:
        time_str = record.get('beijing_time', '')
        if not time_str:
            continue
        
        try:
            dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            bucket_minute = (dt.minute // 10) * 10
            bucket_key = f"{dt.hour:02d}:{bucket_minute:02d}"
            
            if bucket_key not in buckets:
                buckets[bucket_key] = []
            
            buckets[bucket_key].append({
                'time': time_str,
                'up_ratio': record.get('up_ratio', 0),
                'total_change': record.get('cumulative_pct', 0)
            })
        except:
            continue
    
    # 计算每个时段的平均值
    bars = []
    for key in sorted(buckets.keys()):
        records = buckets[key]
        avg_up_ratio = sum(r['up_ratio'] for r in records) / len(records)
        avg_total_change = sum(r['total_change'] for r in records) / len(records)
        color = determine_bar_color(avg_up_ratio)
        
        bars.append({
            'time': key,
            'up_ratio': avg_up_ratio,
            'total_change': avg_total_change,
            'color': color,
            'count': len(records)
        })
    
    return bars

def check_pattern_3(bars):
    """检查筑底信号：黄→绿→黄"""
    detected_patterns = []
    
    # 从最新的柱子开始向前检查
    for i in range(len(bars) - 3, -1, -1):
        colors = [bars[i]['color'], bars[i+1]['color'], bars[i+2]['color']]
        
        # 检查是否匹配模式：黄→绿→黄
        if colors == ['yellow', 'green', 'yellow']:
            trigger_bar = bars[i+2]
            total_change = trigger_bar['total_change']
            
            # 判断是否满足开仓确认条件：27个币涨跌幅总和 < 10%
            can_open_position = (total_change < 10)
            
            pattern_result = {
                'pattern': 'pattern_3',
                'pattern_name': '筑底信号',
                'pattern_type': '黄→绿→黄',
                'time_range': f"{bars[i]['time']} - {bars[i+2]['time']}",
                'bars': [
                    {'time': bars[i]['time'], 'up_ratio': bars[i]['up_ratio'], 'color': bars[i]['color']},
                    {'time': bars[i+1]['time'], 'up_ratio': bars[i+1]['up_ratio'], 'color': bars[i+1]['color']},
                    {'time': bars[i+2]['time'], 'up_ratio': bars[i+2]['up_ratio'], 'color': bars[i+2]['color']}
                ],
                'detected_at': bars[i+2]['time'],
                'trigger_ratio': trigger_bar['up_ratio'],
                'total_change': total_change,
                'can_open_position': can_open_position,
                'open_condition': f"涨跌幅总和{total_change:.2f}% {'<' if can_open_position else '≥'} 10%"
            }
            
            detected_patterns.append(pattern_result)
            break  # 只返回最新的一个
    
    return detected_patterns

def main():
    print("\n=== 筑底信号检测测试 ===\n")
    
    # 1. 聚合10分钟柱子
    bars = aggregate_to_10min_bars()
    print(f"✓ 聚合为 {len(bars)} 个10分钟柱子\n")
    
    # 2. 显示10:00-11:30的柱子
    print("=== 10:00-11:30 柱子情况 ===\n")
    for bar in bars:
        hour = int(bar['time'].split(':')[0])
        if 10 <= hour <= 11:
            emoji = {'green': '🟢', 'yellow': '🟡', 'red': '🔴', 'blank': '⚪'}.get(bar['color'], '')
            print(f"{bar['time']} {emoji} {bar['color']:6s}  上涨占比: {bar['up_ratio']:5.2f}%  累计涨跌: {bar['total_change']:6.2f}%")
    
    # 3. 检测筑底信号
    print("\n=== 筑底信号检测结果 ===\n")
    patterns = check_pattern_3(bars)
    
    if patterns:
        for p in patterns:
            print(f"✅ 检测到筑底信号！\n")
            print(f"模式: {p['pattern_type']}")
            print(f"时间范围: {p['time_range']}")
            print(f"\n连续柱子:")
            for bar in p['bars']:
                emoji = {'green': '🟢', 'yellow': '🟡', 'red': '🔴', 'blank': '⚪'}.get(bar['color'], '')
                print(f"  {bar['time']} {emoji} {bar['color']:6s}  上涨占比: {bar['up_ratio']:5.2f}%")
            
            print(f"\n触发信息:")
            print(f"  检测时间: {p['detected_at']}")
            print(f"  触发时上涨占比: {p['trigger_ratio']:.2f}%")
            print(f"  涨跌幅总和: {p['total_change']:.2f}%")
            print(f"  开仓确认: {p['open_condition']}")
            print(f"  是否满足开仓条件: {'✅ 是' if p['can_open_position'] else '❌ 否'}")
    else:
        print("❌ 未检测到筑底信号")
    
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    main()
