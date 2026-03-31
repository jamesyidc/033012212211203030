#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成2月份所有日期的预测数据（JSONL格式）
基于历史币种涨跌数据重新计算
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict

sys.path.insert(0, '/home/user/webapp')

# 数据目录
PREDICTION_DIR = "/home/user/webapp/data/daily_predictions"

def fetch_coin_change_history(date_str):
    """获取指定日期0-2点的币种涨跌历史数据"""
    try:
        url = f"http://localhost:9002/api/coin-change-tracker/history?date={date_str}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            history = result.get('data', result)
            
            # 筛选0-2点的数据
            morning_records = []
            
            for record in history:
                time_str = record.get('beijing_time', '')
                if not time_str:
                    continue
                
                try:
                    dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    hour = dt.hour
                    
                    if 0 <= hour < 2:
                        changes = record.get('changes', {})
                        if changes:
                            total_coins = len(changes)
                            up_coins = sum(1 for coin_data in changes.values() 
                                         if coin_data.get('change_pct', 0) > 0)
                            up_ratio = (up_coins / total_coins * 100) if total_coins > 0 else 0
                            
                            morning_records.append({
                                'time': time_str,
                                'up_ratio': up_ratio
                            })
                except Exception as e:
                    continue
            
            return {'records': morning_records, 'date': date_str}
        else:
            return None
    except Exception as e:
        print(f"❌ 获取 {date_str} 数据失败: {e}")
        return None

def analyze_bar_colors(data):
    """分析10分钟柱状图颜色"""
    if not data or 'records' not in data:
        return None
    
    records = data['records']
    if not records:
        return None
    
    interval = 10
    grouped = defaultdict(lambda: {'ratios': []})
    
    for record in records:
        time_str = record.get('time', '')
        up_ratio = record.get('up_ratio', 0)
        
        if not time_str:
            continue
        
        try:
            dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            hour = dt.hour
            minute = dt.minute
            total_minutes = hour * 60 + minute
            group_index = total_minutes // interval
            grouped[group_index]['ratios'].append(up_ratio)
        except Exception as e:
            continue
    
    color_counts = {'green': 0, 'red': 0, 'yellow': 0, 'blank': 0}
    total_bars = len(grouped)
    
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
    
    color_counts['blank_ratio'] = (color_counts['blank'] / total_bars * 100) if total_bars > 0 else 0
    
    return color_counts

def determine_market_signal(color_counts):
    """根据颜色分布判断市场信号"""
    if not color_counts:
        return None, None
    
    green = color_counts['green']
    red = color_counts['red']
    yellow = color_counts['yellow']
    blank = color_counts.get('blank', 0)
    blank_ratio = color_counts.get('blank_ratio', 0)
    
    # 情况6: 全部为空白
    if blank > 0 and green == 0 and red == 0 and yellow == 0:
        return "空头强控盘", "⚪⚪⚪ 0点-2点全部为空白，空头强控盘，建议观望。操作提示：不参与"
    
    # 情况5: 红色+空白且空白占比>=25%
    if blank > 0 and blank_ratio >= 25 and green == 0:
        if yellow > 0:
            return "诱空试盘抄底", f"⚪🔴🟡 红色+空白+黄色且空白占比{blank_ratio:.1f}%>=25%，诱空行情，可以试盘抄底。操作提示：低点做多"
        else:
            return "诱空试盘抄底", f"⚪🔴 红色+空白且空白占比{blank_ratio:.1f}%>=25%，诱空行情，可以试盘抄底。操作提示：低点做多"
    
    # 情况4: 全部绿色
    if green > 0 and red == 0 and yellow == 0 and blank == 0:
        return "诱多不参与", "🟢 全部绿色柱子，单边诱多行情，不参与操作。操作提示：不参与"
    
    # 情况3: 只有红色或红色+少量空白
    if red > 0 and green == 0 and yellow == 0 and blank_ratio < 25:
        if blank == 0:
            return "做空", "🔴 只有红色柱子，预判下跌行情，建议做空。操作提示：相对高点做空"
        else:
            return "做空", f"🔴⚪ 红色+少量空白（空白占比{blank_ratio:.1f}%<25%），预判下跌行情，建议做空。操作提示：相对高点做空"
    
    # 情况1: 有绿+有红+无黄
    if green > 0 and red > 0 and yellow == 0:
        return "低吸", "🟢🔴 有绿有红无黄，红色区间为低吸机会。操作提示：低点做多"
    
    # 情况2: 有绿+有红+有黄
    if green > 0 and red > 0 and yellow > 0:
        return "等待新低", "🟢🔴🟡 有绿有红有黄，可能还有新低，建议等待。操作提示：高点做空"
    
    # 情况7: 红色+黄色（无绿色）
    if red > 0 and yellow > 0 and green == 0:
        return "观望", "🔴🟡 红色柱子+黄色柱子，没有绿色柱子，多空博弈方向不明。操作提示：无，不参与"
    
    # 情况8: 只有绿色+黄色（无红色）
    if green > 0 and yellow > 0 and red == 0:
        return "等待新低", "🟢🟡 只有绿色和黄色，可能还有新低，建议等待。操作提示：高点做空"
    
    return "观望", "⚪ 柱状图混合分布，建议观望"

