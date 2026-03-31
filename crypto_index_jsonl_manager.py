#!/usr:bin/env python3
"""
Crypto Index JSONL Manager - 加密货币指数数据管理
"""
import json
import os
from pathlib import Path


class CryptoIndexJSONLManager:
    """加密货币指数JSONL数据管理器"""
    
    def __init__(self, data_dir='/home/user/webapp/data/crypto_index_jsonl'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def get_latest_index(self, limit=100):
        """获取最新的加密货币指数"""
        try:
            all_data = []
            for jsonl_file in sorted(self.data_dir.glob('*.jsonl'), reverse=True)[:10]:
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                all_data.append(data)
                            except json.JSONDecodeError:
                                continue
                
                if len(all_data) >= limit:
                    break
            
            all_data.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            return all_data[:limit]
            
        except Exception as e:
            print(f"[CryptoIndexJSONLManager] 获取数据失败: {e}")
            return []
