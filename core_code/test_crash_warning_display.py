#!/usr/bin/env python3
"""测试暴跌预警标记显示"""

import requests
import json
from datetime import datetime

def test_crash_warning_api():
    """测试暴跌预警API"""
    url = "http://localhost:9002/api/coin-change-tracker/wave-peaks?date=2026-02-26"
    
    print("=" * 60)
    print("测试暴跌预警API")
    print("=" * 60)
    
    response = requests.get(url)
    data = response.json()
    
    if not data.get('success'):
        print("❌ API调用失败")
        return
    
    print("✅ API调用成功")
    print(f"📅 日期: {data.get('date')}")
    print(f"🌊 波峰数量: {len(data.get('peaks', []))}")
    
    crash_warning = data.get('crash_warning')
    if crash_warning:
        print("\n🚨 暴跌预警信息:")
        print(f"  - 模式名称: {crash_warning.get('pattern_name')}")
        print(f"  - 警告信息: {crash_warning.get('warning')}")
        print(f"  - 操作建议: {crash_warning.get('operation_tip')}")
        print(f"  - 警告级别: {crash_warning.get('warning_level')}")
        
        peaks = crash_warning.get('peaks', [])
        if len(peaks) >= 3:
            a3_peak = peaks[2]
            a3_time = a3_peak.get('a_point', {}).get('beijing_time', '')
            a3_value = a3_peak.get('a_point', {}).get('value', 0)
            
            print(f"\n📍 A3点信息（标记显示位置）:")
            print(f"  - 时间: {a3_time}")
            print(f"  - 数值: {a3_value}%")
            
            # 提取时间部分
            if ' ' in a3_time:
                time_part = a3_time.split(' ')[1]
                print(f"  - 图表时间: {time_part}")
        
        print("\n📊 A点递减趋势:")
        comparisons = crash_warning.get('comparisons', {})
        a_values = comparisons.get('a_values', {})
        print(f"  - A1: {a_values.get('a1')}%")
        print(f"  - A2: {a_values.get('a2')}%")
        print(f"  - A3: {a_values.get('a3')}%")
        print(f"  - A1→A2: {a_values.get('a2_vs_a1', {}).get('diff')}% ({a_values.get('a2_vs_a1', {}).get('diff_pct')}%)")
        print(f"  - A2→A3: {a_values.get('a3_vs_a2', {}).get('diff')}% ({a_values.get('a3_vs_a2', {}).get('diff_pct')}%)")
    else:
        print("\n⚠️ 今日无暴跌预警")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_crash_warning_api()
