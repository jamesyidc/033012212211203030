#!/usr/bin/env python3
"""测试筑底信号检测"""

def determine_bar_color(up_ratio):
    """判断柱子颜色"""
    if up_ratio == 0:
        return 'blank'
    elif up_ratio > 55:
        return 'green'
    elif 45 <= up_ratio <= 55:
        return 'yellow'
    else:  # up_ratio < 45
        return 'red'

# 根据截图，10:50前后的数据
test_cases = [
    {'time': '10:40', 'up_ratio': 51.90, 'change': 6.45},
    {'time': '10:50', 'up_ratio': 59.30, 'change': 14.72},
]

print("=" * 60)
print("筑底信号检测分析")
print("=" * 60)
print()

print("📊 数据分析:")
for case in test_cases:
    color = determine_bar_color(case['up_ratio'])
    color_map = {
        'green': '🟢 绿色',
        'yellow': '🟡 黄色',
        'red': '🔴 红色',
        'blank': '⚪ 空白'
    }
    print(f"  {case['time']}: 上涨占比 {case['up_ratio']:.2f}% → {color_map.get(color, color)}")

print()
print("⚠️ 问题分析:")
print("  - 用户截图显示: '黄色 绿色 黄色' 应该触发筑底信号")
print("  - 实际数据10:50: 59.30% > 55% → 绿色")
print("  - 筑底信号触发条件: 最后一根黄色柱的up_ratio < 10%")
print("  - 10:50的up_ratio = 59.30% >> 10%，不符合触发条件")
print()

print("💡 可能的原因:")
print("  1. 截图可能显示的是其他时间段的数据")
print("  2. 前端颜色阈值可能与后端不一致")
print("  3. 筑底信号的触发条件可能需要调整")
print()

print("🔧 建议修改:")
print("  方案1: 调整筑底信号触发条件")
print("    - 当前: 最后一根黄色柱 up_ratio < 10%")
print("    - 建议: 去掉这个限制，只要是黄→绿→黄模式就触发")
print()
print("  方案2: 调整颜色判断阈值")
print("    - 当前黄色: 45% ≤ up_ratio ≤ 55%")
print("    - 可考虑扩大黄色范围")
print()

print("=" * 60)
