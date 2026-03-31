#!/usr/bin/env python3
"""
系统健康监控器 V2.0 - 全面监控所有采集器并自动修复
功能：
1. 监控所有 PM2 进程状态
2. 检查数据采集延迟
3. 自动重启异常进程
4. Telegram 通知无法修复的问题
"""
import subprocess
import json
import time
import requests
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# 添加项目路径
sys.path.insert(0, '/home/user/webapp')

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 尝试加载 Telegram 配置
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
try:
    from config.telegram_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    print("✅ 已加载 Telegram 配置")
except ImportError:
    print("⚠️ 未找到 Telegram 配置文件，通知功能将不可用")
except Exception as e:
    print(f"⚠️ 加载 Telegram 配置失败: {e}")

# 监控配置 - 包含所有实际运行的采集器
MONITOR_CONFIG = {
    # 进程名: (数据文件路径, 最大允许延迟分钟数)
    'signal-collector': ('data/signal_timeline/*.jsonl', 10),
    'price-position-collector': ('data/price_position_10m/*.jsonl', 10),
    'price-speed-collector': ('data/price_speed_10m/*.jsonl', 5),
    'sar-slope-collector': ('data/sar_slope_jsonl/latest_sar_slope.jsonl', 10),
    'sar-bias-stats-collector': ('data/sar_bias_stats/*.jsonl', 10),
    'liquidation-1h-collector': ('data/liquidation_1h/*.jsonl', 120),
    'okx-day-change-collector': ('data/okx_day_change/*.jsonl', 1500),
    'price-comparison-collector': ('data/price_comparison/*.jsonl', 10),
    'v1v2-collector': ('data/v1v2_ratios/*.jsonl', 10),
    'panic-wash-collector': ('data/panic_wash/*.jsonl', 10),
    'coin-change-tracker': ('data/coin_changes/*.jsonl', 10),
    'crypto-index-collector': ('data/crypto_index/*.jsonl', 10),
    'financial-indicators-collector': ('data/financial_indicators/*.jsonl', 1500),
    'okx-trade-history-collector': ('data/okx_trade_history/*.jsonl', 10),
    'okx-trading-marks-collector': ('data/okx_trading_marks/*.jsonl', 10),
    'liquidation-alert-monitor': ('data/liquidation_alerts/*.jsonl', 10),
    'price-baseline-collector': ('data/price_baselines/*.jsonl', 1500),
    'gdrive-jsonl-manager': ('data/dashboard_jsonl/*.jsonl', 30),
    'dashboard-jsonl-manager': ('data/dashboard_jsonl/*.jsonl', 30),
}

# 自动重启计数器
restart_counter = {}

