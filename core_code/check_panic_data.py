#!/usr/bin/env python3
"""检查恐慌指数数据质量"""
import json
from datetime import datetime

def check_data_file(file_path):
    """检查数据文件"""
    print(f"\n{'='*60}")
    print(f"检查文件: {file_path}")
    print('='*60)
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    print(f"总记录数: {len(lines)}")
    
    # 检查错误数据
    errors = []
    valid_records = []
    
    for i, line in enumerate(lines, 1):
        try:
            data = json.loads(line.strip())
            
            # 检查必要字段
            required_fields = ['panic_index', 'beijing_time', 'liquidation_data']
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                errors.append({
                    'line': i,
                    'error': f'缺少字段: {missing_fields}',
                    'data': line[:100]
                })
                continue
            
            # 检查panic_index是否合理
            panic_index = data.get('panic_index', 0)
            if panic_index < 0 or panic_index > 100:
                errors.append({
                    'line': i,
                    'error': f'panic_index异常: {panic_index}',
                    'time': data.get('beijing_time'),
                    'data': line[:100]
                })
                continue
            
            # 检查时间格式
            try:
                datetime.strptime(data['beijing_time'], '%Y-%m-%d %H:%M:%S')
            except:
                errors.append({
                    'line': i,
                    'error': f'时间格式错误: {data.get("beijing_time")}',
                    'data': line[:100]
                })
                continue
            
            valid_records.append(data)
            
        except json.JSONDecodeError as e:
            errors.append({
                'line': i,
                'error': f'JSON解析错误: {e}',
                'data': line[:100]
            })
    
    print(f"✅ 有效记录: {len(valid_records)}")
    print(f"❌ 错误记录: {len(errors)}")
    
    if errors:
        print(f"\n⚠️ 发现 {len(errors)} 个错误记录:")
        for err in errors[:10]:  # 只显示前10个
            print(f"  行{err['line']}: {err['error']}")
            if 'time' in err:
                print(f"    时间: {err['time']}")
    
    # 统计日期分布
    if valid_records:
        dates = {}
        for record in valid_records:
            date = record['beijing_time'].split(' ')[0]
            dates[date] = dates.get(date, 0) + 1
        
        print(f"\n📅 日期分布:")
        for date in sorted(dates.keys()):
            print(f"  {date}: {dates[date]}条")
    
    return valid_records, errors

# 检查主文件
valid_records, errors = check_data_file('data/panic_jsonl/panic_wash_index.jsonl')

print(f"\n{'='*60}")
print("总结")
print('='*60)
print(f"✅ 总有效记录: {len(valid_records)}")
print(f"❌ 总错误记录: {len(errors)}")

if len(errors) > 0:
    print(f"\n建议: 使用以下命令清理错误数据")
    print(f"  python3 clean_panic_data.py")
