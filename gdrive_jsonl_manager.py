#!/usr/bin/env python3
"""
GDrive JSONL Manager - 管理Google Drive的JSONL数据
"""
import os
import json
import time
from datetime import datetime
from pathlib import Path


class GDriveJSONLManager:
    """Google Drive JSONL数据管理器"""
    
    def __init__(self, data_dir='/home/user/webapp/data/gdrive_jsonl'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def get_latest_data(self, symbol=None, limit=100):
        """
        获取最新的数据
        
        Args:
            symbol: 交易对符号（可选）
            limit: 返回的记录数
            
        Returns:
            list: 数据记录列表
        """
        try:
            # 读取所有JSONL文件
            all_data = []
            for jsonl_file in sorted(self.data_dir.glob('*.jsonl'), reverse=True):
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
            
            # 按时间戳排序并返回最新的记录
            all_data.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            return all_data[:limit]
            
        except Exception as e:
            print(f"[GDriveJSONLManager] 获取数据失败: {e}")
            return []
    
    def save_data(self, data):
        """
        保存数据到JSONL文件
        
        Args:
            data: 要保存的数据（dict或list）
        """
        try:
            # 按日期创建文件
            date_str = datetime.now().strftime('%Y%m%d')
            jsonl_file = self.data_dir / f'gdrive_{date_str}.jsonl'
            
            # 追加写入
            with open(jsonl_file, 'a', encoding='utf-8') as f:
                if isinstance(data, list):
                    for item in data:
                        f.write(json.dumps(item, ensure_ascii=False) + '\n')
                else:
                    f.write(json.dumps(data, ensure_ascii=False) + '\n')
            
            print(f"[GDriveJSONLManager] 数据已保存到 {jsonl_file}")
            return True
            
        except Exception as e:
            print(f"[GDriveJSONLManager] 保存数据失败: {e}")
            return False


def main():
    """主函数 - 作为守护进程运行"""
    print(f"[{datetime.now()}] GDrive JSONL Manager 启动...")
    manager = GDriveJSONLManager()
    
    while True:
        try:
            print(f"[{datetime.now()}] GDrive JSONL Manager 正在运行...")
            time.sleep(60)
        except Exception as e:
            print(f"[{datetime.now()}] 错误: {e}")
            time.sleep(10)


if __name__ == '__main__':
    main()
