#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAR Bias Trend 监控脚本
监控看多/看空点数变化，当有增加时发送 Telegram 通知
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Telegram 配置
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# 数据存储路径
STATE_FILE = Path(__file__).parent / "data" / "sar_bias_monitor_state.json"
HISTORY_FILE = Path(__file__).parent / "data" / "sar_bias_monitor_history.jsonl"

# API 端点
API_URL = "http://localhost:9002/api/sar-slope/bias-ratios"

# 监控阈值（偏多/偏空比例）
BULLISH_THRESHOLD = 80  # 看多阈值 >80%
BEARISH_THRESHOLD = 80  # 看空阈值 >80%


def send_telegram(message):
    """发送 Telegram 消息"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ [Telegram] 未配置Bot Token或Chat ID，跳过发送")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ [Telegram] 消息发送成功")
            return True
        else:
            print(f"❌ [Telegram] 发送失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ [Telegram] 发送异常: {str(e)}")
        return False


def load_state():
    """加载上次状态"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 读取状态文件失败: {e}")
    
    return {
        "last_bullish_count": 0,
        "last_bearish_count": 0,
        "last_check_time": None,
        "last_alert_time": None
    }


def save_state(state):
    """保存当前状态"""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存状态文件失败: {e}")


def save_history(record):
    """保存历史记录"""
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    except Exception as e:
        print(f"⚠️ 保存历史记录失败: {e}")


def get_sar_bias_data():
    """获取 SAR Bias 数据"""
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # 计算实际的看多/看空点数（>80% 的币种数量）
            bullish_count = len(data.get('bullish_symbols', []))
            bearish_count = len(data.get('bearish_symbols', []))
            # 添加计算后的值到返回数据
            data['bullish_count'] = bullish_count
            data['bearish_count'] = bearish_count
            return data
        else:
            print(f"❌ API 请求失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ API 请求异常: {e}")
        return None


def format_change_indicator(old_value, new_value):
    """格式化变化指示器"""
    if new_value > old_value:
        return f"📈 +{new_value - old_value}"
    elif new_value < old_value:
        return f"📉 {new_value - old_value}"
    else:
        return "➡️ 0"


