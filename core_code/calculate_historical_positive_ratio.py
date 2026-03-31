#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量计算历史数据的正数占比统计
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

def calculate_positive_ratio_for_date(date_str):
    """计算指定日期的正数占比
    
    Args:
        date_str: 日期字符串，格式为YYYYMMDD
        
    Returns:
        dict: 统计结果，包含positive_ratio, positive_count, total_count等
    """
    data_dir = Path('/home/user/webapp/data/coin_change_tracker')
    coin_change_file = data_dir / f'coin_change_{date_str}.jsonl'
    
    if not coin_change_file.exists():
        return None
    
    # 读取所有数据计算统计
    positive_count = 0
    total_count = 0
    
    try:
        with open(coin_change_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.strip():
                    record = json.loads(line.strip())
                    total_change = record.get('cumulative_pct', 0) or record.get('total_change', 0)
                    
                    total_count += 1
                    if total_change > 0:
                        positive_count += 1
        
        if total_count == 0:
            return None
        
        # 计算占比
        positive_ratio = (positive_count / total_count) * 100
        # 假设数据采集间隔约为75秒 (实际可能在60-90秒之间)
        positive_duration = positive_count * 1.25  # 分钟
        
        stats = {
            'positive_ratio': round(positive_ratio, 2),
            'positive_count': positive_count,
            'total_count': total_count,
            'positive_duration': round(positive_duration, 1),
            'date': date_str
        }
        
        return stats
        
    except Exception as e:
        print(f"  ❌ 处理失败: {e}")
        return None

def save_stats_to_file(date_str, stats):
    """保存统计数据到JSONL文件
    
    Args:
        date_str: 日期字符串，格式为YYYYMMDD
        stats: 统计结果字典
    """
    stats_dir = Path('/home/user/webapp/data/positive_ratio_stats')
    stats_dir.mkdir(parents=True, exist_ok=True)
    
    stats_file = stats_dir / f'positive_ratio_{date_str}.jsonl'
    beijing_now = datetime.now(timezone(timedelta(hours=8)))
    
    stats_record = {
        'timestamp': beijing_now.strftime('%Y-%m-%d %H:%M:%S'),
        'date': date_str,
        **stats
    }
    
    # 覆盖写入（避免重复）
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats_record, f, ensure_ascii=False)
        f.write('\n')

def main():
    """主函数：批量计算所有历史数据的正数占比"""
    print("=" * 80)
    print("批量计算历史数据的正数占比统计")
    print("=" * 80)
    print()
    
    data_dir = Path('/home/user/webapp/data/coin_change_tracker')
    
    # 查找所有coin_change文件
    coin_change_files = sorted(data_dir.glob('coin_change_*.jsonl'))
    
    if not coin_change_files:
        print("❌ 未找到任何历史数据文件")
        return
    
    print(f"📊 找到 {len(coin_change_files)} 个历史数据文件")
    print()
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for file_path in coin_change_files:
        # 提取日期
        filename = file_path.name
        date_str = filename.replace('coin_change_', '').replace('.jsonl', '')
        
        # 格式化日期显示 (YYYYMMDD -> YYYY-MM-DD)
        if len(date_str) == 8:
            display_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
        else:
            display_date = date_str
        
        print(f"处理 {display_date}...", end=' ')
        
        # 计算统计
        stats = calculate_positive_ratio_for_date(date_str)
        
        if stats is None:
            print("⚠️  跳过（无数据或错误）")
            skip_count += 1
            continue
        
        # 保存到文件
        try:
            save_stats_to_file(date_str, stats)
            
            # 显示结果
            positive_ratio = stats['positive_ratio']
            positive_count = stats['positive_count']
            total_count = stats['total_count']
            
            # 根据占比显示不同的状态
            if positive_ratio > 60:
                status_icon = "🟢"
                status = "强势上涨"
            elif positive_ratio > 50:
                status_icon = "🟡"
                status = "偏多"
            elif positive_ratio > 40:
                status_icon = "🟠"
                status = "偏空"
            else:
                status_icon = "🔴"
                status = "大幅下跌"
            
            print(f"✅ {status_icon} {positive_ratio}% ({positive_count}/{total_count}) - {status}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            error_count += 1
    
    print()
    print("=" * 80)
    print("统计完成")
    print("=" * 80)
    print(f"✅ 成功: {success_count} 个")
    print(f"⚠️  跳过: {skip_count} 个")
    print(f"❌ 失败: {error_count} 个")
    print()
    print(f"📁 数据保存位置: data/positive_ratio_stats/")
    print("=" * 80)

if __name__ == '__main__':
    main()
