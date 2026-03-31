#!/usr/bin/env python3
"""
V1V2 JSONL Manager - V1V2数据管理
"""
import json
import os
from pathlib import Path


class V1V2JSONLManager:
    """V1V2 JSONL数据管理器"""
    
    def __init__(self, data_dir='/home/user/webapp/data/v1v2_jsonl'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def get_latest_data(self, symbol=None, limit=100):
        """获取最新的V1V2数据"""
        try:
            all_data = []
            for jsonl_file in sorted(self.data_dir.glob('*.jsonl'), reverse=True)[:10]:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if symbol is None or data.get('symbol') == symbol:
                                    all_data.append(data)
                            except json.JSONDecodeError:
                                continue
                
                if len(all_data) >= limit:
                    break
            
            all_data.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            return all_data[:limit]
            
        except Exception as e:
            print(f"[V1V2JSONLManager] 获取数据失败: {e}")
            return []
