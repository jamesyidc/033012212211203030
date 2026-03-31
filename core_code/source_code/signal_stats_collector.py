#!/usr/bin/env python3
"""
Signal Statistics Collector - 信号统计采集器
滚动窗口统计数据采集器

功能：
1. 从数据库读取 signal_timeline 数据
2. 计算每个时间点的 24h 和 2h 滚动窗口统计
3. 按日期保存为 JSONL 文件

采集间隔：3分钟（与 price_position_collector 同步）
数据存储：data/signal_stats/
文件格式：
  - signal_stats_sell_YYYYMMDD.jsonl  # 逃顶信号统计
  - signal_stats_buy_YYYYMMDD.jsonl   # 抄底信号统计
"""

import sys
import time
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# 配置
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / 'price_position_v2' / 'config' / 'data' / 'db' / 'price_position.db'
DATA_DIR = BASE_DIR / 'data' / 'signal_stats'
COLLECT_INTERVAL = 180  # 3分钟

# 创建数据目录
DATA_DIR.mkdir(parents=True, exist_ok=True)

def get_beijing_time():
    """获取北京时间"""
    beijing_tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(beijing_tz)

def calculate_rolling_stats(conn, target_time_str, window_hours):
    """
    计算指定时间点的滚动窗口统计
    
    Args:
        conn: 数据库连接
        target_time_str: 目标时间（字符串格式）
        window_hours: 窗口大小（小时）
    
    Returns:
        dict: {
            'sell_count': 逃顶信号次数,
            'buy_count': 抄底信号次数,
            'data_points': 数据点数量
        }
    """
    cursor = conn.cursor()
    
    # 计算窗口开始时间
    target_time = datetime.strptime(target_time_str, '%Y-%m-%d %H:%M:%S')
    window_start = target_time - timedelta(hours=window_hours)
    window_start_str = window_start.strftime('%Y-%m-%d %H:%M:%S')
    
    # 查询窗口内的数据
    cursor.execute('''
        SELECT signal_type, COUNT(*) as count
        FROM signal_timeline
        WHERE snapshot_time > ? AND snapshot_time <= ?
        GROUP BY signal_type
    ''', (window_start_str, target_time_str))
    
    results = cursor.fetchall()
    
    # 统计结果
    sell_count = 0
    buy_count = 0
    
    for signal_type, count in results:
        if signal_type == '逃顶信号':
            sell_count = count
        elif signal_type == '抄底信号':
            buy_count = count
    
    # 获取总数据点数
    cursor.execute('''
        SELECT COUNT(*) FROM signal_timeline
        WHERE snapshot_time > ? AND snapshot_time <= ?
    ''', (window_start_str, target_time_str))
    
    data_points = cursor.fetchone()[0]
    
    return {
        'sell_count': sell_count,
        'buy_count': buy_count,
        'data_points': data_points
    }

