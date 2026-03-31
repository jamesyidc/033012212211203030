#!/usr/bin/env python3
"""
Panic Daily Manager - 恐慌指数数据管理器
读取和管理恐慌清洗指数数据
"""
import json
from pathlib import Path
from datetime import datetime
import pytz

BEIJING_TZ = pytz.timezone('Asia/Shanghai')


class PanicDailyManager:
    """恐慌清洗指数日数据管理器"""
    
    def __init__(self, data_dir='/home/user/webapp/data/panic_jsonl'):
        self.data_dir = Path(data_dir)
        self.jsonl_file = self.data_dir / 'panic_wash_index.jsonl'
    
    def get_latest_record(self):
        """获取最新的恐慌指数记录"""
        try:
            if not self.jsonl_file.exists():
                return None
            
            # 读取最后一行
            with open(self.jsonl_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if not lines:
                    return None
                
                last_line = lines[-1].strip()
                if not last_line:
                    return None
                
                record = json.loads(last_line)
                
                # 转换为 API 期望的格式
                panic_index = record.get('panic_index', 0)
                liquidation_data = record.get('liquidation_data', {})
                beijing_time = record.get('beijing_time', '')
                
                return {
                    'timestamp': record.get('timestamp'),
                    'beijing_time': beijing_time,
                    'data': {
                        'record_time': beijing_time,  # 添加 record_time 字段
                        'panic_index': panic_index,
                        'hour_1_amount': liquidation_data.get('liquidation_1h', 0),  # 万美元
                        'hour_24_amount': liquidation_data.get('liquidation_24h', 0),  # 万美元
                        'hour_24_people': liquidation_data.get('liquidation_count_24h', 0),  # 万人
                        'total_position': liquidation_data.get('open_interest', 0),  # 亿美元
                        'wash_index': panic_index  # 洗盘指数与恐慌指数相同
                    }
                }
                
        except Exception as e:
            print(f"[错误] 读取恐慌指数记录失败: {e}")
            return None
    
    def get_records_by_time_range(self, start_time, end_time, limit=100):
        """获取指定时间范围的记录"""
        try:
            if not self.jsonl_file.exists():
                return []
            
            records = []
            with open(self.jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record = json.loads(line)
                        timestamp = record.get('timestamp', 0)
                        
                        if start_time <= timestamp <= end_time:
                            records.append(record)
                            
                            if len(records) >= limit:
                                break
                    except:
                        continue
            
            return records[-limit:] if len(records) > limit else records
            
        except Exception as e:
            print(f"[错误] 读取时间范围记录失败: {e}")
            return []
    
    def get_latest_n_records(self, n=100):
        """获取最新的 N 条记录"""
        try:
            if not self.jsonl_file.exists():
                return []
            
            records = []
            with open(self.jsonl_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                # 从后往前读取最多 n 条
                for line in reversed(lines[-n:]):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        record = json.loads(line)
                        records.insert(0, record)  # 保持时间顺序
                    except:
                        continue
            
            return records
            
        except Exception as e:
            print(f"[错误] 读取最新记录失败: {e}")
            return []
    
    def get_latest_records(self, limit=1440, days_back=2):
        """获取最新的N条记录，转换为API期望的格式"""
        try:
            if not self.jsonl_file.exists():
                return []
            
            # 读取原始记录
            raw_records = self.get_latest_n_records(limit)
            
            # 转换为API期望的格式
            formatted_records = []
            for record in raw_records:
                # 检查是否是新格式（有beijing_time和liquidation_data）
                if 'beijing_time' in record and 'liquidation_data' in record:
                    # 新格式
                    panic_index = record.get('panic_index', 0)
                    liquidation_data = record.get('liquidation_data', {})
                    beijing_time = record.get('beijing_time', '')
                    
                    formatted_record = {
                        'timestamp': record.get('timestamp'),
                        'beijing_time': beijing_time,
                        'data': {
                            'record_time': beijing_time,
                            'panic_index': panic_index,
                            'hour_1_amount': liquidation_data.get('liquidation_1h', 0),
                            'hour_24_amount': liquidation_data.get('liquidation_24h', 0),
                            'hour_24_people': liquidation_data.get('liquidation_count_24h', 0),
                            'total_position': liquidation_data.get('open_interest', 0),
                            'wash_index': panic_index
                        }
                    }
                elif 'record_time' in record:
                    # 旧格式
                    formatted_record = {
                        'timestamp': record.get('timestamp', 0),
                        'beijing_time': record.get('record_time', ''),
                        'data': {
                            'record_time': record.get('record_time', ''),
                            'panic_index': record.get('panic_index', 0),
                            'hour_1_amount': record.get('hour_1_amount', 0),
                            'hour_24_amount': record.get('hour_24_amount', 0),
                            'hour_24_people': record.get('hour_24_people', 0),
                            'total_position': record.get('total_position', 0),
                            'wash_index': record.get('wash_index', 0)
                        }
                    }
                else:
                    # 跳过无法识别的格式
                    continue
                formatted_records.append(formatted_record)
            
            return formatted_records
            
        except Exception as e:
            print(f"[错误] 获取最新记录失败: {e}")
            return []
