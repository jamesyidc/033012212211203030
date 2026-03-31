#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
低吸信号监控系统
监控"低吸"状态下，2:10、2:20、2:30三个时间点的10分钟上涨占比
- 3根绿色（上涨占比>55%）→ 低吸做多
- 3根红色/空白（上涨占比≤55%）→ 低吸做空
在2:30发送TG消息
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
STATUS_API_URL = "http://localhost:9002/api/coin-change-tracker/positive-ratio-stats"
CHART_API_URL = "http://localhost:9002/coin-change-tracker"

# Telegram配置
TG_CONFIG_FILE = Path('/home/user/webapp/config/configs/telegram_config.json')

# 数据存储目录
DATA_DIR = Path('/home/user/webapp/data/low_absorption_monitor')
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = DATA_DIR / 'state.json'
HISTORY_FILE = DATA_DIR / 'history.jsonl'

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class LowAbsorptionMonitor:
    """低吸信号监控器"""
    
    def __init__(self):
        self.state = self.load_state()
        self.tg_config = self.load_telegram_config()
        
    def load_state(self):
        """加载上次的状态"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载状态文件失败: {e}")
        
        return {
            'last_check_date': None,  # 最后检查的日期（YYYY-MM-DD）
            'last_signal_sent': None,  # 最后发送信号的时间
            'check_points': {}  # 存储2:10, 2:20, 2:30的检查结果
        }
    
    def save_state(self):
        """保存当前状态"""
        try:
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存状态文件失败: {e}")
    
    def load_telegram_config(self):
        """加载Telegram配置"""
        try:
            if TG_CONFIG_FILE.exists():
                with open(TG_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.info("✅ Telegram配置加载成功")
                    return config
        except Exception as e:
            logger.error(f"❌ 加载Telegram配置失败: {e}")
        return None
    
    def send_telegram(self, message):
        """发送Telegram消息"""
        if not self.tg_config:
            logger.warning("⚠️ Telegram未配置，跳过发送")
            return False
        
        try:
            bot_token = self.tg_config.get('bot_token')
            chat_id = self.tg_config.get('chat_id')
            
            if not bot_token or not chat_id:
                logger.warning("⚠️ Telegram配置不完整")
                return False
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            logger.info("✅ Telegram消息发送成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ Telegram消息发送失败: {e}")
            return False
    
    def get_current_status(self):
        """获取当前状态（低吸/高抛）"""
        try:
            response = requests.get(STATUS_API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('success'):
                logger.error(f"❌ API返回失败: {data}")
                return None
            
            stats = data.get('stats', {})
            positive_ratio = stats.get('positive_ratio', 0)
            
            # 判断状态：<40% 为低吸，≥40% 为高抛
            status = '低吸' if positive_ratio < 40 else '高抛'
            
            logger.info(f"📊 当前正数占比: {positive_ratio:.2f}% - 状态: {status}")
            
            return {
                'status': status,
                'positive_ratio': positive_ratio,
                'date': stats.get('date'),
                'positive_count': stats.get('positive_count'),
                'total_count': stats.get('total_count')
            }
            
        except Exception as e:
            logger.error(f"❌ 获取当前状态失败: {e}")
            return None
    
    def get_10min_ratio_at_time(self, target_time_str):
        """
        获取指定时间点的上涨占比
        target_time_str: "02:10", "02:20", "02:30"
        返回: 上涨占比百分比 或 None
        """
        try:
            # 解析目标时间
            target_hour, target_minute = map(int, target_time_str.split(':'))
            
            # 获取北京时间
            beijing_tz = timezone(timedelta(hours=8))
            now_beijing = datetime.now(beijing_tz)
            
            # 读取币种变化追踪数据
            date_str = now_beijing.strftime('%Y%m%d')
            data_file = Path(f'/home/user/webapp/data/coin_change_tracker/coin_change_{date_str}.jsonl')
            
            if not data_file.exists():
                logger.error(f"❌ 数据文件不存在: {data_file}")
                return None
            
            # 读取所有数据
            with open(data_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 在目标时间前后2分钟的窗口内查找记录
            # 例如：02:10 → 查找 02:08-02:12 之间的记录
            records = []
            year = now_beijing.year
            month = now_beijing.month
            day = now_beijing.day
            
            for line in lines:
                try:
                    record = json.loads(line.strip())
                    beijing_time = record.get('beijing_time', '')
                    
                    # 检查是否在时间范围内
                    if beijing_time.startswith(f'{year:04d}-{month:02d}-{day:02d} {target_hour:02d}:'):
                        minute = int(beijing_time.split(':')[1])
                        # 允许 ±2分钟的偏差
                        if target_minute - 2 <= minute <= target_minute + 2:
                            records.append(record)
                except json.JSONDecodeError:
                    continue
            
            if records:
                # 选择最接近目标时间的记录
                best_record = min(records, key=lambda r: abs(
                    int(r.get('beijing_time', '00:00:00').split(':')[1]) - target_minute
                ))
                
                up_ratio = best_record.get('up_ratio', 0)
                beijing_time = best_record.get('beijing_time', 'N/A')
                up_coins = best_record.get('up_coins', 0)
                down_coins = best_record.get('down_coins', 0)
                
                logger.info(f"✅ {target_time_str} 的上涨占比: {up_ratio:.2f}% (记录时间: {beijing_time}, 上涨:{up_coins}, 下跌:{down_coins})")
                return up_ratio
            else:
                logger.warning(f"⚠️ 未找到 {target_time_str} 附近的数据")
                return None
            
        except Exception as e:
            logger.error(f"❌ 获取上涨占比失败: {e}")
            return None
    
    def check_and_send_signal(self):
        """检查并发送低吸信号"""
        # 获取北京时间
        beijing_tz = timezone(timedelta(hours=8))
        now_beijing = datetime.now(beijing_tz)
        current_time_str = now_beijing.strftime('%H:%M')
        current_date = now_beijing.strftime('%Y-%m-%d')
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 开始检查 - 北京时间: {now_beijing.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*80}")
        
        # 1. 检查是否已经在今天发送过信号
        if self.state.get('last_check_date') == current_date:
            logger.info(f"✅ 今天已检查过，跳过")
            return
        
        # 2. 获取当前状态
        status_info = self.get_current_status()
        if not status_info:
            logger.error("❌ 无法获取当前状态")
            return
        
        # 3. 检查是否为"低吸"状态
        if status_info['status'] != '低吸':
            logger.info(f"📊 当前状态: {status_info['status']}，不是低吸状态，跳过检查")
            return
        
        logger.info(f"✅ 当前状态: 低吸 ({status_info['positive_ratio']:.2f}%)")
        
        # 4. 收集2:10、2:20、2:30的上涨占比
        check_times = ['02:10', '02:20', '02:30']
        ratios = []
        
        for time_point in check_times:
            ratio = self.get_10min_ratio_at_time(time_point)
            if ratio is not None:
                ratios.append({
                    'time': time_point,
                    'ratio': ratio,
                    'is_green': ratio > 55  # >55% 为绿色
                })
        
        # 5. 如果还没有收集到所有3个时间点的数据，等待
        if len(ratios) < 3:
            logger.info(f"⏰ 已收集 {len(ratios)}/3 个时间点的数据，继续等待...")
            return
        
        # 6. 检查是否到了2:30
        if current_time_str < '02:30':
            logger.info(f"⏰ 尚未到达2:30（当前: {current_time_str}），继续等待...")
            return
        
        # 7. 判断信号类型
        green_count = sum(1 for r in ratios if r['is_green'])
        red_count = 3 - green_count
        
        logger.info(f"\n📊 三个时间点的上涨占比:")
        for r in ratios:
            color = '🟢 绿色' if r['is_green'] else '🔴 红色'
            logger.info(f"   {r['time']}: {r['ratio']:.2f}% - {color}")
        
        logger.info(f"\n📊 统计: 🟢 绿色={green_count}, 🔴 红色={red_count}")
        
        # 8. 判断并发送信号
        signal = None
        
        if green_count == 3:
            signal = '低吸做多'
            emoji = '🟢🟢🟢'
            action = '做多'
        elif red_count == 3:
            signal = '低吸做空'
            emoji = '🔴🔴🔴'
            action = '做空'
        else:
            logger.info(f"⚠️ 未满足信号条件（需要3根同色），不发送信号")
        
        # 9. 发送Telegram通知
        if signal:
            message = f"""
