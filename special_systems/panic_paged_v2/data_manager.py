#!/usr/bin/env python3
"""
Panic Paged V2 数据管理器
提供API接口读取JSONL数据
"""
import json
from pathlib import Path
from datetime import datetime, timedelta

class PanicPagedDataManager:
    """数据管理器"""
    
    def __init__(self, data_dir='/home/user/webapp/panic_paged_v2/data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_date_string(self, date):
        """获取日期字符串 YYYYMMDD"""
        if isinstance(date, str):
            # 如果是字符串，假设格式为 YYYY-MM-DD
            date = datetime.strptime(date, '%Y-%m-%d')
        return date.strftime('%Y%m%d')
    
    def _read_jsonl(self, file_path):
        """读取JSONL文件"""
        if not file_path.exists():
            return []
        
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return records
    
    def get_24h_data_by_date(self, date):
        """
        获取指定日期的24小时数据
        
        参数:
            date: datetime对象或字符串(YYYY-MM-DD)
        
        返回:
            [{
                "timestamp": 1770792843198,
                "beijing_time": "2026-02-11 14:54:03",
                "liquidation_24h": 16642.09,
                "liquidation_count_24h": 7.08,
                "open_interest": 56.27,
                "panic_index": 0.1258,
                "panic_level": "中等恐慌"
            }, ...]
        """
        date_str = self._get_date_string(date)
        file_path = self.data_dir / f"panic_24h_{date_str}.jsonl"
        return self._read_jsonl(file_path)
    
    def get_1h_data_by_date(self, date):
        """
        获取指定日期的1小时数据
        
        参数:
            date: datetime对象或字符串(YYYY-MM-DD)
        
        返回:
            [{
                "timestamp": 1770792843198,
                "beijing_time": "2026-02-11 14:54:03",
                "liquidation_1h": 3996.87
            }, ...]
        """
        date_str = self._get_date_string(date)
        file_path = self.data_dir / f"panic_1h_{date_str}.jsonl"
        return self._read_jsonl(file_path)
    
    def get_24h_latest(self):
        """获取最新的24小时数据"""
        today = datetime.now().strftime('%Y%m%d')
        file_path = self.data_dir / f"panic_24h_{today}.jsonl"
        records = self._read_jsonl(file_path)
        return records[-1] if records else None
    
    def get_1h_latest(self):
        """获取最新的1小时数据"""
        today = datetime.now().strftime('%Y%m%d')
        file_path = self.data_dir / f"panic_1h_{today}.jsonl"
        records = self._read_jsonl(file_path)
        return records[-1] if records else None
    
    def get_24h_date_range(self, start_date, end_date):
        """
        获取日期范围内的24小时数据
        
        参数:
            start_date: 开始日期 (datetime或字符串)
            end_date: 结束日期 (datetime或字符串)
        
        返回:
            {
                "2026-02-10": [{...}, {...}],
                "2026-02-11": [{...}, {...}]
            }
        """
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        result = {}
        current = start_date
        
        while current <= end_date:
            date_key = current.strftime('%Y-%m-%d')
            result[date_key] = self.get_24h_data_by_date(current)
            current += timedelta(days=1)
        
        return result
    
    def get_1h_date_range(self, start_date, end_date):
        """
        获取日期范围内的1小时数据
        """
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        result = {}
        current = start_date
        
        while current <= end_date:
            date_key = current.strftime('%Y-%m-%d')
            result[date_key] = self.get_1h_data_by_date(current)
            current += timedelta(days=1)
        
        return result
    
    def get_available_dates(self):
        """
        获取所有可用的日期列表
        
        返回:
            {
                "dates_24h": ["2026-02-01", "2026-02-02", ...],
                "dates_1h": ["2026-02-01", "2026-02-02", ...]
            }
        """
        dates_24h = set()
        dates_1h = set()
        
        # 扫描24h文件
        for file_path in self.data_dir.glob("panic_24h_*.jsonl"):
            date_str = file_path.stem.replace('panic_24h_', '')
            if len(date_str) == 8:  # YYYYMMDD
                date_obj = datetime.strptime(date_str, '%Y%m%d')
                dates_24h.add(date_obj.strftime('%Y-%m-%d'))
        
        # 扫描1h文件
        for file_path in self.data_dir.glob("panic_1h_*.jsonl"):
            date_str = file_path.stem.replace('panic_1h_', '')
            if len(date_str) == 8:  # YYYYMMDD
                date_obj = datetime.strptime(date_str, '%Y%m%d')
                dates_1h.add(date_obj.strftime('%Y-%m-%d'))
        
        return {
            "dates_24h": sorted(list(dates_24h)),
            "dates_1h": sorted(list(dates_1h))
        }

# 测试代码
if __name__ == '__main__':
    manager = PanicPagedDataManager()
    
    print("=== 可用日期 ===")
    dates = manager.get_available_dates()
    print(f"24h数据: {dates['dates_24h']}")
    print(f"1h数据: {dates['dates_1h']}")
    
    print("\n=== 最新数据 ===")
    latest_24h = manager.get_24h_latest()
    print(f"24h: {latest_24h}")
    
    latest_1h = manager.get_1h_latest()
    print(f"1h: {latest_1h}")
