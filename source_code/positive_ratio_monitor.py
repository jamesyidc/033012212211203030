#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正数占比多空转换监控系统
监控正数占比是否突破40%阈值，并发送Telegram通知
"""

import os
import sys
import time
import json
import logging
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 配置
THRESHOLD_OFFSET = 20.0  # 多空分界线：最高值-20%
CHECK_INTERVAL = 60  # 检查间隔：60秒
API_URL = "http://localhost:9002/api/coin-change-tracker/positive-ratio-stats"
REPEAT_COUNT = 3  # Telegram消息重复发送次数

# Telegram配置（硬编码，与market_sentiment_collector保持一致）
TG_BOT_TOKEN = "8437045462:AAFePnwdC21cqeWhZISMQHGGgjmroVqE2H0"
TG_CHAT_ID = "-1003227444260"

# 数据存储目录
DATA_DIR = Path('/home/user/webapp/data/positive_ratio_monitor')
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = DATA_DIR / 'state.json'
ALERT_HISTORY_FILE = DATA_DIR / 'alert_history.json'

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class PositiveRatioMonitor:
    """正数占比监控器"""
    
    def __init__(self):
        self.state = self.load_state()
        self.alert_history = self.load_alert_history()
        
    def load_state(self):
        """加载上次的状态"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载状态文件失败: {e}")
        
        return {
            'last_ratio': None,
            'last_status': None,  # 'bullish' or 'bearish'
            'last_check_time': None,
            'max_ratio': None,  # 当日最高正数占比
            'threshold': None  # 动态阈值（最高值-20%）
        }
    
    def save_state(self):
        """保存当前状态"""
        try:
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存状态文件失败: {e}")
    
    def load_alert_history(self):
        """加载报警历史"""
        if ALERT_HISTORY_FILE.exists():
            try:
                with open(ALERT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载报警历史失败: {e}")
        return []
    
    def save_alert_history(self, alert):
        """保存报警记录"""
        self.alert_history.append(alert)
        
        # 只保留最近100条记录
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        try:
            with open(ALERT_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.alert_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存报警历史失败: {e}")
    
    def get_today_max_ratio(self):
        """从历史数据中获取今日最高正数占比"""
        try:
            beijing_time = datetime.now(timezone(timedelta(hours=8)))
            date_str = beijing_time.strftime('%Y%m%d')
            
            history_url = f"http://localhost:9002/api/coin-change-tracker/positive-ratio-history?date={date_str}"
            response = requests.get(history_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and data.get('data'):
                ratios = [record['positive_ratio'] for record in data['data']]
                max_ratio = max(ratios)
                logger.info(f"📊 从历史数据获取今日最高值: {max_ratio:.2f}% (共{len(ratios)}条记录)")
                return max_ratio
            else:
                logger.warning("⚠️ 历史数据API返回失败或无数据")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取历史最高值失败: {e}")
            return None
    
    def get_current_ratio(self):
        """获取当前正数占比和历史最高值"""
        try:
            response = requests.get(API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                stats = data.get('stats', {})
                ratio = stats.get('positive_ratio')
                max_ratio_from_api = stats.get('max_positive_ratio')  # 从API获取当日最高值
                
                if ratio is not None:
                    logger.info(f"✅ 获取正数占比成功: {ratio:.2f}%")
                    
                    result = {
                        'ratio': ratio,
                        'positive_count': stats.get('positive_count', 0),
                        'total_count': stats.get('total_count', 0),
                        'date': stats.get('date'),
                        'positive_duration': stats.get('positive_duration', 0)
                    }
                    
                    # 如果API返回了最高值，使用API的值
                    if max_ratio_from_api is not None:
                        result['max_ratio'] = max_ratio_from_api
                        logger.info(f"📊 API返回最高值: {max_ratio_from_api:.2f}%")
                    
                    return result
                else:
                    logger.warning("⚠️ API返回数据中没有positive_ratio字段")
                    return None
            else:
                logger.warning(f"⚠️ API返回失败: {data.get('error', '未知错误')}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取正数占比失败: {e}")
            return None
    
    def send_telegram(self, message, repeat=1):
        """发送Telegram消息（可重复发送）"""
        if not TG_BOT_TOKEN or not TG_CHAT_ID:
            logger.warning("⚠️ Telegram配置未设置，跳过发送")
            return False
        
        success_count = 0
        
        for i in range(repeat):
            try:
                url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
                data = {
                    'chat_id': TG_CHAT_ID,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                
                response = requests.post(url, data=data, timeout=10)
                response.raise_for_status()
                
                success_count += 1
                logger.info(f"✅ Telegram消息发送成功 ({i+1}/{repeat})")
                
                # 发送间隔，避免频率限制
                if i < repeat - 1:
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Telegram消息发送失败 ({i+1}/{repeat}): {e}")
        
        return success_count > 0
    
    def check_and_alert(self):
        """检查并发送报警"""
        current_data = self.get_current_ratio()
        
        if not current_data:
            logger.warning("⚠️ 无法获取当前数据，跳过本次检查")
            return
        
        current_ratio = current_data['ratio']
        
        # 获取今日最高正数占比（从历史数据中计算）
        max_ratio = self.get_today_max_ratio()
        
        if max_ratio is None:
            # 如果无法从历史数据获取，回退到本地状态
            max_ratio = self.state.get('max_ratio')
            if max_ratio is None or current_ratio > max_ratio:
                max_ratio = current_ratio
                self.state['max_ratio'] = max_ratio
                logger.info(f"📈 更新最高正数占比: {max_ratio:.2f}% (本地计算)")
        else:
            # 使用从历史数据获取的最高值
            self.state['max_ratio'] = max_ratio
        
        # 计算动态阈值：最高值 - 20%
        threshold = max_ratio - THRESHOLD_OFFSET
        self.state['threshold'] = threshold
        
        current_status = 'bullish' if current_ratio >= threshold else 'bearish'
        
        beijing_time = datetime.now(timezone(timedelta(hours=8)))
        check_time = beijing_time.strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"📊 当前正数占比: {current_ratio:.2f}% | 最高值: {max_ratio:.2f}% | 阈值: {threshold:.2f}% | 状态: {current_status}")
        
        # 获取上次状态
        last_ratio = self.state.get('last_ratio')
        last_status = self.state.get('last_status')
        
        # 判断是否发生转换
        should_alert = False
        alert_type = None
        
        if last_ratio is not None and last_status is not None:
            # 空转多信号：从<阈值上升到>=阈值
            if last_status == 'bearish' and current_status == 'bullish':
                should_alert = True
                alert_type = 'turn_bullish'
                logger.warning(f"🔥 检测到空转多信号！{last_ratio:.2f}% → {current_ratio:.2f}% (阈值: {threshold:.2f}%)")
            
            # 多转空信号：从>=阈值下降到<阈值
            elif last_status == 'bullish' and current_status == 'bearish':
                should_alert = True
                alert_type = 'turn_bearish'
                logger.warning(f"🔥 检测到多转空信号！{last_ratio:.2f}% → {current_ratio:.2f}% (阈值: {threshold:.2f}%)")
        
        # 发送报警
        if should_alert:
            if alert_type == 'turn_bullish':
                emoji = "🟢"
                title = "空转多信号"
                direction = "上升"
                action = "逢低做多"
                color_from = "🔴 空方"
                color_to = "🟢 多方"
            else:  # turn_bearish
                emoji = "🔴"
                title = "多转空信号"
                direction = "下降"
                action = "逢高做空"
                color_from = "🟢 多方"
                color_to = "🔴 空方"
            
            message = f"""
{emoji} <b>正数占比多空转换预警！</b>

━━━━━━━━━━━━━━━━━━
📊 <b>{title}</b>
━━━━━━━━━━━━━━━━━━

📈 正数占比变化: {last_ratio:.2f}% → <b>{current_ratio:.2f}%</b>
📉 方向: {direction}
🔀 状态转换: {color_from} → {color_to}

⚡ <b>动态阈值: {threshold:.2f}% (最高值 {max_ratio:.2f}% - 20%)</b>
━━━━━━━━━━━━━━━━━━

💡 <b>操作建议: {action}</b>

📊 数据详情:
  • 正数时段: {current_data['positive_count']}/{current_data['total_count']}
  • 正数时长: {current_data['positive_duration']:.1f} 分钟
  • 数据日期: {current_data['date']}

⏰ 检查时间: {check_time}
"""
            
            # 🔥 发送Telegram通知（重复3次）
            self.send_telegram(message, repeat=REPEAT_COUNT)
            
            # 保存报警记录
            alert_record = {
                'time': check_time,
                'type': alert_type,
                'from_ratio': last_ratio,
                'to_ratio': current_ratio,
                'from_status': last_status,
                'to_status': current_status,
                'threshold': threshold,
                'max_ratio': max_ratio,
                'data': current_data
            }
            self.save_alert_history(alert_record)
            
            logger.info(f"💾 报警记录已保存")
        
        # 更新状态
        self.state['last_ratio'] = current_ratio
        self.state['last_status'] = current_status
        self.state['last_check_time'] = check_time
        self.save_state()
    
    def run(self):
        """主循环"""
        logger.info("=" * 60)
        logger.info("🚀 正数占比多空转换监控系统启动")
        logger.info("=" * 60)
        logger.info(f"⚙️  配置参数:")
        logger.info(f"   - 多空分界线: 动态计算（最高值 - {THRESHOLD_OFFSET}%）")
        logger.info(f"   - 检查间隔: {CHECK_INTERVAL}秒")
        logger.info(f"   - API地址: {API_URL}")
        logger.info(f"   - 数据目录: {DATA_DIR}")
        logger.info(f"   - Telegram消息重复次数: {REPEAT_COUNT}次")
        logger.info(f"   - Telegram Bot: {'✅ 已配置' if TG_BOT_TOKEN else '❌ 未配置'}")
        logger.info("=" * 60)
        
        # 首次检查（不发送报警）
        logger.info("🔍 执行首次检查（初始化状态）...")
        current_data = self.get_current_ratio()
        if current_data:
            current_ratio = current_data['ratio']
            
            # 从历史数据获取今日最高值
            max_ratio = self.get_today_max_ratio()
            
            if max_ratio is None:
                # 如果无法从历史数据获取，使用当前值
                max_ratio = current_ratio
                logger.warning(f"⚠️ 无法从历史数据获取最高值，使用当前值: {max_ratio:.2f}%")
            
            threshold = max_ratio - THRESHOLD_OFFSET
            
            self.state['max_ratio'] = max_ratio
            self.state['threshold'] = threshold
            
            current_status = 'bullish' if current_ratio >= threshold else 'bearish'
            beijing_time = datetime.now(timezone(timedelta(hours=8)))
            
            self.state['last_ratio'] = current_ratio
            self.state['last_status'] = current_status
            self.state['last_check_time'] = beijing_time.strftime('%Y-%m-%d %H:%M:%S')
            self.save_state()
            
            logger.info(f"✅ 初始状态: 正数占比 {current_ratio:.2f}%, 最高值 {max_ratio:.2f}%, 阈值 {threshold:.2f}%, 状态 {current_status}")
        
        check_count = 0
        
        while True:
            try:
                check_count += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"🔍 执行第 {check_count} 次检查")
                logger.info(f"{'='*60}")
                
                self.check_and_alert()
                
                logger.info(f"⏳ 等待 {CHECK_INTERVAL} 秒后进行下次检查...")
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("\n⚠️  收到中断信号，正在停止监控...")
                break
            except Exception as e:
                logger.error(f"❌ 监控循环发生错误: {e}")
                logger.info(f"⏳ 等待 {CHECK_INTERVAL} 秒后重试...")
                time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    monitor = PositiveRatioMonitor()
    monitor.run()
