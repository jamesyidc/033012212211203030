#!/usr/bin/env python3
"""
测试RSI最高最低值计算
"""

import json
from datetime import datetime

def test_rsi_minmax(date_str="20260218"):
    """测试指定日期的RSI最高最低值"""
    
    file_path = f"/home/user/webapp/data/coin_change_tracker/rsi_{date_str}.jsonl"
    
    print(f"📊 分析日期: {date_str}")
    print(f"📁 文件路径: {file_path}")
    print()
    
    try:
        rsi_values = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line.strip())
                    if 'total_rsi' in record and record['total_rsi'] is not None:
                        rsi_values.append(record['total_rsi'])
        
        if rsi_values:
            max_rsi = max(rsi_values)
            min_rsi = min(rsi_values)
            avg_rsi = sum(rsi_values) / len(rsi_values)
            
            print(f"✅ RSI数据统计:")
            print(f"  数据点数: {len(rsi_values)}")
            print(f"  最高值: {max_rsi:.2f}")
            print(f"  最低值: {min_rsi:.2f}")
            print(f"  平均值: {avg_rsi:.2f}")
            print(f"  振幅: {max_rsi - min_rsi:.2f}")
            
            # 判断状态
            if max_rsi > 1890:
                print(f"  ⚠️ 出现超买（最高 {max_rsi:.2f} > 1890）")
            if min_rsi < 810:
                print(f"  ⚠️ 出现超卖（最低 {min_rsi:.2f} < 810）")
                
        else:
            print("❌ 没有有效的RSI数据")
            
    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    # 测试今天的数据
    test_rsi_minmax("20260218")
    
    print()
    print("="*60)
    print()
    
    # 测试2月5日（假突破最多的一天）
    test_rsi_minmax("20260205")

