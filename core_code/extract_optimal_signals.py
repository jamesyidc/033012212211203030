#!/usr/bin/env python3
"""
提取最优交易信号
- 最佳做多：5分钟涨速 >= 15%
- 最佳做空：5分钟涨速 <= -15%
"""

import json
import os
from datetime import datetime, timedelta

# 读取所有数据
data_dir = "data/coin_change_tracker"
results = {
    "best_long_signals": [],  # 最佳做多信号
    "best_short_signals": [], # 最佳做空信号
    "statistics": {}
}

# 遍历所有日期的数据
for filename in sorted(os.listdir(data_dir)):
    if not filename.startswith("velocity_") or not filename.endswith(".jsonl"):
        continue
    
    date_str = filename.replace("velocity_", "").replace(".jsonl", "")
    velocity_file = os.path.join(data_dir, filename)
    coin_change_file = os.path.join(data_dir, f"coin_change_{date_str}.jsonl")
    
    if not os.path.exists(coin_change_file):
        continue
    
    print(f"处理日期: {date_str}")
    
    # 读取velocity数据
    with open(velocity_file, 'r', encoding='utf-8') as f:
        velocity_data = [json.loads(line) for line in f]
    
    # 读取coin_change数据
    try:
        with open(coin_change_file, 'r', encoding='utf-8') as f:
            coin_change_data = [json.loads(line) for line in f if line.strip()]
    except Exception as e:
        print(f"  错误：无法读取 {coin_change_file}: {e}")
        continue
    
    # 创建时间戳到coin_change的映射（跳过没有timestamp的数据）
    coin_change_map = {}
    for d in coin_change_data:
        if 'timestamp' in d:
            coin_change_map[d['timestamp']] = d
    
    # 遍历velocity数据，查找信号
    for i, vel_point in enumerate(velocity_data):
        velocity_5min = vel_point.get('velocity_5min', 0)
        timestamp = vel_point.get('timestamp', 0)
        # 确保timestamp是数字类型
        if isinstance(timestamp, str):
            try:
                timestamp = int(timestamp)
            except:
                continue
        beijing_time = vel_point.get('beijing_time', '')
        
        # 查找对应的coin_change数据
        coin_data = coin_change_map.get(timestamp)
        if not coin_data:
            # 尝试查找最接近的时间点
            min_diff = float('inf')
            closest = None
            for cc in coin_change_data:
                diff = abs(cc['timestamp'] - timestamp)
                if diff < min_diff:
                    min_diff = diff
                    closest = cc
            
            if min_diff < 10000:  # 10秒内
                coin_data = closest
        
        if not coin_data:
            continue
        
        current_total_change = vel_point.get('current_total_change', 0)
        up_ratio = coin_data.get('up_ratio', 0)
        
        # 最佳做多信号：5分钟涨速 >= 15%
        if velocity_5min >= 15:
            # 计算2小时后的收益
            entry_value = current_total_change
            future_value = None
            
            # 查找2小时后的数据
            for j in range(i+1, len(velocity_data)):
                future_point = velocity_data[j]
                future_timestamp = future_point.get('timestamp', 0)
                # 确保future_timestamp是数字类型
                if isinstance(future_timestamp, str):
                    try:
                        future_timestamp = int(future_timestamp)
                    except:
                        continue
                
                # 2小时 = 7200秒 = 7200000毫秒
                if future_timestamp - timestamp >= 7200000:
                    future_value = future_point.get('current_total_change', 0)
                    future_beijing_time = future_point.get('beijing_time', '')
                    break
            
            if future_value is not None:
                profit_pct = future_value - entry_value
                
                results["best_long_signals"].append({
                    "date": date_str,
                    "beijing_time": beijing_time,
                    "timestamp": timestamp,
                    "entry_total_change": round(entry_value, 2),
                    "velocity_5min": round(velocity_5min, 2),
                    "up_ratio": round(up_ratio, 2),
                    "exit_total_change_2h": round(future_value, 2),
                    "profit_2h_pct": round(profit_pct, 2),
                    "signal_type": "最佳做多（涨速≥15%）",
                    "win": profit_pct > 0
                })
        
        # 最佳做空信号：5分钟涨速 <= -15%
        if velocity_5min <= -15:
            # 计算2小时后的收益（做空）
            entry_value = current_total_change
            future_value = None
            
            # 查找2小时后的数据
            for j in range(i+1, len(velocity_data)):
                future_point = velocity_data[j]
                future_timestamp = future_point.get('timestamp', 0)
                # 确保future_timestamp是数字类型
                if isinstance(future_timestamp, str):
                    try:
                        future_timestamp = int(future_timestamp)
                    except:
                        continue
                
                # 2小时 = 7200秒 = 7200000毫秒
                if future_timestamp - timestamp >= 7200000:
                    future_value = future_point.get('current_total_change', 0)
                    future_beijing_time = future_point.get('beijing_time', '')
                    break
            
            if future_value is not None:
                # 做空收益 = -(未来值 - 入场值) = 入场值 - 未来值
                profit_pct = entry_value - future_value
                
                results["best_short_signals"].append({
                    "date": date_str,
                    "beijing_time": beijing_time,
                    "timestamp": timestamp,
                    "entry_total_change": round(entry_value, 2),
                    "velocity_5min": round(velocity_5min, 2),
                    "up_ratio": round(up_ratio, 2),
                    "exit_total_change_2h": round(future_value, 2),
                    "profit_2h_pct": round(profit_pct, 2),
                    "signal_type": "最佳做空（涨速≤-15%）",
                    "win": profit_pct > 0
                })

