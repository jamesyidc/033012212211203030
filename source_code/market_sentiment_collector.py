#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场情绪偏向采集器
每15分钟统计一次，比较RSI变化与27币涨跌幅变化
判断市场情绪是偏多还是偏空
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import time
import requests

# 项目根目录
BASE_DIR = Path('/home/user/webapp')
DATA_DIR = BASE_DIR / 'data' / 'market_sentiment'
COIN_CHANGE_DIR = BASE_DIR / 'data' / 'coin_change_tracker'

# 确保数据目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 🔴 Telegram配置（硬编码）
TELEGRAM_BOT_TOKEN = "8437045462:AAFePnwdC21cqeWhZISMQHGGgjmroVqE2H0"
TELEGRAM_CHAT_ID = "-1003227444260"

def get_today_file(data_type):
    """获取今天的数据文件路径"""
    today = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d')
    if data_type == 'coin_change':
        return COIN_CHANGE_DIR / f'coin_change_{today}.jsonl'
    elif data_type == 'rsi':
        return COIN_CHANGE_DIR / f'rsi_{today}.jsonl'
    elif data_type == 'sentiment':
        return DATA_DIR / f'market_sentiment_{today}.jsonl'

def read_latest_records(file_path, n=2):
    """读取最近N条记录"""
    if not file_path.exists():
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        return [json.loads(line) for line in lines[-n:] if line.strip()]

