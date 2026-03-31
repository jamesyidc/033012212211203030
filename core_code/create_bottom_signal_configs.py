#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为所有账户创建见底信号做多策略的默认配置文件"""

import json
import os
from datetime import datetime
from pathlib import Path

# 账户列表
ACCOUNTS = [
    {'id': 'account_main', 'name': '主账户'},
    {'id': 'account_fangfang12', 'name': 'fangfang12'},
    {'id': 'account_anchor', 'name': '锚点账户'},
    {'id': 'account_poit_main', 'name': 'POIT (子账户)'}
]

# 策略类型
STRATEGIES = [
    {'type': 'top8_long', 'desc': '见底信号+涨幅前8做多'},
    {'type': 'bottom8_long', 'desc': '见底信号+涨幅后8做多'}
]

# 配置目录
CONFIG_DIR = Path('/home/user/webapp/data/okx_bottom_signal_strategies')
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

print("🚀 开始创建见底信号做多策略配置文件...\n")

created_files = []

for account in ACCOUNTS:
    for strategy in STRATEGIES:
        # 配置文件路径
        config_file = CONFIG_DIR / f"{account['id']}_bottom_signal_{strategy['type']}.jsonl"
        
        # 默认配置
        config = {
            'timestamp': datetime.now().isoformat(),
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'account_id': account['id'],
            'account_name': account['name'],
            'strategy_type': strategy['type'],
            'description': strategy['desc'],
            'enabled': False,
            'rsi_threshold': 800,
            'max_order_usdt': 5.0,
            'position_percent': 1.5,
            'leverage': 10
        }
        
        # 写入配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(config, ensure_ascii=False) + '\n')
        
        created_files.append(str(config_file))
        print(f"✅ 创建成功: {account['id']}/{strategy['type']}")
        print(f"   账户: {account['name']}")
        print(f"   策略: {strategy['desc']}")
        print(f"   RSI阈值: {config['rsi_threshold']}")
        print(f"   单币限额: {config['max_order_usdt']} USDT")
        print(f"   杠杆: {config['leverage']}x")
        print()

print(f"\n📊 总结:")
print(f"   创建文件数: {len(created_files)}")
print(f"   账户数: {len(ACCOUNTS)}")
print(f"   每账户策略数: {len(STRATEGIES)}")
print(f"\n✅ 所有配置文件创建完成！")
print(f"\n配置目录: {CONFIG_DIR}")
print("\n文件列表:")
for f in created_files:
    print(f"  - {Path(f).name}")
