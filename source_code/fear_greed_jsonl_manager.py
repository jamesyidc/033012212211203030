#!/usr/bin/env python3
"""
Fear & Greed Index JSONL Manager
管理恐惧贪婪指数的JSONL存储
"""
import os
import json
from datetime import datetime
from pathlib import Path


class FearGreedJSONLManager:
    """恐惧贪婪指数JSONL管理器"""
    
    def __init__(self, data_dir='/home/user/webapp/fear_greed_jsonl'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.jsonl_file = self.data_dir / 'fear_greed_index.jsonl'
    
    def get_latest_record(self):
        """获取最新记录"""
        try:
            if not self.jsonl_file.exists():
                return None
            
            last_record = None
            with open(self.jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            record = json.loads(line)
                            last_record = record
                        except json.JSONDecodeError:
                            continue
            
            return last_record
        except Exception as e:
            print(f"[FearGreedJSONLManager] get_latest_record failed: {e}")
            return None
    
    def get_latest_n_records(self, n=30):
        """获取最近N条记录"""
        try:
            if not self.jsonl_file.exists():
                return []
            
            records = []
            with open(self.jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            record = json.loads(line)
                            records.append(record)
                        except json.JSONDecodeError:
                            continue
            
            # Return the last N records
            return records[-n:] if len(records) > n else records
        except Exception as e:
            print(f"[FearGreedJSONLManager] get_latest_n_records failed: {e}")
            return []
    
    def get_records_by_date_range(self, start_date, end_date):
        """按日期范围获取记录"""
        try:
            if not self.jsonl_file.exists():
                return []
            
            records = []
            with open(self.jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            record = json.loads(line)
                            date_str = record.get('datetime', record.get('date', ''))
                            if date_str:
                                # Extract date part
                                rec_date = date_str[:10] if len(date_str) >= 10 else date_str
                                if start_date <= rec_date <= end_date:
                                    records.append(record)
                        except json.JSONDecodeError:
                            continue
            
            return records
        except Exception as e:
            print(f"[FearGreedJSONLManager] get_records_by_date_range failed: {e}")
            return []
    
    def save_record(self, record):
        """保存一条记录"""
        try:
            with open(self.jsonl_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            return True
        except Exception as e:
            print(f"[FearGreedJSONLManager] save_record failed: {e}")
            return False
    
    def get_all_records(self):
        """获取所有记录"""
        try:
            if not self.jsonl_file.exists():
                return []
            
            records = []
            with open(self.jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            return records
        except Exception as e:
            print(f"[FearGreedJSONLManager] get_all_records failed: {e}")
            return []


if __name__ == '__main__':
    manager = FearGreedJSONLManager()
    latest = manager.get_latest_record()
    print(f"Latest record: {latest}")
    records = manager.get_latest_n_records(10)
    print(f"Last 10 records count: {len(records)}")
