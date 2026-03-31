#!/usr/bin/env python3
"""
计算所有历史日期的正数占比多空转换点
将结果存储为 JSONL 文件（每日一条记录）
"""

import json
import glob
import os
from datetime import datetime
import pytz

def calculate_transition_point(date_str):
    """计算指定日期的多空转换点"""
    
    data_file = f"data/coin_change_tracker/coin_change_{date_str}.jsonl"
    
    if not os.path.exists(data_file):
        return None
    
    # 读取数据
    data_points = []
    try:
        with open(data_file, 'r') as f:
            for line in f:
                if line.strip():
                    data_points.append(json.loads(line))
    except Exception as e:
        print(f"❌ 读取 {date_str} 失败: {e}")
        return None
    
    if len(data_points) == 0:
        print(f"⚠️ {date_str} 无数据")
        return None
    
    # 过滤前5分钟
    filtered = []
    for point in data_points:
        beijing_time = point.get('beijing_time', '')
        if not beijing_time:
            continue
            
        time_part = beijing_time.split(' ')[1] if ' ' in beijing_time else beijing_time
        try:
            hour, minute, _ = time_part.split(':')
            hour, minute = int(hour), int(minute)
            
            # 排除 00:00 - 00:04
            if hour == 0 and minute < 5:
                continue
            
            filtered.append(point)
        except:
            continue
    
    if len(filtered) == 0:
        print(f"⚠️ {date_str} 过滤后无数据")
        return None
    
    # 计算每个时间点的累计正数占比
    ratios = []
    for i, point in enumerate(filtered):
        positive_count = sum(1 for p in filtered[:i+1] if p.get('total_change', 0) > 0)
        total_count = i + 1
        ratio = (positive_count / total_count * 100) if total_count > 0 else 0
        
        ratios.append({
            'time': point.get('beijing_time'),
            'ratio': round(ratio, 2),
            'total_change': point.get('total_change', 0),
            'positive_count': positive_count,
            'total_count': total_count,
            'index': i
        })
    
    # 找最高占比
    max_ratio_data = max(ratios, key=lambda x: x['ratio'])
    max_ratio = max_ratio_data['ratio']
    threshold = max_ratio - 20
    
    result = {
        'date': date_str,
        'total_points': len(filtered),
        'max_ratio': max_ratio,
        'max_ratio_time': max_ratio_data['time'],
        'threshold': round(threshold, 2),
        'has_transition': False,
        'transition_time': None,
        'transition_ratio': None,
        'transition_total_change': None,
        'calculated_at': datetime.now(pytz.timezone('Asia/Shanghai')).isoformat()
    }
    
    # 判断是否存在多转空
    if max_ratio <= 50:
        result['note'] = '最高占比≤50%，全天空头，无多转空'
        print(f"  {date_str}: 最高{max_ratio:.1f}% ≤50% → 无多转空")
        return result
    
    # 从最高点之后找跌破临界点的位置
    max_index = ratios.index(max_ratio_data)
    
    for i in range(max_index + 1, len(ratios)):
        if ratios[i]['ratio'] < threshold:
            result['has_transition'] = True
            result['transition_time'] = ratios[i]['time']
            result['transition_ratio'] = ratios[i]['ratio']
            result['transition_total_change'] = ratios[i]['total_change']
            result['transition_index'] = ratios[i]['index']
            result['after_max_points'] = i - max_index
            
            print(f"  {date_str}: 最高{max_ratio:.1f}%({max_ratio_data['time'].split()[1]}) → 转空{ratios[i]['ratio']:.1f}%({ratios[i]['time'].split()[1]}) ✅")
            return result
    
    result['note'] = '未跌破临界点，一直保持多头'
    print(f"  {date_str}: 最高{max_ratio:.1f}% → 未跌破{threshold:.1f}% (保持多头)")
    return result


def main():
    print("=" * 80)
    print("📊 计算所有历史日期的正数占比多空转换点")
    print("=" * 80)
    print()
    
    # 获取所有历史数据文件
    files = sorted(glob.glob("data/coin_change_tracker/coin_change_*.jsonl"))
    
    print(f"找到 {len(files)} 个历史数据文件")
    print()
    
    # 创建输出目录
    output_dir = "data/coin_change_tracker/transitions"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = f"{output_dir}/positive_ratio_transitions.jsonl"
    
    # 处理每个文件
    results = []
    success_count = 0
    transition_count = 0
    
    for file_path in files:
        filename = os.path.basename(file_path)
        date_str = filename.replace('coin_change_', '').replace('.jsonl', '')
        
        result = calculate_transition_point(date_str)
        
        if result:
            results.append(result)
            success_count += 1
            if result['has_transition']:
                transition_count += 1
    
    # 写入JSONL文件
    with open(output_file, 'w') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    print()
    print("=" * 80)
    print("✅ 计算完成！")
    print("=" * 80)
    print(f"总文件数: {len(files)}")
    print(f"成功处理: {success_count}")
    print(f"存在多转空: {transition_count}")
    print(f"无多转空: {success_count - transition_count}")
    print()
    print(f"结果已保存到: {output_file}")
    print("=" * 80)
    
    # 显示统计信息
    if results:
        max_ratios = [r['max_ratio'] for r in results]
        transitions = [r for r in results if r['has_transition']]
        
        print()
        print("📈 统计信息:")
        print(f"  平均最高占比: {sum(max_ratios)/len(max_ratios):.1f}%")
        print(f"  最高记录: {max(max_ratios):.1f}%")
        print(f"  最低记录: {min(max_ratios):.1f}%")
        print(f"  多转空比例: {transition_count}/{success_count} ({transition_count/success_count*100:.1f}%)")
        
        if transitions:
            avg_after_points = sum(t.get('after_max_points', 0) for t in transitions) / len(transitions)
            print(f"  平均转换延迟: {avg_after_points:.0f} 个数据点")


if __name__ == '__main__':
    main()
