#!/bin/bash
# 系统快速检查脚本

echo "========================================="
echo "🚀 加密货币数据分析系统 - 状态检查"
echo "========================================="
echo ""

# 检查PM2服务状态
echo "📊 PM2服务状态:"
pm2 list | grep -E "online|errored|stopped"
echo ""

# 检查Flask端口
echo "🌐 Flask Web应用:"
if netstat -tlnp 2>/dev/null | grep -q ":9002"; then
    echo "✅ Flask应用运行在端口 9002"
    echo "   访问地址: https://9002-izdl7i89gq7ib3tbi6fq1-82b888ba.sandbox.novita.ai"
else
    echo "❌ Flask应用未运行"
fi
echo ""

# 检查数据目录
echo "📁 数据目录状态:"
if [ -d "/home/user/webapp/data" ]; then
    echo "✅ 数据目录存在"
    du -sh /home/user/webapp/data/ 2>/dev/null
else
    echo "❌ 数据目录不存在"
fi
echo ""

# 检查日志
echo "📝 最新日志 (Flask):"
if [ -f "/home/user/webapp/logs/flask-app-out.log" ]; then
    tail -n 3 /home/user/webapp/logs/flask-app-out.log
else
    echo "⚠️  日志文件不存在"
fi
echo ""

echo "========================================="
echo "💡 常用命令:"
echo "   pm2 list          - 查看所有服务"
echo "   pm2 logs [name]   - 查看服务日志"
echo "   pm2 restart all   - 重启所有服务"
echo "   pm2 monit         - 监控资源使用"
echo "========================================="