🔥 <b>低吸信号提醒</b>

━━━━━━━━━━━━━━━━━━
📊 <b>当前状态:</b> 低吸 ({status_info['positive_ratio']:.2f}%)
🎯 <b>信号类型:</b> {signal} {emoji}
💡 <b>操作建议:</b> {action}
━━━━━━━━━━━━━━━━━━

📈 <b>上涨占比:</b>
  • 02:10: {ratios[0]['ratio']:.2f}% {'🟢' if ratios[0]['is_green'] else '🔴'}
  • 02:20: {ratios[1]['ratio']:.2f}% {'🟢' if ratios[1]['is_green'] else '🔴'}
  • 02:30: {ratios[2]['ratio']:.2f}% {'🟢' if ratios[2]['is_green'] else '🔴'}

⏰ 时间: {now_beijing.strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            if self.send_telegram(message):
                logger.info(f"✅ 信号已发送: {signal}")
                
                # 记录到历史
                self.save_history({
                    'time': now_beijing.isoformat(),
                    'signal': signal,
                    'status': status_info,
                    'ratios': ratios
                })
                
                # 更新状态
                self.state['last_check_date'] = current_date
                self.state['last_signal_sent'] = now_beijing.isoformat()
                self.state['check_points'] = {
                    '02:10': ratios[0],
                    '02:20': ratios[1],
                    '02:30': ratios[2]
                }
                self.save_state()
            else:
                logger.error("❌ Telegram消息发送失败")
    
    def save_history(self, record):
        """保存历史记录"""
        try:
            with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"❌ 保存历史记录失败: {e}")
    
    def run(self):
        """主循环"""
        logger.info("=" * 80)
        logger.info("🚀 低吸信号监控系统启动")
        logger.info("=" * 80)
        logger.info(f"⚙️  配置:")
        logger.info(f"   - 检查间隔: {CHECK_INTERVAL}秒")
        logger.info(f"   - 监控时间: 02:10, 02:20, 02:30")
        logger.info(f"   - 绿色阈值: >55%")
        logger.info("=" * 80)
        
        check_count = 0
        
        while True:
            try:
                check_count += 1
                beijing_tz = timezone(timedelta(hours=8))
                beijing_time = datetime.now(beijing_tz)
                
                logger.info(f"\n{'='*80}")
                logger.info(f"🔍 第 {check_count} 次检查 - {beijing_time.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*80}")
                
                # 执行检查
                self.check_and_send_signal()
                
                # 等待下次检查
                logger.info(f"\n⏳ 等待 {CHECK_INTERVAL} 秒后进行下次检查...")
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("\n⚠️  收到中断信号，监控停止")
                break
            except Exception as e:
                logger.error(f"❌ 监控循环错误: {e}")
                logger.info(f"⏳ 等待 {CHECK_INTERVAL} 秒后重试...")
                time.sleep(CHECK_INTERVAL)
        
        logger.info("👋 监控已停止")


if __name__ == '__main__':
    monitor = LowAbsorptionMonitor()
    monitor.run()
