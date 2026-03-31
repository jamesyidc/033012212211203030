#!/usr/bin/env python3
"""
完整检查2月份所有数据的暴跌预警
"""
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, '/home/user/webapp')
sys.path.insert(0, '/home/user/webapp/source_code')

from wave_peak_detector import WavePeakDetector

def check_february_crash_warnings():
    """检查2月份所有数据的暴跌预警"""
    
    data_dir = Path('/home/user/webapp/data/coin_change_tracker')
    detector = WavePeakDetector()
    
    # 2月份所有日期
    start_date = datetime(2026, 2, 1)
    end_date = datetime(2026, 2, 24)
    
    results = []
    crash_warning_days = []
    
    print("\n" + "="*80)
    print("🔍 开始检查2月份完整数据 - 暴跌预警分析")
    print("="*80 + "\n")
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y%m%d')
        data_file = data_dir / f'coin_change_{date_str}.jsonl'
        
        if not data_file.exists():
            print(f"❌ {current_date.strftime('%Y-%m-%d')} - 数据文件不存在")
            results.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'status': 'missing',
                'crash_warning': None
            })
            current_date += timedelta(days=1)
            continue
        
        # 检测该天的数据
        try:
            data = detector.load_data(str(data_file))
            if not data:
                print(f"⚠️  {current_date.strftime('%Y-%m-%d')} - 数据为空")
                results.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'status': 'empty',
                    'crash_warning': None
                })
                current_date += timedelta(days=1)
                continue
            
            # 检测波峰（返回元组：peaks列表和当前状态）
            peaks, current_state = detector.detect_wave_peaks(data)
            
            # 检测暴跌预警
            crash_warning = detector.detect_crash_warning(peaks)
            
            if crash_warning:
                print(f"🚨 {current_date.strftime('%Y-%m-%d')} - 检测到暴跌预警！")
                print(f"   ├─ 信号类型: {crash_warning.get('signal_type')}")
                print(f"   ├─ 模式名称: {crash_warning.get('pattern_name')}")
                print(f"   ├─ 连续波峰数: {crash_warning.get('consecutive_peaks', 0)}")
                print(f"   ├─ 波峰总数: {len(peaks)}")
                print(f"   └─ 详细信息: {crash_warning.get('message', '')}")
                
                # 打印模式详情
                if 'pattern_details' in crash_warning:
                    details = crash_warning['pattern_details']
                    if crash_warning['signal_type'] == 'crash_warning_amplifying':
                        print(f"      震荡幅度递增: {details.get('amplitudes', [])}")
                    elif crash_warning['signal_type'] == 'crash_warning_decreasing_tops':
                        print(f"      A点递减（A1 > A2 > A3）: {details.get('a_values', [])}")
                    # 删除"底部递增"检测（用户要求不要自己瞎编）
                
                crash_warning_days.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'warning': crash_warning,
                    'peaks_count': len(peaks)
                })
            else:
                print(f"✅ {current_date.strftime('%Y-%m-%d')} - 无暴跌预警 (波峰数: {len(peaks)})")
            
            results.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'status': 'ok',
                'peaks_count': len(peaks),
                'crash_warning': crash_warning
            })
            
        except Exception as e:
            print(f"❌ {current_date.strftime('%Y-%m-%d')} - 分析出错: {str(e)}")
            results.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'status': 'error',
                'error': str(e)
            })
        
        current_date += timedelta(days=1)
    
    # 输出汇总
    print("\n" + "="*80)
    print("📊 2月份暴跌预警分析汇总")
    print("="*80 + "\n")
    
    total_days = len(results)
    valid_days = len([r for r in results if r['status'] == 'ok'])
    warning_days = len(crash_warning_days)
    
    print(f"总天数: {total_days}")
    print(f"有效数据天数: {valid_days}")
    print(f"暴跌预警天数: {warning_days}")
    if valid_days > 0:
        print(f"预警比例: {warning_days/valid_days*100:.1f}%\n")
    else:
        print(f"预警比例: N/A (无有效数据)\n")
    
    if crash_warning_days:
        print("🚨 暴跌预警详情:\n")
        for item in crash_warning_days:
            warning = item['warning']
            print(f"📅 {item['date']}")
            print(f"   ├─ 信号类型: {warning.get('signal_type')}")
            print(f"   ├─ 模式名称: {warning.get('pattern_name')}")
            print(f"   ├─ 波峰数: {item['peaks_count']}")
            print(f"   └─ 消息: {warning.get('message', '')}\n")
    else:
        print("✅ 2月份未检测到任何暴跌预警\n")
    
    # 保存结果
    output_file = Path('/home/user/webapp/data/crash_warning_events/february_analysis.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'month': '2026-02',
            'summary': {
                'total_days': total_days,
                'valid_days': valid_days,
                'warning_days': warning_days,
                'warning_rate': f"{warning_days/valid_days*100:.1f}%" if valid_days > 0 else "N/A"
            },
            'crash_warning_days': crash_warning_days,
            'all_results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"📁 分析结果已保存到: {output_file}\n")
    print("="*80)

if __name__ == '__main__':
    check_february_crash_warnings()
