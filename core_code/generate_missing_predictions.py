#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为缺失日期生成预测数据
基于历史币变化数据重新计算0-2点的预判
"""

import sys
import os
sys.path.insert(0, '/home/user/webapp')

from monitors.coin_change_prediction_monitor import (
    fetch_coin_change_history,
    analyze_bar_colors,
    determine_market_signal,
    save_prediction_data
)
from datetime import datetime, timedelta
from pathlib import Path

# 数据目录
prediction_dir = Path("/home/user/webapp/data/daily_predictions")

# 2月份所有日期（1-28日）
all_dates_feb = [f"2026-02-{str(day).zfill(2)}" for day in range(1, 29)]

# 已有预测的日期
existing_jsonl = list(prediction_dir.glob("prediction_202602*.jsonl"))
existing_dates = set()
for f in existing_jsonl:
    date_str = f.stem.replace("prediction_", "")  # 20260202
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    existing_dates.add(date_obj.strftime("%Y-%m-%d"))  # 2026-02-02

# 找出缺失的日期
missing_dates = []
for date_str in all_dates_feb:
    if date_str not in existing_dates:
        # 检查是否有币变化数据
        date_short = date_str.replace("-", "")  # 20260201
        coin_change_file = Path(f"/home/user/webapp/data/coin_change_tracker/coin_change_{date_short}.jsonl")
        if coin_change_file.exists():
            missing_dates.append(date_str)

print("=" * 80)
print("补全缺失日期的预测数据")
print("=" * 80)
print(f"📅 2月份总天数: {len(all_dates_feb)}")
print(f"✅ 已有预测: {len(existing_dates)} 天")
print(f"❌ 缺失预测: {len(missing_dates)} 天")
print()

if not missing_dates:
    print("🎉 所有日期的预测数据都已存在！")
else:
    print(f"🔍 需要补全的日期: {', '.join(missing_dates)}")
    print()
    
    success_count = 0
    fail_count = 0
    
    for date_str in missing_dates:
        try:
            print(f"\n📊 处理日期: {date_str}")
            print("-" * 60)
            
            # 获取该日期的0-2点历史数据
            data = fetch_coin_change_history(date_str)
            
            if not data or not data.get('records'):
                print(f"  ⚠️  该日期没有0-2点数据，跳过")
                fail_count += 1
                continue
            
            print(f"  📈 获取到 {len(data['records'])} 条记录")
            
            # 分析柱状图颜色
            color_counts = analyze_bar_colors(data)
            
            if not color_counts:
                print(f"  ❌ 颜色分析失败")
                fail_count += 1
                continue
            
            print(f"  🟢 绿色: {color_counts['green']}, "
                  f"🔴 红色: {color_counts['red']}, "
                  f"🟡 黄色: {color_counts['yellow']}, "
                  f"⚪ 空白: {color_counts.get('blank', 0)}")
            
            # 判断市场信号
            signal, description = determine_market_signal(color_counts)
            
            print(f"  🎯 信号: {signal}")
            print(f"  📝 描述: {description}")
            
            # 手动构造数据并保存
            # 使用该日期的2:00作为时间戳
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            timestamp = date_obj.replace(hour=2, minute=0, second=0)
            
            import json
            from datetime import timezone
            
            # 构造预测数据
            prediction_data = {
                "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                "date": date_str,
                "analysis_time": "02:00:00",
                "color_counts": color_counts,
                "signal": signal,
                "description": description,
                "is_temp": False,  # 标记为最终预判
                "is_final": True,
                "regenerated": True  # 标记为重新生成的数据
            }
            
            # 保存到JSONL文件
            date_short = date_str.replace("-", "")  # 20260201
            jsonl_file = prediction_dir / f"prediction_{date_short}.jsonl"
            
            with open(jsonl_file, 'w', encoding='utf-8') as f:
                json.dump(prediction_data, f, ensure_ascii=False)
                f.write('\n')
            
            print(f"  ✅ 已保存到: {jsonl_file.name}")
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
            fail_count += 1
    
    print()
    print("=" * 80)
    print("补全完成")
    print("=" * 80)
    print(f"✅ 成功: {success_count} 天")
    print(f"❌ 失败: {fail_count} 天")

print()
print("📋 最终统计:")
final_jsonl = list(prediction_dir.glob("prediction_202602*.jsonl"))
print(f"  2月份预测数据文件总数: {len(final_jsonl)}")
print()

# 列出所有文件
print("📂 文件列表:")
for f in sorted(final_jsonl):
    date_str = f.stem.replace("prediction_", "")
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    size = f.stat().st_size
    print(f"  {date_obj.strftime('%Y-%m-%d')} ({f.name}): {size} bytes")

print()
print("=" * 80)
