#!/usr/bin/env python3
"""
验证不同日期的数据字段格式
"""

import json

dates = ["20260205", "20260209", "20260218"]

for date_str in dates:
    file_path = f"/home/user/webapp/data/coin_change_tracker/coin_change_{date_str}.jsonl"
    
    print(f"\n📅 日期: {date_str}")
    print("="*60)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 读取第一行
            first_line = f.readline().strip()
            if first_line:
                data = json.loads(first_line)
                
                print(f"  time字段: {data.get('time', 'N/A')}")
                print(f"  beijing_time字段: {data.get('beijing_time', 'N/A')}")
                
                # 前端将使用哪个字段
                if data.get('beijing_time'):
                    time_value = data['beijing_time'].split(' ')[1]
                    print(f"  ✅ 使用beijing_time，提取时间: {time_value}")
                elif data.get('time'):
                    time_value = data['time']
                    print(f"  ✅ 使用time字段: {time_value}")
                else:
                    print(f"  ❌ 无法获取时间")
                    
    except FileNotFoundError:
        print(f"  ❌ 文件不存在")
    except Exception as e:
        print(f"  ❌ 错误: {e}")

