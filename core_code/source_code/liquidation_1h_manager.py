#!/usr/bin/env python3
"""
Liquidation 1H Manager - 1小时爆仓数据管理器
从 panic_wash_index.jsonl 读取爆仓数据，提供给前端图表使用
"""
import json
from pathlib import Path
from datetime import datetime
import pytz

BEIJING_TZ = pytz.timezone('Asia/Shanghai')


class Liquidation1HManager:
    """1小时爆仓数据管理器"""
    
    def __init__(self, data_dir='/home/user/webapp/data/panic_jsonl'):
        self.data_dir = Path(data_dir)
        self.jsonl_file = self.data_dir / 'panic_wash_index.jsonl'
    
    def get_range(self, start_time=None, end_time=None, limit=1440):
        """获取指定范围的数据
        
        Args:
            start_time: 开始时间（格式: YYYY-MM-DD HH:MM:SS）
            end_time: 结束时间（格式: YYYY-MM-DD HH:MM:SS）
            limit: 最多返回的记录数
        
        Returns:
            list: 爆仓数据列表
        """
        try:
            if not self.jsonl_file.exists():
                return []
            
            records = []
            
            # 转换时间为timestamp
            start_ts = None
            end_ts = None
            if start_time:
                try:
                    dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                    dt = BEIJING_TZ.localize(dt)
                    start_ts = int(dt.timestamp())
                except:
                    pass
            
            if end_time:
                try:
                    dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                    dt = BEIJING_TZ.localize(dt)
                    end_ts = int(dt.timestamp())
                except:
                    pass
            
            # 读取所有记录
            with open(self.jsonl_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 从后往前读取，获取最新的记录
            for line in reversed(lines):
                if len(records) >= limit:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                    
                    # 检查时间范围
                    timestamp = record.get('timestamp', 0)
                    if start_ts and timestamp < start_ts:
                        continue
                    if end_ts and timestamp > end_ts:
                        continue
                    
                    # 提取需要的字段并转换格式
                    formatted_record = self._format_record(record)
                    if formatted_record:
                        records.insert(0, formatted_record)  # 插入到开头，保持时间顺序
                        
                except Exception as e:
                    continue
            
            return records
            
        except Exception as e:
            print(f"[错误] 读取爆仓数据失败: {e}")
            return []
    
    def get_latest(self, limit=1):
        """获取最新的N条记录"""
        return self.get_range(limit=limit)
    
    def _format_record(self, record):
        """格式化记录为前端期望的格式"""
        try:
            # 检查是否是新格式（有beijing_time和liquidation_data）
            if 'beijing_time' in record and 'liquidation_data' in record:
                # 新格式
                liquidation_data = record.get('liquidation_data', {})
                beijing_time = record.get('beijing_time', '')
                
                return {
                    'record_time': beijing_time,
                    'hour_1_amount': liquidation_data.get('liquidation_1h', 0),  # 万美元
                    'hour_24_amount': liquidation_data.get('liquidation_24h', 0),  # 万美元
                    'hour_24_people': liquidation_data.get('liquidation_count_24h', 0),  # 万人
                    'total_position': liquidation_data.get('open_interest', 0),  # 亿美元
                    'panic_index': record.get('panic_index', 0),
                    'wash_index': record.get('panic_index', 0)
                }
            elif 'record_time' in record:
                # 旧格式
                return {
                    'record_time': record.get('record_time', ''),
                    'hour_1_amount': record.get('hour_1_amount', 0),
                    'hour_24_amount': record.get('hour_24_amount', 0),
                    'hour_24_people': record.get('hour_24_people', 0),
                    'total_position': record.get('total_position', 0),
                    'panic_index': record.get('panic_index', 0),
                    'wash_index': record.get('wash_index', 0)
                }
            else:
                return None
                
        except Exception as e:
            print(f"[错误] 格式化记录失败: {e}")
            return None


if __name__ == '__main__':
    # 测试
    manager = Liquidation1HManager()
    
    print("=" * 60)
    print("测试 Liquidation1HManager")
    print("=" * 60)
    
    # 获取最新10条
    latest_10 = manager.get_latest(limit=10)
    print(f"\n最新10条记录：")
    for record in latest_10:
        print(f"  时间: {record['record_time']}, 1h爆仓: {record['hour_1_amount']}万$")
    
    # 获取最近24小时的数据
    latest_1440 = manager.get_range(limit=1440)
    print(f"\n最近1440条记录数: {len(latest_1440)}")
    if latest_1440:
        print(f"  最早: {latest_1440[0]['record_time']}")
        print(f"  最晚: {latest_1440[-1]['record_time']}")