def get_pm2_status():
    """获取所有 PM2 进程状态"""
    try:
        result = subprocess.run(['pm2', 'jlist'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return []
    except Exception as e:
        print(f"❌ 获取 PM2 状态失败: {e}")
        return []

def check_process_status(process_name):
    """检查单个进程状态"""
    processes = get_pm2_status()
    for proc in processes:
        if proc.get('name') == process_name:
            status = proc.get('pm2_env', {}).get('status', 'unknown')
            return status
    return 'not_found'

def check_data_freshness(data_path, max_delay_minutes):
    """检查数据新鲜度"""
    try:
        data_dir = Path('/home/user/webapp') / Path(data_path).parent
        if not data_dir.exists():
            return False, f"目录不存在: {data_dir}"
        
        # 查找最新的 JSONL 文件
        jsonl_files = list(data_dir.glob('*.jsonl'))
        if not jsonl_files:
            return False, "无数据文件"
        
        # 获取最新文件的修改时间
        latest_file = max(jsonl_files, key=lambda f: f.stat().st_mtime)
        file_mtime = datetime.fromtimestamp(latest_file.stat().st_mtime, tz=BEIJING_TZ)
        now = datetime.now(BEIJING_TZ)
        delay_minutes = (now - file_mtime).total_seconds() / 60
        
        is_fresh = delay_minutes <= max_delay_minutes
        return is_fresh, f"延迟 {delay_minutes:.1f} 分钟 (阈值: {max_delay_minutes})"
    
    except Exception as e:
        return False, f"检查失败: {str(e)}"

def restart_process(process_name):
    """重启进程"""
    try:
        print(f"🔄 正在重启进程: {process_name}")
        result = subprocess.run(['pm2', 'restart', process_name], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            restart_counter[process_name] = restart_counter.get(process_name, 0) + 1
            return True, f"重启成功 (第 {restart_counter[process_name]} 次)"
        else:
            return False, f"重启失败: {result.stderr}"
    
    except Exception as e:
        return False, f"重启异常: {str(e)}"

def send_telegram_notification(message):
    """发送 Telegram 通知"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"⚠️ Telegram 未配置，跳过通知: {message}")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': f"🚨 系统健康监控告警\n\n{message}",
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    
    except Exception as e:
        print(f"❌ Telegram 通知失败: {e}")
        return False

def check_flask_app():
    """检查 Flask 应用是否正常"""
    try:
        response = requests.get('http://localhost:9002/', timeout=5)
        return response.status_code == 200
    except:
        return False

def monitor_cycle():
    """执行一轮监控"""
    beijing_now = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n{'='*70}")
    print(f"🔍 系统健康监控 - {beijing_now}")
    print(f"{'='*70}\n")
    
    issues = []
    fixed_issues = []
    
    # 1. 检查 Flask 应用
    print("📊 检查 Flask 应用...")
    if not check_flask_app():
        print("❌ Flask 应用无响应")
        success, msg = restart_process('flask-app')
        if success:
            fixed_issues.append(f"Flask 应用: {msg}")
            print(f"✅ {msg}")
        else:
            issues.append(f"Flask 应用无响应且重启失败: {msg}")
            print(f"❌ {msg}")
    else:
        print("✅ Flask 应用正常")
    
    # 2. 检查所有配置的采集器
    print(f"\n📋 检查 {len(MONITOR_CONFIG)} 个采集器...")
    for process_name, (data_path, max_delay) in MONITOR_CONFIG.items():
        print(f"\n  ⏺ {process_name}")
        
        # 检查进程状态
        status = check_process_status(process_name)
        print(f"    进程状态: {status}")
        
        if status == 'not_found':
            issue = f"{process_name}: 进程不存在"
            issues.append(issue)
            print(f"    ❌ {issue}")
            continue
        
        if status != 'online':
            print(f"    ⚠️ 进程状态异常，尝试重启...")
            success, msg = restart_process(process_name)
            if success:
                fixed_issues.append(f"{process_name}: {msg}")
                print(f"    ✅ {msg}")
            else:
                issue = f"{process_name}: 状态={status}，重启失败 - {msg}"
                issues.append(issue)
                print(f"    ❌ {msg}")
            continue
        
        # 检查数据新鲜度
        is_fresh, msg = check_data_freshness(data_path, max_delay)
        print(f"    数据状态: {msg}")
        
        if not is_fresh:
            # 尝试重启
            if restart_counter.get(process_name, 0) < 3:  # 最多重启3次
                print(f"    ⚠️ 数据延迟，尝试重启...")
                success, restart_msg = restart_process(process_name)
                if success:
                    fixed_issues.append(f"{process_name}: 数据延迟，{restart_msg}")
                    print(f"    ✅ {restart_msg}")
                else:
                    issue = f"{process_name}: 数据延迟 - {msg}，重启失败 - {restart_msg}"
                    issues.append(issue)
                    print(f"    ❌ {restart_msg}")
            else:
                issue = f"{process_name}: 数据延迟 - {msg}，已重启3次仍失败"
                issues.append(issue)
                print(f"    ❌ 重启次数过多，需人工介入")
        else:
            print(f"    ✅ 正常")
            # 重置重启计数器
            if process_name in restart_counter:
                restart_counter[process_name] = 0
    
    # 3. 输出总结
    print(f"\n{'='*70}")
    print(f"📊 监控总结")
    print(f"{'='*70}")
    print(f"✅ 修复问题: {len(fixed_issues)} 个")
    for issue in fixed_issues:
        print(f"   • {issue}")
    
    print(f"\n❌ 未解决问题: {len(issues)} 个")
    for issue in issues:
        print(f"   • {issue}")
    
    # 4. 发送 Telegram 通知（仅未解决问题）
    if issues:
        message = f"<b>时间:</b> {beijing_now}\n\n"
        message += f"<b>❌ 未解决问题 ({len(issues)}):</b>\n"
        for issue in issues:
            message += f"• {issue}\n"
        
        if fixed_issues:
            message += f"\n<b>✅ 已修复 ({len(fixed_issues)}):</b>\n"
            for issue in fixed_issues[:3]:  # 只显示前3个
                message += f"• {issue}\n"
        
        send_telegram_notification(message)
    
    print(f"\n{'='*70}\n")

def main():
    """主循环"""
    print("🚀 系统健康监控器 V2.0 启动")
    print(f"监控间隔: 5 分钟")
    print(f"监控项目: {len(MONITOR_CONFIG) + 1} 个（Flask + {len(MONITOR_CONFIG)} 个采集器）")
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print(f"✅ Telegram 通知已启用")
    else:
        print(f"⚠️ Telegram 通知未配置")
    
    print(f"{'='*70}\n")
    
    while True:
        try:
            monitor_cycle()
            time.sleep(300)  # 5分钟检查一次
        
        except KeyboardInterrupt:
            print("\n⏹️ 监控器已停止")
            break
        
        except Exception as e:
            print(f"❌ 监控循环异常: {e}")
            time.sleep(60)

if __name__ == '__main__':
    main()
