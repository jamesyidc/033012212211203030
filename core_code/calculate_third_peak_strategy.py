#!/usr/bin/env python3
"""
第三个波峰A点做空策略收益计算
策略：
1. 第3个波峰A点：开20%仓位做空（10倍杠杆）
2. 确认假突破（第3个A点未超过第1个A点）：追加20%仓位做空
3. 在对应的C点平仓
"""

import json
import os

def calculate_third_peak_strategy():
    """计算第三个波峰做空策略收益"""
    
    wave_peaks_dir = '/home/user/webapp/data/coin_change_tracker/wave_peaks'
    
    # 读取汇总数据
    with open(f'{wave_peaks_dir}/summary.json', 'r', encoding='utf-8') as f:
        summary = json.load(f)
    
    print("=" * 120)
    print("📊 第三个波峰A点做空策略收益分析（分批建仓）")
    print("=" * 120)
    print("\n策略说明：")
    print("1️⃣  第3个波峰A点：开20%仓位做空（10倍杠杆）")
    print("2️⃣  确认假突破（第3个A点未超过第1个A点）：追加20%仓位做空（10倍杠杆）")
    print("3️⃣  在第3个波峰的C点统一平仓")
    print("4️⃣  本金：10,000 USDT\n")
    print("=" * 120)
    
    all_trades = []
    total_capital = 10000  # 本金 10,000 USDT
    
    for day_data in summary['daily_data']:
        date = day_data['date']
        
        # 读取详细数据
        file_path = f'{wave_peaks_dir}/wave_peaks_{date}.json'
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        peaks = data.get('peaks', [])
        if len(peaks) < 3:  # 至少需要3个波峰
            continue
        
        false_breakout = data.get('false_breakout')
        
        # 获取第1、2、3个波峰
        peak1 = peaks[0]
        peak2 = peaks[1]
        peak3 = peaks[2]
        
        a1_value = peak1['a_point']['value']
        a2_value = peak2['a_point']['value']
        a3_value = peak3['a_point']['value']
        c3_value = peak3['c_point']['value']
        
        # 判断是否假突破（第3个A点没有超过第1个A点）
        is_false_breakout = (a3_value <= a1_value)
        
        # 第一次开仓：第3个波峰A点，20%仓位
        position1_capital = total_capital * 0.20  # 2,000 USDT
        position1_profit_pct = (a3_value - c3_value) * 10  # 10倍杠杆
        position1_profit = position1_capital * (position1_profit_pct / 100)
        
        # 第二次加仓：确认假突破后，追加20%仓位
        if is_false_breakout:
            position2_capital = total_capital * 0.20  # 2,000 USDT
            position2_profit_pct = (a3_value - c3_value) * 10  # 10倍杠杆（从A3到C3）
            position2_profit = position2_capital * (position2_profit_pct / 100)
        else:
            position2_capital = 0
            position2_profit_pct = 0
            position2_profit = 0
        
        # 总收益
        total_profit = position1_profit + position2_profit
        total_profit_pct = (total_profit / total_capital) * 100
        
        # 处理时间
        if 'beijing_time' in peak3['a_point']:
            a3_time = peak3['a_point']['beijing_time']
        elif isinstance(peak3['a_point']['timestamp'], str):
            a3_time = peak3['a_point']['timestamp']
        else:
            a3_time = f"Index {peak3['a_point']['index']}"
        
        if 'beijing_time' in peak3['c_point']:
            c3_time = peak3['c_point']['beijing_time']
        elif isinstance(peak3['c_point']['timestamp'], str):
            c3_time = peak3['c_point']['timestamp']
        else:
            c3_time = f"Index {peak3['c_point']['index']}"
        
        all_trades.append({
            'date': date,
            'a1': a1_value,
            'a2': a2_value,
            'a3': a3_value,
            'c3': c3_value,
            'false_breakout': is_false_breakout,
            'position1_profit': position1_profit,
            'position2_profit': position2_profit,
            'total_profit': total_profit,
            'total_profit_pct': total_profit_pct,
            'a3_time': a3_time,
            'c3_time': c3_time,
            'decline': peak3['decline']
        })
        
        # 打印每日详情
        print(f"\n📅 {date[:4]}-{date[4:6]}-{date[6:8]} {'🚨 假突破' if false_breakout else '✅ 正常'}")
        print("-" * 120)
        print(f"第1个波峰A点: {a1_value:>8.2f}%")
        print(f"第2个波峰A点: {a2_value:>8.2f}%")
        print(f"第3个波峰A点: {a3_value:>8.2f}%  (A3 {'≤' if is_false_breakout else '>'} A1 → {'假突破 ⚠️' if is_false_breakout else '正常突破 ✅'})")
        print(f"第3个波峰C点: {c3_value:>8.2f}%")
        print(f"下跌幅度: {peak3['decline']:>8.2f}%")
        print()
        print(f"仓位1️⃣  (第3个A点开仓):")
        print(f"  - 仓位: 20% × 10,000 = 2,000 USDT")
        print(f"  - 收益率: {position1_profit_pct:>8.2f}%")
        print(f"  - 收益额: {position1_profit:>+10.2f} USDT")
        
        if is_false_breakout:
            print(f"仓位2️⃣  (确认假突破加仓):")
            print(f"  - 仓位: 20% × 10,000 = 2,000 USDT")
            print(f"  - 收益率: {position2_profit_pct:>8.2f}%")
            print(f"  - 收益额: {position2_profit:>+10.2f} USDT")
        else:
            print(f"仓位2️⃣  (未确认假突破，不加仓)")
        
        print()
        print(f"💰 当日总收益: {total_profit:>+10.2f} USDT ({total_profit_pct:>+8.2f}%)")
        print(f"📈 累计资产: {total_capital + total_profit:>10.2f} USDT")
    
    # 整体统计
    print("\n" + "=" * 120)
    print("📈 整体统计汇总")
    print("=" * 120)
    
    if all_trades:
        # 总收益
        total_all_profit = sum(t['total_profit'] for t in all_trades)
        total_all_profit_pct = (total_all_profit / total_capital) * 100
        
        # 假突破天数
        false_breakout_days = sum(1 for t in all_trades if t['false_breakout'])
        normal_days = len(all_trades) - false_breakout_days
        
        # 假突破期收益
        false_breakout_profit = sum(t['total_profit'] for t in all_trades if t['false_breakout'])
        normal_profit = sum(t['total_profit'] for t in all_trades if not t['false_breakout'])
        
        # 平均收益
        avg_profit = total_all_profit / len(all_trades)
        avg_profit_pct = total_all_profit_pct / len(all_trades)
        
        # 最大/最小收益
        max_trade = max(all_trades, key=lambda x: x['total_profit'])
        min_trade = min(all_trades, key=lambda x: x['total_profit'])
        
        print(f"\n✅ 基本信息:")
        print(f"   本金: {total_capital:,.0f} USDT")
        print(f"   交易天数: {len(all_trades)}天")
        print(f"   假突破天数: {false_breakout_days}天")
        print(f"   正常天数: {normal_days}天")
        
        print(f"\n💰 收益情况:")
        print(f"   累计总收益: {total_all_profit:>+,.2f} USDT ({total_all_profit_pct:>+.2f}%)")
        print(f"   日均收益: {avg_profit:>+,.2f} USDT ({avg_profit_pct:>+.2f}%)")
        print(f"   最终资产: {total_capital + total_all_profit:>,.2f} USDT")
        print(f"   资产倍数: {(total_capital + total_all_profit) / total_capital:.2f}x")
        
        print(f"\n📊 假突破 vs 正常期:")
        print(f"   假突破期总收益: {false_breakout_profit:>+,.2f} USDT")
        print(f"   正常期总收益: {normal_profit:>+,.2f} USDT")
        if false_breakout_days > 0:
            print(f"   假突破期日均: {false_breakout_profit/false_breakout_days:>+,.2f} USDT")
        if normal_days > 0:
            print(f"   正常期日均: {normal_profit/normal_days:>+,.2f} USDT")
        
        print(f"\n📈 极值:")
        print(f"   最大单日收益: {max_trade['total_profit']:>+,.2f} USDT ({max_trade['total_profit_pct']:>+.2f}%)")
        print(f"   └─ 日期: {max_trade['date']}, A3: {max_trade['a3']:.2f}% → C3: {max_trade['c3']:.2f}%")
        print(f"   最小单日收益: {min_trade['total_profit']:>+,.2f} USDT ({min_trade['total_profit_pct']:>+.2f}%)")
        print(f"   └─ 日期: {min_trade['date']}, A3: {min_trade['a3']:.2f}% → C3: {min_trade['c3']:.2f}%")
        
        # 胜率
        win_count = sum(1 for t in all_trades if t['total_profit'] > 0)
        win_rate = (win_count / len(all_trades)) * 100
        print(f"\n🎯 胜率:")
        print(f"   盈利天数: {win_count} / {len(all_trades)}")
        print(f"   胜率: {win_rate:.2f}%")
    
    # 策略对比
    print("\n" + "=" * 120)
    print("📊 策略对比分析")
    print("=" * 120)
    
    # 计算单仓策略（只在第3个A点开20%）
    single_position_profit = sum(t['position1_profit'] for t in all_trades)
    single_position_pct = (single_position_profit / total_capital) * 100
    
    # 计算双仓策略（假突破期40%，正常期20%）
    double_position_profit = total_all_profit
    double_position_pct = total_all_profit_pct
    
    print(f"\n策略A: 单仓策略（第3个A点开20%，不加仓）")
    print(f"   总收益: {single_position_profit:>+,.2f} USDT ({single_position_pct:>+.2f}%)")
    print(f"   最终资产: {total_capital + single_position_profit:>,.2f} USDT")
    print(f"   资产倍数: {(total_capital + single_position_profit) / total_capital:.2f}x")
    
    print(f"\n策略B: 双仓策略（第3个A点20%，假突破确认加20%）✅ 当前策略")
    print(f"   总收益: {double_position_profit:>+,.2f} USDT ({double_position_pct:>+.2f}%)")
    print(f"   最终资产: {total_capital + double_position_profit:>,.2f} USDT")
    print(f"   资产倍数: {(total_capital + double_position_profit) / total_capital:.2f}x")
    
    print(f"\n💡 策略对比:")
    profit_increase = double_position_profit - single_position_profit
    profit_increase_pct = ((double_position_profit / single_position_profit) - 1) * 100 if single_position_profit > 0 else 0
    print(f"   双仓比单仓多赚: {profit_increase:>+,.2f} USDT")
    print(f"   收益提升: {profit_increase_pct:>+.2f}%")
    
    # 实战建议
    print("\n" + "=" * 120)
    print("💡 实战建议")
    print("=" * 120)
    print("""
✅ 优势:
1. 分批建仓降低风险：第3个A点先开20%仓位试探
2. 假突破期额外收益：确认假突破后再加20%，提高假突破期收益
3. 风险可控：最大仓位40%（假突破期），正常期仅20%
4. 灵活应对：根据市场状态动态调整仓位

⚠️  风险:
1. 第3个波峰可能不是最优做空点（有可能第4、5个更高）
2. 需要准确判断假突破（系统自动检测）
3. 加仓时机需要快速决策（假突破确认后立即执行）

🎯 执行要点:
1. 第3个A点确认后立即开20%仓位做空（10倍杠杆）
2. 观察后续A点，若第3个A点未超过第1个A点 → 确认假突破 → 立即加20%仓位
3. 在第3个C点统一平仓（不管有没有加仓）
4. 止损：A3点上方5%（本金损失0.5-1%）
5. 严格风控：日最大回撤10%必须停止交易
    """)

if __name__ == '__main__':
    calculate_third_peak_strategy()

