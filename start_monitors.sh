#!/bin/bash
# 启动所有监控脚本

cd /home/user/webapp

echo "🚀 启动监控脚本..."

# 停止已有的进程
pkill -f "positive_ratio_auto_close.py" 2>/dev/null
pkill -f "velocity_takeprofit_monitor.py" 2>/dev/null

sleep 2

# 创建日志目录
mkdir -p logs

# 启动正数占比止盈止损监控
echo "📊 启动正数占比止盈止损监控..."
nohup python3 scripts/positive_ratio_auto_close.py > logs/positive_ratio_monitor.log 2>&1 &
echo "   PID: $!"

# 启动5分钟涨速止盈监控
echo "⚡ 启动5分钟涨速止盈监控..."
nohup python3 scripts/velocity_takeprofit_monitor.py > logs/velocity_monitor.log 2>&1 &
echo "   PID: $!"

sleep 2

# 检查进程状态
echo ""
echo "✅ 监控脚本状态:"
ps aux | grep -E "positive_ratio_auto_close|velocity_takeprofit_monitor" | grep -v grep | awk '{print "   ", $2, $11, $12, $13}'

echo ""
echo "📋 查看日志:"
echo "   tail -f logs/positive_ratio_monitor.log"
echo "   tail -f logs/velocity_monitor.log"
