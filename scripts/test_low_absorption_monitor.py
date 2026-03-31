#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
低吸信号监控系统测试脚本
用于验证系统是否正常工作，并查看最近的监控数据
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def check_pm2_status():
    """检查 PM2 进程状态"""
    print_header("🔍 PM2 进程状态检查")
    
    import subprocess
    try:
        result = subprocess.run(
            ['pm2', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if 'low-absorption-monitor' in result.stdout:
            print("✅ PM2 进程正在运行")
            
            # 提取进程信息
            for line in result.stdout.split('\n'):
                if 'low-absorption-monitor' in line:
                    print(f"   {line}")
        else:
            print("❌ PM2 进程未运行")
            print("   提示：使用 'pm2 start scripts/low_absorption_monitor.py --name low-absorption-monitor --interpreter python3' 启动")
    
    except subprocess.TimeoutExpired:
        print("⚠️  PM2 命令超时")
    except FileNotFoundError:
        print("❌ PM2 未安装")
        print("   提示：使用 'npm install -g pm2' 安装")
    except Exception as e:
        print(f"❌ 检查失败: {e}")

def check_state_file():
    """检查状态文件"""
    print_header("📊 状态文件检查")
    
    state_file = Path('/home/user/webapp/data/low_absorption_monitor/state.json')
    
    if state_file.exists():
        print(f"✅ 状态文件存在: {state_file}")
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            print(f"\n📅 最后检查日期: {state.get('last_check_date', 'N/A')}")
            print(f"⏰ 最后信号发送: {state.get('last_signal_sent', 'N/A')}")
            
            check_points = state.get('check_points', {})
            if check_points:
                print(f"\n📈 最近检查点数据:")
                for time_point, data in check_points.items():
                    ratio = data.get('ratio', 0)
                    is_green = data.get('is_green', False)
                    color = "🟢 绿色" if is_green else "🔴 红色"
                    print(f"   {time_point}: {ratio:.2f}% - {color}")
            
        except Exception as e:
            print(f"❌ 读取状态文件失败: {e}")
    else:
        print(f"⚠️  状态文件不存在: {state_file}")
        print("   提示：系统首次运行后会创建此文件")

def check_history_file():
    """检查历史记录文件"""
    print_header("📜 历史记录检查")
    
    history_file = Path('/home/user/webapp/data/low_absorption_monitor/history.jsonl')
    
    if history_file.exists():
        print(f"✅ 历史文件存在: {history_file}")
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"\n📊 总记录数: {len(lines)}")
            
            if lines:
                print(f"\n📈 最近 3 条记录:")
                for i, line in enumerate(lines[-3:], 1):
                    try:
                        record = json.loads(line.strip())
                        time = record.get('time', 'N/A')
                        signal = record.get('signal', 'N/A')
                        status = record.get('status', {})
                        positive_ratio = status.get('positive_ratio', 0)
                        
                        print(f"\n   {i}. 时间: {time}")
                        print(f"      信号: {signal}")
                        print(f"      正数占比: {positive_ratio:.2f}%")
                        
                        ratios = record.get('ratios', [])
                        if ratios:
                            print(f"      数据点:")
                            for r in ratios:
                                time_point = r.get('time', 'N/A')
                                ratio = r.get('ratio', 0)
                                is_green = r.get('is_green', False)
                                color = "🟢" if is_green else "🔴"
                                print(f"         {time_point}: {ratio:.2f}% {color}")
                    
                    except json.JSONDecodeError:
                        print(f"   {i}. ❌ 无效记录")
        
        except Exception as e:
            print(f"❌ 读取历史文件失败: {e}")
    else:
        print(f"⚠️  历史文件不存在: {history_file}")
        print("   提示：系统发送第一次信号后会创建此文件")

def check_telegram_config():
    """检查 Telegram 配置"""
    print_header("📱 Telegram 配置检查")
    
    config_file = Path('/home/user/webapp/config/configs/telegram_config.json')
    
    if config_file.exists():
        print(f"✅ 配置文件存在: {config_file}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            bot_token = config.get('bot_token', '')
            chat_id = config.get('chat_id', '')
            
            if bot_token:
                print(f"✅ Bot Token: {bot_token[:10]}...{bot_token[-10:]}")
            else:
                print(f"❌ Bot Token 未配置")
            
            if chat_id:
                print(f"✅ Chat ID: {chat_id}")
            else:
                print(f"❌ Chat ID 未配置")
        
        except Exception as e:
            print(f"❌ 读取配置文件失败: {e}")
    else:
        print(f"❌ 配置文件不存在: {config_file}")
        print("   提示：请确保 Telegram 配置文件存在")

def check_data_files():
    """检查数据文件"""
    print_header("💾 数据文件检查")
    
    beijing_tz = timezone(timedelta(hours=8))
    today = datetime.now(beijing_tz)
    date_str = today.strftime('%Y%m%d')
    
    data_file = Path(f'/home/user/webapp/data/coin_change_tracker/coin_change_{date_str}.jsonl')
    
    if data_file.exists():
        print(f"✅ 今日数据文件存在: {data_file}")
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"\n📊 总记录数: {len(lines)}")
            
            if lines:
                # 最早和最晚记录
                first = json.loads(lines[0].strip())
                last = json.loads(lines[-1].strip())
                
                print(f"\n⏰ 最早记录: {first.get('beijing_time', 'N/A')}")
                print(f"   上涨占比: {first.get('up_ratio', 0):.2f}%")
                
                print(f"\n⏰ 最新记录: {last.get('beijing_time', 'N/A')}")
                print(f"   上涨占比: {last.get('up_ratio', 0):.2f}%")
                
                # 检查凌晨2点的数据
                print(f"\n🔍 检查凌晨 2:00-3:00 的数据:")
                count = 0
                for line in lines:
                    try:
                        record = json.loads(line.strip())
                        beijing_time = record.get('beijing_time', '')
                        if beijing_time.startswith(f'{today.year:04d}-{today.month:02d}-{today.day:02d} 02:'):
                            up_ratio = record.get('up_ratio', 0)
                            color = "🟢" if up_ratio > 55 else "🔴"
                            print(f"   {beijing_time}: {up_ratio:.2f}% {color}")
                            count += 1
                            if count >= 5:
                                print(f"   ... (共 {count} 条记录)")
                                break
                    except:
                        pass
                
                if count == 0:
                    print(f"   ⚠️  未找到凌晨 2 点的数据")
        
        except Exception as e:
            print(f"❌ 读取数据文件失败: {e}")
    else:
        print(f"❌ 今日数据文件不存在: {data_file}")
        print("   提示：请确保 coin-change-tracker 采集器正在运行")

def check_api_status():
    """检查 API 状态"""
    print_header("🌐 API 状态检查")
    
    import requests
    
    api_url = "http://localhost:9002/api/coin-change-tracker/positive-ratio-stats"
    
    try:
        response = requests.get(api_url, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ API 正常: {api_url}")
            
            data = response.json()
            if data.get('success'):
                stats = data.get('stats', {})
                positive_ratio = stats.get('positive_ratio', 0)
                date = stats.get('date', 'N/A')
                positive_count = stats.get('positive_count', 0)
                total_count = stats.get('total_count', 0)
                
                status = "低吸" if positive_ratio < 40 else "高抛"
                
                print(f"\n📊 当前数据:")
                print(f"   日期: {date}")
                print(f"   正数占比: {positive_ratio:.2f}% ({status})")
                print(f"   正数币种: {positive_count}/{total_count}")
            else:
                print(f"❌ API 返回失败: {data}")
        else:
            print(f"❌ API 请求失败: HTTP {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到 API: {api_url}")
        print("   提示：请确保 Flask 应用正在运行")
    except requests.exceptions.Timeout:
        print(f"❌ API 请求超时")
    except Exception as e:
        print(f"❌ 检查失败: {e}")

def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("  🧪 低吸信号监控系统 - 系统测试")
    print("=" * 80)
    print("\n运行时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # 执行各项检查
    check_pm2_status()
    check_api_status()
    check_state_file()
    check_history_file()
    check_telegram_config()
    check_data_files()
    
    print("\n" + "=" * 80)
    print("  ✅ 测试完成")
    print("=" * 80)
    print("\n💡 提示:")
    print("   - 如果发现问题，请参考 LOW_ABSORPTION_MONITOR_GUIDE.md")
    print("   - 查看实时日志: pm2 logs low-absorption-monitor")
    print("   - 重启监控: pm2 restart low-absorption-monitor")
    print()

if __name__ == '__main__':
    main()
