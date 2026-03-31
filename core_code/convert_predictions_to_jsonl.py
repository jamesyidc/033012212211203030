#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将2月份的预测JSON文件转换为JSONL格式
"""

import os
import json
from datetime import datetime
from pathlib import Path

# 数据目录
prediction_dir = Path("/home/user/webapp/data/daily_predictions")

# 统计
converted_count = 0
skipped_count = 0
error_count = 0

print("=" * 80)
print("2月份预测数据转换工具 - JSON → JSONL")
print("=" * 80)
print()

# 遍历所有2月份的JSON文件
json_files = sorted(prediction_dir.glob("prediction_2026-02-*.json"))

print(f"📂 找到 {len(json_files)} 个JSON文件")
print()

for json_file in json_files:
    try:
        # 从文件名提取日期
        # prediction_2026-02-26.json -> 2026-02-26 -> 20260226
        date_str = json_file.stem.replace("prediction_", "")  # 2026-02-26
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        new_date_str = date_obj.strftime("%Y%m%d")  # 20260226
        
        # 新的JSONL文件名
        jsonl_file = prediction_dir / f"prediction_{new_date_str}.jsonl"
        
        # 检查JSONL文件是否已存在
        if jsonl_file.exists():
            print(f"⏭️  跳过 {json_file.name} - JSONL已存在: {jsonl_file.name}")
            skipped_count += 1
            continue
        
        # 读取JSON文件
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 确保数据包含必要字段
        if 'is_final' not in data:
            data['is_final'] = not data.get('is_temp', False)
        
        # 写入JSONL文件（单行，作为最终预判）
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            f.write('\n')
        
        print(f"✅ 转换成功: {json_file.name} → {jsonl_file.name}")
        converted_count += 1
        
    except Exception as e:
        print(f"❌ 转换失败: {json_file.name} - {e}")
        error_count += 1

print()
print("=" * 80)
print("转换完成")
print("=" * 80)
print(f"✅ 成功转换: {converted_count} 个文件")
print(f"⏭️  跳过: {skipped_count} 个文件（已存在）")
print(f"❌ 失败: {error_count} 个文件")
print()

# 显示转换后的文件列表
print("📋 JSONL文件列表:")
jsonl_files = sorted(prediction_dir.glob("prediction_202602*.jsonl"))
for jsonl_file in jsonl_files:
    size = jsonl_file.stat().st_size
    mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
    print(f"  {jsonl_file.name:30s} {size:>6d} bytes  {mtime}")

print()
print("=" * 80)
