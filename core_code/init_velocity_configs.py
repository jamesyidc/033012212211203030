#!/usr/bin/env python3
"""
初始化所有账户的涨速止盈配置
"""
import json
from pathlib import Path

# 所有账户ID
ACCOUNTS = [
    'account_main',
    'account_fangfang12',
    'account_anchor',
    'account_poit'
]

# 默认配置
DEFAULT_CONFIG = {
    'long_permission': True,
    'short_permission': True,
    'last_check_time': None,
    'long_enabled': False,
    'short_enabled': False,
    'max_velocity_threshold': 15.0,
    'min_velocity_threshold': -15.0
}

def init_configs():
    config_dir = Path('/home/user/webapp/data/velocity_takeprofit')
    config_dir.mkdir(parents=True, exist_ok=True)
    
    for account_id in ACCOUNTS:
        config_file = config_dir / f'{account_id}_config.json'
        
        if config_file.exists():
            print(f"✅ {account_id} 配置已存在: {config_file}")
        else:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
            print(f"🆕 创建 {account_id} 配置: {config_file}")
    
    print("\n📋 当前配置文件:")
    for f in sorted(config_dir.glob('*_config.json')):
        print(f"  - {f.name}")

if __name__ == '__main__':
    init_configs()
