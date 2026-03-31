#!/bin/bash

echo "=== Coin Change Tracker 柱状图修复验证 ==="
echo ""

echo "1. API 响应测试："
API_RESPONSE=$(curl -s "http://localhost:9002/api/coin-change-tracker/aggregated/10min_up_ratio")
echo "   Success: $(echo "$API_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('success'))")"
echo "   Data length: $(echo "$API_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('data', [])))")"
echo "   Count: $(echo "$API_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('count'))")"
echo ""

echo "2. 数据文件检查："
ls -lh data/coin_change_tracker/coin_change_20260316.jsonl 2>&1 | awk '{print "   " $0}'
echo ""

echo "3. PM2 服务状态："
pm2 list | grep coin-change-tracker | awk '{print "   " $0}'
echo ""

echo "4. 页面访问地址："
echo "   https://9002-izdl7i89gq7ib3tbi6fq1-82b888ba.sandbox.novita.ai/coin-change-tracker"
echo ""

echo "✅ 验证完成！"
