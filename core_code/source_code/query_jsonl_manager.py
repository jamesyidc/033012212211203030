#!/usr/bin/env python3
"""
Query JSONL Manager - 管理查询数据的JSONL存储
"""
import os
import json
from datetime import datetime
from pathlib import Path


class QueryJSONLManager:
    """查询数据JSONL管理器"""
    
    def __init__(self, data_dir='/home/user/webapp/data/query_jsonl'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def query_data(self, filters=None, limit=100):
        """
        查询数据
        
        Args:
            filters: 过滤条件（dict）
            limit: 返回的记录数
            
        Returns:
            list: 查询结果
        """
        try:
            results = []
            
            # 读取JSONL文件
            for jsonl_file in sorted(self.data_dir.glob('*.jsonl'), reverse=True):
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                
                                # 应用过滤条件
                                if filters:
                                    match = True
                                    for key, value in filters.items():
                                        if data.get(key) != value:
                                            match = False
                                            break
                                    if match:
                                        results.append(data)
                                else:
                                    results.append(data)
                                    
                            except json.JSONDecodeError:
                                continue
                
                if len(results) >= limit:
                    break
            
            return results[:limit]
            
        except Exception as e:
            print(f"[QueryJSONLManager] 查询失败: {e}")
            return []
    
    def save_query_result(self, query_data):
        """
        保存查询结果
        
        Args:
            query_data: 查询结果数据
        """
        try:
            date_str = datetime.now().strftime('%Y%m%d')
            jsonl_file = self.data_dir / f'query_{date_str}.jsonl'
            
            with open(jsonl_file, 'a', encoding='utf-8') as f:
                if isinstance(query_data, list):
                    for item in query_data:
                        f.write(json.dumps(item, ensure_ascii=False) + '\n')
                else:
                    f.write(json.dumps(query_data, ensure_ascii=False) + '\n')
            
            return True
            
        except Exception as e:
            print(f"[QueryJSONLManager] 保存查询结果失败: {e}")
            return False
