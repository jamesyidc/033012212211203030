#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
空转多触发价监控系统
监控正数占比是否达到"0:30后最低值+30%"，并发送Telegram通知
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
CHECK_INTERVAL = 60  # 检查间隔：60秒
API_URL = "http://localhost:9002/api/coin-change-tracker/positive-ratio-history"
TRIGGER_OFFSET = 30.0  # 空转多触发偏移：最低值+30%
REPEAT_COUNT = 3  # Telegram消息重复发送次数

# Telegram配置（硬编码，与market_sentiment_collector保持一致）
TG_BOT_TOKEN = "8437045462:AAFePnwdC21cqeWhZISMQHGGgjmroVqE2H0"
TG_CHAT_ID = "-1003227444260"

# 数据存储目录
DATA_DIR = Path('/home/user/webapp/data/short_to_long_monitor')
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


class ShortToLongTriggerMonitor:
    """空转多触发价监控器"""
    
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
            'last_date': None,  # 上次检查的日期
            'min_ratio_after_0030': None,  # 0:30后最低正数占比
            'min_time': None,  # 最低值出现时间
            'trigger_ratio': None,  # 触发阈值（最低+30）
            'triggered': False,  # 是否已触发
            'trigger_time': None  # 触发时间
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
    
    def get_positive_ratio_history(self):
        """获取今日正数占比历史数据"""
        try:
            beijing_time = datetime.now(timezone(timedelta(hours=8)))
            date_str = beijing_time.strftime('%Y%m%d')
            
            url = f"{API_URL}?date={date_str}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and data.get('data'):
                logger.info(f"✅ 获取历史数据成功: {len(data['data'])}条记录")
                return data['data'], date_str
            else:
                logger.warning("⚠️ 历史数据API返回失败或无数据")
                return None, None
                
        except Exception as e:
            logger.error(f"❌ 获取历史数据失败: {e}")
            return None, None
    
    def calculate_trigger_point(self, history_data):
        """
        计算空转多触发价
        规则：0:30之后正数占比的最低值 + 30%
        """
        if not history_data:
            return None
        
        # 过滤出0:30之后的数据
        data_after_0030 = []
        for record in history_data:
            time_str = record.get('time', '')
            if not time_str:
                continue
            
            # 解析时间（格式：HH:MM:SS）
            try:
                hour, minute, second = map(int, time_str.split(':'))
                # 0:30:00之后的数据
                if hour > 0 or (hour == 0 and minute >= 30):
                    data_after_0030.append(record)
            except:
                continue
        
        if not data_after_0030:
            logger.warning("⚠️ 没有0:30之后的数据")
            return None
        
        # 找到最低正数占比
        min_record = min(data_after_0030, key=lambda x: x.get('positive_ratio', 100))
        min_ratio = min_record.get('positive_ratio')
        min_time = min_record.get('time')
        
        if min_ratio is None:
            return None
        
        # 计算触发价：最低值 + 30
        trigger_ratio = min_ratio + TRIGGER_OFFSET
        
        logger.info(f"📊 空转多触发价计算: 最低{min_ratio:.2f}% (在{min_time}) + 30 = {trigger_ratio:.2f}%")
        
        return {
            'min_ratio': min_ratio,
            'min_time': min_time,
            'trigger_ratio': trigger_ratio,
            'data_after_0030': data_after_0030
        }
    
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
        beijing_time = datetime.now(timezone(timedelta(hours=8)))
        current_date = beijing_time.strftime('%Y%m%d')
        current_time = beijing_time.strftime('%H:%M:%S')
        
        # 检查是否是新的一天（重置状态）
        if self.state.get('last_date') != current_date:
            logger.info(f"🆕 新的一天，重置监控状态: {current_date}")
            self.state = {
                'last_date': current_date,
                'min_ratio_after_0030': None,
                'min_time': None,
                'trigger_ratio': None,
                'triggered': False,
                'trigger_time': None
            }
            self.save_state()
        
        # 获取历史数据
        history_data, date_str = self.get_positive_ratio_history()
        if not history_data:
            logger.warning("⚠️ 无法获取历史数据，跳过本次检查")
            return
        
        # 计算触发点
        trigger_info = self.calculate_trigger_point(history_data)
        if not trigger_info:
            logger.info("⚠️ 无法计算触发点（可能还没到0:30）")
            return
        
        min_ratio = trigger_info['min_ratio']
        min_time = trigger_info['min_time']
        trigger_ratio = trigger_info['trigger_ratio']
        data_after_0030 = trigger_info['data_after_0030']
        
        # 更新状态
        self.state['min_ratio_after_0030'] = min_ratio
        self.state['min_time'] = min_time
        self.state['trigger_ratio'] = trigger_ratio
        
        # 获取当前正数占比
        current_record = history_data[-1]
        current_ratio = current_record.get('positive_ratio')
        
        logger.info(f"📊 当前正数占比: {current_ratio:.2f}% | 触发价: {trigger_ratio:.2f}% | 已触发: {self.state.get('triggered')}")
        
        # 检查是否达到触发条件
        if current_ratio >= trigger_ratio and not self.state.get('triggered'):
            # 找到触发点的具体时间
            trigger_point = None
            for record in data_after_0030:
                if record.get('positive_ratio') >= trigger_ratio:
                    trigger_point = record
                    break
            
            if trigger_point:
                trigger_time_str = trigger_point.get('time')
                trigger_ratio_actual = trigger_point.get('positive_ratio')
                
                logger.warning(f"🔥 检测到空转多信号！触发价: {trigger_ratio:.2f}%, 实际: {trigger_ratio_actual:.2f}%, 时间: {trigger_time_str}")
                
                # 构建通知消息
                message = f"""
🟢 <b>空转多信号触发！</b>

━━━━━━━━━━━━━━━━━━
📊 <b>触发详情</b>
━━━━━━━━━━━━━━━━━━

📉 0:30后最低正数占比: <b>{min_ratio:.2f}%</b> (出现在 {min_time})
⚡ 空转多触发价: <b>{trigger_ratio:.2f}%</b> (最低+30%)
📈 实际触发正数占比: <b>{trigger_ratio_actual:.2f}%</b>
⏰ 触发时间: <b>{trigger_time_str}</b>

━━━━━━━━━━━━━━━━━━

💡 <b>操作建议: 逢低做多</b>

📊 当前数据:
  • 当前正数占比: {current_ratio:.2f}%
  • 数据日期: {date_str}
  • 检查时间: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                # 发送Telegram通知（重复3次）
                self.send_telegram(message, repeat=REPEAT_COUNT)
                
                # 更新状态为已触发
                self.state['triggered'] = True
                self.state['trigger_time'] = trigger_time_str
                self.save_state()
                
                # 保存报警记录
                alert_record = {
                    'date': date_str,
                    'trigger_time': trigger_time_str,
                    'min_ratio': min_ratio,
                    'min_time': min_time,
                    'trigger_ratio': trigger_ratio,
                    'actual_ratio': trigger_ratio_actual,
                    'current_ratio': current_ratio,
                    'check_time': beijing_time.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.save_alert_history(alert_record)
                
                logger.info(f"💾 报警记录已保存")
        
        # 保存状态
        self.save_state()
    
    def run(self):
        """主循环"""
        logger.info("=" * 60)
        logger.info("🚀 空转多触发价监控系统启动")
        logger.info("=" * 60)
        logger.info(f"⚙️  配置参数:")
        logger.info(f"   - 触发规则: 0:30后最低值 + {TRIGGER_OFFSET}%")
        logger.info(f"   - 检查间隔: {CHECK_INTERVAL}秒")
        logger.info(f"   - API地址: {API_URL}")
        logger.info(f"   - 数据目录: {DATA_DIR}")
        logger.info(f"   - Telegram消息重复次数: {REPEAT_COUNT}次")
        logger.info(f"   - Telegram Bot: {'✅ 已配置' if TG_BOT_TOKEN else '❌ 未配置'}")
        logger.info("=" * 60)
        
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
    monitor = ShortToLongTriggerMonitor()
    monitor.run()
