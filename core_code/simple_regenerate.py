#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单重新生成预测数据 - 直接从文件读取
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def determine_market_signal(color_counts):
    """判断市场信号"""
    green = color_counts.get('green', 0)
    red = color_counts.get('red', 0)
    yellow = color_counts.get('yellow', 0)
    blank = color_counts.get('blank', 0)
    
    # 情况2: 有绿+有红+有黄 → 根据绿柱子数量和比例判断
    if green > 0 and red > 0 and yellow > 0:
        # 2a: 绿柱子<3根 OR 黄柱子>=2根 OR 绿柱子<=红柱子 → 等待新低
        if green < 3 or yellow >= 2 or green <= red:
            return "等待新低", f"🟢🔴🟡 有绿有红有黄（绿色{green}根，红色{red}根，黄色{yellow}根），可能还有新低，建议等待。操作提示：高点做空"
        # 2b: 绿柱子>=3根 且 绿柱子>红柱子 → 低吸（绿色为主导）
        else:
            return "低吸", f"🟢🔴🟡 绿色{green}根+红色{red}根+黄色{yellow}根（绿色>红色为主导），红色区间为低吸机会。操作提示：低点做多"
    
    # 情况1c: 有绿色>=3根 + (有红色或有空白) → 低吸
    if green >= 3 and (red > 0 or blank > 0):
        if red > 0 and blank > 0:
            return "低吸", f"🟢🔴⚪ 绿色{green}根+红色{red}根+空白{blank}根，绿色柱子>=3根为主导，红色区间为低吸机会。操作提示：低点做多"
        elif red > 0:
            return "低吸", f"🟢🔴 绿色{green}根+红色{red}根，绿色柱子>=3根为主导，红色区间为低吸机会。操作提示：低点做多"
        else:  # blank > 0
            return "低吸", f"🟢⚪ 绿色{green}根+空白{blank}根，绿色柱子>=3根为主导，空白区间为低吸机会。操作提示：低点做多"
    
    # 情况7: 红色+黄色（无绿色）→ 观望
    if red > 0 and yellow > 0 and green == 0:
        return "观望", "🔴🟡 红色柱子+黄色柱子，没有绿色柱子，多空博弈方向不明。操作提示：无，不参与"
    
    # 情况8: 只有绿色+黄色（无红色）
    if green > 0 and yellow > 0 and red == 0:
        if green >= 3:
            return "低吸", f"🟢🟡 绿色{green}根+黄色{yellow}根，绿色柱子>=3根为主导，黄色区间为低吸机会。操作提示：低点做多"
        return "观望", f"🟢🟡 只有绿色{green}根和黄色{yellow}根，绿色不足3根，无法判断低吸或新低。操作提示：观望"
    
    # 情况3: 只有红色（或红色+空白）→ 做空
    if red > 0 and green == 0 and yellow == 0:
        blank_ratio = blank / 12 * 100 if blank > 0 else 0
        if blank == 0:
            return "做空", "🔴 只有红色柱子，预判下跌行情，建议做空。操作提示：相对高点做空"
        else:
            return "做空", f"🔴⚪ 红色+空白且空白占比{blank_ratio:.1f}%，预判下跌行情，建议做空。操作提示：相对高点做空"
    
    # 情况4: 只有绿色 → 诱多不参与
    if green > 0 and red == 0 and yellow == 0 and blank == 0:
        return "诱多不参与", "🟢 只有绿色柱子（极端情况），可能为诱多陷阱，建议不参与。操作提示：无，不参与"
    
    # 情况5: 只有空白 → 空头强控盘
    if blank > 0 and green == 0 and red == 0 and yellow == 0:
        return "空头强控盘", "⚪ 只有空白柱子（极端情况），空头强控盘，建议不参与。操作提示：无，不参与"
    
    # 其他情况 → 观望（带详细颜色统计）
    return "观望", f"🎨 颜色组合不符合上述规则（绿{green}红{red}黄{yellow}白{blank}），市场方向不明，建议观望。操作提示：无，不参与"

