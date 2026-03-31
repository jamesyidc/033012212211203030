#!/usr/bin/env python3
"""
获取所有采集器的运行状态
通过PM2获取进程状态并输出JSON格式
"""
import subprocess
import json
import os
import sys
from datetime import datetime
from pathlib import Path

BEIJING_OFFSET = 8  # UTC+8

def get_pm2_status():
    """获取PM2进程状态列表"""
    try:
        result = subprocess.run(
            ['pm2', 'jlist'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return []
        
        processes = json.loads(result.stdout)
        return processes
    except Exception as e:
        return []


def check_log_file_freshness(log_file, max_age_minutes=10):
    """检查日志文件的新鲜度"""
    try:
        path = Path(log_file)
        if not path.exists():
            return 'no_log', None
        
        mtime = path.stat().st_mtime
        now = datetime.utcnow().timestamp() + BEIJING_OFFSET * 3600
        age_seconds = now - mtime - BEIJING_OFFSET * 3600
        age_minutes = age_seconds / 60
        
        if age_minutes > max_age_minutes * 6:
            return 'stale', age_minutes
        elif age_minutes > max_age_minutes:
            return 'warning', age_minutes
        else:
            return 'fresh', age_minutes
    except Exception:
        return 'unknown', None


def get_all_collectors_status():
    """获取所有采集器状态"""
    pm2_processes = get_pm2_status()
    
    # Build PM2 process map
    pm2_map = {}
    for proc in pm2_processes:
        name = proc.get('name', '')
        pm2_map[name] = proc
    
    # Define collector configurations
    collectors = [
        {'name': 'flask-app', 'display': 'Flask主服务', 'type': 'service'},
        {'name': 'signal-collector', 'display': '信号采集器', 'type': 'collector'},
        {'name': 'liquidation-1h-collector', 'display': '1小时清算采集器', 'type': 'collector'},
        {'name': 'crypto-index-collector', 'display': '加密指数采集器', 'type': 'collector'},
        {'name': 'v1v2-collector', 'display': 'V1V2采集器', 'type': 'collector'},
        {'name': 'price-speed-collector', 'display': '价格速度采集器', 'type': 'collector'},
        {'name': 'sar-slope-collector', 'display': 'SAR斜率采集器', 'type': 'collector'},
        {'name': 'sar-jsonl-collector', 'display': 'SAR JSONL采集器', 'type': 'collector'},
        {'name': 'price-comparison-collector', 'display': '价格对比采集器', 'type': 'collector'},
        {'name': 'financial-indicators-collector', 'display': '金融指标采集器', 'type': 'collector'},
        {'name': 'okx-day-change-collector', 'display': 'OKX日变化采集器', 'type': 'collector'},
        {'name': 'price-baseline-collector', 'display': '价格基线采集器', 'type': 'collector'},
        {'name': 'sar-bias-stats-collector', 'display': 'SAR偏向统计采集器', 'type': 'collector'},
        {'name': 'panic-wash-collector', 'display': '恐慌洗盘采集器', 'type': 'collector'},
        {'name': 'coin-change-tracker', 'display': '币种涨跌追踪器', 'type': 'collector'},
        {'name': 'coin-price-tracker', 'display': '币种价格追踪器', 'type': 'collector'},
        {'name': 'data-health-monitor', 'display': '数据健康监控', 'type': 'monitor'},
        {'name': 'system-health-monitor', 'display': '系统健康监控', 'type': 'monitor'},
        {'name': 'abc-position-tracker', 'display': 'ABC持仓追踪器', 'type': 'monitor'},
        {'name': 'liquidation-alert-monitor', 'display': '清算预警监控', 'type': 'monitor'},
        {'name': 'dashboard-jsonl-manager', 'display': '仪表盘JSONL管理', 'type': 'manager'},
        {'name': 'gdrive-jsonl-manager', 'display': 'GDrive JSONL管理', 'type': 'manager'},
        {'name': 'okx-tpsl-monitor', 'display': 'OKX止盈止损监控', 'type': 'monitor'},
        {'name': 'sar-bias-monitor', 'display': 'SAR偏向监控', 'type': 'monitor'},
        {'name': 'market-sentiment-collector', 'display': '市场情绪采集器', 'type': 'collector'},
        {'name': 'price-position-collector', 'display': '价格位置采集器', 'type': 'collector'},
        {'name': 'new-high-low-collector', 'display': '新高低采集器', 'type': 'collector'},
    ]
    
    status_list = []
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for col in collectors:
        name = col['name']
        proc_info = pm2_map.get(name)
        
        if proc_info:
            pm2_status = proc_info.get('pm2_env', {}).get('status', 'unknown')
            pid = proc_info.get('pid', 0)
            restarts = proc_info.get('pm2_env', {}).get('restart_time', 0)
            memory = proc_info.get('monit', {}).get('memory', 0)
            cpu = proc_info.get('monit', {}).get('cpu', 0)
            uptime = proc_info.get('pm2_env', {}).get('pm_uptime', 0)
            
            # Determine status
            if pm2_status == 'online':
                if restarts > 10:
                    status = 'warning'
                    message = f'频繁重启 ({restarts}次)'
                else:
                    status = 'normal'
                    message = '运行正常'
            elif pm2_status == 'stopped':
                status = 'stopped'
                message = '已停止'
            elif pm2_status == 'errored':
                status = 'error'
                message = '运行错误'
            else:
                status = 'warning'
                message = f'状态异常: {pm2_status}'
            
            status_list.append({
                'name': name,
                'display': col['display'],
                'type': col['type'],
                'status': status,
                'pm2_status': pm2_status,
                'pid': pid,
                'restarts': restarts,
                'memory_mb': round(memory / 1024 / 1024, 1) if memory else 0,
                'cpu_percent': cpu,
                'message': message,
                'checked_at': now_str
            })
        else:
            # Process not in PM2
            status_list.append({
                'name': name,
                'display': col['display'],
                'type': col['type'],
                'status': 'no_data',
                'pm2_status': 'not_found',
                'pid': 0,
                'restarts': 0,
                'memory_mb': 0,
                'cpu_percent': 0,
                'message': '进程未在PM2中',
                'checked_at': now_str
            })
    
    return status_list


if __name__ == '__main__':
    status = get_all_collectors_status()
    print(json.dumps(status, ensure_ascii=False))