print(f"\n找到 {len(results['best_long_signals'])} 个最佳做多信号")
print(f"找到 {len(results['best_short_signals'])} 个最佳做空信号")

# 计算统计数据
if results['best_long_signals']:
    long_profits = [s['profit_2h_pct'] for s in results['best_long_signals']]
    long_wins = sum(1 for s in results['best_long_signals'] if s['win'])
    long_win_rate = long_wins / len(results['best_long_signals']) * 100
    long_avg_profit = sum(long_profits) / len(long_profits)
    
    results['statistics']['long'] = {
        "total_signals": len(results['best_long_signals']),
        "wins": long_wins,
        "losses": len(results['best_long_signals']) - long_wins,
        "win_rate": round(long_win_rate, 2),
        "avg_profit": round(long_avg_profit, 2),
        "max_profit": round(max(long_profits), 2),
        "min_profit": round(min(long_profits), 2)
    }
    
    print(f"\n✅ 最佳做多信号统计：")
    print(f"  - 信号数量：{len(results['best_long_signals'])}")
    print(f"  - 盈利次数：{long_wins}")
    print(f"  - 亏损次数：{len(results['best_long_signals']) - long_wins}")
    print(f"  - 胜率：{long_win_rate:.2f}%")
    print(f"  - 平均收益：{long_avg_profit:.2f}%")
    print(f"  - 最大盈利：{max(long_profits):.2f}%")
    print(f"  - 最大亏损：{min(long_profits):.2f}%")

if results['best_short_signals']:
    short_profits = [s['profit_2h_pct'] for s in results['best_short_signals']]
    short_wins = sum(1 for s in results['best_short_signals'] if s['win'])
    short_win_rate = short_wins / len(results['best_short_signals']) * 100
    short_avg_profit = sum(short_profits) / len(short_profits)
    
    results['statistics']['short'] = {
        "total_signals": len(results['best_short_signals']),
        "wins": short_wins,
        "losses": len(results['best_short_signals']) - short_wins,
        "win_rate": round(short_win_rate, 2),
        "avg_profit": round(short_avg_profit, 2),
        "max_profit": round(max(short_profits), 2),
        "min_profit": round(min(short_profits), 2)
    }
    
    print(f"\n✅ 最佳做空信号统计：")
    print(f"  - 信号数量：{len(results['best_short_signals'])}")
    print(f"  - 盈利次数：{short_wins}")
    print(f"  - 亏损次数：{len(results['best_short_signals']) - short_wins}")
    print(f"  - 胜率：{short_win_rate:.2f}%")
    print(f"  - 平均收益：{short_avg_profit:.2f}%")
    print(f"  - 最大盈利：{max(short_profits):.2f}%")
    print(f"  - 最大亏损：{min(short_profits):.2f}%")

# 保存结果
output_file = "OPTIMAL_TRADING_SIGNALS.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n✅ 结果已保存到：{output_file}")

# 显示前几个信号示例
if results['best_long_signals']:
    print(f"\n📈 最佳做多信号示例（前5个）：")
    for i, signal in enumerate(results['best_long_signals'][:5], 1):
        print(f"  {i}. {signal['date']} {signal['beijing_time']}")
        print(f"     入场：{signal['entry_total_change']}%, 涨速：{signal['velocity_5min']}%")
        print(f"     2h后：{signal['exit_total_change_2h']}%, 收益：{signal['profit_2h_pct']}%")

if results['best_short_signals']:
    print(f"\n📉 最佳做空信号示例（前5个）：")
    for i, signal in enumerate(results['best_short_signals'][:5], 1):
        print(f"  {i}. {signal['date']} {signal['beijing_time']}")
        print(f"     入场：{signal['entry_total_change']}%, 涨速：{signal['velocity_5min']}%")
        print(f"     2h后：{signal['exit_total_change_2h']}%, 收益：{signal['profit_2h_pct']}%")
