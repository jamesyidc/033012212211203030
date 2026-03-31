#!/usr/bin/env python3
"""
横盘监控数据读取工具类
提供方便的API来读取和分析横盘监控数据
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple


class ConsolidationDataReader:
    """横盘监控数据读取器"""
    
    def __init__(self, data_dir: str = '/home/user/webapp/data/consolidation_monitor'):
        self.data_dir = Path(data_dir)
    
    def read_by_date(self, symbol: str, date: str) -> List[Dict]:
        """
        按日期读取数据
        
        Args:
            symbol: 交易对（BTC-USDT-SWAP/ETH-USDT-SWAP）
            date: 日期（YYYYMMDD格式）
        
        Returns:
            记录列表
        """
        data_file = self.data_dir / f'consolidation_{symbol.replace("-", "_")}_{date}.jsonl'
        
        if not data_file.exists():
            return []
        
        records = []
        with open(data_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except:
                        continue
        
        return records
    
    def read_today(self, symbol: str) -> List[Dict]:
        """
        读取今天的数据
        
        Args:
            symbol: 交易对
        
        Returns:
            今日记录列表
        """
        beijing_time = datetime.now() + timedelta(hours=8)
        date = beijing_time.strftime('%Y%m%d')
        return self.read_by_date(symbol, date)
    
    def read_date_range(self, symbol: str, start_date: str, end_date: str) -> List[Dict]:
        """
        读取日期范围内的数据
        
        Args:
            symbol: 交易对
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）
        
        Returns:
            记录列表
        """
        all_records = []
        
        start = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')
        
        current = start
        while current <= end:
            date_str = current.strftime('%Y%m%d')
            records = self.read_by_date(symbol, date_str)
            all_records.extend(records)
            current += timedelta(days=1)
        
        return all_records
    
    def get_latest_record(self, symbol: str) -> Optional[Dict]:
        """
        获取最新的一条记录
        
        Args:
            symbol: 交易对
        
        Returns:
            最新记录或None
        """
        records = self.read_today(symbol)
        return records[-1] if records else None
    
    def get_consolidation_records(self, symbol: str, date: str) -> List[Dict]:
        """
        获取某天所有横盘记录
        
        Args:
            symbol: 交易对
            date: 日期（YYYYMMDD）
        
        Returns:
            横盘记录列表
        """
        records = self.read_by_date(symbol, date)
        return [r for r in records if r.get('is_consolidation')]
    
    def find_alert_moments(self, symbol: str, date: str, min_consecutive: int = 3) -> List[Dict]:
        """
        查找触发告警的时刻
        
        Args:
            symbol: 交易对
            date: 日期（YYYYMMDD）
            min_consecutive: 最小连续次数
        
        Returns:
            触发告警的记录列表
        """
        records = self.read_by_date(symbol, date)
        alerts = []
        
        for i, record in enumerate(records):
            if record.get('consecutive_count', 0) >= min_consecutive:
                # 检查是否刚达到阈值（避免重复）
                if i == 0 or records[i-1].get('consecutive_count', 0) < min_consecutive:
                    alerts.append(record)
        
        return alerts
    
    def analyze_daily_stats(self, symbol: str, date: str) -> Dict:
        """
        分析每日统计数据
        
        Args:
            symbol: 交易对
            date: 日期（YYYYMMDD）
        
        Returns:
            统计数据字典
        """
        records = self.read_by_date(symbol, date)
        
        if not records:
            return {
                'total_records': 0,
                'consolidation_count': 0,
                'consolidation_ratio': 0,
                'max_consecutive': 0,
                'alert_count': 0
            }
        
        consolidation_count = sum(1 for r in records if r.get('is_consolidation'))
        alerts = self.find_alert_moments(symbol, date)
        
        return {
            'total_records': len(records),
            'consolidation_count': consolidation_count,
            'consolidation_ratio': consolidation_count / len(records),
            'max_consecutive': max((r.get('consecutive_count', 0) for r in records), default=0),
            'alert_count': len(alerts),
            'avg_change': sum(abs(r.get('change_percent', 0)) for r in records) / len(records),
            'first_time': records[0].get('datetime'),
            'last_time': records[-1].get('datetime')
        }
    
    def calculate_consolidation_periods(self, symbol: str, date: str) -> Dict:
        """
        计算横盘周期统计
        
        Args:
            symbol: 交易对
            date: 日期（YYYYMMDD）
        
        Returns:
            周期统计数据
        """
        records = self.read_by_date(symbol, date)
        
        durations = []
        current_duration = 0
        
        for record in records:
            if record.get('is_consolidation'):
                current_duration += 1
            else:
                if current_duration > 0:
                    durations.append(current_duration)
                current_duration = 0
        
        if current_duration > 0:
            durations.append(current_duration)
        
        return {
            'total_periods': len(durations),
            'max_duration': max(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0,
            'avg_duration': sum(durations) / len(durations) if durations else 0,
            'durations': durations
        }
    
    def get_available_dates(self, symbol: str) -> List[str]:
        """
        获取可用的数据日期列表
        
        Args:
            symbol: 交易对
        
        Returns:
            日期列表（YYYYMMDD格式）
        """
        pattern = f'consolidation_{symbol.replace("-", "_")}_*.jsonl'
        dates = []
        
        for file in self.data_dir.glob(pattern):
            # 从文件名提取日期
            parts = file.stem.split('_')
            if len(parts) >= 2:
                date_str = parts[-1]
                if len(date_str) == 8 and date_str.isdigit():
                    dates.append(date_str)
        
        return sorted(dates)
    
    def export_to_dict(self, records: List[Dict]) -> Dict:
        """
        将记录列表导出为字典格式（方便JSON序列化）
        
        Args:
            records: 记录列表
        
        Returns:
            字典格式的数据
        """
        return {
            'count': len(records),
            'records': records
        }


# 使用示例
if __name__ == '__main__':
    reader = ConsolidationDataReader()
    
    # 读取今天的BTC数据
    print("=== 读取今日BTC数据 ===")
    btc_records = reader.read_today('BTC-USDT-SWAP')
    print(f"共 {len(btc_records)} 条记录")
    
    # 统计今日数据
    beijing_time = datetime.now() + timedelta(hours=8)
    today = beijing_time.strftime('%Y%m%d')
    print(f"\n=== 今日统计 ({today}) ===")
    stats = reader.analyze_daily_stats('BTC-USDT-SWAP', today)
    print(f"总记录数: {stats['total_records']}")
    print(f"横盘记录: {stats['consolidation_count']} ({stats['consolidation_ratio']:.1%})")
    print(f"最大连续: {stats['max_consecutive']}次")
    print(f"告警次数: {stats['alert_count']}次")
    
    # 查找告警时刻
    print(f"\n=== 告警时刻 ===")
    alerts = reader.find_alert_moments('BTC-USDT-SWAP', today)
    for alert in alerts:
        print(f"{alert['datetime']}: 连续{alert['consecutive_count']}次横盘, 涨跌{alert['change_percent_display']}")
    
    # 横盘周期分析
    print(f"\n=== 横盘周期分析 ===")
    periods = reader.calculate_consolidation_periods('BTC-USDT-SWAP', today)
    print(f"横盘周期数: {periods['total_periods']}")
    print(f"最长持续: {periods['max_duration']}次")
    print(f"平均持续: {periods['avg_duration']:.1f}次")
    
    # 可用日期
    print(f"\n=== 可用日期 ===")
    dates = reader.get_available_dates('BTC-USDT-SWAP')
    print(f"共有 {len(dates)} 天数据: {', '.join(dates[-5:])}")
