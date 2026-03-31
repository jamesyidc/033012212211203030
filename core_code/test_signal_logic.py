#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试币种涨跌预判逻辑修改"""

import sys
sys.path.insert(0, '/home/user/webapp')

from monitors.coin_change_prediction_monitor import determine_market_signal

# 测试场景
test_cases = [
    {
        "name": "情况3: 纯红色 → 做空",
        "color_counts": {
            "green": 0,
            "red": 12,
            "yellow": 0,
            "blank": 0,
            "blank_ratio": 0
        },
        "expected_signal": "做空"
    },
    {
        "name": "情况3: 红色+空白占比<25% → 做空（已修改）",
        "color_counts": {
            "green": 0,
            "red": 10,
            "yellow": 0,
            "blank": 2,
            "blank_ratio": 16.67  # 2/12 * 100 = 16.67%
        },
        "expected_signal": "做空"
    },
    {
        "name": "情况3: 红色+空白占比>=25% → 做空",
        "color_counts": {
            "green": 0,
            "red": 8,
            "yellow": 0,
            "blank": 4,
            "blank_ratio": 33.33  # 4/12 * 100 = 33.33%
        },
        "expected_signal": "做空"
    },
    {
        "name": "情况4: 全部绿色 → 诱多不参与",
        "color_counts": {
            "green": 12,
            "red": 0,
            "yellow": 0,
            "blank": 0,
            "blank_ratio": 0
        },
        "expected_signal": "诱多不参与"
    },
    {
        "name": "情况5: 全部空白 → 空头强控盘",
        "color_counts": {
            "green": 0,
            "red": 0,
            "yellow": 0,
            "blank": 12,
            "blank_ratio": 100
        },
        "expected_signal": "空头强控盘"
    },
    {
        "name": "情况1: 有绿+有红+无黄 → 低吸",
        "color_counts": {
            "green": 6,
            "red": 6,
            "yellow": 0,
            "blank": 0,
            "blank_ratio": 0
        },
        "expected_signal": "低吸"
    },
    {
        "name": "情况2: 有绿+有红+有黄 → 等待新低",
        "color_counts": {
            "green": 4,
            "red": 4,
            "yellow": 4,
            "blank": 0,
            "blank_ratio": 0
        },
        "expected_signal": "等待新低"
    }
]

print("="*60)
print("测试币种涨跌预判逻辑修改")
print("="*60)

passed = 0
failed = 0

for i, test_case in enumerate(test_cases, 1):
    print(f"\n测试 {i}: {test_case['name']}")
    print(f"输入: {test_case['color_counts']}")
    
    signal, description = determine_market_signal(test_case['color_counts'])
    
    print(f"预期信号: {test_case['expected_signal']}")
    print(f"实际信号: {signal}")
    print(f"描述: {description}")
    
    if signal == test_case['expected_signal']:
        print("✅ 通过")
        passed += 1
    else:
        print("❌ 失败")
        failed += 1

print("\n" + "="*60)
print(f"测试结果: 通过 {passed}/{len(test_cases)}, 失败 {failed}/{len(test_cases)}")
print("="*60)
