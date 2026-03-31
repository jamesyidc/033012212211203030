#!/usr/bin/env python3
"""
币价变化数据后台聚合计算服务
功能：独立于前端，持续计算各种统计指标并写入数据文件
- 10分钟分组上涨占比
- 每分钟上涨占比统计
- 速度指标
- RSI历史数据
- 正数占比统计
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/coin_change_aggregator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据目录
DATA_DIR = Path("data/coin_change_tracker")
AGGREGATED_DIR = DATA_DIR / "aggregated"
AGGREGATED_DIR.mkdir(parents=True, exist_ok=True)

class CoinChangeAggregator:
    """币价变化数据聚合器"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.output_dir = AGGREGATED_DIR
        
    def get_beijing_date(self):
        """获取北京时间日期"""
        beijing_tz = timezone(timedelta(hours=8))
        return datetime.now(beijing_tz).strftime('%Y%m%d')
    
    def get_beijing_time(self):
        """获取北京时间"""
        beijing_tz = timezone(timedelta(hours=8))
        return datetime.now(beijing_tz)
    
    def read_coin_change_data(self, date_str):
        """读取指定日期的币价变化数据"""
        file_path = self.data_dir / f"coin_change_{date_str}.jsonl"
        if not file_path.exists():
            logger.warning(f"数据文件不存在: {file_path}")
            return []
        
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
            logger.info(f"读取数据文件: {file_path}, 共 {len(data)} 条记录")
            return data
        except Exception as e:
            logger.error(f"读取数据文件失败: {e}")
            return []
    
    def calculate_10min_up_ratio(self, data):
        """计算10分钟分组上涨占比"""
        if not data:
            return []
        
        grouped = defaultdict(lambda: {'ratios': [], 'times': []})
        
        for record in data:
            try:
                # 解析时间
                time_str = record.get('beijing_time', '')
                if not time_str:
                    continue
                
                # 格式: YYYY-MM-DD HH:MM:SS 或 HH:MM:SS
                if ' ' in time_str:
                    # 包含日期，提取时间部分
                    time_part = time_str.split(' ')[1]
                else:
                    time_part = time_str
                
                parts = time_part.split(':')
                if len(parts) < 2:
                    continue
                
                hours = int(parts[0])
                minutes = int(parts[1])
                total_minutes = hours * 60 + minutes
                
                # 10分钟分组
                group_index = total_minutes // 10
                
                # 获取上涨占比
                up_ratio = record.get('up_ratio')
                if up_ratio is not None:
                    grouped[group_index]['ratios'].append(up_ratio)
                    grouped[group_index]['times'].append(time_str)
                else:
                    # 如果没有up_ratio，从changes计算
                    changes = record.get('changes', {})
                    if changes:
                        total_coins = len(changes)
                        up_coins = sum(1 for coin in changes.values() if coin.get('change_pct', 0) > 0)
                        up_ratio = (up_coins / total_coins * 100) if total_coins > 0 else 0
                        grouped[group_index]['ratios'].append(up_ratio)
                        grouped[group_index]['times'].append(time_str)
            except Exception as e:
                logger.debug(f"处理记录失败: {e}")
                continue
        
        # 计算每组的平均值
        result = []
        for group_idx in sorted(grouped.keys()):
            group_data = grouped[group_idx]
            if group_data['ratios']:
                avg_ratio = sum(group_data['ratios']) / len(group_data['ratios'])
                start_hour = (group_idx * 10) // 60
                start_minute = (group_idx * 10) % 60
                start_time = f"{start_hour:02d}:{start_minute:02d}"
                
                # 判断颜色 - 与预判逻辑保持一致 (regenerate_all_predictions.py)
                # 0% -> blank, >55% -> green, 45-55% -> yellow, <45% -> red
                if avg_ratio == 0:
                    color = 'blank'
                    status = '空白'
                elif avg_ratio > 55:
                    color = 'green'
                    status = '多头强势'
                elif avg_ratio >= 45:
                    color = 'yellow'
                    status = '震荡'
                else:
                    color = 'red'
                    status = '空头强势'
                
                result.append({
                    'time_range': f"{start_time}",
                    'avg_up_ratio': round(avg_ratio, 2),
                    'count': len(group_data['ratios']),
                    'color': color,
                    'status': status,
                    'group_index': group_idx
                })
        
        return result
    
    def calculate_positive_ratio_stats(self, data):
        """计算正数占比统计"""
        if not data:
            return {
                'total_count': 0,
                'positive_count': 0,
                'positive_ratio': 0.0,
                'positive_duration': 0.0
            }
        
        positive_count = 0
        total_count = len(data)
        
        for record in data:
            total_change = record.get('total_change', 0)
            cumulative_pct = record.get('cumulative_pct', 0)
            
            # 优先使用total_change
            value = total_change if total_change != 0 else cumulative_pct
            
            if value > 0:
                positive_count += 1
        
        positive_ratio = (positive_count / total_count * 100) if total_count > 0 else 0
        positive_duration = positive_count  # 假设每条数据1分钟
        
        return {
            'total_count': total_count,
            'positive_count': positive_count,
            'positive_ratio': round(positive_ratio, 2),
            'positive_duration': positive_duration
        }
    
    def calculate_velocity_stats(self, data):
        """计算速度统计"""
        if not data:
            return []
        
        velocity_data = []
        for record in data:
            time_str = record.get('beijing_time', '')
            total_change = record.get('total_change', 0)
            cumulative_pct = record.get('cumulative_pct', 0)
            
            if time_str:
                velocity_data.append({
                    'time': time_str,
                    'total_change': total_change,
                    'cumulative_pct': cumulative_pct,
                    'velocity': abs(total_change)  # 速度取绝对值
                })
        
        return velocity_data
    
    def save_aggregated_data(self, date_str, data_type, data):
        """保存聚合数据"""
        output_file = self.output_dir / f"{data_type}_{date_str}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'date': date_str,
                    'type': data_type,
                    'generated_at': self.get_beijing_time().isoformat(),
                    'data': data
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"保存聚合数据: {output_file}")
            return True
        except Exception as e:
            logger.error(f"保存聚合数据失败: {e}")
            return False
    
    def process_date(self, date_str):
        """处理指定日期的数据"""
        logger.info(f"开始处理日期: {date_str}")
        
        # 读取原始数据
        raw_data = self.read_coin_change_data(date_str)
        if not raw_data:
            logger.warning(f"没有数据可处理: {date_str}")
            return False
        
        # 计算10分钟分组上涨占比
        ten_min_data = self.calculate_10min_up_ratio(raw_data)
        self.save_aggregated_data(date_str, '10min_up_ratio', ten_min_data)
        
        # 计算正数占比统计
        positive_stats = self.calculate_positive_ratio_stats(raw_data)
        self.save_aggregated_data(date_str, 'positive_ratio_stats', positive_stats)
        
        # 计算速度统计
        velocity_stats = self.calculate_velocity_stats(raw_data)
        self.save_aggregated_data(date_str, 'velocity_stats', velocity_stats)
        
        logger.info(f"完成处理日期: {date_str}")
        logger.info(f"  - 10分钟分组: {len(ten_min_data)} 组")
        logger.info(f"  - 正数占比: {positive_stats['positive_ratio']}%")
        logger.info(f"  - 速度数据: {len(velocity_stats)} 条")
        
        return True
    
    def run_continuous(self, interval=60):
        """持续运行，每隔一定时间处理当天数据"""
        logger.info("启动持续聚合服务...")
        logger.info(f"处理间隔: {interval} 秒")
        
        while True:
            try:
                # 获取当前北京时间日期
                current_date = self.get_beijing_date()
                
                # 处理当天数据
                self.process_date(current_date)
                
                logger.info(f"等待 {interval} 秒后再次处理...")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("收到中断信号，停止服务...")
                break
            except Exception as e:
                logger.error(f"处理过程中出错: {e}", exc_info=True)
                logger.info(f"等待 {interval} 秒后重试...")
                time.sleep(interval)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='币价变化数据聚合服务')
    parser.add_argument('--date', type=str, help='指定日期 (格式: YYYYMMDD)')
    parser.add_argument('--continuous', action='store_true', help='持续运行模式')
    parser.add_argument('--interval', type=int, default=60, help='持续模式下的处理间隔（秒）')
    
    args = parser.parse_args()
    
    aggregator = CoinChangeAggregator()
    
    if args.continuous:
        # 持续运行模式
        aggregator.run_continuous(interval=args.interval)
    elif args.date:
        # 处理指定日期
        aggregator.process_date(args.date)
    else:
        # 处理今天的数据
        today = aggregator.get_beijing_date()
        aggregator.process_date(today)

if __name__ == '__main__':
    main()
