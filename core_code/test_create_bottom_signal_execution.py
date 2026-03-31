#!/usr/bin/env python3
"""创建测试执行记录（按日期分文件）"""
import json
from datetime import datetime
from pathlib import Path

EXECUTION_DIR = Path('data/okx_bottom_signal_execution')
EXECUTION_DIR.mkdir(parents=True, exist_ok=True)

# 创建今天的测试记录
now = datetime.now()
date_str = now.strftime('%Y%m%d')  # 20260226

test_record = {
    'timestamp': now.isoformat(),
    'time': now.strftime('%Y-%m-%d %H:%M:%S'),
    'date': now.strftime('%Y-%m-%d'),
    'account_id': 'account_main',
    'strategy_type': 'top8_long',
    'rsi_value': 450.5,
    'coins': ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'AVAX'],
    'result': {
        'success_count': 8,
        'failed_coins': [],
        'total_investment': 120.0,
        'per_coin_amount': 15.0
    }
}

execution_file = EXECUTION_DIR / f"account_main_bottom_signal_top8_long_execution_{date_str}.jsonl"

with open(execution_file, 'a', encoding='utf-8') as f:
    f.write(json.dumps(test_record, ensure_ascii=False) + '\n')

print(f"✅ 测试执行记录已创建: {execution_file}")
print(f"文件大小: {execution_file.stat().st_size} 字节")
print(f"内容预览:")
print(json.dumps(test_record, ensure_ascii=False, indent=2))