def check_and_alert():
    """检查数据并在有变化时发送告警"""
    print(f"\n{'='*60}")
    print(f"🔍 SAR Bias Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # 加载上次状态
    state = load_state()
    last_bullish = state["last_bullish_count"]
    last_bearish = state["last_bearish_count"]
    
    # 获取当前数据
    data = get_sar_bias_data()
    if not data:
        print("❌ 无法获取数据，跳过本次检查")
        return
    
    current_bullish = data.get('bullish_count', 0)
    current_bearish = data.get('bearish_count', 0)
    total_count = data.get('total_count', 0)
    timestamp = data.get('timestamp', 'N/A')
    
    print(f"\n📊 当前数据:")
    print(f"   看多点数: {current_bullish} (上次: {last_bullish})")
    print(f"   看空点数: {current_bearish} (上次: {last_bearish})")
    print(f"   总币种数: {total_count}")
    print(f"   数据时间: {timestamp}")
    
    # 检查是否有变化
    bullish_changed = current_bullish != last_bullish
    bearish_changed = current_bearish != last_bearish
    
    if not bullish_changed and not bearish_changed:
        print("\n✅ 数据无变化，无需告警")
        state["last_check_time"] = datetime.now().isoformat()
        save_state(state)
        return
    
    # 计算比例
    bullish_ratio = (current_bullish / total_count * 100) if total_count > 0 else 0
    bearish_ratio = (current_bearish / total_count * 100) if total_count > 0 else 0
    
    # 构建告警消息
    message_parts = ["🚨 *SAR Bias Trend 数据变化提醒*\n"]
    
    if bullish_changed:
        change = format_change_indicator(last_bullish, current_bullish)
        status = "⚠️ 偏多" if bullish_ratio > BULLISH_THRESHOLD else ""
        bullish_symbols = data.get('bullish_symbols', [])
        symbol_list = ", ".join([f"{s['symbol']}({s['ratio']:.1f}%)" for s in bullish_symbols[:10]])  # 只显示前10个
        more_text = f"... 等{len(bullish_symbols)}个" if len(bullish_symbols) > 10 else ""
        message_parts.append(
            f"📈 *看多点数*: {current_bullish} {change}\n"
            f"   比例: {bullish_ratio:.1f}% {status}\n"
            f"   币种: {symbol_list}{more_text}" if bullish_symbols else f"📈 *看多点数*: {current_bullish} {change}\n   比例: {bullish_ratio:.1f}% {status}"
        )
    
    if bearish_changed:
        change = format_change_indicator(last_bearish, current_bearish)
        status = "⚠️ 偏空" if bearish_ratio > BEARISH_THRESHOLD else ""
        bearish_symbols = data.get('bearish_symbols', [])
        symbol_list = ", ".join([f"{s['symbol']}({s['ratio']:.1f}%)" for s in bearish_symbols[:10]])
        more_text = f"... 等{len(bearish_symbols)}个" if len(bearish_symbols) > 10 else ""
        if bullish_changed:
            message_parts.append("\n")
        message_parts.append(
            f"📉 *看空点数*: {current_bearish} {change}\n"
            f"   比例: {bearish_ratio:.1f}% {status}\n"
            f"   币种: {symbol_list}{more_text}" if bearish_symbols else f"📉 *看空点数*: {current_bearish} {change}\n   比例: {bearish_ratio:.1f}% {status}"
        )
    
    message_parts.extend([
        f"\n\n📊 总币种数: {total_count}",
        f"⏰ 数据时间: {timestamp}",
        f"\n🔗 查看详情: https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/sar-bias-trend"
    ])
    
    message = "".join(message_parts)
    
    print(f"\n📤 准备发送告警:")
    print(message.replace('*', '').replace('_', ''))
    
    # 发送 Telegram 消息
    if send_telegram(message):
        state["last_alert_time"] = datetime.now().isoformat()
        print("✅ 告警发送成功")
    else:
        print("❌ 告警发送失败")
    
    # 更新状态
    state["last_bullish_count"] = current_bullish
    state["last_bearish_count"] = current_bearish
    state["last_check_time"] = datetime.now().isoformat()
    save_state(state)
    
    # 保存历史记录
    history_record = {
        "timestamp": datetime.now().isoformat(),
        "data_timestamp": timestamp,
        "bullish_count": current_bullish,
        "bearish_count": current_bearish,
        "total_count": total_count,
        "bullish_ratio": bullish_ratio,
        "bearish_ratio": bearish_ratio,
        "bullish_changed": bullish_changed,
        "bearish_changed": bearish_changed,
        "alert_sent": True
    }
    save_history(history_record)
    
    print(f"\n{'='*60}")


def main():
    """主函数 - 持续运行模式"""
    print("🚀 SAR Bias Monitor 启动")
    print(f"监控阈值: 看多 >{BULLISH_THRESHOLD}%, 看空 >{BEARISH_THRESHOLD}%")
    print(f"API: {API_URL}")
    print(f"状态文件: {STATE_FILE}")
    print(f"历史文件: {HISTORY_FILE}")
    print(f"检查间隔: 5 分钟")
    
    # 检查 Telegram 配置
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\n⚠️ 警告: Telegram 未配置，将只打印日志不发送消息")
    
    print("\n🔄 进入监控循环...")
    
    # 持续运行，每5分钟检查一次
    while True:
        try:
            check_and_alert()
        except Exception as e:
            print(f"\n❌ 监控执行失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 等待5分钟
        print(f"\n⏰ 下次检查时间: {datetime.now() + timedelta(minutes=5)}")
        print("=" * 60)
        time.sleep(300)  # 300秒 = 5分钟


if __name__ == "__main__":
    main()
