#!/usr/bin/env python3
"""
检查今天所有的模式并返回（API版本）
"""

import json
import sys
sys.path.insert(0, '/home/user/webapp')

from datetime import datetime, timedelta

def calculate_up_ratio(records):
    """计算上涨占比"""
    if not records:
        return 0
    up_count = sum(1 for r in records if r.get('total_change', 0) > 0)
    return (up_count / len(records)) * 100

def determine_color(up_ratio):
    """判断颜色"""
    if up_ratio == 0:
        return 'blank', '⚪'
    elif up_ratio > 55:
        return 'green', '🟢'
    elif up_ratio >= 45:
        return 'yellow', '🟡'
    else:
        return 'red', '🔴'

def check_all_patterns():
    """检查今天所有的模式"""
    beijing_time = datetime.now() + timedelta(hours=8)
    today_str = beijing_time.strftime('%Y%m%d')
    file_path = f'data/coin_change_tracker/coin_change_{today_str}.jsonl'
    
    # 读取数据
    records = []
    with open(file_path, 'r') as f:
        for line in f:
            records.append(json.loads(line.strip()))
    
    # 获取当前涨跌幅总和
    total_change = records[-1].get('total_change', 0) if records else 0
    
    # 生成10分钟柱子
    bars = []
    start_time = beijing_time.replace(hour=2, minute=0, second=0, microsecond=0)
    current_time = start_time
    
    while current_time < beijing_time:
        target_time = current_time.strftime('%H:%M')
        start_hour, start_min = current_time.hour, current_time.minute
        
        interval_records = []
        for r in records:
            time_str = r.get('beijing_time') or r.get('time', '')
            if not time_str:
                continue
            
            try:
                record_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                if record_time.tzinfo is not None:
                    record_time = record_time.astimezone(None).replace(tzinfo=None) + timedelta(hours=8)
                
                if record_time.hour == start_hour and start_min <= record_time.minute < start_min + 10:
                    interval_records.append(r)
            except:
                continue
        
        if interval_records:
            up_ratio = calculate_up_ratio(interval_records)
            color, emoji = determine_color(up_ratio)
            
            bars.append({
                'time': target_time,
                'up_ratio': up_ratio,
                'color': color,
                'emoji': emoji
            })
        
        current_time += timedelta(minutes=10)
    
    # 检测所有模式（分为满足和不满足条件两类）
    qualified_patterns = []      # 满足触发条件的
    unqualified_patterns = []    # 不满足触发条件的
    
    # 模式1：红→黄→绿 或 绿→黄→红（3根），红→黄→黄→绿（4根）
    # 检查4根模式
    if len(bars) >= 4:
        for i in range(len(bars) - 3):
            colors = [bars[i]['color'], bars[i+1]['color'], bars[i+2]['color'], bars[i+3]['color']]
            
            if colors == ['red', 'yellow', 'yellow', 'green']:
                trigger_ratio = bars[i+3]['up_ratio']
                pattern_data = {
                    'pattern': 'pattern_1',
                    'pattern_name': '诱多等待新低',
                    'pattern_type': '红→黄→黄→绿 (4根)',
                    'signal': '逢高做空',
                    'time_range': f"{bars[i]['time']} - {bars[i+3]['time']}",
                    'bars': [
                        f"{bars[i]['time']} {bars[i]['emoji']} {bars[i]['up_ratio']:.1f}%",
                        f"{bars[i+1]['time']} {bars[i+1]['emoji']} {bars[i+1]['up_ratio']:.1f}%",
                        f"{bars[i+2]['time']} {bars[i+2]['emoji']} {bars[i+2]['up_ratio']:.1f}%",
                        f"{bars[i+3]['time']} {bars[i+3]['emoji']} {bars[i+3]['up_ratio']:.1f}%"
                    ],
                    'trigger_time': bars[i+3]['time'],
                    'trigger_ratio': trigger_ratio
                }
                
                if trigger_ratio >= 65:  # 满足条件
                    qualified_patterns.append(pattern_data)
                else:  # 不满足条件
                    pattern_data['failure_reasons'] = [f'最后一根柱子上涨占比 {trigger_ratio:.2f}% < 65% (需要 ≥65%)']
                    unqualified_patterns.append(pattern_data)
    
    # 检查3根模式
    if len(bars) >= 3:
        for i in range(len(bars) - 2):
            colors = [bars[i]['color'], bars[i+1]['color'], bars[i+2]['color']]
            
            # 模式1: 红→黄→绿 或 绿→黄→红
            if colors == ['red', 'yellow', 'green'] or colors == ['green', 'yellow', 'red']:
                pattern_type = "红→黄→绿" if colors == ['red', 'yellow', 'green'] else "绿→黄→红"
                trigger_ratio = bars[i+2]['up_ratio']
                pattern_data = {
                    'pattern': 'pattern_1',
                    'pattern_name': '诱多等待新低',
                    'pattern_type': f'{pattern_type} (3根)',
                    'signal': '逢高做空',
                    'time_range': f"{bars[i]['time']} - {bars[i+2]['time']}",
                    'bars': [
                        f"{bars[i]['time']} {bars[i]['emoji']} {bars[i]['up_ratio']:.1f}%",
                        f"{bars[i+1]['time']} {bars[i+1]['emoji']} {bars[i+1]['up_ratio']:.1f}%",
                        f"{bars[i+2]['time']} {bars[i+2]['emoji']} {bars[i+2]['up_ratio']:.1f}%"
                    ],
                    'trigger_time': bars[i+2]['time'],
                    'trigger_ratio': trigger_ratio
                }
                
                if trigger_ratio >= 65:  # 满足条件
                    qualified_patterns.append(pattern_data)
                else:  # 不满足条件
                    pattern_data['failure_reasons'] = [f'最后一根柱子上涨占比 {trigger_ratio:.2f}% < 65% (需要 ≥65%)']
                    unqualified_patterns.append(pattern_data)
            
            # 模式3: 黄→绿→黄（筑底信号）
            if colors == ['yellow', 'green', 'yellow']:
                trigger_ratio = bars[i+2]['up_ratio']
                pattern_data = {
                    'pattern': 'pattern_3',
                    'pattern_name': '筑底信号',
                    'pattern_type': '黄→绿→黄 (3根)',
                    'signal': '逢低做多',
                    'time_range': f"{bars[i]['time']} - {bars[i+2]['time']}",
                    'bars': [
                        f"{bars[i]['time']} {bars[i]['emoji']} {bars[i]['up_ratio']:.1f}%",
                        f"{bars[i+1]['time']} {bars[i+1]['emoji']} {bars[i+1]['up_ratio']:.1f}%",
                        f"{bars[i+2]['time']} {bars[i+2]['emoji']} {bars[i+2]['up_ratio']:.1f}%"
                    ],
                    'trigger_time': bars[i+2]['time'],
                    'trigger_ratio': trigger_ratio,
                    'total_change': total_change
                }
                
                # 检查两个条件
                failure_reasons = []
                if trigger_ratio >= 10:
                    failure_reasons.append(f'最后一根柱子上涨占比 {trigger_ratio:.2f}% >= 10% (需要 <10%)')
                if total_change >= -50:
                    failure_reasons.append(f'当日涨跌幅总和 {total_change:.2f}% >= -50% (需要 < -50%)')
                
                if not failure_reasons:  # 满足所有条件
                    qualified_patterns.append(pattern_data)
                else:  # 不满足条件
                    pattern_data['failure_reasons'] = failure_reasons
                    unqualified_patterns.append(pattern_data)
            
            # 模式4: 绿→红→绿（诱空信号）
            if colors == ['green', 'red', 'green']:
                middle_ratio = bars[i+1]['up_ratio']
                pattern_data = {
                    'pattern': 'pattern_4',
                    'pattern_name': '诱空信号',
                    'pattern_type': '绿→红→绿 (3根)',
                    'signal': '逢低做多',
                    'time_range': f"{bars[i]['time']} - {bars[i+2]['time']}",
                    'bars': [
                        f"{bars[i]['time']} {bars[i]['emoji']} {bars[i]['up_ratio']:.1f}%",
                        f"{bars[i+1]['time']} {bars[i+1]['emoji']} {bars[i+1]['up_ratio']:.1f}%",
                        f"{bars[i+2]['time']} {bars[i+2]['emoji']} {bars[i+2]['up_ratio']:.1f}%"
                    ],
                    'trigger_time': bars[i+1]['time'],
                    'trigger_ratio': middle_ratio
                }
                
                if middle_ratio < 10:  # 满足条件
                    qualified_patterns.append(pattern_data)
                else:  # 不满足条件
                    pattern_data['failure_reasons'] = [f'中间红色柱子上涨占比 {middle_ratio:.2f}% >= 10% (需要 <10%)']
                    unqualified_patterns.append(pattern_data)
    
    # 检查4根模式4（绿→红→红→绿）
    if len(bars) >= 4:
        for i in range(len(bars) - 3):
            colors = [bars[i]['color'], bars[i+1]['color'], bars[i+2]['color'], bars[i+3]['color']]
            
            if colors == ['green', 'red', 'red', 'green']:
                middle_ratio_1 = bars[i+1]['up_ratio']
                middle_ratio_2 = bars[i+2]['up_ratio']
                pattern_data = {
                    'pattern': 'pattern_4',
                    'pattern_name': '诱空信号',
                    'pattern_type': '绿→红→红→绿 (4根)',
                    'signal': '逢低做多',
                    'time_range': f"{bars[i]['time']} - {bars[i+3]['time']}",
                    'bars': [
                        f"{bars[i]['time']} {bars[i]['emoji']} {bars[i]['up_ratio']:.1f}%",
                        f"{bars[i+1]['time']} {bars[i+1]['emoji']} {bars[i+1]['up_ratio']:.1f}%",
                        f"{bars[i+2]['time']} {bars[i+2]['emoji']} {bars[i+2]['up_ratio']:.1f}%",
                        f"{bars[i+3]['time']} {bars[i+3]['emoji']} {bars[i+3]['up_ratio']:.1f}%"
                    ],
                    'trigger_time': bars[i+1]['time'],
                    'trigger_ratio': [middle_ratio_1, middle_ratio_2]
                }
                
                if middle_ratio_1 < 10 and middle_ratio_2 < 10:  # 满足条件
                    qualified_patterns.append(pattern_data)
                else:  # 不满足条件
                    pattern_data['failure_reasons'] = [f'中间红色柱子上涨占比 [{middle_ratio_1:.2f}%, {middle_ratio_2:.2f}%] 存在 ≥10% 的情况 (需要全部 <10%)']
                    unqualified_patterns.append(pattern_data)
    
    return {
        'success': True,
        'date': beijing_time.strftime('%Y-%m-%d'),
        'total_bars': len(bars),
        'total_change': total_change,
        'qualified_patterns': qualified_patterns,
        'unqualified_patterns': unqualified_patterns,
        'summary': {
            'qualified_count': len(qualified_patterns),
            'unqualified_count': len(unqualified_patterns),
            'total_count': len(qualified_patterns) + len(unqualified_patterns)
        }
    }

if __name__ == '__main__':
    result = check_all_patterns()
    print(json.dumps(result, ensure_ascii=False, indent=2))
