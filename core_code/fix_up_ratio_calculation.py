#!/usr/bin/env python3
"""
修复历史数据的 up_ratio 计算错误
问题：之前的计算包含了 change_pct == 0 的币种
正确：只应该统计 change_pct != 0 的币种
"""
import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path('/home/user/webapp/data/coin_change_tracker')

def fix_record(record):
    """修复单条记录的 up_ratio, up_coins, down_coins"""
    if 'changes' not in record:
        return record, False
    
    changes = record['changes']
    
    # 重新计算
    up_coins = sum(1 for item in changes.values() if item['change_pct'] > 0)
    down_coins = sum(1 for item in changes.values() if item['change_pct'] < 0)
    total_coins = up_coins + down_coins  # 只计算有涨跌的币种
    
    # 计算正确的 up_ratio
    up_ratio = round((up_coins / total_coins * 100), 1) if total_coins > 0 else 0
    
    # 检查是否需要更新
    needs_update = False
    if record.get('up_ratio') != up_ratio or record.get('up_coins') != up_coins or record.get('down_coins') != down_coins:
        needs_update = True
        old_values = f"up_ratio:{record.get('up_ratio')}, up_coins:{record.get('up_coins')}, down_coins:{record.get('down_coins')}"
        new_values = f"up_ratio:{up_ratio}, up_coins:{up_coins}, down_coins:{down_coins}"
        print(f"  [{record.get('beijing_time', 'N/A')}] 修正: {old_values} -> {new_values}")
    
    # 更新记录
    record['up_ratio'] = up_ratio
    record['up_coins'] = up_coins
    record['down_coins'] = down_coins
    
    return record, needs_update

def fix_file(filepath):
    """修复单个文件"""
    print(f"\n处理文件: {filepath.name}")
    
    lines = []
    updated_count = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                fixed_record, was_updated = fix_record(record)
                
                if was_updated:
                    updated_count += 1
                
                lines.append(json.dumps(fixed_record, ensure_ascii=False))
                
            except json.JSONDecodeError as e:
                print(f"  ⚠️ JSON解析错误: {e}")
                lines.append(line)
    
    # 写回文件
    if updated_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
        print(f"✅ 修正了 {updated_count} 条记录")
    else:
        print(f"✓ 无需修正")
    
    return updated_count

def main():
    """主函数"""
    print("=" * 60)
    print("修复 up_ratio 计算错误")
    print("=" * 60)
    
    # 获取今天的数据文件
    today = datetime.now().strftime('%Y%m%d')
    today_file = DATA_DIR / f'coin_change_{today}.jsonl'
    
    if not today_file.exists():
        print(f"❌ 今天的数据文件不存在: {today_file}")
        return
    
    total_updated = fix_file(today_file)
    
    print("\n" + "=" * 60)
    print(f"✅ 完成！总共修正了 {total_updated} 条记录")
    print("=" * 60)

if __name__ == '__main__':
    main()
