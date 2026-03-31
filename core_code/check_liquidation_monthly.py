#!/usr/bin/env python3
"""检查 liquidation-monthly 页面的数据加载情况"""
import requests
import json

# 测试页面访问
print("="*60)
print("检查 /liquidation-monthly 页面")
print("="*60)

url = "http://localhost:5000/liquidation-monthly"
try:
    response = requests.get(url, timeout=5)
    print(f"✅ 页面状态码: {response.status_code}")
    print(f"✅ 页面大小: {len(response.text)} 字节")
    
    # 检查是否包含关键元素
    if 'liquidationChart' in response.text:
        print("✅ 包含图表容器")
    else:
        print("❌ 缺少图表容器")
    
    if 'echarts' in response.text:
        print("✅ 包含ECharts库")
    else:
        print("❌ 缺少ECharts库")
        
except Exception as e:
    print(f"❌ 访问失败: {e}")

print()

# 测试数据API（页面可能使用的API）
print("="*60)
print("检查数据API")
print("="*60)

# 检查panic_wash_index.jsonl文件
import os
data_file = '/home/user/webapp/data/panic_jsonl/panic_wash_index.jsonl'
if os.path.exists(data_file):
    with open(data_file, 'r') as f:
        lines = f.readlines()
        print(f"✅ 数据文件存在: {len(lines)} 条记录")
        
        # 读取最后一条
        try:
            last_record = json.loads(lines[-1].strip())
            print(f"✅ 最新记录时间: {last_record.get('beijing_time', 'N/A')}")
            liq_data = last_record.get('liquidation_data', {})
            print(f"✅ 1小时爆仓: {liq_data.get('liquidation_1h', 0)} 万美元")
        except:
            print("❌ 无法解析最后一条记录")
else:
    print(f"❌ 数据文件不存在: {data_file}")

print()
print("="*60)
print("检查完成")
print("="*60)
