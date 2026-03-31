#!/usr/bin/env python3
"""
生成首页系统的每日数据详情报告
"""
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def analyze_jsonl_files(directory):
    """分析JSONL文件的每日数据"""
    files = list(Path(directory).glob("*.jsonl"))
    if not files:
        return None
    
    daily_stats = {}
    total_records = 0
    
    for file in sorted(files):
        # 提取日期
        date = None
        filename = file.stem
        
        # 尝试从文件名提取日期
        parts = filename.split('_')
        for part in parts:
            if len(part) == 10 and part.count('-') == 2:  # YYYY-MM-DD
                date = part
                break
            elif len(part) == 8 and part.isdigit():  # YYYYMMDD
                date = f"{part[:4]}-{part[4:6]}-{part[6:8]}"
                break
        
        # 统计记录数
        try:
            with open(file, 'r', encoding='utf-8') as f:
                record_count = sum(1 for line in f if line.strip())
        except:
            record_count = 0
        
        file_size = file.stat().st_size / 1024  # KB
        
        if date:
            if date not in daily_stats:
                daily_stats[date] = {
                    'files': [],
                    'total_records': 0,
                    'total_size': 0
                }
            
            daily_stats[date]['files'].append(file.name)
            daily_stats[date]['total_records'] += record_count
            daily_stats[date]['total_size'] += file_size
        
        total_records += record_count
    
    return {
        'daily_stats': daily_stats,
        'total_files': len(files),
        'total_records': total_records,
        'date_range': f"{min(daily_stats.keys())} ~ {max(daily_stats.keys())}" if daily_stats else "N/A",
        'days_count': len(daily_stats)
    }

# 有JSONL数据的8个系统
SYSTEMS_WITH_DATA = {
    "SAR趋势系统": {
        "dirs": ["sar_jsonl", "sar_slope_jsonl", "sar_1min", "sar_bias_stats"],
        "color": "🟢"
    },
    "支撑压力(大盘)": {
        "dirs": ["support_resistance_jsonl", "support_resistance_daily"],
        "color": "🔵"
    },
    "OKX全生态": {
        "dirs": ["okx_trading_jsonl", "okx_trading_history", "okx_trading_logs", 
                "okx_angle_analysis", "okx_auto_strategy", "okx_tpsl_settings"],
        "color": "🟡"
    },
    "OKX日涨幅统计日记": {
        "dirs": ["okx_day_change"],
        "color": "🟠"
    },
    "恐慌监控洗盘": {
        "dirs": ["panic_jsonl", "panic_daily"],
        "color": "🔴"
    },
    "11信号日线总": {
        "dirs": ["signal_stats"],
        "color": "🟣"
    },
    "逃顶信号系统": {
        "dirs": ["escape_signal_jsonl"],
        "color": "🟤"
    },
    "价格位置预警系统": {
        "dirs": ["price_speed_jsonl", "price_speed_10m", "price_position"],
        "color": "⚪"
    }
}

def main():
    data_base = Path("/home/user/webapp/data")
    
    print("="*80)
    print("首页系统每日数据详情报告")
    print(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    all_systems_stats = {}
    
    for system_name, info in SYSTEMS_WITH_DATA.items():
        print(f"\n{info['color']} {system_name}")
        print("-" * 80)
        
        system_total_files = 0
        system_total_records = 0
        system_total_days = set()
        system_daily_details = defaultdict(lambda: {'records': 0, 'files': [], 'size': 0})
        
        for dir_name in info['dirs']:
            dir_path = data_base / dir_name
            if not dir_path.exists():
                continue
            
            result = analyze_jsonl_files(dir_path)
            if not result:
                continue
            
            system_total_files += result['total_files']
            system_total_records += result['total_records']
            
            print(f"\n  📁 {dir_name}/")
            print(f"     • 文件数: {result['total_files']}")
            print(f"     • 总记录数: {result['total_records']:,}")
            print(f"     • 日期范围: {result['date_range']}")
            print(f"     • 数据天数: {result['days_count']} 天")
            
            if result['daily_stats']:
                print(f"     • 每日详情:")
                for date in sorted(result['daily_stats'].keys()):
                    stats = result['daily_stats'][date]
                    system_total_days.add(date)
                    system_daily_details[date]['records'] += stats['total_records']
                    system_daily_details[date]['files'].extend(stats['files'])
                    system_daily_details[date]['size'] += stats['total_size']
                    
                    print(f"       - {date}: {stats['total_records']:,} 条记录, "
                          f"{stats['total_size']:.2f} KB, "
                          f"{len(stats['files'])} 文件")
        
        # 系统总计
        print(f"\n  📊 系统汇总:")
        print(f"     • 总文件数: {system_total_files}")
        print(f"     • 总记录数: {system_total_records:,}")
        print(f"     • 数据天数: {len(system_total_days)} 天")
        
        if system_total_days:
            print(f"     • 时间跨度: {min(system_total_days)} ~ {max(system_total_days)}")
            
            # 显示每日汇总（如果有多个子目录）
            if len(info['dirs']) > 1:
                print(f"\n  📅 每日汇总 (所有子目录合并):")
                for date in sorted(system_daily_details.keys()):
                    details = system_daily_details[date]
                    print(f"     {date}: {details['records']:,} 条记录, "
                          f"{details['size']:.2f} KB, "
                          f"{len(details['files'])} 文件")
        
        all_systems_stats[system_name] = {
            'files': system_total_files,
            'records': system_total_records,
            'days': len(system_total_days),
            'date_range': f"{min(system_total_days)} ~ {max(system_total_days)}" if system_total_days else "N/A"
        }
    
    # 总体统计
    print("\n" + "="*80)
    print("总体统计")
    print("="*80)
    
    total_files = sum(s['files'] for s in all_systems_stats.values())
    total_records = sum(s['records'] for s in all_systems_stats.values())
    
    print(f"\n有JSONL数据的系统数: {len(all_systems_stats)}")
    print(f"总文件数: {total_files}")
    print(f"总记录数: {total_records:,}")
    
    print(f"\n各系统数据天数:")
    for system_name, stats in sorted(all_systems_stats.items(), 
                                     key=lambda x: x[1]['days'], 
                                     reverse=True):
        print(f"  • {system_name}: {stats['days']} 天 ({stats['date_range']})")
    
    # 无JSONL数据的系统说明
    print("\n" + "="*80)
    print("无JSONL数据的系统说明 (6个)")
    print("="*80)
    
    no_data_systems = {
        "OKX利润分析": "基于OKX交易数据实时计算利润，不独立存储JSONL",
        "数据管理与备份": "纯Web管理工具，用于管理其他系统的JSONL数据",
        "重大事件监控": "聚合多个系统的事件数据，不独立存储JSONL",
        "数据健康监控": "监控其他系统的数据健康状态，不独立存储JSONL",
        "ZT行高跌盘预警系统": "可能尚未实现数据采集功能",
        "支撑压力系统配置": "纯配置页面，用于设置系统参数"
    }
    
    for system, reason in no_data_systems.items():
        print(f"\n⚪ {system}")
        print(f"   原因: {reason}")

if __name__ == "__main__":
    main()
