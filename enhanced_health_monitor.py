#!/usr/bin/env python3
"""
Enhanced Data Health Monitor - 增强型数据健康监控器
功能：
1. 监控所有采集器和数据文件的健康状态
2. 自动修复常见问题（重启进程、清理数据等）
3. Telegram 通知无法自动修复的问题
"""
import os
import sys
import time
import json
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import pytz
import requests

# 添加项目路径
sys.path.insert(0, '/home/user/webapp/source_code')

# 配置
BEIJING_TZ = pytz.timezone('Asia/Shanghai')
DATA_DIR = Path('/home/user/webapp/data')
DB_PATH = Path('/home/user/webapp/crypto_monitor.db')
CHECK_INTERVAL = 180  # 检查间隔（秒）- 3分钟

# Telegram 配置（从环境变量读取）
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

# 需要监控的PM2进程列表
MONITORED_PROCESSES = [
    'flask-app',
    'signal-collector',
    'price-speed-collector',
    'sar-slope-collector',
    'sar-bias-stats-collector',
    'price-comparison-collector',
    'financial-indicators-collector',
    'okx-day-change-collector',
    'price-baseline-collector',
    'panic-wash-collector',
    'liquidation-1h-collector',
    'crypto-index-collector',
    'v1v2-collector',
    'liquidation-alert-monitor',
    'system-health-monitor',
    'coin-change-tracker',
    'dashboard-jsonl-manager',
    'gdrive-jsonl-manager',
    'okx-trade-history-collector',
    'okx-trading-marks-collector',
    'price-position-collector'
]

# 需要监控的数据表
MONITORED_TABLES = {
    'signal_timeline': {'max_delay_minutes': 10, 'description': '信号时间线'},
    'price_speed_10m': {'max_delay_minutes': 10, 'description': '10分钟涨速'},
    'sar_slope_data': {'max_delay_minutes': 10, 'description': 'SAR斜率数据'},
    'price_comparison': {'max_delay_minutes': 30, 'description': '价格对比'},
    'panic_wash_data': {'max_delay_minutes': 30, 'description': '恐慌洗盘数据'},
    'liquidation_1h': {'max_delay_minutes': 120, 'description': '1小时清算数据'},
}

# 需要监控的JSONL文件（按日期分割）
MONITORED_JSONL_DIRS = {
    'sar_bias_stats': {'max_delay_minutes': 10, 'description': 'SAR偏向统计'},
    'price_speed_10m': {'max_delay_minutes': 10, 'description': '10分钟涨速JSONL'},
    'signal_stats': {'max_delay_minutes': 10, 'description': '信号统计'},
}


