#!/usr/bin/env python3
"""测试市场情绪止盈开关保存"""
import json

# 读取主账户配置
with open('data/okx_tpsl_settings/account_main_tpsl.jsonl', 'r') as f:
    config = json.loads(f.readline())
    print("=== account_main 当前配置 ===")
    print(f"account_id: {config.get('account_id')}")
    print(f"enabled: {config.get('enabled')}")
    print(f"sentiment_take_profit_enabled: {config.get('sentiment_take_profit_enabled')}")
    print(f"sentiment_signals: {config.get('sentiment_signals')}")
    print(f"sentiment_position_side: {config.get('sentiment_position_side')}")
    print(f"last_updated: {config.get('last_updated')}")
    print()

# 模拟打开市场情绪止盈开关
print("=== 模拟打开市场情绪止盈开关 ===")
config['sentiment_take_profit_enabled'] = True
config['sentiment_signals'] = ['见顶信号', '顶部背离']
config['sentiment_position_side'] = 'long'
config['last_updated'] = '2026-02-19 19:30:00'

# 保存
with open('data/okx_tpsl_settings/account_main_tpsl.jsonl', 'w') as f:
    f.write(json.dumps(config, ensure_ascii=False) + '\n')

print("✅ 已手动打开 account_main 的市场情绪止盈开关")
print()

# 验证
with open('data/okx_tpsl_settings/account_main_tpsl.jsonl', 'r') as f:
    config = json.loads(f.readline())
    print("=== 验证保存结果 ===")
    print(f"sentiment_take_profit_enabled: {config.get('sentiment_take_profit_enabled')}")
    print(f"sentiment_signals: {config.get('sentiment_signals')}")
