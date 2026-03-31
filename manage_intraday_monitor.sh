#!/bin/bash
# 日内模式监控器管理脚本

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WEBAPP_DIR="$(dirname "$SCRIPT_DIR")"
MONITOR_SCRIPT="$WEBAPP_DIR/monitors/intraday_pattern_monitor.py"
LOG_FILE="$WEBAPP_DIR/logs/intraday_pattern_monitor.log"
PID_FILE="$WEBAPP_DIR/logs/intraday_pattern_monitor.pid"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查监控器是否运行
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# 启动监控器
start() {
    if is_running; then
        echo -e "${YELLOW}⚠️  监控器已在运行中 (PID: $(cat $PID_FILE))${NC}"
        return 1
    fi
    
    echo -e "${GREEN}🚀 启动日内模式监控器...${NC}"
    
    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # 启动监控器
    cd "$WEBAPP_DIR"
    nohup python3 "$MONITOR_SCRIPT" > "$LOG_FILE" 2>&1 &
    PID=$!
    
    # 保存PID
    echo $PID > "$PID_FILE"
    
    # 等待几秒检查是否成功启动
    sleep 3
    
    if is_running; then
        echo -e "${GREEN}✅ 监控器启动成功 (PID: $PID)${NC}"
        echo -e "${GREEN}📄 日志文件: $LOG_FILE${NC}"
        return 0
    else
        echo -e "${RED}❌ 监控器启动失败${NC}"
        echo -e "${YELLOW}查看日志: tail -f $LOG_FILE${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 停止监控器
stop() {
    if ! is_running; then
        echo -e "${YELLOW}⚠️  监控器未运行${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    echo -e "${YELLOW}⏹️  停止监控器 (PID: $PID)...${NC}"
    
    # 发送TERM信号
    kill "$PID" 2>/dev/null
    
    # 等待最多10秒
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 监控器已停止${NC}"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    # 如果还在运行，强制kill
    echo -e "${RED}⚠️  正常停止失败，强制终止...${NC}"
    kill -9 "$PID" 2>/dev/null
    rm -f "$PID_FILE"
    echo -e "${GREEN}✅ 监控器已强制停止${NC}"
    return 0
}

# 重启监控器
restart() {
    echo -e "${YELLOW}🔄 重启监控器...${NC}"
    stop
    sleep 2
    start
}

# 查看状态
status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✅ 监控器正在运行${NC}"
        echo -e "${GREEN}   PID: $PID${NC}"
        echo -e "${GREEN}   日志: $LOG_FILE${NC}"
        
        # 显示进程信息
        echo -e "\n${GREEN}进程信息:${NC}"
        ps -p "$PID" -o pid,ppid,%cpu,%mem,etime,cmd
        
        # 显示最近日志
        if [ -f "$LOG_FILE" ]; then
            echo -e "\n${GREEN}最近日志 (最后20行):${NC}"
            tail -20 "$LOG_FILE"
        fi
    else
        echo -e "${RED}❌ 监控器未运行${NC}"
        rm -f "$PID_FILE"
    fi
}

# 查看日志
logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${RED}❌ 日志文件不存在${NC}"
        return 1
    fi
    
    if [ "$1" = "-f" ]; then
        tail -f "$LOG_FILE"
    else
        tail -n 50 "$LOG_FILE"
    fi
}

# 帮助信息
usage() {
    echo "日内模式监控器管理脚本"
    echo ""
    echo "用法: $0 {start|stop|restart|status|logs}"
    echo ""
    echo "命令:"
    echo "  start    - 启动监控器"
    echo "  stop     - 停止监控器"
    echo "  restart  - 重启监控器"
    echo "  status   - 查看运行状态"
    echo "  logs     - 查看最近50行日志"
    echo "  logs -f  - 实时查看日志"
    echo ""
}

# 主逻辑
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs "$2"
        ;;
    *)
        usage
        exit 1
        ;;
esac

exit $?
