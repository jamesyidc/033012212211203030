#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易模型买点分发系统 - 核心监控器
支持6个交易模型的信号监控和分发
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
API_BASE_URL = "http://localhost:9002"
LIQUIDATION_API = f"{API_BASE_URL}/liquidation-monthly"
POSITIVE_RATIO_API = f"{API_BASE_URL}/api/coin-change-tracker/positive-ratio-stats"

# Telegram配置
TG_CONFIG_FILE = Path('/home/user/webapp/config/configs/telegram_config.json')

# 数据存储目录
DATA_DIR = Path('/home/user/webapp/data/trading_signals')
DATA_DIR.mkdir(parents=True, exist_ok=True)

STATE_FILE = DATA_DIR / 'monitor_state.json'
SIGNALS_FILE = DATA_DIR / 'pending_signals.jsonl'
HISTORY_FILE = DATA_DIR / 'signals_history.jsonl'

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class TradingSignalMonitor:
    """交易信号监控器"""
    
    def __init__(self):
        self.state = self.load_state()
        self.tg_config = self.load_telegram_config()
        self.beijing_tz = timezone(timedelta(hours=8))
        
    def load_state(self):
        """加载监控状态"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载状态文件失败: {e}")
        
        return {
            'last_check_date': None,
            'model_1_low_absorption': {
                'last_signal_time': None,
                'check_points': {}
            }
        }
    
    def save_state(self):
        """保存监控状态"""
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
    
    def get_market_trend(self):
        """
        判断当前市场趋势（多头区间 vs 空头区间）
        参考：https://9002-iq7zoh927x8lpyitg5alc-a402f90a.sandbox.novita.ai/liquidation-monthly
        
        规则：
        - 多头爆仓 > 1.45亿 → 空头区间
        - 空头爆仓 > 1.45亿 → 多头区间
        """
        try:
            response = requests.get(LIQUIDATION_API, timeout=10)
            response.raise_for_status()
            
            # 这里需要解析API返回的数据
            # 假设API返回格式：{"long_liquidation": xxx, "short_liquidation": yyy}
            data = response.json()
            
            long_liq = data.get('long_liquidation', 0)
            short_liq = data.get('short_liquidation', 0)
            
            threshold = 145000000  # 1.45亿
            
            if long_liq > threshold:
                return "空头区间"
            elif short_liq > threshold:
                return "多头区间"
            else:
                return "震荡区间"
                
        except Exception as e:
            logger.error(f"❌ 获取市场趋势失败: {e}")
            return "未知"
    
    def get_positive_ratio(self):
        """获取当前正数占比"""
        try:
            response = requests.get(POSITIVE_RATIO_API, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                stats = data.get('stats', {})
                return stats.get('positive_ratio', 0)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取正数占比失败: {e}")
            return None
    
    def get_up_ratio_at_time(self, target_time_str):
        """
        获取指定时间点的上涨占比
        target_time_str: "02:10", "02:20", "02:30"
        """
        try:
            target_hour, target_minute = map(int, target_time_str.split(':'))
            now_beijing = datetime.now(self.beijing_tz)
            
            date_str = now_beijing.strftime('%Y%m%d')
            data_file = Path(f'/home/user/webapp/data/coin_change_tracker/coin_change_{date_str}.jsonl')
            
            if not data_file.exists():
                logger.error(f"❌ 数据文件不存在: {data_file}")
                return None
            
            with open(data_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 在目标时间前后2分钟窗口内查找
            records = []
            year = now_beijing.year
            month = now_beijing.month
            day = now_beijing.day
            
            for line in lines:
                try:
                    record = json.loads(line.strip())
                    beijing_time = record.get('beijing_time', '')
                    
                    if beijing_time.startswith(f'{year:04d}-{month:02d}-{day:02d} {target_hour:02d}:'):
                        minute = int(beijing_time.split(':')[1])
                        if target_minute - 2 <= minute <= target_minute + 2:
                            records.append(record)
                except json.JSONDecodeError:
                    continue
            
            if records:
                best_record = min(records, key=lambda r: abs(
                    int(r.get('beijing_time', '00:00:00').split(':')[1]) - target_minute
                ))
                
                up_ratio = best_record.get('up_ratio', 0)
                beijing_time = best_record.get('beijing_time', 'N/A')
                
                logger.info(f"✅ {target_time_str} 的上涨占比: {up_ratio:.2f}% (时间: {beijing_time})")
                return up_ratio
            else:
                logger.warning(f"⚠️ 未找到 {target_time_str} 附近的数据")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取上涨占比失败: {e}")
            return None
    
    def get_velocity(self):
        """获取当前1.5分钟涨速"""
        try:
            response = requests.get(f"{API_BASE_URL}/api/coin-change-tracker/velocity", timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('success'):
                return data.get('velocity', 0)
            return None
        except Exception as e:
            logger.error(f"❌ 获取涨速失败: {e}")
            return None
    
    def get_5min_velocity(self):
        """获取5分钟涨速"""
        try:
            # 读取最近5分钟的数据计算
            now_beijing = datetime.now(self.beijing_tz)
            date_str = now_beijing.strftime('%Y%m%d')
            data_file = Path(f'/home/user/webapp/data/coin_change_tracker/coin_change_{date_str}.jsonl')
            
            if not data_file.exists():
                return None
            
            with open(data_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 获取最近5分钟的记录（约5条记录）
            recent_records = []
            for line in reversed(lines[-10:]):
                try:
                    record = json.loads(line.strip())
                    recent_records.append(record)
                    if len(recent_records) >= 5:
                        break
                except json.JSONDecodeError:
                    continue
            
            if len(recent_records) < 2:
                return None
            
            # 计算5分钟涨速（最新 - 5分钟前）
            latest_cumulative = recent_records[0].get('cumulative_percentage_change', 0)
            old_cumulative = recent_records[-1].get('cumulative_percentage_change', 0)
            velocity_5min = latest_cumulative - old_cumulative
            
            return velocity_5min
            
        except Exception as e:
            logger.error(f"❌ 获取5分钟涨速失败: {e}")
            return None
    
    def count_candles_0_to_2(self):
        """
        统计0点到2点之间的柱子颜色
        绿色: up_ratio > 55%
        红色: up_ratio <= 55%
        黄色: 可以有1根黄色（视为特殊情况）
        """
        try:
            now_beijing = datetime.now(self.beijing_tz)
            date_str = now_beijing.strftime('%Y%m%d')
            data_file = Path(f'/home/user/webapp/data/coin_change_tracker/coin_change_{date_str}.jsonl')
            
            if not data_file.exists():
                return None
            
            with open(data_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 收集0点到2点的数据
            candles = []
            year = now_beijing.year
            month = now_beijing.month
            day = now_beijing.day
            
            for line in lines:
                try:
                    record = json.loads(line.strip())
                    beijing_time = record.get('beijing_time', '')
                    
                    # 检查是否在0点到2点之间
                    if beijing_time.startswith(f'{year:04d}-{month:02d}-{day:02d}'):
                        hour = int(beijing_time.split()[1].split(':')[0])
                        if 0 <= hour < 2:
                            up_ratio = record.get('up_ratio', 0)
                            candles.append({
                                'time': beijing_time,
                                'up_ratio': up_ratio,
                                'color': 'green' if up_ratio > 55 else 'red'
                            })
                except json.JSONDecodeError:
                    continue
            
            # 统计颜色
            green_count = sum(1 for c in candles if c['color'] == 'green')
            red_count = sum(1 for c in candles if c['color'] == 'red')
            
            return {
                'green_count': green_count,
                'red_count': red_count,
                'total_count': len(candles),
                'candles': candles
            }
            
        except Exception as e:
            logger.error(f"❌ 统计0-2点柱子失败: {e}")
            return None
    
    def check_model_1_low_absorption(self):
        """
        模型1：低吸模型 - 完整规则
        
        【初始条件】
        1. 0点-2点交易窗口：需要>=3根绿柱，红柱+黄柱<25%（<3根），黄柱<=1根
        2. 必须存在红色或空白柱子才算低吸
        
        【2:30评估】
        3. 评估02:10, 02:20, 02:30三个10分钟上涨占比
           - 3根绿色（>55%）→ 低吸做多
           - 3根红色（<=55%，含空白）→ 低吸做空
        
        【2:30后入场条件】
        4. 做多：1.5分钟涨速<-15% 且 正数占比>40%，然后正数占比上升突破40%
        5. 做空：1.5分钟涨速>8% 且 正数占比<40%，然后正数占比下降跌破40%
        
        【仓位配置】
        6. 做多：每币1%
        7. 做空：每币1.5-2-3-5%（根据情况调整）
        
        【止盈规则】
        8. 做多：5分钟涨速>+8%平半，>+15%平全部
        9. 做空：5分钟涨速<-15%平半，<-20%平全部
        
        【多空区间判定】
        10. 参考爆仓数据：多头爆仓>1.45亿→空头区间，反之亦然
        """
        now_beijing = datetime.now(self.beijing_tz)
        current_date = now_beijing.strftime('%Y-%m-%d')
        current_time_str = now_beijing.strftime('%H:%M')
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 模型1：低吸信号检查 - {now_beijing.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*80}")
        
        # 检查今天是否已发送信号
        model_state = self.state['model_1_low_absorption']
        last_signal_date = None
        if model_state.get('last_signal_time'):
            last_signal_date = model_state['last_signal_time'].split('T')[0]
        
        if last_signal_date == current_date:
            logger.info(f"✅ 今天已发送信号，跳过")
            return
        
        # 获取当前正数占比
        positive_ratio = self.get_positive_ratio()
        if positive_ratio is None:
            logger.error("❌ 无法获取正数占比")
            return
        
        logger.info(f"📊 当前正数占比: {positive_ratio:.2f}%")
        
        # 【步骤1】检查0-2点交易窗口的柱子颜色
        candle_stats = self.count_candles_0_to_2()
        if candle_stats:
            green_count = candle_stats['green_count']
            red_count = candle_stats['red_count']
            total_count = candle_stats['total_count']
            
            logger.info(f"📊 0-2点柱子统计: 绿={green_count}, 红={red_count}, 总计={total_count}")
            
            # 检查是否满足低吸条件
            # 需要: 绿>=3, 红+黄<3 (即<25%)
            if green_count < 3:
                logger.info(f"⚠️ 绿柱数量不足（{green_count}<3），不满足低吸条件")
                return
            
            if red_count >= 3:
                logger.info(f"✅ 满足初始低吸窗口条件（绿>={green_count}, 红={red_count}）")
            else:
                logger.info(f"⚠️ 未检测到足够红柱（{red_count}<3），可能不是明显低吸")
        
        # 【步骤2】判断是否为低吸状态
        is_low_absorption = positive_ratio < 40
        if not is_low_absorption:
            logger.info(f"📊 当前不是低吸状态（正数占比: {positive_ratio:.2f}% >= 40%）")
            return
        
        logger.info(f"✅ 当前处于低吸状态（正数占比: {positive_ratio:.2f}% < 40%）")
        
        # 收集2:10, 2:20, 2:30的数据
        check_times = ['02:10', '02:20', '02:30']
        ratios = []
        
        for time_point in check_times:
            ratio = self.get_up_ratio_at_time(time_point)
            if ratio is not None:
                ratios.append({
                    'time': time_point,
                    'ratio': ratio,
                    'is_green': ratio > 55
                })
        
        # 如果还没收集到所有数据，等待
        if len(ratios) < 3:
            logger.info(f"⏰ 已收集 {len(ratios)}/3 个时间点的数据，继续等待...")
            return
        
        # 检查是否到了2:30
        if current_time_str < '02:30':
            logger.info(f"⏰ 尚未到达2:30（当前: {current_time_str}），继续等待...")
            return
        
        # 判断信号类型
        green_count = sum(1 for r in ratios if r['is_green'])
        red_count = 3 - green_count
        
        logger.info(f"\n📊 三个时间点的上涨占比:")
        for r in ratios:
            color = '🟢 绿色' if r['is_green'] else '🔴 红色'
            logger.info(f"   {r['time']}: {r['ratio']:.2f}% - {color}")
        
        logger.info(f"\n📊 统计: 🟢 绿色={green_count}, 🔴 红色={red_count}")
        
        # 判断信号
        signal = None
        direction = None
        
        if green_count == 3:
            signal = '低吸做多'
            direction = 'long'
            emoji = '🟢🟢🟢'
        elif red_count == 3:
            signal = '低吸做空'
            direction = 'short'
            emoji = '🔴🔴🔴'
        else:
            logger.info(f"⚠️ 未满足信号条件（需要3根同色），不发送信号")
            return
        
        # 【步骤5】获取市场趋势
        market_trend = self.get_market_trend()
        
        # 【步骤6】获取当前涨速（用于后续入场判断）
        current_velocity = self.get_velocity()
        velocity_5min = self.get_5min_velocity()
        
        logger.info(f"📊 当前涨速: 1.5分钟={current_velocity:.2f}%, 5分钟={velocity_5min:.2f}%")
        
        # 【步骤7】判断是否满足2:30后入场条件
        entry_condition_met = False
        entry_reason = ""
        
        if direction == 'long':
            # 做多：1.5分钟涨速<-15% 且 正数占比>40%
            if current_velocity is not None and current_velocity < -15 and positive_ratio > 40:
                entry_condition_met = True
                entry_reason = f"涨速{current_velocity:.2f}%<-15% 且 正数占比{positive_ratio:.2f}%>40%"
        else:  # short
            # 做空：1.5分钟涨速>8% 且 正数占比<40%
            if current_velocity is not None and current_velocity > 8 and positive_ratio < 40:
                entry_condition_met = True
                entry_reason = f"涨速{current_velocity:.2f}%>8% 且 正数占比{positive_ratio:.2f}%<40%"
        
        logger.info(f"📊 入场条件: {'✅ 满足' if entry_condition_met else '❌ 不满足'} - {entry_reason}")
        
        # 创建待执行信号
        signal_data = {
            'model_id': 'model_1_low_absorption',
            'model_name': '低吸模型',
            'trigger_time': now_beijing.isoformat(),
            'signal_type': signal,
            'direction': direction,
            'market_trend': market_trend,
            'market_data': {
                'positive_ratio': positive_ratio,
                'check_points': ratios
            },
            'trading_params': {
                'symbols_count': 8,  # 常用币中涨幅后8
                'position_per_symbol': '1%' if direction == 'long' else '1.5-2-3-5%',
                'leverage': 3 if direction == 'long' else 5,
                'max_position_per_symbol': '5%',
                'take_profit': {
                    'long': '5分钟涨速>+8%平半，>+15%平全部',
                    'short': '5分钟涨速<-15%平半，<-20%平全部'
                }
            },
            'entry_condition': {
                'met': entry_condition_met,
                'reason': entry_reason,
                'velocity_1_5min': current_velocity,
                'velocity_5min': velocity_5min
            },
            'candle_stats_0_to_2': candle_stats,
            'status': 'pending',
            'executed': False,
            'execution_subsystem': None,
            'created_at': now_beijing.isoformat()
        }
        
        # 保存到待执行队列
        self.save_pending_signal(signal_data)
        
        # 发送Telegram通知
        message = f"""
