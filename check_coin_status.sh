#!/bin/bash
# 币种采集状态监控脚本

echo "========================================="
echo "币种采集状态监控"
echo "========================================="
echo ""

# 查看API返回的币种数
API_COUNT=$(curl -s "http://localhost:9002/api/coin-change-tracker/latest" | python3 -c "import json, sys; d = json.load(sys.stdin); print(len(d.get('data', {}).get('changes', {})))" 2>/dev/null)

echo "📊 当前API返回币种数: ${API_COUNT:-0}/27"
echo ""

# 查看最近的采集日志
echo "📝 最近采集日志:"
echo "----------------------------------------"
tail -50 /home/user/webapp/logs/coin-change-tracker-out.log | grep -E "开始采集|数据完整|数据不完整|跳过保存|统计|缺失" | tail -10
echo ""

# 查看是否有完整性检查的输出
echo "🔍 完整性检查状态:"
echo "----------------------------------------"
if tail -100 /home/user/webapp/logs/coin-change-tracker-out.log | grep -q "数据完整"; then
    echo "✅ 最近有成功采集到完整数据"
    tail -100 /home/user/webapp/logs/coin-change-tracker-out.log | grep "数据完整" | tail -1
elif tail -100 /home/user/webapp/logs/coin-change-tracker-out.log | grep -q "数据不完整"; then
    echo "❌ 最近的采集数据不完整"
    tail -100 /home/user/webapp/logs/coin-change-tracker-out.log | grep "数据不完整" | tail -1
else
    echo "⏳ 等待采集完成..."
fi
echo ""

# 查看缺失的币种
echo "🔎 最近缺失的币种:"
echo "----------------------------------------"
tail -100 /home/user/webapp/logs/coin-change-tracker-out.log | grep "缺失:" | tail -1
echo ""

echo "========================================="
echo "提示: 运行 'pm2 logs coin-change-tracker' 查看实时日志"
echo "========================================="
