#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成历史预判数据
遍历所有历史日期，分析0-2点数据，生成预判结果
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitors.coin_change_prediction_monitor import analyze_bar_colors, determine_market_signal

def generate_prediction_for_date(date_str):
    """为指定日期生成预判数据"""
    try:
        url = f"https://9002-iopxcqas7abbrajoi4k4x-2e77fc33.sandbox.novita.ai/api/coin-change-tracker/history?date={date_str}"
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            return None
        
        result = response.json()
        history = result.get('data', result)
        
        # 收集0-2点的数据
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
        
        if not morning_records:
            return None
        
        # 分析数据
        data = {'records': morning_records, 'date': date_str}
        color_counts = analyze_bar_colors(data)
        
        if not color_counts:
            return None
        
        signal, description = determine_market_signal(color_counts)
        
        return {
            'date': date_str,
            'timestamp': f"{date_str} 02:00:00",  # 假设在2点完成分析
            'color_counts': color_counts,
            'signal': signal,
            'description': description
        }
    
    except Exception as e:
        print(f"  ❌ {date_str}: {e}")
        return None

def main():
    """主函数：生成所有历史日期的预判数据"""
    print("🚀 开始生成历史预判数据...")
    
    # 创建输出目录
    output_dir = Path('data/daily_predictions')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成日期范围（最近30天）
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    predictions = {}
    success_count = 0
    fail_count = 0
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"📊 处理 {date_str}...", end=' ')
        
        prediction = generate_prediction_for_date(date_str)
        
        if prediction:
            predictions[date_str] = prediction
            
            # 保存单个文件
            output_file = output_dir / f'prediction_{date_str}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(prediction, f, ensure_ascii=False, indent=2)
            
            print(f"✅ {prediction['signal']}")
            success_count += 1
        else:
            print(f"⚠️ 无数据")
            fail_count += 1
        
        current_date += timedelta(days=1)
    
    # 保存汇总文件
    summary_file = output_dir / 'predictions_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 完成！成功: {success_count}, 失败: {fail_count}")
    print(f"📁 输出目录: {output_dir}")
    print(f"📄 汇总文件: {summary_file}")

if __name__ == "__main__":
    main()
