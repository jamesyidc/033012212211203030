#!/usr/bin/env python3
"""
测试做空入场条件扩展逻辑
"""
import sys
sys.path.insert(0, '/home/user/webapp/trading_signals_system/scripts')

from models.model_1_low_absorption import Model1LowAbsorption
import json

# 加载配置
with open('/home/user/webapp/trading_signals_system/config/system_config.json', 'r') as f:
    config = json.load(f)

# 初始化模型
model = Model1LowAbsorption(config)

# 测试参数
test_positive_ratio = 7.5  # 低吸状态

print("="*80)
print("做空入场条件测试")
print("="*80)
print(f"测试参数: 正数占比={test_positive_ratio}%")
print()

# 执行检查
result = model.check_entry_condition_short(test_positive_ratio)

print("检查结果:")
print(f"  是否满足: {result['met']}")
print(f"  原因: {result['reason']}")
print(f"  当前涨速: {result.get('velocity', 'N/A')}%")
print(f"  是否在02:30后: {result.get('after_cutoff', 'N/A')}")
print(f"  BTC涨跌幅: {result.get('btc_change', 'N/A')}%")
print()

# 测试BTC获取
print("-"*80)
print("BTC涨跌幅测试:")
btc_change = model._get_btc_change()
print(f"  BTC涨跌幅: {btc_change}%")
print()

# 测试正数占比下降
print("-"*80)
print("正数占比下降趋势测试:")
positive_ratio_dropped = model._check_positive_ratio_drop()
print(f"  是否从>40%降至<40%: {positive_ratio_dropped}")
print()

print("="*80)
