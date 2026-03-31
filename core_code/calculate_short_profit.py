#!/usr/bin/env python3
"""
计算在A点做空10倍杠杆的收益率
策略：在A点（峰顶）做空，在C点（回调）平仓
"""

import json
import os
from datetime import datetime

def calculate_short_profits():
    """计算所有波峰的做空收益"""
    
    wave_peaks_dir = '/home/user/webapp/data/coin_change_tracker/wave_peaks'
    
    # 读取汇总数据
    with open(f'{wave_peaks_dir}/summary.json', 'r', encoding='utf-8') as f:
        summary = json.load(f)
    
    all_profits = []
    daily_stats = []
    
    print("=" * 80)
    print("📊 A点做空10倍杠杆收益率分析")
    print("=" * 80)
    print("\n策略说明：")
    print("- 入场：A点（峰顶）做空")
    print("- 出场：C点（回调）平仓")
    print("- 杠杆：10倍")
    print("- 收益计算：(A点 - C点) × 10倍杠杆\n")
    print("=" * 80)
    
    # 遍历每一天
    for day_data in summary['daily_data']:
        date = day_data['date']
        
        # 读取详细数据
        file_path = f'{wave_peaks_dir}/wave_peaks_{date}.json'
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        peaks = data.get('peaks', [])
        if not peaks:
            continue
        
        day_profits = []
        
        print(f"\n📅 {date[:4]}-{date[4:6]}-{date[6:8]} | 波峰数: {len(peaks)} | 假突破: {'⚠️ 是' if day_data.get('false_breakout') else '✅ 否'}")
        print("-" * 80)
        
        for i, peak in enumerate(peaks, 1):
            a_value = peak['a_point']['value']
            c_value = peak['c_point']['value']
            
            # 做空收益 = (A点价格 - C点价格) × 10倍杠杆
            # 因为做空，所以A点价格更高时收益更大
            profit = (a_value - c_value) * 10
            
            # 处理时间显示
            if 'beijing_time' in peak['a_point']:
                a_time = peak['a_point']['beijing_time']
            elif isinstance(peak['a_point']['timestamp'], str):
                a_time = peak['a_point']['timestamp'][-8:]
            else:
                a_time = str(peak['a_point']['index'])
            
            if 'beijing_time' in peak['c_point']:
                c_time = peak['c_point']['beijing_time']
            elif isinstance(peak['c_point']['timestamp'], str):
                c_time = peak['c_point']['timestamp'][-8:]
            else:
                c_time = str(peak['c_point']['index'])
            
            amplitude = peak['amplitude']
            decline = peak['decline']
            decline_ratio = peak['decline_ratio']
            
            day_profits.append(profit)
            all_profits.append({
                'date': date,
                'peak': i,
                'profit': profit,
                'a_value': a_value,
                'c_value': c_value,
                'decline': decline
            })
            
            # 显示每个波峰的收益
            profit_emoji = "🟢" if profit > 0 else "🔴"
            print(f"Peak {i:2d} | A点 {a_time} {a_value:7.2f}% → C点 {c_time} {c_value:7.2f}% | "
                  f"下跌 {decline:6.2f}% | {profit_emoji} 收益: {profit:+7.2f}%")
        
        # 每日统计
        if day_profits:
            day_avg = sum(day_profits) / len(day_profits)
            day_total = sum(day_profits)
            day_max = max(day_profits)
            day_min = min(day_profits)
            win_count = sum(1 for p in day_profits if p > 0)
            win_rate = win_count / len(day_profits) * 100
            
            daily_stats.append({
                'date': date,
                'total': day_total,
                'avg': day_avg,
                'max': day_max,
                'min': day_min,
                'count': len(day_profits),
                'win_rate': win_rate,
                'false_breakout': day_data.get('false_breakout')
            })
            
            print(f"\n📊 当日汇总: 总收益 {day_total:+.2f}% | 平均 {day_avg:+.2f}% | "
                  f"最大 {day_max:+.2f}% | 最小 {day_min:+.2f}% | 胜率 {win_rate:.1f}%")
    
    # 整体统计
    print("\n" + "=" * 80)
    print("📈 2月份整体统计（2026-02-01 至 2026-02-18）")
    print("=" * 80)
    
    if all_profits:
        total_profit = sum(p['profit'] for p in all_profits)
        avg_profit = total_profit / len(all_profits)
        max_profit = max(all_profits, key=lambda x: x['profit'])
        min_profit = min(all_profits, key=lambda x: x['profit'])
        win_count = sum(1 for p in all_profits if p['profit'] > 0)
        win_rate = win_count / len(all_profits) * 100
        
        print(f"\n总交易次数: {len(all_profits)} 次")
        print(f"累计收益率: {total_profit:+.2f}%")
        print(f"平均收益率: {avg_profit:+.2f}%")
        print(f"最大单次收益: {max_profit['profit']:+.2f}% (日期: {max_profit['date']}, Peak {max_profit['peak']})")
        print(f"最小单次收益: {min_profit['profit']:+.2f}% (日期: {min_profit['date']}, Peak {min_profit['peak']})")
        print(f"盈利次数: {win_count} / {len(all_profits)}")
        print(f"胜率: {win_rate:.2f}%")
    
    # 假突破期 vs 正常期对比
    print("\n" + "=" * 80)
    print("📊 假突破期 vs 正常期对比")
    print("=" * 80)
    
    false_breakout_stats = [s for s in daily_stats if s['false_breakout']]
    normal_stats = [s for s in daily_stats if not s['false_breakout']]
    
    if false_breakout_stats:
        fb_total = sum(s['total'] for s in false_breakout_stats)
        fb_avg = sum(s['avg'] for s in false_breakout_stats) / len(false_breakout_stats)
        fb_days = len(false_breakout_stats)
        fb_trades = sum(s['count'] for s in false_breakout_stats)
        
        print(f"\n⚠️  假突破期（{fb_days}天）:")
        print(f"   总收益: {fb_total:+.2f}%")
        print(f"   日均收益: {fb_avg:+.2f}%")
        print(f"   交易次数: {fb_trades}次")
    
    if normal_stats:
        normal_total = sum(s['total'] for s in normal_stats)
        normal_avg = sum(s['avg'] for s in normal_stats) / len(normal_stats)
        normal_days = len(normal_stats)
        normal_trades = sum(s['count'] for s in normal_stats)
        
        print(f"\n✅ 正常期（{normal_days}天）:")
        print(f"   总收益: {normal_total:+.2f}%")
        print(f"   日均收益: {normal_avg:+.2f}%")
        print(f"   交易次数: {normal_trades}次")
    
    # 分阶段统计
    print("\n" + "=" * 80)
    print("📊 分阶段收益分析")
    print("=" * 80)
    
    # 前10天 vs 后8天
    first_10_days = [s for s in daily_stats if int(s['date'][6:8]) <= 10]
    last_8_days = [s for s in daily_stats if int(s['date'][6:8]) > 10]
    
    if first_10_days:
        f10_total = sum(s['total'] for s in first_10_days)
        f10_avg = sum(s['avg'] for s in first_10_days) / len(first_10_days)
        print(f"\n📅 前10天（2月1-10日）:")
        print(f"   总收益: {f10_total:+.2f}%")
        print(f"   日均收益: {f10_avg:+.2f}%")
        print(f"   天数: {len(first_10_days)}天")
    
    if last_8_days:
        l8_total = sum(s['total'] for s in last_8_days)
        l8_avg = sum(s['avg'] for s in last_8_days) / len(last_8_days)
        print(f"\n📅 后8天（2月11-18日）:")
        print(f"   总收益: {l8_total:+.2f}%")
        print(f"   日均收益: {l8_avg:+.2f}%")
        print(f"   天数: {len(last_8_days)}天")
    
    # 风险评估
    print("\n" + "=" * 80)
    print("⚠️  风险评估")
    print("=" * 80)
    
    negative_profits = [p for p in all_profits if p['profit'] < 0]
    if negative_profits:
        avg_loss = sum(p['profit'] for p in negative_profits) / len(negative_profits)
        max_loss = min(p['profit'] for p in negative_profits)
        print(f"\n亏损次数: {len(negative_profits)} / {len(all_profits)}")
        print(f"平均亏损: {avg_loss:.2f}%")
        print(f"最大亏损: {max_loss:.2f}%")
        print(f"亏损风险: {'🔴 高' if abs(max_loss) > 50 else '🟡 中' if abs(max_loss) > 30 else '🟢 低'}")
    
    print("\n" + "=" * 80)
    print("💡 策略建议")
    print("=" * 80)
    print("""
1. ✅ 正常期收益稳定，可正常执行A点做空策略
2. ⚠️  假突破期虽然总收益可能更高，但波动大，建议降低仓位
3. 🎯 10倍杠杆下，平均单次收益可观，但需严格止损
4. 📊 胜率高说明A→C回调机制有效，适合做空
5. ⚡ 建议设置止损：A点上方5-10%（即0.5-1%本金损失）
    """)

if __name__ == '__main__':
    calculate_short_profits()

