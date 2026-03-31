#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量计算2月份每天的波峰数据
按天保存结果到 data/coin_change_tracker/wave_peaks/
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加源代码目录到路径
sys.path.insert(0, '/home/user/webapp/source_code')
from wave_peak_detector import WavePeakDetector

def process_daily_wave_peaks(start_date='20260201', end_date='20260218'):
    """
    处理指定日期范围的波峰数据
    
    Args:
        start_date: 开始日期，格式YYYYMMDD
        end_date: 结束日期，格式YYYYMMDD
    """
    data_dir = Path('/home/user/webapp/data/coin_change_tracker')
    output_dir = data_dir / 'wave_peaks'
    output_dir.mkdir(exist_ok=True)
    
    # 转换日期
    start_dt = datetime.strptime(start_date, '%Y%m%d')
    end_dt = datetime.strptime(end_date, '%Y%m%d')
    
    print('=' * 80)
    print('📊 批量波峰检测分析')
    print('=' * 80)
    print(f"\n日期范围: {start_date} ~ {end_date}")
    print(f"输出目录: {output_dir}")
    print(f"\n开始处理...\n")
    
    # 创建检测器
    detector = WavePeakDetector(min_amplitude=35.0, window_minutes=15)
    
    # 统计信息
    total_days = 0
    success_days = 0
    total_peaks = 0
    false_breakout_days = 0
    
    summary_data = []
    
    # 遍历每一天
    current_dt = start_dt
    while current_dt <= end_dt:
        date_str = current_dt.strftime('%Y%m%d')
        data_file = data_dir / f'coin_change_{date_str}.jsonl'
        
        total_days += 1
        
        if not data_file.exists():
            print(f"⚠️  {date_str}: 数据文件不存在，跳过")
            current_dt += timedelta(days=1)
            continue
        
        print(f"📅 处理 {date_str}...", end=' ')
        
        try:
            # 加载数据
            data_records = detector.load_data(str(data_file))
            
            if len(data_records) == 0:
                print("❌ 数据为空")
                current_dt += timedelta(days=1)
                continue
            
            # 检测波峰（关闭调试输出）
            import io
            import contextlib
            
            # 临时捕获输出
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                wave_peaks = detector.detect_wave_peaks(data_records)
                false_breakout = detector.detect_false_breakout(wave_peaks)
            
            # 构建结果
            result = {
                'date': date_str,
                'data_points': len(data_records),
                'peaks_count': len(wave_peaks),
                'false_breakout': false_breakout,
                'peaks': wave_peaks,
                'processed_at': datetime.now().isoformat()
            }
            
            # 保存到文件
            output_file = output_dir / f'wave_peaks_{date_str}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # 统计
            success_days += 1
            total_peaks += len(wave_peaks)
            if false_breakout:
                false_breakout_days += 1
            
            # 简要信息
            fb_flag = '⚠️ 假突破' if false_breakout else ''
            print(f"✅ {len(wave_peaks)}个波峰 {fb_flag}")
            
            # 记录摘要
            summary_data.append({
                'date': date_str,
                'peaks_count': len(wave_peaks),
                'has_false_breakout': false_breakout is not None,
                'data_points': len(data_records)
            })
            
        except Exception as e:
            print(f"❌ 错误: {str(e)}")
        
        current_dt += timedelta(days=1)
    
    # 保存汇总数据
    summary_file = output_dir / 'summary.json'
    summary = {
        'date_range': {
            'start': start_date,
            'end': end_date
        },
        'statistics': {
            'total_days': total_days,
            'success_days': success_days,
            'total_peaks': total_peaks,
            'false_breakout_days': false_breakout_days,
            'avg_peaks_per_day': total_peaks / success_days if success_days > 0 else 0
        },
        'daily_data': summary_data,
        'generated_at': datetime.now().isoformat()
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print('\n' + '=' * 80)
    print('📊 处理完成统计')
    print('=' * 80)
    print(f"\n总天数: {total_days}")
    print(f"成功处理: {success_days}天")
    print(f"检测到波峰总数: {total_peaks}个")
    print(f"假突破天数: {false_breakout_days}天")
    print(f"平均每天波峰数: {total_peaks / success_days if success_days > 0 else 0:.2f}个")
    print(f"\n结果保存位置:")
    print(f"  详细数据: {output_dir}/wave_peaks_YYYYMMDD.json")
    print(f"  汇总数据: {summary_file}")
    print('=' * 80)
    
    return summary

if __name__ == '__main__':
    # 处理2月份的数据
    summary = process_daily_wave_peaks(start_date='20260201', end_date='20260218')
