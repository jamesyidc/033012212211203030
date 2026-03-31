#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查今天全天的10分钟柱状图模式
回溯分析所有可能触发的信号
"""

import json
import requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict

API_BASE = 'http://localhost:9002'

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.now(timezone.utc)
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time

def get_color(up_ratio):
    """根据上涨占比判断颜色"""
    if up_ratio is None or up_ratio == 0:
        return '⚪ 空白'
    elif up_ratio > 55:
        return '🟢 绿色'
    elif up_ratio >= 45:
        return '🟡 黄色'
    else:
        return '🔴 红色'

def get_10min_bars():
    """获取今天的10分钟柱子序列"""
    try:
        url = f'{API_BASE}/api/coin-change-tracker/history?limit=2000'
        response = requests.get(url, timeout=10)
        result = response.json()
        
        if not result.get('success') or not result.get('data'):
            print("❌ 获取数据失败")
            return []
        
        data = result['data']
        beijing_time = get_beijing_time()
        today_str = beijing_time.strftime('%Y-%m-%d')
        
        # 过滤今天的数据
        today_data = [d for d in data if d.get('beijing_time', '').startswith(today_str)]
        
        print(f"✅ 获取到 {len(today_data)} 条今日数据")
        
        # 按10分钟分组
        interval = 10
        grouped = defaultdict(lambda: {'ratios': [], 'times': []})
        
        for record in today_data:
            time_str = record.get('beijing_time', '')
            up_ratio = record.get('up_ratio')
            
            if not time_str or up_ratio is None:
                continue
            
            dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            hour = dt.hour
            minute = dt.minute
            
            total_minutes = hour * 60 + minute
            group_index = total_minutes // interval
            
            grouped[group_index]['ratios'].append(up_ratio)
            grouped[group_index]['times'].append(time_str)
        
        # 构建柱子序列
        bars = []
        for group_idx in sorted(grouped.keys()):
            ratios = grouped[group_idx]['ratios']
            if not ratios:
                continue
            
            avg_ratio = sum(ratios) / len(ratios)
            hour = (group_idx * interval) // 60
            minute = (group_idx * interval) % 60
            time_label = f"{hour:02d}:{minute:02d}"
            
            bars.append({
                'index': group_idx,
                'time': time_label,
                'avg_ratio': avg_ratio,
                'color': get_color(avg_ratio),
                'data_count': len(ratios)
            })
        
        return bars
        
    except Exception as e:
        print(f"❌ 获取10分钟柱子失败: {e}")
        import traceback
        traceback.print_exc()
        return []

def check_pattern_1(bars, i):
    """
    模式1: 诱多等待新低
    - 连续3根：红→黄→绿 或 绿→黄→红
    - 连续4根：红→黄→黄→绿
    """
    if i < 2:
        return None
    
    # 连续3根：红→黄→绿
    if i >= 2:
        b1, b2, b3 = bars[i-2], bars[i-1], bars[i]
        c1 = '红' if '红' in b1['color'] else ('黄' if '黄' in b1['color'] else ('绿' if '绿' in b1['color'] else '其他'))
        c2 = '红' if '红' in b2['color'] else ('黄' if '黄' in b2['color'] else ('绿' if '绿' in b2['color'] else '其他'))
        c3 = '红' if '红' in b3['color'] else ('黄' if '黄' in b3['color'] else ('绿' if '绿' in b3['color'] else '其他'))
        
        if (c1 == '红' and c2 == '黄' and c3 == '绿') or (c1 == '绿' and c2 == '黄' and c3 == '红'):
            return {
                'pattern': '诱多等待新低 (3根)',
                'sequence': f"{c1}→{c2}→{c3}",
                'bars': [b1, b2, b3],
                'action': '逢高做空'
            }
    
    # 连续4根：红→黄→黄→绿
    if i >= 3:
        b1, b2, b3, b4 = bars[i-3], bars[i-2], bars[i-1], bars[i]
        c1 = '红' if '红' in b1['color'] else ('黄' if '黄' in b1['color'] else ('绿' if '绿' in b1['color'] else '其他'))
        c2 = '红' if '红' in b2['color'] else ('黄' if '黄' in b2['color'] else ('绿' if '绿' in b2['color'] else '其他'))
        c3 = '红' if '红' in b3['color'] else ('黄' if '黄' in b3['color'] else ('绿' if '绿' in b3['color'] else '其他'))
        c4 = '红' if '红' in b4['color'] else ('黄' if '黄' in b4['color'] else ('绿' if '绿' in b4['color'] else '其他'))
        
        if c1 == '红' and c2 == '黄' and c3 == '黄' and c4 == '绿':
            return {
                'pattern': '诱多等待新低 (4根)',
                'sequence': f"{c1}→{c2}→{c3}→{c4}",
                'bars': [b1, b2, b3, b4],
                'action': '逢高做空'
            }
    
    return None

def main():
    """主函数"""
    print("=" * 80)
    print("📊 检查今天全天的10分钟柱状图模式")
    print("=" * 80)
    
    # 获取今日预判
    try:
        url = f'{API_BASE}/api/coin-change-tracker/daily-prediction'
        response = requests.get(url, timeout=10)
        result = response.json()
        if result.get('success') and result.get('data'):
            signal = result['data'].get('signal', '未知')
            description = result['data'].get('description', '')
            print(f"\n✅ 今日预判: {signal}")
            print(f"   {description}\n")
        else:
            print("\n⚠️ 未获取到今日预判\n")
    except:
        print("\n⚠️ 未获取到今日预判\n")
    
    # 获取10分钟柱子
    bars = get_10min_bars()
    if not bars:
        print("❌ 没有数据")
        return
    
    print(f"📊 共有 {len(bars)} 个10分钟柱子\n")
    
    # 检查所有模式
    patterns_found = []
    
    for i in range(len(bars)):
        # 检查模式1
        pattern = check_pattern_1(bars, i)
        if pattern:
            patterns_found.append({
                'index': i,
                'time': bars[i]['time'],
                **pattern
            })
    
    # 输出结果
    print("=" * 80)
    print(f"🔍 检测结果: 找到 {len(patterns_found)} 个模式触发点")
    print("=" * 80)
    
    if patterns_found:
        for idx, pattern in enumerate(patterns_found, 1):
            print(f"\n【触发点 #{idx}】")
            print(f"  时间: {pattern['time']}")
            print(f"  模式: {pattern['pattern']}")
            print(f"  序列: {pattern['sequence']}")
            print(f"  操作: {pattern['action']}")
            print(f"  柱子详情:")
            for bar in pattern['bars']:
                print(f"    - {bar['time']}: {bar['color']} (上涨占比 {bar['avg_ratio']:.1f}%)")
    else:
        print("\n✓ 今日未触发任何模式")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
