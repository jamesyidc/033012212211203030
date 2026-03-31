#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成所有2月份的预判文件
基于原始数据重新计算，确保准确性
"""

import json
import glob
import os
from datetime import datetime, timezone, timedelta
from collections import defaultdict

def analyze_date(date_str):
    """分析指定日期的0-2点数据并生成预判"""
    date_file = date_str.replace('-', '')
    data_file = f'data/coin_change_tracker/coin_change_{date_file}.jsonl'
    
    if not os.path.exists(data_file):
        print(f"⚠️  {date_str}: 数据文件不存在")
        return None
    
    try:
        # 读取0-2点数据
        with open(data_file, 'r') as f:
            records = []
            for line in f:
                record = json.loads(line)
                time_str = record.get('beijing_time', '')
                if not time_str:
                    continue
                
                dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                hour = dt.hour
                
                if 0 <= hour < 2:
                    changes = record.get('changes', {})
                    if changes:
                        total_coins = len(changes)
                        up_coins = sum(1 for coin_data in changes.values() 
                                     if coin_data.get('change_pct', 0) > 0)
                        up_ratio = (up_coins / total_coins * 100) if total_coins > 0 else 0
                        
                        records.append({
                            'time': time_str,
                            'up_ratio': up_ratio
                        })
        
        if not records:
            print(f"⚠️  {date_str}: 没有0-2点数据")
            return None
        
        # 按10分钟分组
        interval = 10
        grouped = defaultdict(lambda: {'ratios': []})
        
        for record in records:
            time_str = record['time']
            up_ratio = record['up_ratio']
            
            dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            hour = dt.hour
            minute = dt.minute
            
            total_minutes = hour * 60 + minute
            group_index = total_minutes // interval
            
            grouped[group_index]['ratios'].append(up_ratio)
        
        # 判断颜色
        color_counts = {'green': 0, 'red': 0, 'yellow': 0, 'blank': 0}
        
        for group_idx in sorted(grouped.keys()):
            ratios = grouped[group_idx]['ratios']
            if not ratios:
                continue
            
            avg_up_ratio = sum(ratios) / len(ratios)
            
            if avg_up_ratio == 0:
                color_counts['blank'] += 1
            elif avg_up_ratio > 55:
                color_counts['green'] += 1
            elif avg_up_ratio >= 45:
                color_counts['yellow'] += 1
            else:
                color_counts['red'] += 1
        
        # 判断信号
        green = color_counts['green']
        red = color_counts['red']
        yellow = color_counts['yellow']
        blank = color_counts['blank']
        blank_ratio = (blank / (green + red + yellow + blank) * 100) if (green + red + yellow + blank) > 0 else 0
        
        color_counts['blank_ratio'] = blank_ratio
        
        # 情况6: 全部为空白（空头强控盘）
        if blank > 0 and green == 0 and red == 0 and yellow == 0:
            signal = "空头强控盘"
            description = "⚪⚪⚪ 0点-2点全部为空白，空头强控盘，建议观望。操作提示：不参与"
        # 情况4: 全部绿色（诱多）
        elif green > 0 and red == 0 and yellow == 0 and blank == 0:
            signal = "诱多不参与"
            description = "🟢 全部绿色柱子，单边诱多行情，不参与操作。操作提示：不参与"
        # 情况3: 只有红色或红色+空白（做空）- 允许做空不允许做多
        # 包含：纯红色（blank=0）或 红色+空白（无论空白占比多少）
        elif red > 0 and green == 0 and yellow == 0:
            if blank == 0:
                signal = "做空"
                description = "🔴 只有红色柱子，预判下跌行情，建议做空。操作提示：相对高点做空"
            else:  # blank > 0，无论占比多少都是做空
                signal = "做空"
                description = f"🔴⚪ 红色+空白（空白占比{blank_ratio:.1f}%），预判下跌行情，建议做空。操作提示：相对高点做空"
        # 情况1: 有绿+有红+无黄 → 低吸（要求绿>=3根）
        elif green >= 3 and red > 0 and yellow == 0:
            signal = "低吸"
            description = f"🟢🔴 绿色{green}根+红色{red}根（绿色>=3根为主导，无黄色），红色区间为低吸机会。操作提示：低点做多"
        # 情况2优先: 有绿+有红+有黄，且黄柱子 >= 2根（大于1根）→ 等待新低（新增逻辑）
        elif green > 0 and red > 0 and yellow >= 2:
            signal = "等待新低"
            description = f"🟢🔴🟡 有绿有红有黄，黄色柱子{yellow}根(>=2根)，可能还有新低，建议等待。操作提示：高点做空"
        # 情况1扩展: 有绿+有红+有黄，但(红+黄) < 3根 OR 黄柱子只有1根 → 低吸（要求绿>=3根）
        elif green >= 3 and red > 0 and yellow > 0 and ((red + yellow) < 3 or yellow == 1):
            signal = "低吸"
            description = f"🟢🔴🟡 绿色{green}根+红色{red}根+黄色{yellow}根（绿色>=3根为主导，红+黄共{red+yellow}根），红色区间为低吸机会。操作提示：低点做多"
        # 情况7: 红色+黄色（无绿色）→ 观望
        elif red > 0 and yellow > 0 and green == 0:
            signal = "观望"
            description = "🔴🟡 红色柱子+黄色柱子，没有绿色柱子，多空博弈方向不明。操作提示：无，不参与"
        # 情况8: 只有绿色+黄色（无红色）→ 根据绿色数量判断
        elif green > 0 and yellow > 0 and red == 0:
            if green >= 3:
                signal = "低吸"
                description = f"🟢🟡 绿色{green}根+黄色{yellow}根（绿色>=3根为主导，无红色），黄色区间为低吸机会。操作提示：低点做多"
            else:
                signal = "观望"
                description = f"🟢🟡 绿色{green}根+黄色{yellow}根（绿色<3根，无红色），无法判断低吸或新低。操作提示：观望"
        # 其他情况
        else:
            signal = "观望"
            description = "⚪ 柱状图混合分布，建议观望"
        
        return {
            'date': date_str,
            'timestamp': f'{date_str} 02:00:00',
            'analysis_time': '02:00:00',
            'color_counts': color_counts,
            'signal': signal,
            'description': description,
            'is_temp': False
        }
    except Exception as e:
        print(f"❌ {date_str}: 分析失败 - {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("="*80)
    print("🔧 重新生成所有历史预判文件（使用最新逻辑）")
    print("="*80)
    print()
    
    # 获取所有数据文件（不限制月份）
    data_files = sorted(glob.glob('data/coin_change_tracker/coin_change_2026*.jsonl'))
    
    if not data_files:
        print("❌ 未找到历史数据文件")
        return
    
    print(f"📊 找到 {len(data_files)} 个数据文件")
    print()
    
    success_count = 0
    error_count = 0
    
    for data_file in data_files:
        # 提取日期
        filename = os.path.basename(data_file)
        date_num = filename.replace('coin_change_', '').replace('.jsonl', '')
        date_str = f"{date_num[:4]}-{date_num[4:6]}-{date_num[6:8]}"
        
        # 分析数据
        prediction = analyze_date(date_str)
        
        if prediction:
            # 保存预判文件（使用JSONL格式）
            pred_dir = 'data/daily_predictions'
            os.makedirs(pred_dir, exist_ok=True)
            pred_file = f'{pred_dir}/prediction_{date_num}.jsonl'
            
            # 写入JSONL格式（单行，is_final=True）
            prediction['is_final'] = True
            with open(pred_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(prediction, ensure_ascii=False) + '\n')
            
            colors = prediction['color_counts']
            print(f"✅ {date_str}: 绿{colors['green']} 红{colors['red']} 黄{colors['yellow']} | {prediction['signal']}")
            success_count += 1
        else:
            error_count += 1
    
    print()
    print("="*80)
    print(f"✅ 重新生成完成！")
    print(f"  成功: {success_count} 个")
    print(f"  失败: {error_count} 个")
    print(f"  保存格式: JSONL")
    print(f"  保存目录: data/daily_predictions/")
    print("="*80)

if __name__ == "__main__":
    main()