def analyze_bar_colors_from_file(data_file):
    """从文件读取并分析0-2点的柱状图颜色"""
    color_counts = {'green': 0, 'red': 0, 'yellow': 0, 'blank': 0}
    
    # 读取数据
    records = []
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    
    # 过滤0-2点数据
    filtered_records = []
    for record in records:
        time_str = record.get('time', record.get('beijing_time', ''))
        if not time_str:
            continue
        
        # 处理两种时间格式:
        # 1. "HH:MM:SS" (time字段)
        # 2. "YYYY-MM-DD HH:MM:SS" (beijing_time字段)
        if ' ' in time_str:  # beijing_time格式
            time_part = time_str.split(' ')[1]
            hour = int(time_part.split(':')[0])
        else:  # time格式
            hour = int(time_str.split(':')[0])
        
        if 0 <= hour < 2:
            filtered_records.append(record)
    
    print(f"📊 找到 {len(filtered_records)} 条0-2点数据")
    
    # 按10分钟分组
    time_slots = {}
    for record in filtered_records:
        time_str = record.get('time', record.get('beijing_time', ''))
        
        # 处理两种时间格式
        if ' ' in time_str:  # beijing_time格式
            time_part = time_str.split(' ')[1]
        else:  # time格式
            time_part = time_str
        
        hour, minute, _ = time_part.split(':')
        hour = int(hour)
        minute = int(minute)
        
        # 计算时间槽(0-11, 每10分钟一个槽)
        # 0-2点 = 0:00-1:59 = 12个10分钟槽
        slot_key = hour * 6 + minute // 10
        
        if slot_key not in time_slots:
            time_slots[slot_key] = []
        time_slots[slot_key].append(record)
    
    # 分析每个时间段
    for slot_key in sorted(time_slots.keys()):
        records_in_slot = time_slots[slot_key]
        if not records_in_slot:
            continue
        
        # 计算该时间段的涨跌情况
        up_count = 0
        down_count = 0
        total_count = 0
        
        for record in records_in_slot:
            up_ratio = record.get('up_ratio')
            if up_ratio is not None:
                total_count += 1
                if up_ratio >= 50:
                    up_count += 1
                else:
                    down_count += 1
        
        # 判断颜色
        if total_count > 0:
            up_percentage = up_count / total_count * 100
            
            if up_percentage >= 70:
                color_counts['green'] += 1
            elif up_percentage <= 30:
                color_counts['red'] += 1
            elif 40 <= up_percentage <= 60:
                color_counts['yellow'] += 1
            else:
                color_counts['blank'] += 1
    
    return color_counts

def regenerate_prediction(date_str):
    """重新生成指定日期的预测数据"""
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    data_file = f"data/coin_change_tracker/coin_change_{date_obj.strftime('%Y%m%d')}.jsonl"
    output_file = f"data/daily_predictions/prediction_{date_obj.strftime('%Y%m%d')}.jsonl"
    
    print(f"📊 正在分析 {date_str} 的数据...")
    print(f"📁 数据文件: {data_file}")
    
    # 分析柱状图颜色
    color_counts = analyze_bar_colors_from_file(data_file)
    
    print(f"🎨 柱状图颜色统计: {color_counts}")
    
    # 生成预测信号
    signal, message = determine_market_signal(color_counts)
    
    # 构造预测数据
    prediction = {
        'date': date_str,
        'signal': signal,
        'message': message,
        'color_counts': color_counts,
        'generated_at': datetime.now().isoformat()
    }
    
    # 写入文件
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(prediction, f, ensure_ascii=False)
        f.write('\n')
    
    print(f"✅ 预测数据已生成: {output_file}")
    print(f"📈 信号: {signal}")
    print(f"💬 消息: {message}")
    
    return True

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("用法: python3 simple_regenerate.py YYYY-MM-DD")
        sys.exit(1)
    
    date_str = sys.argv[1]
    success = regenerate_prediction(date_str)
    sys.exit(0 if success else 1)
