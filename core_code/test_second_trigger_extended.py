#!/usr/bin/env python3
"""
测试二级触发逻辑扩展
"""
import sys
sys.path.insert(0, '/home/user/webapp')

from monitors.coin_change_prediction_monitor import analyze_second_trigger

# 测试用例
test_cases = [
    # 原有的测试用例
    {
        'name': '情况1: 三根全绿',
        'bars': ['green', 'green', 'green'],
        'expected_triggered': True,
        'expected_action': 'immediate_long'
    },
    {
        'name': '情况2: 三根全空白',
        'bars': ['blank', 'blank', 'blank'],
        'expected_triggered': True,
        'expected_action': 'wait_dip_then_long'
    },
    
    # 新增的测试用例
    {
        'name': '情况3: 三根全红',
        'bars': ['red', 'red', 'red'],
        'expected_triggered': True,
        'expected_action': 'wait_dip_then_long'
    },
    {
        'name': '情况4a: 红红空白',
        'bars': ['red', 'red', 'blank'],
        'expected_triggered': True,
        'expected_action': 'wait_dip_then_long'
    },
    {
        'name': '情况4b: 红空白红',
        'bars': ['red', 'blank', 'red'],
        'expected_triggered': True,
        'expected_action': 'wait_dip_then_long'
    },
    {
        'name': '情况4c: 空白红红',
        'bars': ['blank', 'red', 'red'],
        'expected_triggered': True,
        'expected_action': 'wait_dip_then_long'
    },
    {
        'name': '情况5a: 红空白空白',
        'bars': ['red', 'blank', 'blank'],
        'expected_triggered': True,
        'expected_action': 'wait_dip_then_long'
    },
    {
        'name': '情况5b: 空白红空白',
        'bars': ['blank', 'red', 'blank'],
        'expected_triggered': True,
        'expected_action': 'wait_dip_then_long'
    },
    {
        'name': '情况5c: 空白空白红',
        'bars': ['blank', 'blank', 'red'],
        'expected_triggered': True,
        'expected_action': 'wait_dip_then_long'
    },
    
    # 不应触发的情况
    {
        'name': '混合: 绿红空白',
        'bars': ['green', 'red', 'blank'],
        'expected_triggered': False,
        'expected_action': None
    },
    {
        'name': '混合: 绿绿红',
        'bars': ['green', 'green', 'red'],
        'expected_triggered': False,
        'expected_action': None
    },
    {
        'name': '混合: 黄黄黄',
        'bars': ['yellow', 'yellow', 'yellow'],
        'expected_triggered': False,
        'expected_action': None
    }
]

print("=" * 70)
print("二级触发逻辑测试")
print("=" * 70)

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    result = analyze_second_trigger(test['bars'])
    
    triggered = result.get('triggered', False)
    action = result.get('action', None)
    
    # 检查是否符合预期
    triggered_match = (triggered == test['expected_triggered'])
    action_match = (action == test['expected_action'])
    
    if triggered_match and action_match:
        status = "✅ PASS"
        passed += 1
    else:
        status = "❌ FAIL"
        failed += 1
    
    print(f"\n测试 {i}: {test['name']}")
    print(f"  输入: {test['bars']}")
    print(f"  预期: triggered={test['expected_triggered']}, action={test['expected_action']}")
    print(f"  实际: triggered={triggered}, action={action}")
    print(f"  描述: {result.get('description', '')}")
    print(f"  结果: {status}")

print("\n" + "=" * 70)
print(f"测试完成: {passed} passed, {failed} failed")
print("=" * 70)

if failed == 0:
    print("✅ 所有测试通过！")
    sys.exit(0)
else:
    print(f"❌ {failed} 个测试失败")
    sys.exit(1)
