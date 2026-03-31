#!/usr/bin/env python3
"""
Anchor Daily Reader - 读取每日锚点数据
"""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path


class AnchorDailyReader:
    """锚点每日数据读取器"""
    
    def __init__(self, data_dir='/home/user/webapp/data/anchor_daily'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._cache = {}
    
    def get_anchor_data(self, symbol=None, days=7):
        """
        获取锚点数据
        
        Args:
            symbol: 交易对符号（可选）
            days: 获取最近几天的数据
            
        Returns:
            list: 锚点数据列表
        """
        try:
            all_data = []
            
            # 生成最近N天的日期
            date_list = []
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                date_list.append(date.strftime('%Y%m%d'))
            
            # 读取每天的数据文件
            for date_str in date_list:
                jsonl_file = self.data_dir / f'anchor_daily_{date_str}.jsonl'
                
                if jsonl_file.exists():
                    with open(jsonl_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    if symbol is None or data.get('symbol') == symbol:
                                        all_data.append(data)
                                except json.JSONDecodeError:
                                    continue
            
            # 按时间戳排序
            all_data.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            return all_data
            
        except Exception as e:
            print(f"[AnchorDailyReader] 读取数据失败: {e}")
            return []
    
    def get_latest_anchor(self, symbol):
        """
        获取指定交易对的最新锚点
        
        Args:
            symbol: 交易对符号
            
        Returns:
            dict: 最新锚点数据
        """
        data_list = self.get_anchor_data(symbol=symbol, days=1)
        return data_list[0] if data_list else None
    
    def clear_cache(self):
        """清除缓存"""
        self._cache = {}
