#!/usr/bin/env python3
"""
重新生成历史预测数据（使用新逻辑）
"""
import sys
sys.path.insert(0, '/home/user/webapp')

from monitors.coin_change_prediction_monitor import determine_market_signal
import json
import glob
from pathlib import Path

def regenerate_historical_predictions():
    """重新生成所有历史预测的signal"""
    
    prediction_files = glob.glob('data/daily_predictions/prediction_2026*.jsonl')
    
    print(f"找到 {len(prediction_files)} 个预测文件")
    
    updated_count = 0
    
    for pred_file in prediction_files:
        try:
            with open(pred_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                continue
            
            # 处理最后一行（最终预测）
            last_line = lines[-1].strip()
            prediction = json.loads(last_line)
            
            # 获取颜色统计
            color_counts = prediction.get('color_counts', {})
            
            # 使用新逻辑重新计算signal
            new_signal, new_description = determine_market_signal(color_counts)
            
            old_signal = prediction.get('signal', '')
            
            # 如果signal变化，更新
            if new_signal != old_signal:
                print(f"\n{Path(pred_file).name}:")
                print(f"  颜色: 绿{color_counts.get('green', 0)} 红{color_counts.get('red', 0)} 黄{color_counts.get('yellow', 0)} 空白{color_counts.get('blank', 0)}")
                print(f"  旧signal: {old_signal}")
                print(f"  新signal: {new_signal}")
                
                prediction['signal'] = new_signal
                prediction['description'] = new_description
                
                # 更新最后一行
                lines[-1] = json.dumps(prediction, ensure_ascii=False) + '\n'
                
                # 写回文件
                with open(pred_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                updated_count += 1
        
        except Exception as e:
            print(f"处理 {pred_file} 失败: {str(e)}")
    
    print(f"\n✅ 完成！更新了 {updated_count} 个预测文件")

if __name__ == '__main__':
    regenerate_historical_predictions()
