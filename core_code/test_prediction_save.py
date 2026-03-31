#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试行情预测数据保存功能
"""

import sys
import os
sys.path.insert(0, '/home/user/webapp')

from monitors.coin_change_prediction_monitor import save_prediction_data

# 测试数据
color_counts = {
    'green': 3,
    'red': 5,
    'yellow': 2,
    'blank': 2,
    'blank_ratio': 16.7
}

signal = "测试信号"
description = "🔴 这是一个测试预判数据"

print("=" * 60)
print("测试行情预测数据保存")
print("=" * 60)

# 测试临时数据保存
print("\n1. 测试临时数据保存（is_temp=True）")
result1 = save_prediction_data(color_counts, signal, description, is_temp=True)
print(f"结果: {'成功✅' if result1 else '失败❌'}")

# 测试最终数据保存
print("\n2. 测试最终数据保存（is_temp=False）")
result2 = save_prediction_data(color_counts, signal + "_最终", description + "（最终预判）", is_temp=False)
print(f"结果: {'成功✅' if result2 else '失败❌'}")

# 检查生成的文件
print("\n3. 检查生成的JSONL文件")
import subprocess
result = subprocess.run(['ls', '-lh', 'data/daily_predictions/'], capture_output=True, text=True)
print(result.stdout)

print("\n4. 查看今天的JSONL文件内容")
from datetime import datetime
today_str = datetime.now().strftime('%Y%m%d')
jsonl_file = f"data/daily_predictions/prediction_{today_str}.jsonl"

if os.path.exists(jsonl_file):
    print(f"文件: {jsonl_file}")
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"总行数: {len(lines)}")
        print("\n最后2行数据:")
        for line in lines[-2:]:
            print(line.strip())
else:
    print(f"❌ 文件不存在: {jsonl_file}")

print("\n=" * 60)
print("测试完成")
print("=" * 60)
