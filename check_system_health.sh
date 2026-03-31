#!/bin/bash
# 系统健康检查脚本
# 用于快速验证所有服务状态

echo "========================================"
echo "🏥 系统健康检查"
echo "========================================"
echo ""

# 1. PM2进程状态
echo "📊 PM2进程状态:"
PM2_ONLINE=$(pm2 list | grep -c "online")
PM2_TOTAL=26
echo "  在线进程: $PM2_ONLINE / $PM2_TOTAL"
if [ "$PM2_ONLINE" -eq "$PM2_TOTAL" ]; then
    echo "  ✅ 所有进程正常运行"
else
    echo "  ⚠️  警告: 有进程离线"
fi
echo ""

# 2. Flask应用状态
echo "🌐 Flask应用状态:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9002/)
if [ "$HTTP_CODE" -eq "200" ]; then
    echo "  ✅ Flask应用正常 (HTTP $HTTP_CODE)"
else
    echo "  ❌ Flask应用异常 (HTTP $HTTP_CODE)"
fi
echo ""

# 3. JSONL数据文件
echo "📁 数据文件统计:"
JSONL_COUNT=$(find /home/user/webapp/data -name "*.jsonl" -type f | wc -l)
DATA_SIZE=$(du -sh /home/user/webapp/data/ | cut -f1)
echo "  JSONL文件: $JSONL_COUNT 个"
echo "  数据大小: $DATA_SIZE"
echo ""

# 4. 日志目录
echo "📝 日志文件:"
LOG_COUNT=$(ls -1 /home/user/webapp/logs/*.log 2>/dev/null | wc -l)
echo "  日志文件: $LOG_COUNT 个"
echo ""

# 5. 内存使用
echo "💾 内存使用:"
TOTAL_MEM=$(pm2 list | awk 'NR>3 && NR<31 {sum+=$10} END {print sum}')
echo "  总内存: ~${TOTAL_MEM}MB"
echo ""

# 6. 关键服务检查
echo "🔍 关键服务检查:"
SERVICES=("flask-app" "okx-tpsl-monitor" "coin-change-predictor" "signal-collector")
for SERVICE in "${SERVICES[@]}"; do
    if pm2 list | grep -q "$SERVICE.*online"; then
        echo "  ✅ $SERVICE: 运行中"
    else
        echo "  ❌ $SERVICE: 离线"
    fi
done
echo ""

# 7. 访问地址
echo "🌐 访问地址:"
echo "  Web界面: https://9002-imp6ky5dtwten0w001hfy-82b888ba.sandbox.novita.ai"
echo "  本地地址: http://localhost:9002"
echo ""

echo "========================================"
echo "检查完成! $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