🔥 <b>【模型1】低吸信号触发</b>

━━━━━━━━━━━━━━━━━━
📊 <b>市场状态:</b> 低吸 ({positive_ratio:.2f}%)
🎯 <b>信号类型:</b> {signal} {emoji}
💡 <b>操作方向:</b> {'做多' if direction == 'long' else '做空'}
🌊 <b>市场趋势:</b> {market_trend}
━━━━━━━━━━━━━━━━━━

📈 <b>关键时间点上涨占比:</b>
  • 02:10: {ratios[0]['ratio']:.2f}% {'🟢' if ratios[0]['is_green'] else '🔴'}
  • 02:20: {ratios[1]['ratio']:.2f}% {'🟢' if ratios[1]['is_green'] else '🔴'}
  • 02:30: {ratios[2]['ratio']:.2f}% {'🟢' if ratios[2]['is_green'] else '🔴'}

📊 <b>0-2点窗口统计:</b>
  • 绿柱: {candle_stats['green_count']}根
  • 红柱: {candle_stats['red_count']}根
  • 总计: {candle_stats['total_count']}根

⚡ <b>当前市场涨速:</b>
  • 1.5分钟: {current_velocity:.2f}%
  • 5分钟: {velocity_5min:.2f}%
  • 入场条件: {'✅ 满足' if entry_condition_met else '⏳ 待满足'}

