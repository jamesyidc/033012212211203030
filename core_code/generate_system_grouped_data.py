#!/usr/bin/env python3
"""
生成按首页系统分组的JSONL数据统计
"""
import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 首页系统与JSONL目录的映射关系
# 注意：只显示当前正在运行的系统
# 已停用系统：支撑压力(大盘) (已被价格位置预警系统替代)
#            逃顶信号系统 (已合并到价格位置预警系统)
SYSTEM_MAPPING = {
    "SAR趋势系统": {
        "dirs": ["sar_jsonl", "sar_slope_jsonl", "sar_1min", "sar_bias_stats"],
        "icon": "📈",
        "color": "#10B981"
    },
    "OKX全生态": {
        "dirs": ["okx_trading_jsonl", "okx_trading_history", "okx_trading_logs", 
                "okx_angle_analysis", "okx_auto_strategy", "okx_tpsl_settings"],
        "icon": "💹",
        "color": "#F59E0B"
    },
    "OKX日涨幅统计日记": {
        "dirs": ["okx_day_change"],
        "icon": "📊",
        "color": "#EF4444"
    },
    "恐慌监控洗盘": {
        "dirs": ["panic_jsonl", "panic_daily"],
        "icon": "⚠️",
        "color": "#DC2626"
    },
    "11信号日线总": {
        "dirs": ["signal_stats"],
        "icon": "🔔",
        "color": "#8B5CF6"
    },
    "价格位置预警系统": {
        "dirs": ["price_speed_jsonl", "price_speed_10m", "price_position"],
        "icon": "📍",
        "color": "#06B6D4"
    },
    "27币涨跌幅追踪系统": {
        "dirs": ["coin_change_tracker"],
        "icon": "📉",
        "color": "#6366F1"
    },
    "创新高创新低统计系统": {
        "dirs": ["new_high_low"],
        "icon": "🔥",
        "color": "#EC4899"
    }
}

# 🗄️ 历史数据目录（仅供归档参考，不在界面显示）
ARCHIVED_SYSTEMS = {
    "支撑压力(大盘)_已停用": {
        "dirs": ["support_resistance_jsonl", "support_resistance_daily"],
        "stopped_date": "2026-02-07",
        "reason": "已被价格位置预警系统v2.0.5替代",
        "icon": "🎯"
    },
    "逃顶信号系统_已停用": {
        "dirs": ["escape_signal_jsonl"],
        "stopped_date": "2026-01-28",
        "reason": "已合并到价格位置预警系统",
        "icon": "🚨"
    }
}

def analyze_jsonl_file(file_path):
    """分析单个JSONL文件"""
    try:
        record_count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record_count += 1
        
        file_size = os.path.getsize(file_path)
        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        # 尝试从文件名提取日期
        filename = os.path.basename(file_path)
        date = None
        parts = filename.replace('.jsonl', '').split('_')
        for part in parts:
            if len(part) == 8 and part.isdigit():  # YYYYMMDD
                date = f"{part[:4]}-{part[4:6]}-{part[6:8]}"
                break
            elif len(part) == 10 and part.count('-') == 2:  # YYYY-MM-DD
                date = part
                break
        
        return {
            'filename': filename,
            'path': str(file_path),
            'records': record_count,
            'size': file_size,
            'modified': mod_time.strftime('%Y-%m-%d %H:%M:%S'),
            'date': date
        }
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return None

def scan_system_data():
    """扫描所有系统的JSONL数据"""
    data_base = Path('/home/user/webapp/data')
    systems_data = {}
    
    for system_name, config in SYSTEM_MAPPING.items():
        system_info = {
            'name': system_name,
            'icon': config['icon'],
            'color': config['color'],
            'directories': {},
            'total_files': 0,
            'total_records': 0,
            'total_size': 0,
            'total_days': 0,
            'date_range': {'min': None, 'max': None}
        }
        
        all_dates = set()
        
        for dir_name in config['dirs']:
            dir_path = data_base / dir_name
            if not dir_path.exists():
                continue
            
            jsonl_files = list(dir_path.glob('*.jsonl'))
            if not jsonl_files:
                continue
            
            dir_info = {
                'name': dir_name,
                'files': [],
                'total_records': 0,
                'total_size': 0,
                'daily_stats': {}
            }
            
            for file_path in sorted(jsonl_files):
                file_info = analyze_jsonl_file(file_path)
                if file_info:
                    dir_info['files'].append(file_info)
                    dir_info['total_records'] += file_info['records']
                    dir_info['total_size'] += file_info['size']
                    
                    # 按日期统计
                    if file_info['date']:
                        all_dates.add(file_info['date'])
                        if file_info['date'] not in dir_info['daily_stats']:
                            dir_info['daily_stats'][file_info['date']] = {
                                'files': [],
                                'records': 0,
                                'size': 0
                            }
                        dir_info['daily_stats'][file_info['date']]['files'].append(file_info['filename'])
                        dir_info['daily_stats'][file_info['date']]['records'] += file_info['records']
                        dir_info['daily_stats'][file_info['date']]['size'] += file_info['size']
            
            if dir_info['files']:
                system_info['directories'][dir_name] = dir_info
                system_info['total_files'] += len(dir_info['files'])
                system_info['total_records'] += dir_info['total_records']
                system_info['total_size'] += dir_info['total_size']
        
        # 计算日期范围
        if all_dates:
            sorted_dates = sorted(all_dates)
            system_info['date_range']['min'] = sorted_dates[0]
            system_info['date_range']['max'] = sorted_dates[-1]
            system_info['total_days'] = len(all_dates)
        
        if system_info['total_files'] > 0:
            systems_data[system_name] = system_info
    
    return systems_data

if __name__ == '__main__':
    print("扫描系统数据...")
    data = scan_system_data()
    
    # 保存到JSON文件
    output_file = '/home/user/webapp/data/system_grouped_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 数据已保存到: {output_file}")
    
    # 显示统计
    print("\n系统统计:")
    for system_name, info in data.items():
        print(f"\n{info['icon']} {system_name}")
        print(f"  文件数: {info['total_files']}")
        print(f"  记录数: {info['total_records']:,}")
        print(f"  大小: {info['total_size'] / 1024 / 1024:.2f} MB")
        print(f"  数据天数: {info['total_days']} 天")
        if info['date_range']['min']:
            print(f"  日期范围: {info['date_range']['min']} ~ {info['date_range']['max']}")
