#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新计算历史【低吸】信号的二级触发
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入监控器的函数
from monitors.coin_change_prediction_monitor import fetch_after_2am_bars, analyze_second_trigger

def get_all_prediction_files():
    """获取所有预判文件"""
    prediction_dir = "/home/user/webapp/data/daily_predictions"
    files = []
    
    if not os.path.exists(prediction_dir):
        return files
    
    for filename in os.listdir(prediction_dir):
        if filename.startswith('prediction_') and filename.endswith('.jsonl') and 'temp' not in filename:
            files.append(os.path.join(prediction_dir, filename))
    
    return sorted(files)

def process_prediction_file(filepath):
    """处理单个预判文件"""
    print(f"\n{'='*60}")
    print(f"处理文件: {os.path.basename(filepath)}")
    print(f"{'='*60}")
    
    try:
        # 读取文件的所有行
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print("⚠️ 文件为空，跳过")
            return False
        
        # 解析最后一行（最终预判）
        last_line = lines[-1].strip()
        prediction = json.loads(last_line)
        
        signal = prediction.get('signal', '')
        date = prediction.get('date', '')
        is_final = prediction.get('is_final', False)
        
        print(f"日期: {date}")
        print(f"信号: {signal}")
        print(f"是否最终: {is_final}")
        
        # 只处理低吸信号且是最终预判的
        if signal != '低吸':
            print(f"❌ 信号为【{signal}】，非【低吸】，跳过")
            return False
        
        if not is_final:
            print(f"⚠️ 非最终预判，跳过")
            return False
        
        # 检查是否已有二级触发数据
        if 'second_trigger' in prediction:
            print(f"ℹ️ 已有二级触发数据，将重新计算")
        
        # 获取2点后的三根柱子
        print(f"\n📊 获取 {date} 2点后的前三根柱子...")
        after_2am_data = fetch_after_2am_bars(date)
        
        if not after_2am_data['success']:
            print(f"❌ 获取2点后数据失败: {after_2am_data.get('message', '未知错误')}")
            return False
        
        bars = after_2am_data['bars']
        bar_details = after_2am_data['bar_details']
        
        print(f"📊 2点后前三根柱子:")
        for i, detail in enumerate(bar_details, 1):
            color_emoji = {
                'green': '🟢',
                'red': '🔴',
                'yellow': '🟡',
                'blank': '⚪'
            }.get(detail['color'], '⚫')
            print(f"  柱子{i}: {color_emoji} {detail['color']} (上涨占比: {detail['up_ratio']:.1f}%)")
        
        # 分析二级触发
        trigger_result = analyze_second_trigger(bars)
        
        print(f"\n🎯 二级触发结果:")
        print(f"  触发状态: {'✅ 已触发' if trigger_result['triggered'] else '⭕ 未触发'}")
        print(f"  操作建议: {trigger_result.get('action', '无') or '无'}")
        print(f"  描述: {trigger_result['description']}")
        
        # 更新预判数据
        prediction['second_trigger'] = {
            'checked_at': datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S'),
            'bars': bars,
            'bar_details': bar_details,
            'triggered': trigger_result['triggered'],
            'action': trigger_result.get('action'),
            'description': trigger_result['description'],
            'detail': trigger_result.get('detail')
        }
        
        # 重写最后一行
        lines[-1] = json.dumps(prediction, ensure_ascii=False) + '\n'
        
        # 保存文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"💾 二级触发信息已保存")
        return True
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 开始重新计算历史【低吸】信号的二级触发")
    print("="*60)
    
    # 获取所有预判文件
    files = get_all_prediction_files()
    print(f"📁 找到 {len(files)} 个预判文件")
    
    if not files:
        print("❌ 未找到任何预判文件")
        return
    
    # 统计
    total = 0
    success = 0
    skipped = 0
    failed = 0
    
    # 处理每个文件
    for filepath in files:
        total += 1
        result = process_prediction_file(filepath)
        
        if result:
            success += 1
        elif result is False:
            skipped += 1
        else:
            failed += 1
    
    # 总结
    print(f"\n{'='*60}")
    print(f"✅ 重新计算完成")
    print(f"{'='*60}")
    print(f"📊 统计:")
    print(f"  总文件数: {total}")
    print(f"  成功处理: {success}")
    print(f"  跳过（非低吸或数据不足）: {skipped}")
    print(f"  失败: {failed}")
    print(f"\n✨ 所有【低吸】信号的二级触发已重新计算完成！")

if __name__ == "__main__":
    main()