def send_telegram_notification(message, repeat=3):
    """
    发送Telegram通知
    @param message: 消息内容
    @param repeat: 重复发送次数（默认3次）
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram配置未设置，跳过通知")
        return False
    
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    success_count = 0
    
    for i in range(repeat):
        try:
            response = requests.post(url, json={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }, timeout=10)
            
            if response.status_code == 200:
                success_count += 1
                print(f"✅ Telegram通知发送成功 ({i+1}/{repeat})")
            else:
                print(f"❌ Telegram通知发送失败 ({i+1}/{repeat}): {response.text}")
            
            # 间隔1秒再发送下一条
            if i < repeat - 1:
                time.sleep(1)
                
        except Exception as e:
            print(f"❌ Telegram通知异常 ({i+1}/{repeat}): {e}")
    
    return success_count > 0

def calculate_sentiment():
    """计算市场情绪偏向"""
    try:
        # 读取最近2条coin_change记录（用于计算27币涨跌幅变化）
        coin_change_file = get_today_file('coin_change')
        coin_changes = read_latest_records(coin_change_file, 2)
        
        # 读取最近2条RSI记录
        rsi_file = get_today_file('rsi')
        rsi_records = read_latest_records(rsi_file, 2)
        
        if len(coin_changes) < 2 or len(rsi_records) < 2:
            print(f"⚠️  数据不足: coin_change={len(coin_changes)}, rsi={len(rsi_records)}")
            return None
        
        # 获取当前和上一次的数据
        prev_coin = coin_changes[0]
        curr_coin = coin_changes[1]
        prev_rsi = rsi_records[0]
        curr_rsi = rsi_records[1]
        
        # 计算27币累计涨跌幅变化
        prev_total_change = prev_coin.get('cumulative_pct', 0)  # 之前的累计涨跌幅
        curr_total_change = curr_coin.get('cumulative_pct', 0)  # 当前的累计涨跌幅
        coin_change_delta = curr_total_change - prev_total_change  # 涨跌幅变化量
        
        # 计算RSI总和变化
        prev_total_rsi = prev_rsi.get('total_rsi', 0)
        curr_total_rsi = curr_rsi.get('total_rsi', 0)
        rsi_change_delta = curr_total_rsi - prev_total_rsi  # RSI变化量
        
        # 计算变化百分比（相对于前一次的值）
        if prev_total_change != 0:
            coin_change_pct = (coin_change_delta / abs(prev_total_change)) * 100
        else:
            coin_change_pct = 0
        
        if prev_total_rsi != 0:
            rsi_change_pct = (rsi_change_delta / prev_total_rsi) * 100
        else:
            rsi_change_pct = 0
        
        # 判断市场情绪（基于倍数关系）
        sentiment = "中性"
        sentiment_type = "neutral"
        reason = ""
        
        # 计算倍数关系（避免除零）
        if abs(coin_change_pct) > 0.01:  # 币价变化大于0.01%才计算倍数
            ratio = abs(rsi_change_pct) / abs(coin_change_pct)
        else:
            ratio = 1.0
        
        # 下跌行情判断（币价累计涨跌幅变化为负）
        if coin_change_delta < 0:
            # 市场下跌
            if rsi_change_delta < 0:
                # RSI也下跌（同向）
                if ratio >= 10 and curr_total_rsi < 700:
                    # RSI降幅远大于币价跌幅（10倍以上）且 RSI总和<700 → 阶段性底部
                    sentiment = "🔥见底信号"
                    sentiment_type = "bullish"
                    reason = f"下跌中RSI降幅({abs(rsi_change_pct):.2f}%) 是币价跌幅({abs(coin_change_pct):.2f}%)的{ratio:.1f}倍，恐慌过度，阶段性底部★★★（RSI总和{curr_total_rsi:.2f}<700）"
                    
                    # 🔴 发送TG通知（3遍）
                    beijing_time = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
                    tg_message = (
                        f"🔥🔥🔥 <b>见底信号</b> 🔥🔥🔥\n\n"
                        f"⏰ 时间: {beijing_time}\n\n"
                        f"📊 市场情况:\n"
                        f"• 27币累计涨跌幅: {curr_total_change:.2f}%\n"
                        f"• 涨跌幅变化: {coin_change_delta:.2f}% ({coin_change_pct:+.2f}%)\n\n"
                        f"📈 RSI情况:\n"
                        f"• RSI总和: {curr_total_rsi:.2f}\n"
                        f"• RSI变化: {rsi_change_delta:.2f} ({rsi_change_pct:+.2f}%)\n\n"
                        f"💡 分析:\n"
                        f"{reason}\n\n"
                        f"🎯 <b>操作建议: 考虑逢低做多</b>"
                    )
                    send_telegram_notification(tg_message, repeat=3)
                    
                elif ratio >= 1.5:
                    # RSI降幅 > 币价跌幅（1.5倍以上）→ 恐慌过度
                    sentiment = "偏多"
                    sentiment_type = "bullish"
                    reason = f"下跌中RSI降幅({abs(rsi_change_pct):.2f}%) > 币价跌幅({abs(coin_change_pct):.2f}%)，恐慌过度★★"
                else:
                    # RSI降幅 < 币价跌幅 → 还会继续跌
                    sentiment = "偏空"
                    sentiment_type = "bearish"
                    reason = f"下跌中RSI降幅({abs(rsi_change_pct):.2f}%) < 币价跌幅({abs(coin_change_pct):.2f}%)，继续下跌★"
            else:
                # RSI上涨但币价下跌（背离）→ 强烈底部信号
                sentiment = "🚀底部背离"
                sentiment_type = "bullish"
                reason = f"下跌中RSI反涨({abs(rsi_change_pct):.2f}%)，底部背离信号★★★"
        
        # 上涨行情判断（币价累计涨跌幅变化为正）
        elif coin_change_delta > 0:
            # 市场上涨
            if rsi_change_delta > 0:
                # RSI也上涨（同向）
                if ratio >= 10:
                    # RSI涨幅远大于币价涨幅（10倍以上）→ 见顶信号
                    sentiment = "⚠️见顶信号"
                    sentiment_type = "bearish"
                    reason = f"上涨中RSI涨幅({abs(rsi_change_pct):.2f}%) 是币价涨幅({abs(coin_change_pct):.2f}%)的{ratio:.1f}倍，贪婪过度★★★"
                    
                    # 🔴 发送TG通知（3遍）
                    beijing_time = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
                    tg_message = (
                        f"⚠️⚠️⚠️ <b>见顶信号</b> ⚠️⚠️⚠️\n\n"
                        f"⏰ 时间: {beijing_time}\n\n"
                        f"📊 市场情况:\n"
                        f"• 27币累计涨跌幅: {curr_total_change:.2f}%\n"
                        f"• 涨跌幅变化: {coin_change_delta:.2f}% ({coin_change_pct:+.2f}%)\n\n"
                        f"📈 RSI情况:\n"
                        f"• RSI总和: {curr_total_rsi:.2f}\n"
                        f"• RSI变化: {rsi_change_delta:.2f} ({rsi_change_pct:+.2f}%)\n\n"
                        f"💡 分析:\n"
                        f"{reason}\n\n"
                        f"🎯 <b>操作建议: 考虑减仓或止盈</b>"
                    )
                    send_telegram_notification(tg_message, repeat=3)
                    
                elif ratio >= 1.5:
                    # RSI涨幅 > 币价涨幅（1.5倍以上）→ 贪婪过度
                    sentiment = "偏空"
                    sentiment_type = "bearish"
                    reason = f"上涨中RSI涨幅({abs(rsi_change_pct):.2f}%) > 币价涨幅({abs(coin_change_pct):.2f}%)，贪婪过度★★"
                else:
                    # RSI涨幅 < 币价涨幅 → 还能继续涨
                    sentiment = "偏多"
                    sentiment_type = "bullish"
                    reason = f"上涨中RSI涨幅({abs(rsi_change_pct):.2f}%) < 币价涨幅({abs(coin_change_pct):.2f}%)，理性上涨★"
            else:
                # RSI下跌但币价上涨（背离）→ 顶部信号
                sentiment = "⛔顶部背离"
                sentiment_type = "bearish"
                reason = f"上涨中RSI反跌({abs(rsi_change_pct):.2f}%)，顶部背离信号★★★"
        else:
            sentiment = "中性"
            sentiment_type = "neutral"
            reason = "市场无明显变化"
        
        # 构建结果
        result = {
            'timestamp': int(time.time() * 1000),
            'beijing_time': datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S'),
            
            # 27币涨跌幅数据
            'coin_data': {
                'prev_cumulative_pct': round(prev_total_change, 2),
                'curr_cumulative_pct': round(curr_total_change, 2),
                'change_delta': round(coin_change_delta, 2),
                'change_pct': round(coin_change_pct, 2),
            },
            
            # RSI数据
            'rsi_data': {
                'prev_total_rsi': round(prev_total_rsi, 2),
                'curr_total_rsi': round(curr_total_rsi, 2),
                'change_delta': round(rsi_change_delta, 2),
                'change_pct': round(rsi_change_pct, 2),
            },
            
            # 市场情绪判断
            'sentiment': sentiment,
            'sentiment_type': sentiment_type,
            'reason': reason,
            
            # 原始时间戳（用于排查）
            'source_timestamps': {
                'coin_change_prev': prev_coin.get('beijing_time'),
                'coin_change_curr': curr_coin.get('beijing_time'),
                'rsi_prev': prev_rsi.get('beijing_time'),
                'rsi_curr': curr_rsi.get('beijing_time'),
            }
        }
        
        return result
        
    except Exception as e:
        print(f"❌ 计算市场情绪失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_sentiment(data):
    """保存市场情绪数据到JSONL"""
    if not data:
        return False
    
    sentiment_file = get_today_file('sentiment')
    
    try:
        with open(sentiment_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        print(f"✅ 数据已保存: {sentiment_file}")
        return True
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False

def print_sentiment_report(data):
    """打印市场情绪报告"""
    if not data:
        return
    
    print("\n" + "="*60)
    print(f"市场情绪偏向分析 - {data['beijing_time']}")
    print("="*60)
    
    # 27币涨跌幅变化
    coin = data['coin_data']
    print(f"\n📊 27币累计涨跌幅:")
    print(f"  上次: {coin['prev_cumulative_pct']:>8.2f}%")
    print(f"  本次: {coin['curr_cumulative_pct']:>8.2f}%")
    print(f"  变化: {coin['change_delta']:>8.2f}% ({coin['change_pct']:>+6.2f}%)")
    
    # RSI变化
    rsi = data['rsi_data']
    print(f"\n📈 RSI总和 (27币):")
    print(f"  上次: {rsi['prev_total_rsi']:>8.2f}")
    print(f"  本次: {rsi['curr_total_rsi']:>8.2f}")
    print(f"  变化: {rsi['change_delta']:>8.2f} ({rsi['change_pct']:>+6.2f}%)")
    
    # 市场情绪
    emoji_map = {
        'bullish': '🐂',
        'bearish': '🐻',
        'neutral_bullish': '😐🐂',
        'neutral_bearish': '😐🐻',
        'neutral': '😐'
    }
    emoji = emoji_map.get(data['sentiment_type'], '❓')
    
    print(f"\n{emoji} 市场情绪: {data['sentiment']}")
    print(f"📝 判断依据: {data['reason']}")
    print("="*60 + "\n")

def main():
    """主函数"""
    print("\n🚀 市场情绪偏向采集器启动")
    print(f"📁 数据目录: {DATA_DIR}")
    print(f"⏰ 采集间隔: 15分钟")
    print(f"📊 数据源: coin_change + rsi\n")
    
    # 立即执行第一次采集
    first_run = True
    
    while True:
        try:
            if not first_run:
                # 等待15分钟（从第二次开始）
                beijing_tz = timezone(timedelta(hours=8))
                next_time = datetime.now(beijing_tz).replace(second=0, microsecond=0)
                next_time = next_time.replace(minute=(next_time.minute // 15 + 1) * 15 % 60)
                if next_time.minute == 0:
                    next_time = next_time.replace(hour=next_time.hour + 1)
                
                wait_seconds = (next_time - datetime.now(beijing_tz)).total_seconds()
                print(f"⏳ 下次采集时间: {next_time.strftime('%H:%M:%S')}")
                print(f"💤 等待 {int(wait_seconds)} 秒...\n")
                
                time.sleep(wait_seconds)
            
            print(f"\n{'='*60}")
            print(f"开始采集 - {datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # 计算市场情绪
            sentiment_data = calculate_sentiment()
            
            if sentiment_data:
                # 打印报告
                print_sentiment_report(sentiment_data)
                
                # 保存数据
                save_sentiment(sentiment_data)
            else:
                print("⚠️  本次采集无有效数据\n")
            
            first_run = False
            
        except KeyboardInterrupt:
            print("\n\n👋 采集器已停止")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            print("⏳ 60秒后重试...\n")
            time.sleep(60)

if __name__ == '__main__':
    main()
