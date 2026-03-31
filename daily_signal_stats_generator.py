#!/usr/bin/env python3
"""
Daily Signal Stats Generator - 每日信号统计生成器
确保每天都有完整的信号统计数据（每3分钟一个数据点）

功能：
1. 每天生成480个时间点（00:00 到 23:57，每3分钟）
2. 查询每个时间点之前24h和2h的信号统计
3. 即使没有信号，也生成零值记录
4. 确保图表能显示完整的24小时数据

使用方法：
1. 生成今天的数据: python3 daily_signal_stats_generator.py
2. 生成指定日期: python3 daily_signal_stats_generator.py 2026-02-16
3. 生成日期范围: python3 daily_signal_stats_generator.py 2026-02-16 2026-02-17
"""

import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import json
import pytz

# 配置
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / 'price_position_v2' / 'config' / 'data' / 'db' / 'price_position.db'
DATA_DIR = BASE_DIR / 'data' / 'signal_stats'
DATA_DIR.mkdir(parents=True, exist_ok=True)

def get_beijing_time():
    """获取北京时间"""
    beijing_tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(beijing_tz)

def calculate_signal_counts(conn, target_time, window_hours):
    """
    计算指定时间点之前N小时内的信号统计
    
    Returns:
        tuple: (sell_count, buy_count)
    """
    cursor = conn.cursor()
    window_start = target_time - timedelta(hours=window_hours)
    
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN signal_type = '逃顶信号' THEN 1 ELSE 0 END) as sell_count,
            SUM(CASE WHEN signal_type = '抄底信号' THEN 1 ELSE 0 END) as buy_count
        FROM signal_timeline
        WHERE snapshot_time > ? AND snapshot_time <= ?
    ''', (window_start.strftime('%Y-%m-%d %H:%M:%S'), 
          target_time.strftime('%Y-%m-%d %H:%M:%S')))
    
    result = cursor.fetchone()
    sell_count = result[0] if result[0] is not None else 0
    buy_count = result[1] if result[1] is not None else 0
    
    return sell_count, buy_count

def generate_daily_stats(date_str):
    """
    生成指定日期的完整统计数据（480个数据点）
    
    Args:
        date_str: 日期字符串，格式 YYYY-MM-DD
    """
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    date_file_str = date_obj.strftime('%Y%m%d')
    
    print(f"\n{'='*60}")
    print(f"生成 {date_str} 的信号统计数据")
    print(f"{'='*60}")
    
    # 连接数据库
    conn = sqlite3.connect(str(DB_PATH))
    
    # 准备输出文件
    sell_file = DATA_DIR / f'signal_stats_sell_{date_file_str}.jsonl'
    buy_file = DATA_DIR / f'signal_stats_buy_{date_file_str}.jsonl'
    
    # 判断是否是今天
    beijing_time = get_beijing_time()
    today_str = beijing_time.strftime('%Y-%m-%d')
    is_today = (date_str == today_str)
    
    # 生成时间点（每3分钟）
    time_points = []
    # 确保 current_time 是 naive datetime (无时区信息)
    current_time = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 如果是今天，只生成到当前时间；如果是历史日期，生成全天24小时
    if is_today:
        # 只生成到当前时间，向下取整到3分钟
        # beijing_time 是 aware datetime，需要转换为 naive
        end_time = beijing_time.replace(tzinfo=None)
        # 向下取整到3分钟边界
        minutes = (end_time.minute // 3) * 3
        end_time = end_time.replace(minute=minutes, second=0, microsecond=0)
        print(f"⚠️  今天的数据，只生成到当前时间: {end_time.strftime('%H:%M:%S')}")
    else:
        # 历史日期，生成全天数据
        end_time = current_time + timedelta(days=1)
    
    while current_time < end_time:
        time_points.append(current_time)
        current_time += timedelta(minutes=3)
    
    print(f"生成 {len(time_points)} 个时间点")
    
    # 写入数据
    with open(sell_file, 'w', encoding='utf-8') as f_sell, \
         open(buy_file, 'w', encoding='utf-8') as f_buy:
        
        for i, time_point in enumerate(time_points):
            time_str = time_point.strftime('%Y-%m-%d %H:%M:%S')
            
            # 计算24h和2h统计
            sell_24h, buy_24h = calculate_signal_counts(conn, time_point, 24)
            sell_2h, buy_2h = calculate_signal_counts(conn, time_point, 2)
            
            # 逃顶信号记录
            sell_entry = {
                'time': time_str,
                'sell_24h': sell_24h,
                'sell_2h': sell_2h
            }
            
            # 抄底信号记录
            buy_entry = {
                'time': time_str,
                'buy_24h': buy_24h,
                'buy_2h': buy_2h
            }
            
            f_sell.write(json.dumps(sell_entry, ensure_ascii=False) + '\n')
            f_buy.write(json.dumps(buy_entry, ensure_ascii=False) + '\n')
            
            if (i + 1) % 100 == 0:
                print(f"  已生成 {i+1}/{len(time_points)} 个数据点...")
    
    print(f"✅ 完成！生成 {len(time_points)} 条记录")
    print(f"  逃顶统计: {sell_file}")
    print(f"  抄底统计: {buy_file}")
    
    conn.close()

def main():
    """主函数"""
    if len(sys.argv) == 1:
        # 没有参数，生成今天的数据
        beijing_time = get_beijing_time()
        date_str = beijing_time.strftime('%Y-%m-%d')
        generate_daily_stats(date_str)
    
    elif len(sys.argv) == 2:
        # 一个参数，生成指定日期
        date_str = sys.argv[1]
        generate_daily_stats(date_str)
    
    elif len(sys.argv) == 3:
        # 两个参数，生成日期范围
        start_date_str = sys.argv[1]
        end_date_str = sys.argv[2]
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            generate_daily_stats(date_str)
            current_date += timedelta(days=1)
    
    else:
        print("使用方法:")
        print("  生成今天:     python3 daily_signal_stats_generator.py")
        print("  生成指定日期: python3 daily_signal_stats_generator.py 2026-02-16")
        print("  生成日期范围: python3 daily_signal_stats_generator.py 2026-02-16 2026-02-17")

if __name__ == '__main__':
    main()
