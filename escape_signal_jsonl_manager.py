#!/usr/bin/env python3
"""
Escape Signal JSONL Manager
管理逃顶信号的JSONL存储
"""
import os
import json
import gzip
from datetime import datetime, timedelta
from pathlib import Path


class EscapeSignalJSONLManager:
    """逃顶信号JSONL管理器"""
    
    def __init__(self, data_dir='/home/user/webapp/escape_signal_jsonl'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.daily_dir = Path('/home/user/webapp/escape_signal_daily')
        self.daily_dir.mkdir(parents=True, exist_ok=True)
        
        # 主要存储文件
        self.peaks_file = self.data_dir / 'escape_signal_peaks.jsonl'
        self.stats_file = self.data_dir / 'escape_signal_stats.jsonl'
    
    def get_latest_peaks(self, limit=100):
        """获取最新的关键点数据"""
        try:
            if not self.peaks_file.exists():
                return []
            
            records = []
            with open(self.peaks_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            
            return records[-limit:] if len(records) > limit else records
        except Exception as e:
            print(f"[EscapeSignalJSONLManager] get_latest_peaks failed: {e}")
            return []
    
    def get_peaks_by_date(self, date_str):
        """按日期获取关键点数据"""
        try:
            # Check compressed daily files first
            gz_file = self.daily_dir / f'escape_signal_{date_str}.jsonl.gz'
            plain_file = self.daily_dir / f'escape_signal_{date_str}.jsonl'
            
            records = []
            
            if gz_file.exists():
                with gzip.open(gz_file, 'rt', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                records.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
            elif plain_file.exists():
                with open(plain_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                records.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
            else:
                # Fallback to peaks file filtered by date
                if self.peaks_file.exists():
                    with open(self.peaks_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    record = json.loads(line)
                                    ts = record.get('timestamp', record.get('time', ''))
                                    if date_str in str(ts):
                                        records.append(record)
                                except json.JSONDecodeError:
                                    continue
            
            return records
        except Exception as e:
            print(f"[EscapeSignalJSONLManager] get_peaks_by_date failed: {e}")
            return []
    
    def get_available_dates(self):
        """获取可用的日期列表"""
        try:
            dates = set()
            
            # From daily gz files
            for gz_file in self.daily_dir.glob('escape_signal_*.jsonl.gz'):
                name = gz_file.stem.replace('.jsonl', '')
                date_part = name.replace('escape_signal_', '')
                dates.add(date_part)
            
            # From daily jsonl files
            for f in self.daily_dir.glob('escape_signal_*.jsonl'):
                name = f.stem
                date_part = name.replace('escape_signal_', '')
                dates.add(date_part)
            
            return sorted(list(dates), reverse=True)
        except Exception as e:
            print(f"[EscapeSignalJSONLManager] get_available_dates failed: {e}")
            return []
    
    def get_stats(self, limit=30):
        """获取统计数据"""
        try:
            if not self.stats_file.exists():
                return []
            
            records = []
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            
            return records[-limit:] if len(records) > limit else records
        except Exception as e:
            print(f"[EscapeSignalJSONLManager] get_stats failed: {e}")
            return []
    
    def get_latest_snapshot(self):
        """获取最新快照"""
        try:
            if self.peaks_file.exists():
                last_record = None
                with open(self.peaks_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                last_record = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                return last_record
            return None
        except Exception as e:
            print(f"[EscapeSignalJSONLManager] get_latest_snapshot failed: {e}")
            return None
    
    def get_recent_data(self, hours=24):
        """获取最近N小时的数据"""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            records = []
            
            if self.peaks_file.exists():
                with open(self.peaks_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                record = json.loads(line)
                                ts = record.get('timestamp', record.get('time', ''))
                                if ts:
                                    try:
                                        # Parse timestamp
                                        if isinstance(ts, (int, float)):
                                            rec_time = datetime.fromtimestamp(ts)
                                        else:
                                            rec_time = datetime.fromisoformat(str(ts)[:19])
                                        if rec_time >= cutoff:
                                            records.append(record)
                                    except Exception:
                                        records.append(record)  # Include if can't parse
                            except json.JSONDecodeError:
                                continue
            
            return records
        except Exception as e:
            print(f"[EscapeSignalJSONLManager] get_recent_data failed: {e}")
            return []
    
    def save_snapshot(self, data):
        """保存快照"""
        try:
            with open(self.peaks_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
            return True
        except Exception as e:
            print(f"[EscapeSignalJSONLManager] save_snapshot failed: {e}")
            return False


if __name__ == '__main__':
    manager = EscapeSignalJSONLManager()
    dates = manager.get_available_dates()
    print(f"Available dates: {dates[:5]}")
    latest = manager.get_latest_snapshot()
    print(f"Latest snapshot: {latest}")
