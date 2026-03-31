#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5分钟涨速暴跌监控
监控最低涨速，当小于-30%时发送TG消息提醒"多头爆仓，低吸机会"
每次触发发送3条消息
"""

import json
import os
import sys
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path

# 项目根目录
BASE_DIR = Path('/home/user/webapp')
sys.path.insert(0, str(BASE_DIR))

# 数据目录
DATA_DIR = BASE_DIR / 'data'
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 监控记录目录
MONITOR_DIR = BASE_DIR / 'data' / 'five_min_speed_monitor'
MONITOR_DIR.mkdir(parents=True, exist_ok=True)

# Telegram配置
TELEGRAM_BOT_TOKEN = "8437045462:AAFePnwdC21cqeWhZISMQHGGgjmroVqE2H0"
TELEGRAM_CHAT_ID = "-1003227444260"

# 监控配置
CRASH_THRESHOLD = -30.0  # 5分钟涨速阈值（百分比）
CHECK_INTERVAL = 30  # 检查间隔（秒）
COOLDOWN_MINUTES = 30  # 冷却期（分钟）- 同一个低点30分钟内不重复报警

def send_telegram_message(message, repeat_count=3):
    """发送Telegram消息（重复指定次数）
    
    Args:
        message: 消息内容
        repeat_count: 重复发送次数（默认3次）
    
    Returns:
        成功发送的次数
    """
    success_count = 0
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    for i in range(repeat_count):
        try:
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                success_count += 1
                print(f"✅ Telegram消息第 {i+1}/{repeat_count} 次发送成功")
                time.sleep(0.5)  # 每条消息间隔0.5秒
            else:
                print(f"❌ Telegram消息第 {i+1}/{repeat_count} 次发送失败: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Telegram消息第 {i+1}/{repeat_count} 次发送异常: {e}")
    
    return success_count

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time

def get_latest_velocity_from_api():
    """从API获取最新的5分钟涨速数据
    
    Returns:
        dict: 包含current, min, max, avg的涨速数据
    """
    try:
        # 调用velocity-history API，只获取最新的几条数据
        response = requests.get('http://localhost:9002/api/coin-change-tracker/velocity-history?limit=50', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and data.get('data'):
                velocity_data = data.get('data', [])
                
                if len(velocity_data) > 0:
                    # 提取所有velocity_5min值
                    velocities = [item.get('velocity_5min') for item in velocity_data if item.get('velocity_5min') is not None]
                    
                    if velocities:
                        current_velocity = velocity_data[0].get('velocity_5min')  # 最新的值
                        min_velocity = min(velocities)
                        max_velocity = max(velocities)
                        avg_velocity = sum(velocities) / len(velocities)
                        
                        return {
                            'success': True,
                            'current': current_velocity,
                            'min': min_velocity,
                            'max': max_velocity,
                            'avg': avg_velocity,
                            'data_points': len(velocities),
                            'latest_time': velocity_data[0].get('beijing_time')
                        }
            
            return {'success': False, 'error': '无velocity数据'}
        else:
            return {'success': False, 'error': f'API返回错误: {response.status_code}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def load_alert_history():
    """加载报警历史记录"""
    history_file = MONITOR_DIR / 'alert_history.json'
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'alerts': []}
    return {'alerts': []}

def save_alert_history(history):
    """保存报警历史记录"""
    history_file = MONITOR_DIR / 'alert_history.json'
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ 保存报警历史失败: {e}")

def should_send_alert(current_time):
    """检查是否应该发送报警（冷却期检查）
    
    Args:
        current_time: 当前时间（datetime对象）
    
    Returns:
        bool: True表示可以发送，False表示在冷却期内
    """
    history = load_alert_history()
    alerts = history.get('alerts', [])
    
    # 检查最近的报警时间
    if alerts:
        last_alert_time_str = alerts[-1].get('time')
        if last_alert_time_str:
            try:
                last_alert_time = datetime.strptime(last_alert_time_str, '%Y-%m-%d %H:%M:%S')
                time_diff = (current_time - last_alert_time).total_seconds() / 60
                
                if time_diff < COOLDOWN_MINUTES:
                    print(f"⏳ 冷却期中，距离上次报警 {time_diff:.1f} 分钟（需要 {COOLDOWN_MINUTES} 分钟）")
                    return False
            except:
                pass
    
    return True

def record_alert(five_min_speed, beijing_time_str):
    """记录报警信息"""
    history = load_alert_history()
    
    alert_record = {
        'time': beijing_time_str,
        'five_min_speed': five_min_speed,
        'threshold': CRASH_THRESHOLD
    }
    
    history['alerts'].append(alert_record)
    
    # 只保留最近100条记录
    if len(history['alerts']) > 100:
        history['alerts'] = history['alerts'][-100:]
    
    save_alert_history(history)

def check_five_min_speed():
    """检查5分钟涨速并在需要时发送报警"""
    beijing_time = get_beijing_time()
    beijing_time_str = beijing_time.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"\n{'='*60}")
    print(f"🕐 检查时间: {beijing_time_str}")
    
    # 获取velocity数据
    velocity_result = get_latest_velocity_from_api()
    
    if not velocity_result.get('success'):
        print(f"⚠️ 获取velocity数据失败: {velocity_result.get('error', '未知错误')}")
        return
    
    current_speed = velocity_result.get('current')
    min_speed = velocity_result.get('min')
    max_speed = velocity_result.get('max')
    avg_speed = velocity_result.get('avg')
    data_points = velocity_result.get('data_points')
    latest_time = velocity_result.get('latest_time')
    
    print(f"📊 5分钟涨速数据（最近{data_points}个数据点）:")
    print(f"   最新时间: {latest_time}")
    print(f"   当前涨速: {current_speed:.2f}%")
    print(f"   最低涨速: {min_speed:.2f}%")
    print(f"   最高涨速: {max_speed:.2f}%")
    print(f"   平均涨速: {avg_speed:.2f}%")
    
    # 检查最低涨速是否触发阈值
    if min_speed < CRASH_THRESHOLD:
        print(f"🚨 触发报警！最低涨速 {min_speed:.2f}% < 阈值 {CRASH_THRESHOLD}%")
        
        # 检查冷却期
        if not should_send_alert(beijing_time):
            print("⏳ 在冷却期内，不发送报警")
            return
        
        # 构造消息
        message = f"""🚨 <b>多头爆仓，低吸机会！</b> 🚨

