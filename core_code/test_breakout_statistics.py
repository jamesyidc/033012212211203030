#!/usr/bin/env python3
"""
波峰统计分析脚本
根据新规则：
1. 如果C点后面没有更低的点，那么C点可以直接作为下一个波峰的B点
2. 如果B到A的振幅没有增加20%，则判定为假突破
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

def load_data(file_path: str) -> List[Dict]:
    """加载数据"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                record = json.loads(line.strip())
                if 'beijing_time' not in record and 'timestamp' in record:
                    dt = datetime.fromtimestamp(record['timestamp'] / 1000)
                    record['beijing_time'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                data.append(record)
    return data

def check_lower_point_after_c(data: List[Dict], c_index: int, c_value: float) -> Optional[Dict]:
    """
    检查C点后面是否有更低的点
    返回：如果有更低的点，返回该点的信息；否则返回None
    """
    for i in range(c_index + 1, len(data)):
        current_value = data[i].get('change_percent') or data[i].get('change', 0)
        if current_value < c_value:
            return {
                'index': i,
                'time': data[i]['beijing_time'],
                'value': current_value,
                'minutes_after_c': (i - c_index) * 1.17  # 约1.17分钟/条数据
            }
    return None

def analyze_wave_peaks(data: List[Dict], peaks: List[Dict]) -> Dict:
    """
    分析波峰统计
    """
    stats = {
        'total_peaks': len(peaks),
        'real_breakouts': 0,  # 真突破（振幅>=20%）
        'false_breakouts': 0,  # 假突破（振幅<20%）
        'c_reusable': 0,  # C点可复用为下一个B点
        'c_need_new_b': 0,  # C点后有更低点，需要重新找B点
        'details': []
    }
    
    for i, peak in enumerate(peaks):
        peak_num = i + 1
        b_value = peak['b_point']['value']
        a_value = peak['a_point']['value']
        c_value = peak['c_point']['value']
        c_index = peak['c_point']['index']
        
        # 计算振幅
        amplitude = a_value - b_value
        
        # 判断是否为假突破
        is_false_breakout = amplitude < 20.0
        
        # 检查C点后是否有更低的点
        lower_point = check_lower_point_after_c(data, c_index, c_value)
        c_can_reuse = (lower_point is None)
        
        # 更新统计
        if is_false_breakout:
            stats['false_breakouts'] += 1
        else:
            stats['real_breakouts'] += 1
            
        if c_can_reuse:
            stats['c_reusable'] += 1
        else:
            stats['c_need_new_b'] += 1
        
        # 详细信息
        detail = {
            'peak_num': peak_num,
            'b_point': {
                'time': peak['b_point']['beijing_time'],
                'value': b_value
            },
            'a_point': {
                'time': peak['a_point']['beijing_time'],
                'value': a_value
            },
            'c_point': {
                'time': peak['c_point']['beijing_time'],
                'value': c_value
            },
            'amplitude': amplitude,
            'is_false_breakout': is_false_breakout,
            'c_can_reuse': c_can_reuse,
            'lower_point_after_c': lower_point
        }
        
        stats['details'].append(detail)
    
    return stats

def print_statistics(stats: Dict):
    """打印统计结果"""
    print("=" * 80)
    print("📊 波峰统计分析（新规则）")
    print("=" * 80)
    print(f"\n总波峰数: {stats['total_peaks']}")
    print(f"\n突破类型统计：")
    print(f"  ✅ 真突破（振幅≥20%）: {stats['real_breakouts']} ({stats['real_breakouts']/stats['total_peaks']*100:.1f}%)")
    print(f"  ❌ 假突破（振幅<20%）: {stats['false_breakouts']} ({stats['false_breakouts']/stats['total_peaks']*100:.1f}%)")
    
    print(f"\nC点复用统计：")
    print(f"  ✅ C点可复用（后面无更低点）: {stats['c_reusable']} ({stats['c_reusable']/stats['total_peaks']*100:.1f}%)")
    print(f"  ❌ C点不可复用（后面有更低点）: {stats['c_need_new_b']} ({stats['c_need_new_b']/stats['total_peaks']*100:.1f}%)")
    
    print("\n" + "=" * 80)
    print("📋 详细波峰信息")
    print("=" * 80)
    
    for detail in stats['details']:
        print(f"\n🔹 波峰 {detail['peak_num']}:")
        print(f"  B点: {detail['b_point']['time']} = {detail['b_point']['value']:+.2f}%")
        print(f"  A点: {detail['a_point']['time']} = {detail['a_point']['value']:+.2f}%")
        print(f"  C点: {detail['c_point']['time']} = {detail['c_point']['value']:+.2f}%")
        print(f"  振幅: {detail['amplitude']:.2f}%")
        
        # 突破类型
        if detail['is_false_breakout']:
            print(f"  类型: ❌ 假突破（振幅 {detail['amplitude']:.2f}% < 20%）")
        else:
            print(f"  类型: ✅ 真突破（振幅 {detail['amplitude']:.2f}% ≥ 20%）")
        
        # C点复用情况
        if detail['c_can_reuse']:
            print(f"  C点复用: ✅ 可以直接作为下一个波峰的B点（后面无更低点）")
        else:
            lower = detail['lower_point_after_c']
            print(f"  C点复用: ❌ 不可复用（后面有更低点）")
            print(f"    → {lower['time']} 出现更低点 {lower['value']:+.2f}%")
            print(f"    → C点后 {lower['minutes_after_c']:.1f} 分钟出现")

def main():
    """主函数"""
    # 加载今天的数据
    date_str = "20260218"
    file_path = f"/home/user/webapp/data/coin_change_tracker/coin_change_{date_str}.jsonl"
    
    print(f"加载数据: {file_path}")
    data = load_data(file_path)
    print(f"数据条数: {len(data)}")
    
    # 使用现有的波峰检测器
    from source_code.wave_peak_detector import WavePeakDetector
    
    # 使用35%振幅检测波峰（检测逻辑不变）
    detector = WavePeakDetector(min_amplitude=35.0, window_minutes=15)
    peaks, current_state = detector.detect_wave_peaks(data)
    
    print(f"检测到的波峰数: {len(peaks)}")
    
    if len(peaks) == 0:
        print("没有检测到完整的波峰")
        return
    
    # 分析统计
    stats = analyze_wave_peaks(data, peaks)
    
    # 打印结果
    print_statistics(stats)

if __name__ == "__main__":
    main()
