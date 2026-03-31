#!/usr/bin/env python3
"""验证导入的数据"""
import json
from collections import defaultdict

# 读取数据
records = []
with open('data/panic_jsonl/panic_wash_index.jsonl', 'r') as f:
    for line in f:
        records.append(json.loads(line.strip()))

print("="*60)
print("数据验证报告")
print("="*60)

# 1. 总量统计
print(f"\n📊 总记录数: {len(records)}")

# 2. 日期分布
date_counts = defaultdict(int)
for r in records:
    date = r['beijing_time'].split(' ')[0]
    date_counts[date] += 1

print(f"\n📅 日期分布:")
for date in sorted(date_counts.keys()):
    print(f"  {date}: {date_counts[date]}条")

# 3. 数据质量检查
print(f"\n🔍 数据质量检查:")
errors = []
for i, r in enumerate(records):
    if not r.get('beijing_time'):
        errors.append(f"记录{i}: 缺少beijing_time")
    if not r.get('timestamp') or r['timestamp'] == 0:
        errors.append(f"记录{i}: 无效timestamp")
    if r.get('panic_index', 0) < 0:
        errors.append(f"记录{i}: panic_index为负数")

if errors:
    print(f"  ❌ 发现 {len(errors)} 个问题:")
    for err in errors[:10]:  # 只显示前10个
        print(f"     {err}")
else:
    print(f"  ✅ 数据质量良好，未发现错误")

# 4. 1小时爆仓金额统计
hour_1_amounts = []
for r in records:
    liq_data = r.get('liquidation_data', {})
    amount = liq_data.get('liquidation_1h', 0)
    if amount > 0:
        hour_1_amounts.append(amount)

if hour_1_amounts:
    print(f"\n💰 1小时爆仓金额统计:")
    print(f"  最小值: {min(hour_1_amounts):.2f}万美元")
    print(f"  最大值: {max(hour_1_amounts):.2f}万美元")
    print(f"  平均值: {sum(hour_1_amounts)/len(hour_1_amounts):.2f}万美元")

# 5. 时间连续性检查
print(f"\n⏰ 时间连续性检查:")
timestamps = [r['timestamp'] for r in records if r['timestamp'] > 0]
timestamps.sort()

gaps = []
for i in range(1, len(timestamps)):
    gap_minutes = (timestamps[i] - timestamps[i-1]) / 1000 / 60
    if gap_minutes > 10:  # 超过10分钟的间隙
        gaps.append(gap_minutes)

if gaps:
    print(f"  ⚠️  发现 {len(gaps)} 个时间间隙 (>10分钟)")
    print(f"     最大间隙: {max(gaps):.1f}分钟")
else:
    print(f"  ✅ 时间连续性良好")

print("\n" + "="*60)
print("✅ 验证完成")