💰 <b>交易参数:</b>
  • 标的数量: {signal_data['trading_params']['symbols_count']}个
  • 单币仓位: {signal_data['trading_params']['position_per_symbol']}
  • 杠杆倍数: {signal_data['trading_params']['leverage']}倍
  • 最大仓位: {signal_data['trading_params']['max_position_per_symbol']}

⏰ 触发时间: {now_beijing.strftime('%Y-%m-%d %H:%M:%S')}

📋 查看待执行信号: http://localhost:9002/trading-signals
"""
        
        if self.send_telegram(message):
            logger.info(f"✅ 信号已发送并加入待执行队列: {signal}")
            
            # 保存历史记录
            self.save_history(signal_data)
            
            # 更新状态
            model_state['last_signal_time'] = now_beijing.isoformat()
            model_state['check_points'] = {
                '02:10': ratios[0],
                '02:20': ratios[1],
                '02:30': ratios[2]
            }
            self.save_state()
        else:
            logger.error("❌ Telegram消息发送失败")
    
    def save_pending_signal(self, signal_data):
        """保存待执行信号"""
        try:
            with open(SIGNALS_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(signal_data, ensure_ascii=False) + '\n')
            logger.info(f"✅ 信号已保存到待执行队列")
        except Exception as e:
            logger.error(f"❌ 保存待执行信号失败: {e}")
    
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
        logger.info("🚀 交易模型买点分发系统启动")
        logger.info("=" * 80)
        logger.info(f"⚙️  配置:")
        logger.info(f"   - 检查间隔: {CHECK_INTERVAL}秒")
        logger.info(f"   - 支持模型: 6个（当前激活：模型1-低吸）")
        logger.info("=" * 80)
        
        check_count = 0
        
        while True:
            try:
                check_count += 1
                beijing_time = datetime.now(self.beijing_tz)
                
                logger.info(f"\n{'='*80}")
                logger.info(f"🔍 第 {check_count} 次检查 - {beijing_time.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*80}")
                
                # 执行模型1检查
                self.check_model_1_low_absorption()
                
                # TODO: 添加其他5个模型的检查
                # self.check_model_2_xxx()
                # self.check_model_3_xxx()
                # ...
                
                logger.info(f"\n⏳ 等待 {CHECK_INTERVAL} 秒后进行下次检查...")
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("\n⚠️  收到中断信号，监控停止")
                break
            except Exception as e:
                logger.error(f"❌ 监控循环错误: {e}")
                import traceback
                traceback.print_exc()
                logger.info(f"⏳ 等待 {CHECK_INTERVAL} 秒后重试...")
                time.sleep(CHECK_INTERVAL)
        
        logger.info("👋 监控已停止")


if __name__ == '__main__':
    monitor = TradingSignalMonitor()
    monitor.run()
