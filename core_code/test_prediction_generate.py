#!/usr/bin/env python3
"""测试预判生成"""
import requests
import json

# 获取今天的历史数据
date = '2026-03-10'
url = f"http://localhost:9002/api/coin-change-tracker/history?date={date}&lite=true"
response = requests.get(url, timeout=30)

print(f"Status code: {response.status_code}")
print(f"Response type: {type(response.text)}")
print(f"Response first 200 chars: {response.text[:200]}")

if response.status_code == 200:
    result = response.json()
    print(f"\nParsed JSON type: {type(result)}")
    print(f"Keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
    
    if isinstance(result, dict) and 'data' in result:
        data = result['data']
        print(f"\nData type: {type(data)}")
        print(f"Data length: {len(data)}")
        if len(data) > 0:
            print(f"First record type: {type(data[0])}")
            print(f"First record: {data[0]}")
