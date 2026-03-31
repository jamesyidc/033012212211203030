#!/usr/bin/env python3
"""
数据管理系统 - 统计和管理所有JSONL数据
扫描data目录下的所有JSONL文件，统计数据量和日期范围
"""
import os
import json
from datetime import datetime
from collections import defaultdict
from pathlib import Path

class DataManager:
    def __init__(self, data_dir='data'):
        self.data_dir = Path(data_dir)
        self.stats = {}
        
    def scan_all_data(self):
        """扫描所有JSONL文件并统计"""
        print(f"🔍 开始扫描数据目录: {self.data_dir}")
        
        # 按子目录分类统计
        dir_stats = defaultdict(lambda: {
            'files': [],
            'total_records': 0,
            'total_size': 0,
            'date_range': {'min': None, 'max': None}
        })
        
        # 遍历所有JSONL文件
        for jsonl_file in self.data_dir.rglob('*.jsonl'):
            relative_path = jsonl_file.relative_to(self.data_dir)
            parent_dir = str(relative_path.parent) if relative_path.parent != Path('.') else 'root'
            
            # 统计文件信息
            file_info = self.analyze_file(jsonl_file)
            
            # 添加到目录统计
            dir_stats[parent_dir]['files'].append({
                'name': jsonl_file.name,
                'path': str(relative_path),
                'records': file_info['records'],
                'size': file_info['size'],
                'size_mb': file_info['size_mb'],
                'dates': file_info['dates'],
                'modified': file_info['modified']
            })
            
            dir_stats[parent_dir]['total_records'] += file_info['records']
            dir_stats[parent_dir]['total_size'] += file_info['size']
            
            # 更新日期范围
            if file_info['dates']['min']:
                if not dir_stats[parent_dir]['date_range']['min'] or \
                   file_info['dates']['min'] < dir_stats[parent_dir]['date_range']['min']:
                    dir_stats[parent_dir]['date_range']['min'] = file_info['dates']['min']
                    
            if file_info['dates']['max']:
                if not dir_stats[parent_dir]['date_range']['max'] or \
                   file_info['dates']['max'] > dir_stats[parent_dir]['date_range']['max']:
                    dir_stats[parent_dir]['date_range']['max'] = file_info['dates']['max']
        
        self.stats = dict(dir_stats)
        return self.stats
    
    def analyze_file(self, file_path):
        """分析单个JSONL文件"""
        records = 0
        dates = {'min': None, 'max': None}
        
        try:
            # 统计行数
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        records += 1
                        
                        # 尝试提取日期信息
                        try:
                            data = json.loads(line)
                            date_str = self.extract_date(data)
                            if date_str:
                                if not dates['min'] or date_str < dates['min']:
                                    dates['min'] = date_str
                                if not dates['max'] or date_str > dates['max']:
                                    dates['max'] = date_str
                        except:
                            pass
            
            # 文件大小
            size = os.path.getsize(file_path)
            size_mb = round(size / (1024 * 1024), 2)
            
            # 修改时间
            modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'records': records,
                'size': size,
                'size_mb': size_mb,
                'dates': dates,
                'modified': modified
            }
        except Exception as e:
            print(f"  ⚠️ 分析文件失败 {file_path}: {e}")
            return {
                'records': 0,
                'size': 0,
                'size_mb': 0,
                'dates': dates,
                'modified': 'unknown'
            }
    
    def extract_date(self, data):
        """从JSON数据中提取日期"""
        # 常见的日期字段
        date_fields = ['date', 'time', 'timestamp', 'snapshot_time', 'created_at', 'updated_at']
        
        for field in date_fields:
            if field in data:
                value = data[field]
                if isinstance(value, str):
                    # 提取日期部分 (YYYY-MM-DD)
                    if len(value) >= 10:
                        return value[:10]
        
        return None
    
    def print_summary(self):
        """打印统计摘要"""
        if not self.stats:
            print("⚠️ 没有统计数据，请先运行 scan_all_data()")
            return
        
        print("\n" + "="*80)
        print("📊 数据统计摘要")
        print("="*80)
        
        # 总体统计
        total_dirs = len(self.stats)
        total_files = sum(len(d['files']) for d in self.stats.values())
        total_records = sum(d['total_records'] for d in self.stats.values())
        total_size_mb = sum(d['total_size'] for d in self.stats.values()) / (1024 * 1024)
        
        print(f"\n📁 总目录数: {total_dirs}")
        print(f"📄 总文件数: {total_files}")
        print(f"📝 总记录数: {total_records:,}")
        print(f"💾 总大小: {total_size_mb:.2f} MB")
        
        # 按目录统计
        print("\n" + "-"*80)
        print("📂 各系统数据统计")
        print("-"*80)
        
        # 排序：按记录数降序
        sorted_dirs = sorted(self.stats.items(), key=lambda x: x[1]['total_records'], reverse=True)
        
        for dir_name, info in sorted_dirs:
            print(f"\n📁 {dir_name}")
            print(f"   文件数: {len(info['files'])} 个")
            print(f"   记录数: {info['total_records']:,} 条")
            print(f"   大小: {info['total_size'] / (1024 * 1024):.2f} MB")
            
            if info['date_range']['min'] and info['date_range']['max']:
                date_min = info['date_range']['min']
                date_max = info['date_range']['max']
                
                # 计算天数
                try:
                    d1 = datetime.strptime(date_min, '%Y-%m-%d')
                    d2 = datetime.strptime(date_max, '%Y-%m-%d')
                    days = (d2 - d1).days + 1
                    print(f"   日期范围: {date_min} 至 {date_max} ({days} 天)")
                except:
                    print(f"   日期范围: {date_min} 至 {date_max}")
            
            # 显示部分文件
            if len(info['files']) <= 5:
                for file_info in info['files']:
                    print(f"      • {file_info['name']}: {file_info['records']} 条记录")
            else:
                print(f"      • 最近的5个文件:")
                # 按修改时间排序
                sorted_files = sorted(info['files'], key=lambda x: x['modified'], reverse=True)
                for file_info in sorted_files[:5]:
                    print(f"        - {file_info['name']}: {file_info['records']} 条, {file_info['size_mb']} MB, 修改于 {file_info['modified']}")
    
    def save_report(self, output_file='data_statistics.json'):
        """保存统计报告为JSON"""
        report = {
            'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_directories': len(self.stats),
                'total_files': sum(len(d['files']) for d in self.stats.values()),
                'total_records': sum(d['total_records'] for d in self.stats.values()),
                'total_size_mb': sum(d['total_size'] for d in self.stats.values()) / (1024 * 1024)
            },
            'directories': self.stats
        }
        
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 统计报告已保存到: {output_path}")
        return output_path

if __name__ == '__main__':
    # 运行数据管理器
    manager = DataManager(data_dir='data')
    
    print("🚀 启动数据管理系统...")
    stats = manager.scan_all_data()
    
    # 打印摘要
    manager.print_summary()
    
    # 保存报告
    manager.save_report('data/data_statistics.json')
    
    print("\n✅ 数据扫描完成！")
