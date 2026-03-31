#!/usr/bin/env python3
"""
SAR偏离趋势每日统计生成器
每天凌晨0:05执行，统计前一天的数据并保存到summary文件
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 数据目录
DATA_DIR = Path('/home/user/webapp/data/sar_bias_stats')
DATA_DIR.mkdir(parents=True, exist_ok=True)

def calculate_daily_stats(date_str):
    """计算指定日期的每日统计
    
    Args:
        date_str: 日期字符串，格式 YYYYMMDD
    
    Returns:
        dict: {
            'date': 'YYYY-MM-DD',
            'total_bullish': int,  # 所有时间点的偏多count之和
            'total_bearish': int,  # 所有时间点的偏空count之和
            'total_points': int,   # 总数据点数
            'unique_bullish_symbols': list,  # 去重后的偏多币种列表
            'unique_bearish_symbols': list,  # 去重后的偏空币种列表
            'generated_at': 'YYYY-MM-DD HH:MM:SS'
        }
    """
    jsonl_file = DATA_DIR / f'bias_stats_{date_str}.jsonl'
    
    if not jsonl_file.exists():
        print(f'⚠️ 文件不存在: {jsonl_file}')
        return None
    
    total_bullish = 0
    total_bearish = 0
    total_points = 0
    unique_bullish = set()
    unique_bearish = set()
    
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                total_bullish += record.get('bullish_count', 0)
                total_bearish += record.get('bearish_count', 0)
                total_points += 1
                
                # 收集所有出现过的币种（去重）
                for symbol_info in record.get('bullish_symbols', []):
                    unique_bullish.add(symbol_info['symbol'])
                
                for symbol_info in record.get('bearish_symbols', []):
                    unique_bearish.add(symbol_info['symbol'])
                    
            except json.JSONDecodeError as e:
                print(f'⚠️ 解析JSON失败: {e}')
                continue
    
    beijing_now = datetime.now(BEIJING_TZ)
    
    # 格式化日期
    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    
    stats = {
        'date': formatted_date,
        'total_bullish': total_bullish,
        'total_bearish': total_bearish,
        'total_points': total_points,
        'unique_bullish_symbols': sorted(list(unique_bullish)),
        'unique_bearish_symbols': sorted(list(unique_bearish)),
        'unique_bullish_count': len(unique_bullish),
        'unique_bearish_count': len(unique_bearish),
        'generated_at': beijing_now.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    print(f'✅ 统计完成: {formatted_date}')
    print(f'   偏多总点数: {total_bullish}, 去重币种数: {len(unique_bullish)}')
    print(f'   偏空总点数: {total_bearish}, 去重币种数: {len(unique_bearish)}')
    print(f'   总数据点: {total_points}')
    
    return stats

def save_daily_stats(stats):
    """保存每日统计到单独的summary文件"""
    if not stats:
        return False
    
    date_str = stats['date'].replace('-', '')
    summary_file = DATA_DIR / f'daily_summary_{date_str}.json'
    
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f'✅ 统计已保存: {summary_file.name}')
        return True
    except Exception as e:
        print(f'❌ 保存失败: {e}')
        return False

def generate_yesterday_stats():
    """生成昨天的统计（用于定时任务）"""
    beijing_now = datetime.now(BEIJING_TZ)
    yesterday = beijing_now - timedelta(days=1)
    date_str = yesterday.strftime('%Y%m%d')
    
    print('='*60)
    print(f'SAR偏离趋势每日统计生成器')
    print(f'生成日期: {yesterday.strftime("%Y-%m-%d")}')
    print('='*60)
    
    stats = calculate_daily_stats(date_str)
    
    if stats:
        if save_daily_stats(stats):
            print('✅ 昨日统计生成成功')
            return True
        else:
            print('❌ 保存统计失败')
            return False
    else:
        print('❌ 计算统计失败')
        return False

def generate_specific_date_stats(date_str):
    """生成指定日期的统计（用于手动补充历史数据）
    
    Args:
        date_str: 日期字符串，格式 YYYY-MM-DD 或 YYYYMMDD
    """
    # 标准化日期格式
    date_str = date_str.replace('-', '')
    
    if len(date_str) != 8:
        print('❌ 日期格式错误，应为 YYYYMMDD')
        return False
    
    print('='*60)
    print(f'SAR偏离趋势每日统计生成器')
    print(f'生成日期: {date_str[:4]}-{date_str[4:6]}-{date_str[6:]}')
    print('='*60)
    
    stats = calculate_daily_stats(date_str)
    
    if stats:
        if save_daily_stats(stats):
            print('✅ 统计生成成功')
            return True
        else:
            print('❌ 保存统计失败')
            return False
    else:
        print('❌ 计算统计失败')
        return False

def generate_all_historical_stats():
    """生成所有历史数据的统计（批量处理）"""
    print('='*60)
    print('批量生成所有历史数据统计')
    print('='*60)
    
    jsonl_files = sorted(DATA_DIR.glob('bias_stats_*.jsonl'))
    
    if not jsonl_files:
        print('⚠️ 没有找到任何数据文件')
        return
    
    success_count = 0
    fail_count = 0
    
    for jsonl_file in jsonl_files:
        date_str = jsonl_file.stem.replace('bias_stats_', '')
        
        # 检查summary文件是否已存在
        summary_file = DATA_DIR / f'daily_summary_{date_str}.json'
        if summary_file.exists():
            print(f'⏭️  {date_str[:4]}-{date_str[4:6]}-{date_str[6:]} 已有统计，跳过')
            continue
        
        print(f'\n处理: {date_str[:4]}-{date_str[4:6]}-{date_str[6:]}')
        print('-' * 60)
        
        stats = calculate_daily_stats(date_str)
        
        if stats and save_daily_stats(stats):
            success_count += 1
        else:
            fail_count += 1
    
    print('\n' + '='*60)
    print(f'批量生成完成: 成功 {success_count} 个, 失败 {fail_count} 个')
    print('='*60)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) == 1:
        # 无参数：生成昨天的统计
        generate_yesterday_stats()
    elif sys.argv[1] == '--all':
        # --all: 生成所有历史统计
        generate_all_historical_stats()
    elif sys.argv[1] == '--date' and len(sys.argv) == 3:
        # --date YYYY-MM-DD: 生成指定日期的统计
        generate_specific_date_stats(sys.argv[2])
    else:
        print('用法:')
        print('  python3 sar_bias_daily_stats_generator.py           # 生成昨天的统计')
        print('  python3 sar_bias_daily_stats_generator.py --all     # 生成所有历史统计')
        print('  python3 sar_bias_daily_stats_generator.py --date 2026-02-28  # 生成指定日期的统计')
        sys.exit(1)
