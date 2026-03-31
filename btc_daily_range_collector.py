#!/usr/bin/env python3
"""
BTC当日涨跌幅状态采集器
功能：
1. 获取BTC当天最低价、最高价、当前价
2. 计算当前价格在当天区间的百分比位置（最低价=0%, 最高价=100%）
3. 计算5分钟涨速
4. 数据按日期存储为JSONL格式
"""

import ccxt
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque
from pytz import timezone

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/btc_daily_range.log'),
        logging.StreamHandler()
    ]
)

class BTCDailyRangeCollector:
    """BTC当日涨跌幅状态采集器"""
    
    def __init__(self, data_dir='data/btc_daily_range'):
        """初始化采集器"""
        self.exchange = ccxt.okx()
        self.symbol = 'BTC/USDT'
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 5分钟价格历史（用于计算涨速）
        self.price_history = deque(maxlen=300)  # 300秒 = 5分钟
        
        logging.info("✅ BTC当日涨跌幅状态采集器初始化完成")
    
    def get_beijing_time(self):
        """获取北京时间"""
        beijing_tz = timezone('Asia/Shanghai')
        return datetime.now(beijing_tz)
    
    def get_beijing_date_str(self):
        """获取北京日期字符串 (YYYYMMDD)"""
        return self.get_beijing_time().strftime('%Y%m%d')
    
    def get_data_file_path(self, date_str=None):
        """获取数据文件路径"""
        if date_str is None:
            date_str = self.get_beijing_date_str()
        return self.data_dir / f"btc_range_{date_str}.jsonl"
    
    def get_daily_data(self):
        """获取当日价格数据（使用日线K线）"""
        try:
            # 获取当前价格
            ticker = self.exchange.fetch_ticker(self.symbol)
            current_price = ticker['last']
            
            # 获取最新的日线K线（包含今日开盘价、最高价、最低价）
            daily_candle = self.exchange.fetch_ohlcv(
                self.symbol,
                timeframe='1d',
                limit=1
            )
            
            if not daily_candle:
                # 如果没有K线数据，使用当前价格
                logging.warning("⚠️ 没有获取到日线数据，使用当前价格")
                return {
                    'current_price': current_price,
                    'daily_high': current_price,
                    'daily_low': current_price,
                    'daily_open': current_price
                }
            
            # 从日线K线中提取数据
            # K线格式: [timestamp, open, high, low, close, volume]
            daily_open = daily_candle[0][1]   # 开盘价
            daily_high = daily_candle[0][2]   # 最高价
            daily_low = daily_candle[0][3]    # 最低价
            
            # 确保当前价格在范围内（因为日线数据可能有延迟）
            if current_price > daily_high:
                daily_high = current_price
            if current_price < daily_low:
                daily_low = current_price
            
            logging.info(
                f"📊 价格数据: 当前={current_price:.2f}, "
                f"最低={daily_low:.2f}, 最高={daily_high:.2f}, 开盘={daily_open:.2f} "
                f"(来自日线K线)"
            )
            
            return {
                'current_price': current_price,
                'daily_high': daily_high,
                'daily_low': daily_low,
                'daily_open': daily_open
            }
            
        except Exception as e:
            logging.error(f"获取价格数据失败: {e}", exc_info=True)
            return None
    
    def calculate_position_percentage(self, current_price, daily_low, daily_high):
        """计算当前价格在当天区间的百分比位置
        最低价 = 0%
        最高价 = 100%
        """
        if daily_high == daily_low:
            return 50.0  # 如果最高最低相同，返回50%
        
        percentage = ((current_price - daily_low) / (daily_high - daily_low)) * 100
        return round(percentage, 2)
    
    def calculate_5min_velocity(self):
        """计算5分钟涨速"""
        if len(self.price_history) < 2:
            return 0.0
        
        # 获取5分钟前的价格（或最早的价格）
        earliest_price = self.price_history[0]
        current_price = self.price_history[-1]
        
        # 计算涨速百分比
        velocity = ((current_price - earliest_price) / earliest_price) * 100
        return round(velocity, 2)
    
    def get_status(self, position_pct):
        """根据位置百分比判断状态
        图示中的分类（从上到下）：
        - 主跌（红色）: 跌幅 > 3%
        - 大幅下跌（橙色）: -3% ~ -1.5%
        - 小幅跌涨偏空（黄色）: -1.5% ~ 0%
        - 小幅跌涨偏多（浅绿）: 0% ~ 1.5%
        - 大幅上涨（绿色）: 1.5% ~ 3%
        - 主升（深绿）: 涨幅 > 3%
        
        位置百分比：0%=最低价，100%=最高价
        当价格在低位时，说明相对开盘价跌了很多（主跌）
        当价格在高位时，说明相对开盘价涨了很多（主升）
        """
        if position_pct <= 20:
            return "主跌"  # 在20%以下，接近最低价
        elif position_pct <= 35:
            return "大幅下跌"  # 20-35%
        elif position_pct <= 50:
            return "小幅跌/涨偏空"  # 35-50%
        elif position_pct <= 65:
            return "小幅跌/涨偏多"  # 50-65%
        elif position_pct <= 80:
            return "大幅上涨"  # 65-80%
        else:
            return "主升"  # 80%以上，接近最高价
    
    def collect_data(self):
        """采集一次数据"""
        try:
            # 获取当日价格数据
            daily_data = self.get_daily_data()
            if not daily_data:
                logging.warning("⚠️ 无法获取价格数据")
                return False
            
            current_price = daily_data['current_price']
            
            # 添加到价格历史
            self.price_history.append(current_price)
            
            # 计算位置百分比
            position_pct = self.calculate_position_percentage(
                current_price,
                daily_data['daily_low'],
                daily_data['daily_high']
            )
            
            # 计算5分钟涨速
            velocity_5min = self.calculate_5min_velocity()
            
            # 获取北京时间
            beijing_time = self.get_beijing_time()
            timestamp = int(beijing_time.timestamp() * 1000)
            
            # 构建数据记录
            record = {
                'timestamp': timestamp,
                'beijing_time': beijing_time.strftime('%Y-%m-%d %H:%M:%S'),
                'current_price': round(current_price, 2),
                'daily_high': round(daily_data['daily_high'], 2),
                'daily_low': round(daily_data['daily_low'], 2),
                'daily_open': round(daily_data['daily_open'], 2),
                'daily_range': round(daily_data['daily_high'] - daily_data['daily_low'], 2),
                'position_percentage': position_pct,
                'velocity_5min': velocity_5min,
                'status': self.get_status(position_pct)
            }
            
            # 保存到文件
            file_path = self.get_data_file_path()
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            
            logging.info(
                f"✅ BTC: 价格={current_price:.2f} "
                f"位置={position_pct:.1f}% "
                f"涨速5min={velocity_5min:+.2f}% "
                f"状态={record['status']}"
            )
            
            return True
            
        except Exception as e:
            logging.error(f"采集数据失败: {e}", exc_info=True)
            return False
    
    def run(self, interval=60):
        """运行采集器"""
        logging.info(f"🚀 开始运行BTC当日涨跌幅状态采集器 (间隔={interval}秒)")
        
        while True:
            try:
                self.collect_data()
                time.sleep(interval)
            except KeyboardInterrupt:
                logging.info("⏹️ 用户中断，停止采集")
                break
            except Exception as e:
                logging.error(f"运行出错: {e}", exc_info=True)
                time.sleep(interval)


def main():
    """主函数"""
    collector = BTCDailyRangeCollector()
    collector.run(interval=60)  # 每60秒采集一次


if __name__ == '__main__':
    main()
