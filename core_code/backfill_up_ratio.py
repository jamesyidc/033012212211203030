#!/usr/bin/env python3
"""
补全历史数据的 up_ratio, up_coins, down_coins 字段
"""
import json
import os
from pathlib import Path
from datetime import datetime

DATA_DIR = Path('/home/user/webapp/data/coin_change_tracker')

def calculate_up_ratio(changes):
    """计算上涨占比、上涨币数、下跌币数"""
    if not changes or not isinstance(changes, dict):
        return None, None, None
    
    up_coins = 0
    down_coins = 0
    
    for coin, data in changes.items():
        if isinstance(data, dict) and 'change_pct' in data:
            change_pct = data['change_pct']
            if change_pct > 0:
                up_coins += 1
            elif change_pct < 0:
                down_coins += 1
    
    total_coins = up_coins + down_coins
    if total_coins == 0:
        return 0, 0, 0
    
    up_ratio = round((up_coins / total_coins) * 100, 1)
    
    return up_ratio, up_coins, down_coins

def process_file(filepath):
    """处理单个文件，补全缺失的字段"""
    print(f"处理文件: {filepath.name}")
    
    # 读取所有行
    lines = []
    updated_count = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                
                # 检查是否缺少字段
                needs_update = False
                if 'up_ratio' not in data or 'up_coins' not in data or 'down_coins' not in data:
                    needs_update = True
                
                if needs_update and 'changes' in data:
                    up_ratio, up_coins, down_coins = calculate_up_ratio(data['changes'])
                    
                    if up_ratio is not None:
                        data['up_ratio'] = up_ratio
                        data['up_coins'] = up_coins
                        data['down_coins'] = down_coins
                        updated_count += 1
                
                lines.append(json.dumps(data, ensure_ascii=False))
            
            except json.JSONDecodeError as e:
                print(f"  错误: 解析JSON失败 - {e}")
                lines.append(line)
    
    if updated_count > 0:
        # 写回文件
        with open(filepath, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
        
        print(f"  ✅ 更新了 {updated_count} 条记录")
    else:
        print(f"  ⏭️  无需更新")
    
    return updated_count

def main():
    """主函数"""
    print("开始补全历史数据的 up_ratio 字段...\n")
    
    # 获取所有2月份的数据文件
    files = sorted(DATA_DIR.glob('coin_change_202602*.jsonl'))
    
    if not files:
        print("❌ 未找到2月份的数据文件")
        return
    
    print(f"找到 {len(files)} 个文件\n")
    
    total_updated = 0
    
    for filepath in files:
        updated = process_file(filepath)
        total_updated += updated
    
    print(f"\n✅ 完成！总共更新了 {total_updated} 条记录")

if __name__ == '__main__':
    main()