def collect_today_stats():
    """采集今天的统计数据"""
    beijing_time = get_beijing_time()
    today_str = beijing_time.strftime('%Y%m%d')
    
    print(f"\n{'='*60}")
    print(f"开始采集信号统计数据 - {beijing_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # 连接数据库
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # 查询今天的所有数据点
    today_start = beijing_time.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_str = today_start.strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        SELECT snapshot_time, 
               support_line_48h, support_line_7d,
               pressure_line_48h, pressure_line_7d,
               signal_type, signal_triggered, trigger_reason
        FROM signal_timeline
        WHERE snapshot_time >= ?
        ORDER BY snapshot_time ASC
    ''', (today_start_str,))
    
    rows = cursor.fetchall()
    
    # 如果今天没有数据，生成当前时间点的零值记录
    if not rows:
        print("⚠ 今天还没有信号数据，生成零值记录")
        current_time_str = beijing_time.strftime('%Y-%m-%d %H:%M:%S')
        rows = [(current_time_str, 0, 0, 0, 0, '', 0, '')]
    
    print(f"✓ 找到/生成今天的 {len(rows)} 条数据点")
    
    # 准备 JSONL 文件路径
    sell_file = DATA_DIR / f'signal_stats_sell_{today_str}.jsonl'
    buy_file = DATA_DIR / f'signal_stats_buy_{today_str}.jsonl'
    
    # 打开文件（覆盖模式）
    with open(sell_file, 'w', encoding='utf-8') as f_sell, \
         open(buy_file, 'w', encoding='utf-8') as f_buy:
        
        processed_count = 0
        
        for row in rows:
            snapshot_time_str = row[0]
            support_48h = row[1]
            support_7d = row[2]
            pressure_48h = row[3]
            pressure_7d = row[4]
            signal_type = row[5] or ''
            signal_triggered = row[6]
            trigger_reason = row[7] or ''
            
            # 计算 24h 和 2h 滚动统计
            stats_24h = calculate_rolling_stats(conn, snapshot_time_str, 24)
            stats_2h = calculate_rolling_stats(conn, snapshot_time_str, 2)
            
            # 准备逃顶信号统计数据
            sell_entry = {
                'time': snapshot_time_str,
                'sell_24h': stats_24h['sell_count'],
                'sell_2h': stats_2h['sell_count'],
                'pressure_48h': pressure_48h,
                'pressure_7d': pressure_7d,
                'signal_type': signal_type if signal_type == '逃顶信号' else '',
                'signal_triggered': signal_triggered if signal_type == '逃顶信号' else 0,
                'trigger_reason': trigger_reason if signal_type == '逃顶信号' else '',
                'data_points_24h': stats_24h['data_points'],
                'data_points_2h': stats_2h['data_points']
            }
            
            # 准备抄底信号统计数据
            buy_entry = {
                'time': snapshot_time_str,
                'buy_24h': stats_24h['buy_count'],
                'buy_2h': stats_2h['buy_count'],
                'support_48h': support_48h,
                'support_7d': support_7d,
                'signal_type': signal_type if signal_type == '抄底信号' else '',
                'signal_triggered': signal_triggered if signal_type == '抄底信号' else 0,
                'trigger_reason': trigger_reason if signal_type == '抄底信号' else '',
                'data_points_24h': stats_24h['data_points'],
                'data_points_2h': stats_2h['data_points']
            }
            
            # 写入 JSONL
            f_sell.write(json.dumps(sell_entry, ensure_ascii=False) + '\n')
            f_buy.write(json.dumps(buy_entry, ensure_ascii=False) + '\n')
            
            processed_count += 1
            
            if processed_count % 50 == 0:
                print(f"  已处理 {processed_count}/{len(rows)} 条数据...")
    
    conn.close()
    
    print(f"✓ 处理完成: {processed_count} 条数据")
    print(f"✓ 逃顶统计文件: {sell_file}")
    print(f"✓ 抄底统计文件: {buy_file}")

def backfill_historical_data():
    """回填历史数据（一次性运行）"""
    print("\n" + "="*60)
    print("开始回填历史统计数据")
    print("="*60)
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # 获取所有不同的日期
    cursor.execute('''
        SELECT DISTINCT DATE(snapshot_time) as date
        FROM signal_timeline
        ORDER BY date ASC
    ''')
    
    dates = cursor.fetchall()
    
    if not dates:
        print("⚠ 数据库中没有数据")
        conn.close()
        return
    
    print(f"✓ 找到 {len(dates)} 个日期需要回填")
    
    for date_row in dates:
        date_str = date_row[0]
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        date_file_str = date_obj.strftime('%Y%m%d')
        
        print(f"\n处理日期: {date_str}")
        
        # 查询该日期的所有数据
        cursor.execute('''
            SELECT snapshot_time, 
                   support_line_48h, support_line_7d,
                   pressure_line_48h, pressure_line_7d,
                   signal_type, signal_triggered, trigger_reason
            FROM signal_timeline
            WHERE DATE(snapshot_time) = ?
            ORDER BY snapshot_time ASC
        ''', (date_str,))
        
        rows = cursor.fetchall()
        
        if not rows:
            continue
        
        # 准备文件路径
        sell_file = DATA_DIR / f'signal_stats_sell_{date_file_str}.jsonl'
        buy_file = DATA_DIR / f'signal_stats_buy_{date_file_str}.jsonl'
        
        with open(sell_file, 'w', encoding='utf-8') as f_sell, \
             open(buy_file, 'w', encoding='utf-8') as f_buy:
            
            for row in rows:
                snapshot_time_str = row[0]
                support_48h = row[1]
                support_7d = row[2]
                pressure_48h = row[3]
                pressure_7d = row[4]
                signal_type = row[5] or ''
                signal_triggered = row[6]
                trigger_reason = row[7] or ''
                
                # 计算滚动统计
                stats_24h = calculate_rolling_stats(conn, snapshot_time_str, 24)
                stats_2h = calculate_rolling_stats(conn, snapshot_time_str, 2)
                
                # 逃顶统计
                sell_entry = {
                    'time': snapshot_time_str,
                    'sell_24h': stats_24h['sell_count'],
                    'sell_2h': stats_2h['sell_count'],
                    'pressure_48h': pressure_48h,
                    'pressure_7d': pressure_7d,
                    'signal_type': signal_type if signal_type == '逃顶信号' else '',
                    'signal_triggered': signal_triggered if signal_type == '逃顶信号' else 0,
                    'trigger_reason': trigger_reason if signal_type == '逃顶信号' else '',
                    'data_points_24h': stats_24h['data_points'],
                    'data_points_2h': stats_2h['data_points']
                }
                
                # 抄底统计
                buy_entry = {
                    'time': snapshot_time_str,
                    'buy_24h': stats_24h['buy_count'],
                    'buy_2h': stats_2h['buy_count'],
                    'support_48h': support_48h,
                    'support_7d': support_7d,
                    'signal_type': signal_type if signal_type == '抄底信号' else '',
                    'signal_triggered': signal_triggered if signal_type == '抄底信号' else 0,
                    'trigger_reason': trigger_reason if signal_type == '抄底信号' else '',
                    'data_points_24h': stats_24h['data_points'],
                    'data_points_2h': stats_2h['data_points']
                }
                
                f_sell.write(json.dumps(sell_entry, ensure_ascii=False) + '\n')
                f_buy.write(json.dumps(buy_entry, ensure_ascii=False) + '\n')
        
        print(f"  ✓ {date_str}: {len(rows)} 条数据 -> {sell_file.name}, {buy_file.name}")
    
    conn.close()
    print("\n✓ 历史数据回填完成！")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Signal Statistics Collector')
    parser.add_argument('--backfill', action='store_true', 
                       help='回填所有历史数据（一次性运行）')
    parser.add_argument('--daemon', action='store_true',
                       help='后台运行模式（持续采集）')
    
    args = parser.parse_args()
    
    if args.backfill:
        # 回填历史数据
        backfill_historical_data()
    elif args.daemon:
        # 后台持续运行模式
        print("Signal Statistics Collector 启动")
        print(f"数据库路径: {DB_PATH}")
        print(f"数据目录: {DATA_DIR}")
        print(f"采集间隔: {COLLECT_INTERVAL} 秒")
        
        while True:
            try:
                collect_today_stats()
                next_time = get_beijing_time() + timedelta(seconds=COLLECT_INTERVAL)
                print(f"\n下次采集时间: {next_time.strftime('%H:%M:%S')}")
                print("等待中...")
                time.sleep(COLLECT_INTERVAL)
            except KeyboardInterrupt:
                print("\n收到停止信号，退出...")
                break
            except Exception as e:
                print(f"采集出错: {e}")
                import traceback
                traceback.print_exc()
                print(f"等待 {COLLECT_INTERVAL} 秒后重试...")
                time.sleep(COLLECT_INTERVAL)
    else:
        # 单次运行（手动测试）
        print("单次运行模式 - 采集今天的数据")
        collect_today_stats()
        print("\n提示: 使用 --backfill 回填历史数据，使用 --daemon 持续运行")

if __name__ == '__main__':
    main()
