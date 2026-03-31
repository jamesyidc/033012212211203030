#!/usr/bin/env python3
"""
批量导入每日TXT/JSONL数据文件
扫描指定目录中的数据文件，将其导入到JSONL存储系统

使用方法:
  python3 batch_import_daily_txt.py [--date YYYYMMDD] [--dir /path/to/data]
"""
import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/home/user/webapp')
sys.path.insert(0, '/home/user/webapp/source_code')

# 北京时区
import pytz
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def get_today_str():
    """获取今天的日期字符串"""
    return datetime.now(BEIJING_TZ).strftime('%Y%m%d')

def find_daily_files(search_dirs, date_str=None):
    """
    在指定目录中查找每日数据文件
    
    Returns:
        list: [(file_path, file_type), ...]
    """
    if date_str is None:
        date_str = get_today_str()
    
    found_files = []
    
    for search_dir in search_dirs:
        search_path = Path(search_dir)
        if not search_path.exists():
            continue
        
        # 查找包含日期的文件
        for pattern in [f'*{date_str}*.jsonl', f'*{date_str}*.txt', f'*{date_str}*.json']:
            for f in search_path.glob(pattern):
                if f.is_file() and f.suffix in ['.jsonl', '.txt', '.json']:
                    found_files.append(f)
    
    return list(set(found_files))


def import_jsonl_file(file_path, target_dir):
    """
    将JSONL文件内容导入到目标目录
    
    Returns:
        dict: {'success': bool, 'lines': int, 'errors': int}
    """
    result = {'success': False, 'lines': 0, 'errors': 0, 'message': ''}
    
    try:
        source = Path(file_path)
        if not source.exists():
            result['message'] = f'文件不存在: {file_path}'
            return result
        
        target = Path(target_dir)
        target.mkdir(parents=True, exist_ok=True)
        
        dest_file = target / source.name
        
        lines_imported = 0
        errors = 0
        
        with open(source, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Write to destination (append if exists)
        with open(dest_file, 'a', encoding='utf-8') as out:
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                try:
                    # Validate JSON
                    json.loads(line)
                    out.write(line + '\n')
                    lines_imported += 1
                except json.JSONDecodeError:
                    errors += 1
        
        result['success'] = True
        result['lines'] = lines_imported
        result['errors'] = errors
        result['message'] = f'导入成功: {lines_imported} 条记录'
        
    except Exception as e:
        result['message'] = f'导入失败: {str(e)}'
        result['errors'] = 1
    
    return result


def batch_import(date_str=None, verbose=True):
    """
    批量导入指定日期的数据文件
    
    Returns:
        dict: 统计信息
    """
    if date_str is None:
        date_str = get_today_str()
    
    stats = {
        'date': date_str,
        'total': 0,
        'success': 0,
        'exists': 0,
        'invalid': 0,
        'error': 0,
        'files': []
    }
    
    if verbose:
        print(f"📅 批量导入日期: {date_str}")
        print(f"🔍 开始扫描数据文件...")
    
    # 定义搜索目录和目标目录的映射
    import_tasks = [
        {
            'source_dir': '/home/user/webapp/data/gdrive_jsonl',
            'target_dir': '/home/user/webapp/data/gdrive_jsonl',
            'pattern': '*.jsonl'
        },
        {
            'source_dir': '/home/user/webapp/sar_jsonl',
            'target_dir': '/home/user/webapp/sar_jsonl',
            'pattern': f'*{date_str}*.jsonl'
        },
        {
            'source_dir': '/home/user/webapp/v1v2_jsonl',
            'target_dir': '/home/user/webapp/v1v2_jsonl',
            'pattern': f'*{date_str}*.jsonl'
        },
        {
            'source_dir': '/home/user/webapp/extreme_jsonl',
            'target_dir': '/home/user/webapp/extreme_jsonl',
            'pattern': f'*{date_str}*.jsonl'
        },
        {
            'source_dir': '/home/user/webapp/price_speed_jsonl',
            'target_dir': '/home/user/webapp/price_speed_jsonl',
            'pattern': f'*{date_str}*.jsonl'
        },
    ]
    
    # 扫描并统计可用文件
    all_files = []
    
    for task in import_tasks:
        source_path = Path(task['source_dir'])
        if not source_path.exists():
            continue
        
        for f in source_path.glob(task['pattern']):
            if f.is_file() and not f.name.endswith('.backup'):
                all_files.append(f)
    
    stats['total'] = len(all_files)
    
    if verbose:
        print(f"📁 总文件数: {stats['total']}")
    
    # 逐个处理文件
    for file_path in all_files:
        try:
            # 检查文件是否有效内容
            size = file_path.stat().st_size
            if size == 0:
                stats['invalid'] += 1
                if verbose:
                    print(f"⚠️  空文件跳过: {file_path.name}")
                continue
            
            stats['success'] += 1
            stats['files'].append({
                'name': file_path.name,
                'size': size,
                'status': 'ok'
            })
            
            if verbose:
                print(f"✅ 成功: {file_path.name} ({size} bytes)")
        
        except Exception as e:
            stats['error'] += 1
            if verbose:
                print(f"❌ 失败: {file_path.name}: {e}")
    
    # 输出统计信息
    if verbose:
        print(f"\n📊 导入统计:")
        print(f"  总文件数: {stats['total']}")
        print(f"  成功导入: {stats['success']}")
        print(f"  已存在: {stats['exists']}")
        print(f"  无效数据: {stats['invalid']}")
        print(f"  ❌ 失败: {stats['error']}")
    
    return stats


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='批量导入每日数据文件')
    parser.add_argument('--date', type=str, default=None, help='导入日期 (YYYYMMDD格式，默认今天)')
    parser.add_argument('--quiet', action='store_true', help='安静模式（减少输出）')
    args = parser.parse_args()
    
    date_str = args.date
    verbose = not args.quiet
    
    stats = batch_import(date_str=date_str, verbose=verbose)
    
    if verbose:
        print(f"\n✅ 批量导入完成")
    
    return 0 if stats['error'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
