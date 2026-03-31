#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成指定日期的预测数据
使用修正后的逻辑（绿柱>=3根才判定为低吸）
"""

import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from monitors.coin_change_prediction_monitor import determine_market_signal, analyze_bar_colors, fetch_coin_change_history

def regenerate_prediction(date_str):
    """
    重新生成指定日期的预测数据
    
    Args:
        date_str: 日期字符串，格式：YYYY-MM-DD
    """
    # 构造文件路径
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    output_file = f"data/daily_predictions/prediction_{date_obj.strftime('%Y%m%d')}.jsonl"
    
    # 获取0-2点数据
    print(f"📊 正在分析 {date_str} 的0-2点数据...")
    data = fetch_coin_change_history(date=date_obj)
    
    if not data:
        print(f"❌ 无法获取数据: {date_str}")
        return False
    
    # 分析柱状图颜色
    analysis = analyze_bar_colors(data)
    
    if not analysis:
        print(f"❌ 无法分析数据: {date_str}")
        return False
    
    # 生成预测信号
    color_counts = analysis['color_counts']
    signal, message = determine_market_signal(color_counts)
    
    # 构造预测数据
    prediction = {
        'date': date_str,
        'signal': signal,
        'message': message,
        'color_counts': color_counts,
        'statistics': analysis['statistics'],
        'generated_at': datetime.now().isoformat()
    }
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 写入预测文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(prediction, f, ensure_ascii=False)
        f.write('\n')
    
    print(f"✅ 预测数据已生成: {output_file}")
    print(f"📈 信号: {signal}")
    print(f"💬 消息: {message}")
    print(f"🎨 柱状图颜色统计: {color_counts}")
    
    return True

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("用法: python3 regenerate_prediction.py YYYY-MM-DD")
        sys.exit(1)
    
    date_str = sys.argv[1]
    success = regenerate_prediction(date_str)
    sys.exit(0 if success else 1)
