#!/usr/bin/env python3
"""
Panic JSONL Manager
管理恐慌数据的JSONL存储 - 通用JSONL读写管理器
"""
import os
import json
from datetime import datetime
from pathlib import Path


class PanicJSONLManager:
    """恐慌/通用数据JSONL管理器"""
    
    def __init__(self, base_dir='/home/user/webapp/panic_jsonl'):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, data_type, date_str=None):
        """获取JSONL文件路径"""
        if date_str:
            return self.base_dir / f'{data_type}_{date_str}.jsonl'
        return self.base_dir / f'{data_type}.jsonl'
    
    def save_record(self, data_type, record):
        """保存一条记录"""
        try:
            file_path = self._get_file_path(data_type)
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            return True
        except Exception as e:
            print(f"[PanicJSONLManager] save_record({data_type}) failed: {e}")
            return False
    
    def get_latest(self, data_type):
        """获取最新一条记录"""
        try:
            file_path = self._get_file_path(data_type)
            if not file_path.exists():
                return None
            
            last_record = None
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            last_record = json.loads(line)
                        except json.JSONDecodeError:
                            continue
            
            return last_record
        except Exception as e:
            print(f"[PanicJSONLManager] get_latest({data_type}) failed: {e}")
            return None
    
    def read_records(self, data_type, limit=100, reverse=False, date_str=None):
        """读取记录列表"""
        try:
            file_path = self._get_file_path(data_type, date_str)
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
            
            if reverse:
                records = list(reversed(records))
            
            return records[:limit] if len(records) > limit else records
        except Exception as e:
            print(f"[PanicJSONLManager] read_records({data_type}) failed: {e}")
            return []
    
    def get_records_by_date(self, data_type, date_str):
        """按日期获取记录"""
        try:
            records = self.read_records(data_type, limit=10000)
            filtered = []
            for record in records:
                # Check if the record matches the date
                for time_key in ['record_time', 'timestamp', 'time', 'datetime', 'date']:
                    ts = record.get(time_key, '')
                    if ts and date_str.replace('-', '') in str(ts).replace('-', '').replace(' ', ''):
                        filtered.append(record)
                        break
                    elif ts and date_str in str(ts):
                        filtered.append(record)
                        break
            return filtered
        except Exception as e:
            print(f"[PanicJSONLManager] get_records_by_date({data_type}) failed: {e}")
            return []
    
    def count_records(self, data_type):
        """统计记录数量"""
        try:
            file_path = self._get_file_path(data_type)
            if not file_path.exists():
                return 0
            
            count = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        count += 1
            return count
        except Exception as e:
            print(f"[PanicJSONLManager] count_records({data_type}) failed: {e}")
            return 0
    
    def list_data_types(self):
        """列出所有数据类型"""
        try:
            types = []
            for f in self.base_dir.glob('*.jsonl'):
                name = f.stem
                if '_' in name:
                    # Remove date suffix if any
                    parts = name.rsplit('_', 1)
                    if len(parts[1]) == 8 and parts[1].isdigit():
                        types.append(parts[0])
                    else:
                        types.append(name)
                else:
                    types.append(name)
            return list(set(types))
        except Exception as e:
            print(f"[PanicJSONLManager] list_data_types failed: {e}")
            return []


if __name__ == '__main__':
    manager = PanicJSONLManager()
    types = manager.list_data_types()
    print(f"Data types: {types}")
    
    # Test sar_bias_stats
    latest = manager.get_latest('sar_bias_stats')
    print(f"SAR bias stats latest: {latest}")
