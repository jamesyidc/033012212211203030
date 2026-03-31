#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新增的低吸判断逻辑（情况1c）
"""

import sys
sys.path.insert(0, '/home/user/webapp')

from monitors.coin_change_prediction_monitor import determine_market_signal

def test_case(name, color_counts, expected_signal):
    """测试单个案例"""
    signal, description = determine_market_signal(color_counts)
    status = "✅" if signal == expected_signal else "❌"
    print(f"{status} {name}")
    print(f"   输入: 绿{color_counts['green']} 红{color_counts['red']} 黄{color_counts['yellow']} 空白{color_counts.get('blank', 0)}")
    print(f"   预期: {expected_signal}")
    print(f"   实际: {signal}")
    print(f"   描述: {description}")
    print()
    return signal == expected_signal

if __name__ == "__main__":
    print("🧪 测试新增的低吸判断逻辑（情况1c）\n")
    print("=" * 80)
    print()
    
    all_pass = True
    
    # 测试情况1c：绿色>=3根 + 有红色
    print("📊 测试组1：绿色>=3根 + 有红色 → 应该判断为【低吸】")
    print("-" * 80)
    all_pass &= test_case(
        "Case 1.1: 绿3红1黄0",
        {'green': 3, 'red': 1, 'yellow': 0, 'blank': 0},
        "低吸"
    )
    all_pass &= test_case(
        "Case 1.2: 绿4红2黄0",
        {'green': 4, 'red': 2, 'yellow': 0, 'blank': 0},
        "低吸"
    )
    all_pass &= test_case(
        "Case 1.3: 绿5红1黄0",
        {'green': 5, 'red': 1, 'yellow': 0, 'blank': 0},
        "低吸"
    )
    
    # 测试情况1c：绿色>=3根 + 有空白
    print("📊 测试组2：绿色>=3根 + 有空白 → 应该判断为【低吸】")
    print("-" * 80)
    all_pass &= test_case(
        "Case 2.1: 绿3空白1红0",
        {'green': 3, 'red': 0, 'yellow': 0, 'blank': 1, 'blank_ratio': 8.3},
        "低吸"
    )
    all_pass &= test_case(
        "Case 2.2: 绿4空白2红0",
        {'green': 4, 'red': 0, 'yellow': 0, 'blank': 2, 'blank_ratio': 16.7},
        "低吸"
    )
    
    # 测试情况1c：绿色>=3根 + 红色 + 空白
    print("📊 测试组3：绿色>=3根 + 红色 + 空白 → 应该判断为【低吸】")
    print("-" * 80)
    all_pass &= test_case(
        "Case 3.1: 绿3红1空白1",
        {'green': 3, 'red': 1, 'yellow': 0, 'blank': 1, 'blank_ratio': 8.3},
        "低吸"
    )
    all_pass &= test_case(
        "Case 3.2: 绿4红1空白2",
        {'green': 4, 'red': 1, 'yellow': 0, 'blank': 2, 'blank_ratio': 16.7},
        "低吸"
    )
    
    # 测试情况1c：绿色>=3根 + 黄色（无红色）
    print("📊 测试组4：绿色>=3根 + 黄色（无红色）→ 应该判断为【低吸】")
    print("-" * 80)
    all_pass &= test_case(
        "Case 4.1: 绿3黄1红0",
        {'green': 3, 'red': 0, 'yellow': 1, 'blank': 0},
        "低吸"
    )
    all_pass &= test_case(
        "Case 4.2: 绿4黄2红0",
        {'green': 4, 'red': 0, 'yellow': 2, 'blank': 0},
        "低吸"
    )
    
    # 测试边界情况：绿色<3根
    print("📊 测试组5：绿色<3根 → 应该判断为【观望】或其他")
    print("-" * 80)
    all_pass &= test_case(
        "Case 5.1: 绿2红1黄0（绿色不足3根）",
        {'green': 2, 'red': 1, 'yellow': 0, 'blank': 0},
        "低吸"  # 仍然符合情况1：有绿有红无黄
    )
    all_pass &= test_case(
        "Case 5.2: 绿2黄1红0（绿色不足3根，无红色）",
        {'green': 2, 'red': 0, 'yellow': 1, 'blank': 0},
        "观望"  # 不符合情况1c（绿色<3），也不符合其他低吸条件
    )
    
    # 测试原有逻辑不受影响
    print("📊 测试组6：原有逻辑不受影响")
    print("-" * 80)
    all_pass &= test_case(
        "Case 6.1: 全绿色 → 诱多不参与",
        {'green': 12, 'red': 0, 'yellow': 0, 'blank': 0},
        "诱多不参与"
    )
    all_pass &= test_case(
        "Case 6.2: 全红色 → 做空",
        {'green': 0, 'red': 12, 'yellow': 0, 'blank': 0},
        "做空"
    )
    all_pass &= test_case(
        "Case 6.3: 绿+红+黄(黄>=2) → 等待新低",
        {'green': 3, 'red': 3, 'yellow': 2, 'blank': 0},
        "等待新低"
    )
    
    print("=" * 80)
    if all_pass:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败！")
    
    print()
    print("📝 新增逻辑总结：")
    print("   情况1c: 绿色>=3根 + (有红色 或 有空白) → 低吸")
    print("   适用场景: 绿色柱子足够多(>=3根)，且有红色或空白柱子存在")
