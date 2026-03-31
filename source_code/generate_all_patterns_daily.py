#!/usr/bin/env python3
"""
每日生成所有模式检测结果的脚本（包括满足和不满足条件的）
将结果存储到 data/intraday_patterns/all_detections_<date>.jsonl
"""
import os
import sys
import json
from datetime import datetime, date
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from check_all_patterns_detailed import check_all_patterns_for_date


def generate_daily_patterns(target_date=None):
    """
    生成指定日期的所有模式检测结果
    
    Args:
        target_date: 目标日期，格式为 'YYYY-MM-DD'，默认为今天
    
    Returns:
        dict: 包含检测结果的字典
    """
    if target_date is None:
        target_date = date.today().strftime('%Y-%m-%d')
    
    print(f"🔍 开始检测日期: {target_date}")
    
    # 调用检测函数
    result = check_all_patterns_for_date(target_date)
    
    if not result['success']:
        print(f"❌ 检测失败: {result.get('error', 'Unknown error')}")
        return result
    
    # 准备存储目录
    data_dir = Path(__file__).parent.parent / 'data' / 'intraday_patterns'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 文件路径
    output_file = data_dir / f'all_detections_{target_date}.jsonl'
    
    # 准备写入的数据
    detection_record = {
        'timestamp': datetime.now().isoformat(),
        'date': target_date,
        'daily_prediction': result.get('daily_prediction'),
        'total_bars': result.get('total_bars'),
        'total_change': result.get('total_change'),
        'summary': result.get('summary', {}),
        'qualified_patterns': result.get('qualified_patterns', []),
        'unqualified_patterns': result.get('unqualified_patterns', [])
    }
    
    # 写入JSONL文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(detection_record, ensure_ascii=False) + '\n')
    
    print(f"✅ 检测结果已保存到: {output_file}")
    print(f"📊 统计信息:")
    print(f"   - 总柱子数: {result['total_bars']}")
    print(f"   - 总涨跌幅: {result['total_change']:.2f}%")
    print(f"   - 大周期预判: {result['daily_prediction']}")
    print(f"   - 满足条件: {result['summary']['qualified_count']} 个")
    print(f"   - 不满足条件: {result['summary']['unqualified_count']} 个")
    print(f"   - 总检测数: {result['summary']['total_count']} 个")
    
    # 详细输出满足条件的模式
    if result['qualified_patterns']:
        print(f"\n✅ 满足条件的模式:")
        for i, pattern in enumerate(result['qualified_patterns'], 1):
            print(f"   {i}. {pattern['pattern_name']} ({pattern.get('bar_type', pattern['pattern_type'])})")
            print(f"      时间: {pattern['time_range']}")
            print(f"      信号: {pattern['signal']}")
            
            # 处理trigger_ratio（可能是数字或列表）
            trigger_ratio = pattern.get('trigger_ratio')
            threshold = pattern.get('threshold')
            if trigger_ratio is not None and threshold is not None:
                if isinstance(trigger_ratio, list):
                    print(f"      触发占比: {trigger_ratio}")
                else:
                    print(f"      触发占比: {trigger_ratio}% (阈值: {threshold}%)")
            elif trigger_ratio is not None:
                if isinstance(trigger_ratio, list):
                    print(f"      触发占比: {trigger_ratio}")
                else:
                    print(f"      触发占比: {trigger_ratio}%")
    
    # 详细输出不满足条件的模式
    if result['unqualified_patterns']:
        print(f"\n⚠️ 不满足条件的模式:")
        for i, pattern in enumerate(result['unqualified_patterns'], 1):
            print(f"   {i}. {pattern['pattern_name']} ({pattern.get('bar_type', pattern['pattern_type'])})")
            print(f"      时间: {pattern['time_range']}")
            print(f"      信号: {pattern['signal']}")
            
            # 处理trigger_ratio（可能是数字或列表）
            trigger_ratio = pattern.get('trigger_ratio')
            threshold = pattern.get('threshold')
            if trigger_ratio is not None and threshold is not None:
                if isinstance(trigger_ratio, list):
                    print(f"      触发占比: {trigger_ratio}")
                else:
                    print(f"      触发占比: {trigger_ratio}% (阈值: {threshold}%)")
            elif trigger_ratio is not None:
                if isinstance(trigger_ratio, list):
                    print(f"      触发占比: {trigger_ratio}")
                else:
                    print(f"      触发占比: {trigger_ratio}%")
            
            if pattern.get('failure_reasons'):
                print(f"      失败原因:")
                for reason in pattern['failure_reasons']:
                    print(f"        - {reason}")
    
    return result


def backfill_patterns(start_date, end_date=None):
    """
    批量生成历史日期的模式检测结果
    
    Args:
        start_date: 开始日期 'YYYY-MM-DD'
        end_date: 结束日期 'YYYY-MM-DD'，默认为今天
    """
    from datetime import datetime, timedelta
    
    if end_date is None:
        end_date = date.today().strftime('%Y-%m-%d')
    
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    current = start
    success_count = 0
    fail_count = 0
    
    print(f"🔄 开始批量生成从 {start_date} 到 {end_date} 的模式检测结果\n")
    
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        try:
            result = generate_daily_patterns(date_str)
            if result['success']:
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"❌ {date_str} 处理失败: {e}")
            fail_count += 1
        
        current += timedelta(days=1)
        print()  # 空行分隔
    
    print(f"\n📊 批量生成完成:")
    print(f"   - 成功: {success_count} 天")
    print(f"   - 失败: {fail_count} 天")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='生成每日模式检测结果（包括满足和不满足条件的）')
    parser.add_argument('--date', type=str, help='目标日期 (YYYY-MM-DD)，默认为今天')
    parser.add_argument('--backfill', action='store_true', help='批量生成历史数据')
    parser.add_argument('--start-date', type=str, help='批量生成的开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='批量生成的结束日期 (YYYY-MM-DD)，默认为今天')
    
    args = parser.parse_args()
    
    if args.backfill:
        if not args.start_date:
            print("❌ 批量生成模式需要指定 --start-date 参数")
            sys.exit(1)
        backfill_patterns(args.start_date, args.end_date)
    else:
        generate_daily_patterns(args.date)
