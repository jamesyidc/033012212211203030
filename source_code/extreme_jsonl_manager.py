#!/usr/bin/env python3
"""
Extreme JSONL Manager - 极端信号数据管理
"""
import json
import os
from pathlib import Path
from datetime import datetime


class ExtremeJSONLManager:
    """极端信号JSONL数据管理器"""
    
    def __init__(self, data_dir='/home/user/webapp/data/extreme_jsonl'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def get_latest_signals(self, symbol=None, limit=100):
        """
        获取最新的极端信号
        
        Args:
            symbol: 交易对符号（可选）
            limit: 返回记录数
            
        Returns:
            list: 极端信号列表
        """
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
            print(f"[ExtremeJSONLManager] 获取数据失败: {e}")
            return []
