#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试0-2点行情预判逻辑
展示新旧逻辑的对比
"""

def test_scenario(green, red, yellow, scenario_name):
    """测试一个场景"""
    print(f"\n{'='*60}")
    print(f"📊 {scenario_name}")
    print(f"   颜色分布: 绿{green}根 红{red}根 黄{yellow}根")
    print(f"   红+黄: {red + yellow}根")
    
    # 新逻辑判断
    if green > 0 and red > 0 and yellow > 0 and (red + yellow) >= 3:
        signal = "等待新低"
        operation = "高点做空"
        reason = f"有绿有红有黄，红色+黄色共{red + yellow}根(>=3根)"
    elif green > 0 and red > 0 and (yellow == 0 or (red + yellow) < 3):
        signal = "低吸"
        operation = "低点做多"
        if yellow == 0:
            reason = "有绿有红无黄"
        else:
            reason = f"有绿有红有黄，但红色+黄色共{red + yellow}根(<3根)"
    elif green > 0 and yellow >= 3 and red == 0:
        signal = "等待新低"
        operation = "高点做空"
        reason = f"只有绿色和黄色（黄色{yellow}根>=3根）"
    elif green > 0 and yellow > 0 and yellow < 3 and red == 0:
        signal = "观望"
        operation = "观望"
        reason = f"只有绿色和黄色（黄色{yellow}根<3根），信号不明确"
    else:
        signal = "其他"
        operation = "见具体规则"
        reason = "不属于情况1或情况2"
    
    print(f"\n   ✅ 新逻辑判断:")
    print(f"      信号: {signal}")
    print(f"      操作: {operation}")
    print(f"      理由: {reason}")

def main():
    print("="*60)
    print("🧪 0-2点行情预判逻辑测试")
    print("="*60)
    
    # 测试情况2: 等待新低（红+黄>=3根）
    print("\n【情况2：等待新低】")
    test_scenario(4, 7, 1, "2026-02-06实例")
    test_scenario(1, 8, 1, "2026-02-09实例")
    test_scenario(7, 3, 1, "2026-02-18实例")
    test_scenario(3, 7, 2, "2026-02-21实例")
    test_scenario(5, 4, 3, "边界测试: 红+黄=7根")
    
    # 测试情况1: 低吸（无黄或红+黄<3根）
    print("\n【情况1：低吸】")
    test_scenario(8, 4, 0, "2026-02-10实例（无黄）")
    test_scenario(9, 3, 0, "2026-02-12实例（无黄）")
    test_scenario(10, 1, 1, "2026-02-25实例（红+黄=2根）")
    test_scenario(6, 1, 1, "边界测试: 红+黄=2根")
    
    # 测试情况2特殊: 只有绿+黄
    print("\n【情况2特殊：只有绿+黄】")
    test_scenario(8, 0, 4, "黄色4根（>=3根）→ 等待新低")
    test_scenario(10, 0, 2, "黄色2根（<3根）→ 观望")
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60)

if __name__ == "__main__":
    main()
