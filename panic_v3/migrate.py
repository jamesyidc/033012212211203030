#!/usr/bin/env python3
"""
数据迁移脚本
从旧的panic_wash_index.jsonl迁移到新的按日分文件格式
"""

import json
from pathlib import Path
from datetime import datetime
import pytz
from collections import defaultdict

BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 路径配置
OLD_DATA_FILE = Path('/home/user/webapp/data/panic_jsonl/panic_wash_index.jsonl')
NEW_DATA_DIR = Path('/home/user/webapp/panic_v3/data')


def migrate_data():
    """迁移旧数据到新格式"""
    
    if not OLD_DATA_FILE.exists():
        print(f"[错误] 旧数据文件不存在: {OLD_DATA_FILE}")
        return
    
    print(f"[开始] 从 {OLD_DATA_FILE} 迁移数据...")
    
    # 按日期分组
    daily_data = defaultdict(list)
    total_count = 0
    success_count = 0
    error_count = 0
    
    # 读取旧数据
    with open(OLD_DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            total_count += 1
            
            try:
                old_record = json.loads(line)
                
                # 转换为新格式
                new_record = convert_record(old_record)
                
                if new_record:
                    # 提取日期
                    beijing_time = new_record.get('beijing_time', '')
                    if beijing_time:
                        date_str = beijing_time.split(' ')[0].replace('-', '')  # YYYYMMDD
                        daily_data[date_str].append(new_record)
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                print(f"[错误] 解析记录失败: {e}")
                error_count += 1
    
    print(f"\n[统计] 总记录数: {total_count}")
    print(f"[统计] 成功转换: {success_count}")
    print(f"[统计] 失败记录: {error_count}")
    print(f"[统计] 涵盖日期: {len(daily_data)} 天")
    
    # 按日期写入文件
    NEW_DATA_DIR.mkdir(exist_ok=True)
    
    for date_str, records in sorted(daily_data.items()):
        file_path = NEW_DATA_DIR / f'panic_{date_str}.jsonl'
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        print(f"[保存] {date_str}: {len(records)} 条记录 -> {file_path}")
    
    print(f"\n[完成] 数据迁移完成！")
    print(f"[路径] 新数据目录: {NEW_DATA_DIR.absolute()}")


def convert_record(old_record):
    """
    转换旧格式记录到新格式
    
    旧格式可能的字段:
    - beijing_time / record_time
    - liquidation_data.liquidation_1h / hour_1_amount
    - liquidation_data.liquidation_24h / hour_24_amount
    - liquidation_data.liquidation_count_24h / hour_24_people
    - liquidation_data.open_interest / total_position
    - panic_index
    - level
    
    新格式:
    {
        'liquidation_1h': float,
        'liquidation_24h': float,
        'liquidation_count_24h': float,
        'open_interest': float,
        'panic_index': float,
        'panic_level': str,
        'timestamp': int,
        'beijing_time': str
    }
    """
    try:
        # 提取时间
        beijing_time = old_record.get('beijing_time') or old_record.get('record_time', '')
        if not beijing_time:
            return None
        
        # 计算时间戳
        try:
            dt = datetime.strptime(beijing_time, '%Y-%m-%d %H:%M:%S')
            dt = BEIJING_TZ.localize(dt)
            timestamp = int(dt.timestamp() * 1000)
        except:
            timestamp = old_record.get('timestamp', 0)
        
        # 提取爆仓数据
        liq_data = old_record.get('liquidation_data', {})
        
        liquidation_1h = liq_data.get('liquidation_1h') or old_record.get('hour_1_amount', 0)
        liquidation_24h = liq_data.get('liquidation_24h') or old_record.get('hour_24_amount', 0)
        liquidation_count_24h = liq_data.get('liquidation_count_24h') or old_record.get('hour_24_people', 0)
        open_interest = liq_data.get('open_interest') or old_record.get('total_position', 0)
        
        # 提取恐慌指数
        panic_index = old_record.get('panic_index', 0)
        
        # 确定恐慌级别
        level = old_record.get('level', '')
        if not level:
            if panic_index > 0.15:
                level = '高恐慌'
            elif panic_index > 0.08:
                level = '中等恐慌'
            else:
                level = '低恐慌'
        else:
            # 转换英文级别到中文
            level_map = {
                'high': '高恐慌',
                'medium': '中等恐慌',
                'low': '低恐慌'
            }
            level = level_map.get(level, level)
        
        # 构建新记录
        new_record = {
            'liquidation_1h': round(float(liquidation_1h), 2),
            'liquidation_24h': round(float(liquidation_24h), 2),
            'liquidation_count_24h': round(float(liquidation_count_24h), 2),
            'open_interest': round(float(open_interest), 2),
            'panic_index': round(float(panic_index), 4),
            'panic_level': level,
            'timestamp': timestamp,
            'beijing_time': beijing_time
        }
        
        return new_record
        
    except Exception as e:
        print(f"[错误] 转换记录失败: {e}")
        return None


if __name__ == '__main__':
    migrate_data()
