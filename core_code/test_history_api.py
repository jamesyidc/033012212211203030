#!/usr/bin/env python3
"""
测试读取2月1-10日的历史数据
"""
import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path('/home/user/webapp/data/panic_daily')

def load_history_range(start_date, end_date):
    """加载日期范围内的所有数据"""
    all_data = []
    
    # 生成日期列表
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    while current <= end:
        date_str = current.strftime('%Y%m%d')
        file_path = DATA_DIR / f"panic_{date_str}.jsonl"
        
        if file_path.exists():
            print(f"读取 {date_str}...")
            count = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        all_data.append(record)
                        count += 1
                    except:
                        continue
            print(f"  ✅ {count} 条记录")
        else:
            print(f"  ❌ 文件不存在: {file_path}")
        
        # 下一天
        current = current.replace(day=current.day + 1)
    
    return all_data

if __name__ == '__main__':
    print("=" * 60)
    print("读取 2026-02-01 到 2026-02-10 的历史数据")
    print("=" * 60)
    
    data = load_history_range('2026-02-01', '2026-02-10')
    
    print("\n" + "=" * 60)
    print(f"总计: {len(data)} 条记录")
    print("=" * 60)
    
    if data:
        print("\n第一条记录示例：")
        print(json.dumps(data[0], indent=2, ensure_ascii=False))
        
        print("\n最后一条记录示例：")
        print(json.dumps(data[-1], indent=2, ensure_ascii=False))
