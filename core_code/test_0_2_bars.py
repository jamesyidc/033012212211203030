#!/usr/bin/env python3
"""
测试0-2点柱状图计算逻辑
"""
import json
from datetime import datetime

# 读取今天的数据
data_file = '/home/user/webapp/data/coin_change_tracker/coin_change_20260310.jsonl'

records = []
with open(data_file, 'r') as f:
    for line in f:
        if line.strip():
            record = json.loads(line.strip())
            records.append(record)

print(f"📊 总记录数: {len(records)}")

# 过滤0-2点的数据
filtered = []
for record in records:
    time_str = record.get('beijing_time', '')
    if not time_str:
        continue
    
    # 提取时间部分
    time_part = time_str.split(' ')[1] if ' ' in time_str else time_str
    hour = int(time_part.split(':')[0])
    
    # 只保留0-2点的数据
    if hour >= 0 and hour < 2:
        filtered.append(record)

print(f"📊 0-2点记录数: {len(filtered)}")

# 按10分钟区间分组
grouped = {}
for record in filtered:
    time_str = record.get('beijing_time', '')
    if not time_str:
        continue
    
    time_part = time_str.split(' ')[1] if ' ' in time_str else time_str
    parts = time_part.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    
    total_minutes = hours * 60 + minutes
    group_index = total_minutes // 10
    
    if group_index not in grouped:
        grouped[group_index] = []
    
    # 获取up_ratio
    up_ratio = record.get('up_ratio', 0)
    grouped[group_index].append(up_ratio)

print(f"\n📊 10分钟区间统计:")
print(f"区间数: {len(grouped)}")

# 计算每个区间的颜色
bars = []
for i in range(12):  # 0-2点有12个10分钟区间
    if i not in grouped or len(grouped[i]) == 0:
        print(f"区间 {i} (未完成): ⚪ 空白 - 无数据")
        continue
    
    ratios = grouped[i]
    avg_ratio = sum(ratios) / len(ratios)
    
    # 判断颜色
    if avg_ratio == 0:
        color_emoji = '⚪'
        color_name = '空白'
    elif avg_ratio >= 55:
        color_emoji = '🟢'
        color_name = '绿色'
    elif avg_ratio > 45:
        color_emoji = '🟡'
        color_name = '黄色'
    else:
        color_emoji = '🔴'
        color_name = '红色'
    
    bars.append(color_emoji)
    
    start_hour = (i * 10) // 60
    start_min = (i * 10) % 60
    end_hour = ((i + 1) * 10) // 60
    end_min = ((i + 1) * 10) % 60
    
    print(f"区间 {i} ({start_hour:02d}:{start_min:02d}-{end_hour:02d}:{end_min:02d}): {color_emoji} {color_name} - 平均{avg_ratio:.2f}% (样本数:{len(ratios)})")

# 统计颜色
green_count = bars.count('🟢')
red_count = bars.count('🔴')
yellow_count = bars.count('🟡')
blank_count = bars.count('⚪')

print(f"\n📊 颜色统计:")
print(f"🟢 绿色: {green_count}根")
print(f"🔴 红色: {red_count}根")
print(f"🟡 黄色: {yellow_count}根")
print(f"⚪ 空白: {blank_count}根")
print(f"总计: {len(bars)}根 / 12根")

print(f"\n柱状图: {''.join(bars)}")

# 判断信号（严格按照后端逻辑 determine_market_signal_v2）
if blank_count > 0 and green_count == 0 and red_count == 0 and yellow_count == 0:
    # 情况5: 全部为空白
    signal = '空头强控盘'
elif green_count > 0 and red_count == 0 and yellow_count == 0 and blank_count == 0:
    # 情况4: 全部绿色
    signal = '诱多不参与'
elif red_count > 0 and green_count == 0 and yellow_count == 0:
    # 情况3: 只有红色（或红色+空白）
    signal = '做空'
elif green_count > 0 and red_count > 0 and yellow_count == 0:
    # 情况1: 有绿+有红+无黄
    signal = '低吸'
elif green_count > 0 and red_count > 0 and yellow_count >= 2:
    # 情况2: 有绿+有红+有黄，且黄柱子>=2根
    signal = '等待新低'
elif green_count > 0 and red_count > 0 and yellow_count > 0:
    # 情况1扩展: 有绿+有红+有黄，但(红+黄)<3根 OR 黄柱子只有1根
    if (red_count + yellow_count) < 3 or yellow_count == 1:
        signal = '低吸'
    else:
        signal = '观望'
elif green_count >= 3 and (red_count > 0 or blank_count > 0):
    # 情况1c: 有绿色柱子 + (有红色或有空白) + 绿色>=3根
    signal = '低吸'
elif red_count > 0 and yellow_count > 0 and green_count == 0:
    # 情况7: 红色+黄色（无绿色）
    signal = '观望'
elif green_count > 0 and yellow_count > 0 and red_count == 0:
    # 情况8: 只有绿色+黄色（无红色）
    if green_count >= 3:
        signal = '低吸'
    else:
        signal = '观望'
else:
    signal = '观望'

print(f"\n🔮 预判信号: {signal}")