def save_prediction_jsonl(date_str, color_counts, signal, description):
    """保存预测数据为JSONL格式"""
    try:
        # 转换日期格式
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        date_compact = dt.strftime('%Y%m%d')  # 20260202
        
        prediction_data = {
            "timestamp": f"{date_str} 02:00:00",  # 假设为2点的最终预判
            "date": date_str,
            "analysis_time": "02:00:00",
            "color_counts": color_counts,
            "signal": signal,
            "description": description,
            "is_temp": False,
            "is_final": True,
            "regenerated": True  # 标记为重新生成的数据
        }
        
        os.makedirs(PREDICTION_DIR, exist_ok=True)
        jsonl_file = os.path.join(PREDICTION_DIR, f"prediction_{date_compact}.jsonl")
        
        # 写入JSONL（覆盖模式，因为是重新生成）
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            json.dump(prediction_data, f, ensure_ascii=False)
            f.write('\n')
        
        return True
    except Exception as e:
        print(f"❌ 保存 {date_str} 数据失败: {e}")
        return False

def regenerate_february_predictions():
    """重新生成2月份所有预测数据"""
    print("=" * 80)
    print("重新生成2月份预测数据（JSONL格式）")
    print("=" * 80)
    print()
    
    # 2月份的所有日期（2026-02-01 到 2026-02-26）
    start_date = datetime(2026, 2, 1)
    end_date = datetime(2026, 2, 26)
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        print(f"\n{'='*80}")
        print(f"处理日期: {date_str}")
        print(f"{'='*80}")
        
        # 获取历史数据
        print(f"📥 获取 {date_str} 的0-2点数据...")
        data = fetch_coin_change_history(date_str)
        
        if not data or not data.get('records'):
            print(f"⚠️  {date_str} 没有数据，跳过")
            skip_count += 1
            current_date += timedelta(days=1)
            continue
        
        print(f"✅ 获取到 {len(data['records'])} 条记录")
        
        # 分析颜色
        print(f"📊 分析柱状图颜色...")
        color_counts = analyze_bar_colors(data)
        
        if not color_counts:
            print(f"❌ {date_str} 数据解析失败，跳过")
            fail_count += 1
            current_date += timedelta(days=1)
            continue
        
        print(f"  🟢 绿色: {color_counts['green']}根")
        print(f"  🔴 红色: {color_counts['red']}根")
        print(f"  🟡 黄色: {color_counts['yellow']}根")
        print(f"  ⚪ 空白: {color_counts.get('blank', 0)}根 (占比: {color_counts.get('blank_ratio', 0):.1f}%)")
        
        # 判断信号
        signal, description = determine_market_signal(color_counts)
        print(f"\n🎯 市场信号: {signal}")
        print(f"📝 说明: {description}")
        
        # 保存JSONL
        print(f"\n💾 保存JSONL文件...")
        if save_prediction_jsonl(date_str, color_counts, signal, description):
            print(f"✅ {date_str} 数据已保存")
            success_count += 1
        else:
            print(f"❌ {date_str} 保存失败")
            fail_count += 1
        
        current_date += timedelta(days=1)
    
    # 统计结果
    print("\n" + "=" * 80)
    print("重新生成完成")
    print("=" * 80)
    print(f"✅ 成功: {success_count} 天")
    print(f"❌ 失败: {fail_count} 天")
    print(f"⚠️  跳过: {skip_count} 天 (无数据)")
    print(f"📊 总计: {success_count + fail_count + skip_count} 天")
    print()
    
    # 显示生成的文件
    print("=" * 80)
    print("生成的JSONL文件列表")
    print("=" * 80)
    import subprocess
    result = subprocess.run(
        ['ls', '-lh', PREDICTION_DIR],
        capture_output=True,
        text=True,
        cwd='/home/user/webapp'
    )
    
    # 只显示JSONL文件
    for line in result.stdout.split('\n'):
        if '.jsonl' in line and 'prediction_2026' in line:
            print(line)

if __name__ == "__main__":
    regenerate_february_predictions()