📉 <b>5分钟涨速暴跌</b>
━━━━━━━━━━━━━━━━━━━
📊 <b>最低涨速</b>: {min_speed:.2f}%
📊 <b>当前涨速</b>: {current_speed:.2f}%
📊 <b>平均涨速</b>: {avg_speed:.2f}%
📊 <b>最高涨速</b>: {max_speed:.2f}%

⚠️ <b>阈值</b>: {CRASH_THRESHOLD}%
🕐 <b>检查时间</b>: {beijing_time_str}
🕐 <b>数据时间</b>: {latest_time}
📈 <b>数据点数</b>: {data_points}

💡 <b>建议</b>: 多头大量爆仓，考虑低吸机会
━━━━━━━━━━━━━━━━━━━
🤖 5分钟涨速监控系统"""
        
        # 发送3条消息
        print(f"📤 开始发送Telegram报警消息（共3条）...")
        success_count = send_telegram_message(message, repeat_count=3)
        
        if success_count > 0:
            print(f"✅ 成功发送 {success_count}/3 条消息")
            # 记录报警
            record_alert(min_speed, beijing_time_str)
        else:
            print("❌ 所有消息发送失败")
    else:
        print(f"✅ 正常范围内（最低涨速 {min_speed:.2f}% >= 阈值 {CRASH_THRESHOLD}%）")

def main():
    """主循环"""
    print("="*60)
    print("🚀 5分钟涨速暴跌监控启动")
    print(f"📍 监控阈值: {CRASH_THRESHOLD}%")
    print(f"⏱️  检查间隔: {CHECK_INTERVAL}秒")
    print(f"⏳ 冷却期: {COOLDOWN_MINUTES}分钟")
    print(f"📂 数据目录: {MONITOR_DIR}")
    print("="*60)
    
    while True:
        try:
            check_five_min_speed()
        except Exception as e:
            print(f"❌ 检查过程出错: {e}")
            import traceback
            traceback.print_exc()
        
        # 等待下次检查
        print(f"⏰ 等待 {CHECK_INTERVAL} 秒后进行下次检查...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 监控已停止")
    except Exception as e:
        print(f"❌ 程序异常退出: {e}")
        import traceback
        traceback.print_exc()