class HealthMonitor:
    def __init__(self):
        self.issues = []
        self.auto_fixed = []
        self.cannot_fix = []
        
    def send_telegram(self, message):
        """发送Telegram通知"""
        if not TELEGRAM_ENABLED:
            print(f"[Telegram] 未配置，跳过通知: {message}")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"[Telegram] ✅ 通知发送成功")
                return True
            else:
                print(f"[Telegram] ❌ 通知发送失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"[Telegram] ❌ 发送异常: {e}")
            return False
    
    def check_pm2_processes(self):
        """检查PM2进程状态"""
        print("\n" + "="*60)
        print("📋 检查 PM2 进程状态")
        print("="*60)
        
        try:
            result = subprocess.run(['pm2', 'jlist'], capture_output=True, text=True)
            if result.returncode != 0:
                issue = "⚠️ PM2 命令执行失败"
                self.issues.append(issue)
                self.cannot_fix.append(issue)
                return
            
            processes = json.loads(result.stdout)
            
            for proc_name in MONITORED_PROCESSES:
                proc = next((p for p in processes if p['name'] == proc_name), None)
                
                if not proc:
                    issue = f"❌ 进程不存在: {proc_name}"
                    print(issue)
                    self.issues.append(issue)
                    self.cannot_fix.append(f"进程 {proc_name} 未在PM2中配置")
                    continue
                
                status = proc['pm2_env']['status']
                
                if status != 'online':
                    issue = f"⚠️ 进程状态异常: {proc_name} ({status})"
                    print(issue)
                    self.issues.append(issue)
                    
                    # 尝试自动重启
                    try:
                        print(f"   🔧 尝试重启进程: {proc_name}")
                        restart_result = subprocess.run(
                            ['pm2', 'restart', proc_name],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        
                        if restart_result.returncode == 0:
                            fix_msg = f"✅ 成功重启进程: {proc_name}"
                            print(f"   {fix_msg}")
                            self.auto_fixed.append(fix_msg)
                        else:
                            fail_msg = f"重启失败: {proc_name} - {restart_result.stderr}"
                            self.cannot_fix.append(fail_msg)
                            
                    except Exception as e:
                        fail_msg = f"重启异常: {proc_name} - {str(e)}"
                        print(f"   ❌ {fail_msg}")
                        self.cannot_fix.append(fail_msg)
                else:
                    print(f"✅ {proc_name}: 正常运行")
                    
        except Exception as e:
            issue = f"⚠️ PM2检查异常: {str(e)}"
            print(issue)
            self.issues.append(issue)
            self.cannot_fix.append(issue)
    
    def check_database_tables(self):
        """检查数据库表的数据新鲜度"""
        print("\n" + "="*60)
        print("📊 检查数据库表数据新鲜度")
        print("="*60)
        
        if not DB_PATH.exists():
            issue = "❌ 数据库文件不存在"
            print(issue)
            self.issues.append(issue)
            self.cannot_fix.append(issue)
            return
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            for table_name, config in MONITORED_TABLES.items():
                try:
                    # 检查表是否存在
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (table_name,)
                    )
                    if not cursor.fetchone():
                        issue = f"⚠️ 表不存在: {table_name}"
                        print(issue)
                        self.issues.append(issue)
                        self.cannot_fix.append(f"数据库表 {table_name} 不存在")
                        continue
                    
                    # 获取最新数据的时间戳
                    cursor.execute(f"SELECT MAX(timestamp) FROM {table_name}")
                    result = cursor.fetchone()
                    
                    if not result or not result[0]:
                        issue = f"⚠️ 表中无数据: {table_name}"
                        print(issue)
                        self.issues.append(issue)
                        self.cannot_fix.append(f"表 {table_name} ({config['description']}) 中无数据")
                        continue
                    
                    # 转换时间戳
                    last_timestamp = result[0]
                    if last_timestamp > 1e12:  # 毫秒级时间戳
                        last_timestamp = last_timestamp / 1000
                    
                    last_time = datetime.fromtimestamp(last_timestamp, tz=BEIJING_TZ)
                    now = datetime.now(BEIJING_TZ)
                    delay_minutes = (now - last_time).total_seconds() / 60
                    
                    max_delay = config['max_delay_minutes']
                    
                    if delay_minutes > max_delay:
                        issue = f"⚠️ 数据延迟: {table_name} ({config['description']}) - 延迟 {int(delay_minutes)} 分钟（最大允许 {max_delay} 分钟）"
                        print(issue)
                        self.issues.append(issue)
                        self.cannot_fix.append(f"表 {table_name} 数据延迟 {int(delay_minutes)} 分钟，需检查对应采集器")
                    else:
                        print(f"✅ {table_name} ({config['description']}): 数据正常，延迟 {int(delay_minutes)} 分钟")
                        
                except sqlite3.Error as e:
                    issue = f"⚠️ 查询失败: {table_name} - {str(e)}"
                    print(issue)
                    self.issues.append(issue)
                    self.cannot_fix.append(issue)
            
            conn.close()
            
        except Exception as e:
            issue = f"⚠️ 数据库检查异常: {str(e)}"
            print(issue)
            self.issues.append(issue)
            self.cannot_fix.append(issue)
    
    def check_jsonl_files(self):
        """检查JSONL文件的数据新鲜度"""
        print("\n" + "="*60)
        print("📄 检查 JSONL 文件数据新鲜度")
        print("="*60)
        
        today = datetime.now(BEIJING_TZ).strftime('%Y%m%d')
        
        for dir_name, config in MONITORED_JSONL_DIRS.items():
            dir_path = DATA_DIR / dir_name
            
            if not dir_path.exists():
                issue = f"⚠️ 目录不存在: {dir_name}"
                print(issue)
                self.issues.append(issue)
                self.cannot_fix.append(f"JSONL目录 {dir_name} 不存在")
                continue
            
            # 查找今日的JSONL文件
            today_files = list(dir_path.glob(f"*{today}*.jsonl"))
            
            if not today_files:
                issue = f"⚠️ 今日文件不存在: {dir_name}"
                print(issue)
                self.issues.append(issue)
                self.cannot_fix.append(f"{config['description']} 今日JSONL文件不存在")
                continue
            
            # 检查最新文件的修改时间
            latest_file = max(today_files, key=lambda f: f.stat().st_mtime)
            last_modified = datetime.fromtimestamp(latest_file.stat().st_mtime, tz=BEIJING_TZ)
            now = datetime.now(BEIJING_TZ)
            delay_minutes = (now - last_modified).total_seconds() / 60
            
            max_delay = config['max_delay_minutes']
            
            if delay_minutes > max_delay:
                issue = f"⚠️ 文件未更新: {dir_name}/{latest_file.name} - 延迟 {int(delay_minutes)} 分钟（最大允许 {max_delay} 分钟）"
                print(issue)
                self.issues.append(issue)
                self.cannot_fix.append(f"{config['description']} JSONL文件 {int(delay_minutes)} 分钟未更新，需检查对应采集器")
            else:
                print(f"✅ {dir_name} ({config['description']}): 文件正常，最后更新 {int(delay_minutes)} 分钟前")
    
    def check_flask_app(self):
        """检查Flask应用是否正常响应"""
        print("\n" + "="*60)
        print("🌐 检查 Flask 应用响应")
        print("="*60)
        
        try:
            response = requests.get('http://localhost:9002/api/data-health-monitor/status', timeout=10)
            
            if response.status_code == 200:
                print("✅ Flask应用响应正常")
            else:
                issue = f"⚠️ Flask应用响应异常: HTTP {response.status_code}"
                print(issue)
                self.issues.append(issue)
                
                # 尝试重启Flask应用
                try:
                    print("   🔧 尝试重启 Flask 应用")
                    subprocess.run(['pm2', 'restart', 'flask-app'], timeout=30)
                    time.sleep(5)
                    
                    # 再次检查
                    retry_response = requests.get('http://localhost:9002/api/data-health-monitor/status', timeout=10)
                    if retry_response.status_code == 200:
                        fix_msg = "✅ Flask应用重启成功"
                        print(f"   {fix_msg}")
                        self.auto_fixed.append(fix_msg)
                    else:
                        fail_msg = f"Flask应用重启后仍然异常: HTTP {retry_response.status_code}"
                        self.cannot_fix.append(fail_msg)
                        
                except Exception as e:
                    fail_msg = f"Flask应用重启失败: {str(e)}"
                    print(f"   ❌ {fail_msg}")
                    self.cannot_fix.append(fail_msg)
                    
        except requests.RequestException as e:
            issue = f"⚠️ Flask应用无法连接: {str(e)}"
            print(issue)
            self.issues.append(issue)
            self.cannot_fix.append(issue)
    
    def run_check(self):
        """执行完整的健康检查"""
        print("\n" + "🔍"*30)
        print(f"开始健康检查 - {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
        print("🔍"*30)
        
        self.issues = []
        self.auto_fixed = []
        self.cannot_fix = []
        
        # 执行各项检查
        self.check_pm2_processes()
        self.check_database_tables()
        self.check_jsonl_files()
        self.check_flask_app()
        
        # 汇总结果
        print("\n" + "="*60)
        print("📊 健康检查汇总")
        print("="*60)
        print(f"🔍 发现问题: {len(self.issues)} 个")
        print(f"✅ 自动修复: {len(self.auto_fixed)} 个")
        print(f"⚠️ 无法修复: {len(self.cannot_fix)} 个")
        
        # 发送Telegram通知（仅当有无法修复的问题时）
        if self.cannot_fix:
            print("\n⚠️ 发现无法自动修复的问题，准备发送Telegram通知...")
            
            message = f"🚨 <b>数据健康监控告警</b>\n\n"
            message += f"🕐 时间: {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"⚠️ 无法自动修复的问题 ({len(self.cannot_fix)} 个):\n\n"
            
            for i, issue in enumerate(self.cannot_fix, 1):
                message += f"{i}. {issue}\n"
            
            if self.auto_fixed:
                message += f"\n✅ 已自动修复 ({len(self.auto_fixed)} 个):\n"
                for i, fix in enumerate(self.auto_fixed, 1):
                    message += f"{i}. {fix}\n"
            
            self.send_telegram(message)
        
        elif self.auto_fixed:
            print("\n✅ 所有问题已自动修复，无需人工干预")
        
        else:
            print("\n✅ 系统健康，所有检查通过")
        
        print("\n" + "="*60 + "\n")


def main():
    """主函数"""
    print("="*60)
    print("🏥 Enhanced Data Health Monitor 启动")
    print("="*60)
    print(f"📅 启动时间: {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  检查间隔: {CHECK_INTERVAL} 秒")
    print(f"📱 Telegram通知: {'✅ 已启用' if TELEGRAM_ENABLED else '❌ 未启用'}")
    
    if not TELEGRAM_ENABLED:
        print("\n⚠️ Telegram通知未启用")
        print("请设置环境变量:")
        print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("  export TELEGRAM_CHAT_ID='your_chat_id'")
    
    print("="*60 + "\n")
    
    monitor = HealthMonitor()
    
    while True:
        try:
            monitor.run_check()
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n⚠️ 收到退出信号，监控器停止")
            break
            
        except Exception as e:
            print(f"\n❌ 监控异常: {str(e)}")
            print("等待10秒后重试...")
            time.sleep(10)


if __name__ == '__main__':
    main()
