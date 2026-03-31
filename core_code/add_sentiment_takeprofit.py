#!/usr/bin/env python3
"""
为OKX止盈止损系统添加市场情绪止盈功能
当市场情绪最新信号为"见顶信号"或"顶部背离"时，自动平掉所有多单
"""

import json
from pathlib import Path
from datetime import datetime

WEBAPP_DIR = Path('/home/user/webapp')
SETTINGS_DIR = WEBAPP_DIR / 'data' / 'okx_tpsl_settings'

def upgrade_tpsl_config():
    """为所有账户的TPSL配置添加市场情绪止盈开关"""
    
    print("🔧 开始升级止盈止损配置...")
    
    jsonl_files = list(SETTINGS_DIR.glob('*_tpsl.jsonl'))
    upgraded_count = 0
    
    for jsonl_file in jsonl_files:
        if '_execution' in jsonl_file.name:
            continue
            
        print(f"\n📄 处理文件: {jsonl_file.name}")
        
        # 读取所有行
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print(f"   ⚠️  文件为空，跳过")
            continue
        
        # 解析第一行（配置行）
        try:
            config = json.loads(lines[0])
        except:
            print(f"   ❌ 解析失败，跳过")
            continue
        
        # 检查是否已有市场情绪止盈配置
        if 'sentiment_take_profit_enabled' in config:
            print(f"   ✅ 已有市场情绪止盈配置，跳过")
            continue
        
        # 添加新字段
        config['sentiment_take_profit_enabled'] = True  # 默认启用
        config['sentiment_signals'] = ['见顶信号', '顶部背离']  # 触发信号
        config['sentiment_position_side'] = 'long'  # 只平多单
        config['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        config['comment'] = config.get('comment', '') + ' + 市场情绪止盈'
        
        # 重写配置行
        lines[0] = json.dumps(config, ensure_ascii=False) + '\n'
        
        # 写回文件
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"   ✅ 升级成功！")
        print(f"      - sentiment_take_profit_enabled: {config['sentiment_take_profit_enabled']}")
        print(f"      - sentiment_signals: {config['sentiment_signals']}")
        print(f"      - sentiment_position_side: {config['sentiment_position_side']}")
        
        upgraded_count += 1
    
    print(f"\n🎉 升级完成！共升级 {upgraded_count} 个配置文件")

if __name__ == '__main__':
    upgrade_tpsl_config()
