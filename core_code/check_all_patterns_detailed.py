#!/usr/bin/env python3
"""
检测今日所有模式（满足和不满足条件的都列出）
用于实时监控和显示
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pytz

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from monitors.intraday_pattern_monitor import (
    fetch_today_data,
    check_pattern_1,
    check_pattern_3,
    check_pattern_4
)


def calculate_up_ratio(records):
    """计算上涨占比"""
    if not records:
        return 0
    up_count = sum(1 for r in records if r.get('total_change', 0) > 0)
    return (up_count / len(records)) * 100


def determine_color(up_ratio):
    """判断颜色"""
    if up_ratio == 0:
        return 'blank', '⚪'
    elif up_ratio > 55:
        return 'green', '🟢'
    elif up_ratio >= 45:
        return 'yellow', '🟡'
    else:
        return 'red', '🔴'


def convert_to_10min_bars(records, date_str):
    """将记录转换为10分钟柱子"""
    bars = []
    beijing_tz = pytz.timezone('Asia/Shanghai')
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    
    # 从凌晨2点到23:59
    start_time = date_obj.replace(hour=2, minute=0, second=0, tzinfo=beijing_tz)
    end_time = date_obj.replace(hour=23, minute=59, second=0, tzinfo=beijing_tz)
    
    current_time = start_time
    
    while current_time < end_time:
        target_time_str = current_time.strftime('%H:%M')
        
        # 收集这个10分钟内的记录
        interval_records = []
        for r in records:
            time_str = r.get('beijing_time') or r.get('time', '')
            if not time_str:
                continue
            
            try:
                # 提取小时和分钟
                if ' ' in time_str:
                    time_part = time_str.split()[1]
                else:
                    time_part = time_str
                
                hour, minute, *_ = map(int, time_part.split(':'))
                
                # 判断是否在这个10分钟区间内
                if hour == current_time.hour and minute >= current_time.minute and minute < current_time.minute + 10:
                    interval_records.append(r)
            except:
                continue
        
        # 计算上涨占比
        up_ratio = calculate_up_ratio(interval_records)
        color, emoji = determine_color(up_ratio)
        
        bars.append({
            'time': target_time_str,
            'up_ratio': round(up_ratio, 2),
            'color': color,
            'emoji': emoji
        })
        
        # 移动到下一个10分钟
        current_time += timedelta(minutes=10)
    
    return bars


def get_daily_prediction(date_str):
    """获取当日预判"""
    prediction_file = Path(f'data/daily_predictions/prediction_{date_str}.json')
    if prediction_file.exists():
        try:
            with open(prediction_file, 'r', encoding='utf-8') as f:
                pred_data = json.load(f)
                return pred_data.get('signal', '')
        except:
            pass
    return None


def calculate_total_change(records):
    """计算总涨跌幅"""
    if not records:
        return 0
    return records[-1].get('total_change', 0)

def format_pattern_result(pattern_info, satisfied=True):
    """格式化模式检测结果"""
    if not pattern_info:
        return None
    
    result = {
        'pattern': pattern_info['pattern'],
        'pattern_name': pattern_info.get('pattern_name', pattern_info.get('name', '未知模式')),
        'pattern_type': pattern_info.get('pattern_type', pattern_info.get('type', 'unknown')),
        'bar_type': pattern_info.get('bar_type', ''),
        'signal': pattern_info['signal'],
        'time_range': pattern_info['time_range'],
        'bars': pattern_info.get('bars', []),
        'detection_time': pattern_info.get('detection_time', pattern_info.get('detected_at', datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S'))),
        'satisfied': satisfied,  # 是否满足触发条件
        'failure_reasons': []    # 不满足的原因列表
    }
    
    # 添加额外信息
    if 'trigger_ratio' in pattern_info:
        result['trigger_ratio'] = pattern_info['trigger_ratio']
    if 'threshold' in pattern_info:
        result['threshold'] = pattern_info['threshold']
    if 'blank_ratio' in pattern_info:
        result['blank_ratio'] = pattern_info['blank_ratio']
    if 'total_change' in pattern_info:
        result['total_change'] = pattern_info['total_change']
    if 'total_change_at_trigger' in pattern_info:
        result['total_change_at_trigger'] = pattern_info['total_change_at_trigger']
    if 'entry_time' in pattern_info:
        result['entry_time'] = pattern_info['entry_time']
    if 'entry_total_change' in pattern_info:
        result['entry_total_change'] = pattern_info['entry_total_change']
    
    return result

def check_pattern_1_all(bars, daily_prediction=None, records=None):
    """
    检查模式1：诱多等待新低（返回所有检测到的模式，不管是否满足阈值）
    
    连续3根：红→黄→绿 或 绿→黄→红
    连续4根：红→黄→黄→绿
    
    阈值说明（27个币涨幅之和）：
    - "等待新低" → 27币涨幅之和 > +65%
    - "做空"或"观望" → 27币涨幅之和 > +50%
    
    ⚠️ 只检测 02:00-23:59 的模式（排除 00:00-01:59）
    """
    if len(bars) < 3:
        return []
    
    # 确定阈值（这是27个币涨幅之和的阈值，不是10分钟上涨占比）
    signal = daily_prediction.get('signal', '') if daily_prediction else ''
    threshold = 65 if '等待新低' in signal else 50
    
    # 🔧 时间过滤辅助函数：只检测 02:00-23:59
    def is_valid_time(time_str):
        """检查时间是否在 02:00-23:59 范围内"""
        try:
            hour = int(time_str.split(':')[0])
            return 2 <= hour <= 23
        except:
            return True  # 如果解析失败，保留（避免误删）
    
    # 🔧 追踪触发后的时间点，找到第一个达到阈值的时刻
    def find_entry_point(trigger_time_str, threshold, time_to_total_change, bars):
        """
        从触发时间点开始，往后追踪找到第一个 total_change >= threshold 的时刻
        返回：(entry_time, entry_total_change) 或 (None, None)
        """
        # 找到触发柱子在bars中的索引
        trigger_index = None
        for idx, bar in enumerate(bars):
            if bar['time'] == trigger_time_str:
                trigger_index = idx
                break
        
        if trigger_index is None:
            return None, None
        
        # 从触发点开始往后查找
        for idx in range(trigger_index, len(bars)):
            bar_time = bars[idx]['time']
            if bar_time in time_to_total_change:
                total_change = time_to_total_change[bar_time]['total_change']
                if total_change >= threshold:
                    return bar_time, total_change
        
        return None, None
    
    detected_patterns = []
    
    # 获取原始记录数据，用于查询total_change（27币涨幅之和）
    time_to_total_change = {}
    if records:
        for record in records:
            beijing_time = record.get('beijing_time', '')
            if beijing_time:
                # 提取时间部分 HH:MM
                time_str = beijing_time.split(' ')[1][:5] if ' ' in beijing_time else beijing_time[:5]
                total_change = record.get('total_change', 0)
                # 保存最新的total_change
                if time_str not in time_to_total_change or beijing_time > time_to_total_change[time_str]['timestamp']:
                    time_to_total_change[time_str] = {
                        'total_change': total_change,
                        'timestamp': beijing_time
                    }
    
    # 先检查4根柱子模式：红→黄→黄→绿
    if len(bars) >= 4:
        for i in range(len(bars) - 3):
            # 🔧 时间过滤：只检测最后一根柱子时间在 02:00-23:59 的模式
            trigger_time = bars[i+3]['time']
            if not is_valid_time(trigger_time):
                continue
            
            colors = [bars[i]['color'], bars[i+1]['color'], bars[i+2]['color'], bars[i+3]['color']]
            
            if colors == ['red', 'yellow', 'yellow', 'green']:
                # 最后一根柱子的10分钟上涨占比（仅用于显示）
                trigger_bar_ratio = bars[i+3]['up_ratio']
                
                # 获取模式触发时刻的27币涨幅之和
                trigger_time = bars[i+3]['time']
                total_change_at_trigger = 0
                if time_to_total_change and trigger_time in time_to_total_change:
                    total_change_at_trigger = time_to_total_change[trigger_time]['total_change']
                
                # 🔧 查找开仓点：触发后第一个达到阈值的时间点
                entry_time, entry_total_change = find_entry_point(
                    trigger_time, threshold, time_to_total_change, bars
                )
                
                detected_patterns.append({
                    'pattern': 'pattern_1',
                    'pattern_name': '诱多等待新低',
                    'pattern_type': 'pattern_1_4',  # 4根
                    'bar_type': '红→黄→黄→绿',
                    'signal': '逢高做空',
                    'signal_type': 'short',
                    'time_range': f"{bars[i]['time']}-{bars[i+3]['time']}",
                    'bars': [
                        {'time': bars[i]['time'], 'up_ratio': bars[i]['up_ratio'], 'color': bars[i]['color'], 'emoji': '🔴'},
                        {'time': bars[i+1]['time'], 'up_ratio': bars[i+1]['up_ratio'], 'color': bars[i+1]['color'], 'emoji': '🟡'},
                        {'time': bars[i+2]['time'], 'up_ratio': bars[i+2]['up_ratio'], 'color': bars[i+2]['color'], 'emoji': '🟡'},
                        {'time': bars[i+3]['time'], 'up_ratio': bars[i+3]['up_ratio'], 'color': bars[i+3]['color'], 'emoji': '🟢'}
                    ],
                    'detected_at': bars[i+3]['time'],
                    'threshold': threshold,  # 27币涨幅之和的阈值
                    'trigger_ratio': trigger_bar_ratio,  # 10分钟上涨占比（仅用于显示）
                    'total_change_at_trigger': total_change_at_trigger,  # 27币涨幅之和（用于判断）
                    'entry_time': entry_time,  # 🆕 开仓点时间
                    'entry_total_change': entry_total_change  # 🆕 开仓点27币涨幅之和
                })
    
    # 检查3根柱子模式
    for i in range(len(bars) - 2):
        # 🔧 时间过滤：只检测最后一根柱子时间在 02:00-23:59 的模式
        trigger_time = bars[i+2]['time']
        if not is_valid_time(trigger_time):
            continue
        
        colors = [bars[i]['color'], bars[i+1]['color'], bars[i+2]['color']]
        
        # 检查是否匹配模式
        is_red_yellow_green = (colors == ['red', 'yellow', 'green'])
        is_green_yellow_red = (colors == ['green', 'yellow', 'red'])
        
        if is_red_yellow_green or is_green_yellow_red:
            if is_red_yellow_green:
                pattern_type = "pattern_1_3"
                bar_type = "红→黄→绿"
                emojis = ['🔴', '🟡', '🟢']
            else:
                pattern_type = "pattern_1_2"
                bar_type = "绿→黄→红"
                emojis = ['🟢', '🟡', '🔴']
            
            # 最后一根柱子的10分钟上涨占比（仅用于显示，不用于判断）
            trigger_bar_ratio = bars[i+2]['up_ratio']
            
            # 获取模式触发时刻（最后一根柱子时间）的27币涨幅之和
            trigger_time = bars[i+2]['time']
            total_change_at_trigger = 0
            if time_to_total_change and trigger_time in time_to_total_change:
                total_change_at_trigger = time_to_total_change[trigger_time]['total_change']
            
            # 🔧 查找开仓点：触发后第一个达到阈值的时间点
            entry_time, entry_total_change = find_entry_point(
                trigger_time, threshold, time_to_total_change, bars
            )
            
            detected_patterns.append({
                'pattern': 'pattern_1',
                'pattern_name': '诱多等待新低',
                'pattern_type': pattern_type,
                'bar_type': bar_type,
                'signal': '逢高做空',
                'signal_type': 'short',
                'time_range': f"{bars[i]['time']}-{bars[i+2]['time']}",
                'bars': [
                    {'time': bars[i]['time'], 'up_ratio': bars[i]['up_ratio'], 'color': bars[i]['color'], 'emoji': emojis[0]},
                    {'time': bars[i+1]['time'], 'up_ratio': bars[i+1]['up_ratio'], 'color': bars[i+1]['color'], 'emoji': emojis[1]},
                    {'time': bars[i+2]['time'], 'up_ratio': bars[i+2]['up_ratio'], 'color': bars[i+2]['color'], 'emoji': emojis[2]}
                ],
                'detected_at': bars[i+2]['time'],
                'threshold': threshold,  # 这是27币涨幅之和的阈值
                'trigger_ratio': trigger_bar_ratio,  # 10分钟上涨占比（仅用于显示）
                'total_change_at_trigger': total_change_at_trigger,  # 模式触发时刻的27币涨幅之和（用于判断是否满足开仓条件）
                'entry_time': entry_time,  # 🆕 开仓点时间
                'entry_total_change': entry_total_change  # 🆕 开仓点27币涨幅之和
            })
    
    return detected_patterns


def check_pattern_3_all(bars, total_change=None):
    """
    检查模式3：筑底信号（返回所有检测到的模式）
    
    连续3根：黄→绿→黄
    
    ⚠️ 只检测 02:00-23:59 的模式
    """
    if len(bars) < 3:
        return []
    
    # 时间过滤辅助函数
    def is_valid_time(time_str):
        try:
            hour = int(time_str.split(':')[0])
            return 2 <= hour <= 23
        except:
            return True
    
    detected_patterns = []
    
    for i in range(len(bars) - 2):
        # 🔧 时间过滤
        trigger_time = bars[i+2]['time']
        if not is_valid_time(trigger_time):
            continue
        
        colors = [bars[i]['color'], bars[i+1]['color'], bars[i+2]['color']]
        
        if colors == ['yellow', 'green', 'yellow']:
            trigger_bar_ratio = bars[i+2]['up_ratio']
            
            detected_patterns.append({
                'pattern': 'pattern_3',
                'pattern_name': '筑底信号',
                'pattern_type': 'pattern_3',
                'bar_type': '黄→绿→黄',
                'signal': '低吸抄底',
                'signal_type': 'long',
                'time_range': f"{bars[i]['time']}-{bars[i+2]['time']}",
                'bars': [
                    {'time': bars[i]['time'], 'up_ratio': bars[i]['up_ratio'], 'color': bars[i]['color'], 'emoji': '🟡'},
                    {'time': bars[i+1]['time'], 'up_ratio': bars[i+1]['up_ratio'], 'color': bars[i+1]['color'], 'emoji': '🟢'},
                    {'time': bars[i+2]['time'], 'up_ratio': bars[i+2]['up_ratio'], 'color': bars[i+2]['color'], 'emoji': '🟡'}
                ],
                'detected_at': bars[i+2]['time'],
                'trigger_ratio': trigger_bar_ratio,
                'total_change': total_change
            })
    
    return detected_patterns


def check_pattern_4_all(bars):
    """
    检查模式4：诱空信号（返回所有检测到的模式）
    
    连续3根：绿→红→绿
    连续4根：绿→红→红→绿
    
    ⚠️ 只检测 02:00-23:59 的模式
    """
    if len(bars) < 3:
        return []
    
    # 时间过滤辅助函数
    def is_valid_time(time_str):
        try:
            hour = int(time_str.split(':')[0])
            return 2 <= hour <= 23
        except:
            return True
    
    detected_patterns = []
    
    # 检查4根柱子模式：绿→红→红→绿
    if len(bars) >= 4:
        for i in range(len(bars) - 3):
            # 🔧 时间过滤
            trigger_time = bars[i+3]['time']
            if not is_valid_time(trigger_time):
                continue
            
            colors = [bars[i]['color'], bars[i+1]['color'], bars[i+2]['color'], bars[i+3]['color']]
            
            if colors == ['green', 'red', 'red', 'green']:
                middle_ratios = [bars[i+1]['up_ratio'], bars[i+2]['up_ratio']]
                
                detected_patterns.append({
                    'pattern': 'pattern_4',
                    'pattern_name': '诱空信号',
                    'pattern_type': 'pattern_4_4',
                    'bar_type': '绿→红→红→绿',
                    'signal': '逢低做多',
                    'signal_type': 'long',
                    'time_range': f"{bars[i]['time']}-{bars[i+3]['time']}",
                    'bars': [
                        {'time': bars[i]['time'], 'up_ratio': bars[i]['up_ratio'], 'color': bars[i]['color'], 'emoji': '🟢'},
                        {'time': bars[i+1]['time'], 'up_ratio': bars[i+1]['up_ratio'], 'color': bars[i+1]['color'], 'emoji': '🔴'},
                        {'time': bars[i+2]['time'], 'up_ratio': bars[i+2]['up_ratio'], 'color': bars[i+2]['color'], 'emoji': '🔴'},
                        {'time': bars[i+3]['time'], 'up_ratio': bars[i+3]['up_ratio'], 'color': bars[i+3]['color'], 'emoji': '🟢'}
                    ],
                    'detected_at': bars[i+3]['time'],
                    'trigger_ratio': middle_ratios
                })
    
    # 检查3根柱子模式：绿→红→绿
    for i in range(len(bars) - 2):
        # 🔧 时间过滤
        trigger_time = bars[i+2]['time']
        if not is_valid_time(trigger_time):
            continue
        
        colors = [bars[i]['color'], bars[i+1]['color'], bars[i+2]['color']]
        
        if colors == ['green', 'red', 'green']:
            middle_ratio = bars[i+1]['up_ratio']
            
            detected_patterns.append({
                'pattern': 'pattern_4',
                'pattern_name': '诱空信号',
                'pattern_type': 'pattern_4_3',
                'bar_type': '绿→红→绿',
                'signal': '逢低做多',
                'signal_type': 'long',
                'time_range': f"{bars[i]['time']}-{bars[i+2]['time']}",
                'bars': [
                    {'time': bars[i]['time'], 'up_ratio': bars[i]['up_ratio'], 'color': bars[i]['color'], 'emoji': '🟢'},
                    {'time': bars[i+1]['time'], 'up_ratio': bars[i+1]['up_ratio'], 'color': bars[i+1]['color'], 'emoji': '🔴'},
                    {'time': bars[i+2]['time'], 'up_ratio': bars[i+2]['up_ratio'], 'color': bars[i+2]['color'], 'emoji': '🟢'}
                ],
                'detected_at': bars[i+2]['time'],
                'trigger_ratio': [middle_ratio]
            })
    
    return detected_patterns


def check_pattern_with_conditions(bars, total_change, daily_prediction, records=None):
    """检测所有模式并返回满足和不满足条件的模式"""
    
    qualified_patterns = []      # 满足触发条件的
    unqualified_patterns = []    # 不满足触发条件的
    
    # 检查模式1：诱多等待新低
    pattern_1_list = check_pattern_1_all(bars, daily_prediction, records)
    for pattern_info in pattern_1_list:
        # 检查触发条件：27个币涨幅之和（不是10分钟上涨占比！）
        total_change_at_trigger = pattern_info.get('total_change_at_trigger', 0)
        threshold = pattern_info.get('threshold', 65)
        entry_time = pattern_info.get('entry_time')
        
        # 🔧 新逻辑：
        # 1. 如果触发时刻就满足条件（total_change_at_trigger >= threshold）→ 已达到开仓点
        # 2. 如果触发时刻不满足，但后续有entry_time（找到了开仓点）→ 也算已达到开仓点
        # 3. 否则 → 等待开仓点
        
        if total_change_at_trigger >= threshold:
            # 情况1：触发时刻就满足条件
            qualified_patterns.append(format_pattern_result(pattern_info, satisfied=True))
        elif entry_time:
            # 情况2：后续找到了开仓点
            qualified_patterns.append(format_pattern_result(pattern_info, satisfied=True))
        else:
            # 情况3：尚未找到开仓点
            result = format_pattern_result(pattern_info, satisfied=False)
            result['failure_reasons'].append(f'27币涨幅之和 {total_change_at_trigger:.2f}% < {threshold:.2f}%（真正开仓点在涨幅之和≥{threshold}%时）')
            unqualified_patterns.append(result)
    
    # 检查模式3：筑底信号（黄→绿→黄）
    pattern_3_list = check_pattern_3_all(bars, total_change)
    for pattern_info in pattern_3_list:
        # 检查触发条件：
        # 1. 最后一根黄色柱子的涨幅占比需<10%
        # 2. 当日涨跌幅总和需<-50%
        last_bar_ratio = pattern_info.get('trigger_ratio')
        current_total_change = pattern_info.get('total_change', total_change)
        
        satisfied = True
        reasons = []
        
        if last_bar_ratio is None or last_bar_ratio >= 10:
            satisfied = False
            reasons.append(f'最后一根柱子上涨占比 {last_bar_ratio:.2f}% >= 10.00% (需要 < 10.00%)')
        
        if current_total_change is None or current_total_change >= -50:
            satisfied = False
            reasons.append(f'当日涨跌幅总和 {current_total_change:.2f}% >= -50.00% (需要 < -50.00%)')
        
        if satisfied:
            qualified_patterns.append(format_pattern_result(pattern_info, satisfied=True))
        else:
            result = format_pattern_result(pattern_info, satisfied=False)
            result['failure_reasons'] = reasons
            unqualified_patterns.append(result)
    
    # 检查模式4：诱空信号（绿→红→绿 或 绿→红→红→绿）
    pattern_4_list = check_pattern_4_all(bars)
    for pattern_info in pattern_4_list:
        # 检查触发条件：中间的红色柱子涨幅占比需<10%
        trigger_ratios = pattern_info.get('trigger_ratio', [])
        
        if not trigger_ratios:
            # 没有trigger_ratio信息，默认不满足
            result = format_pattern_result(pattern_info, satisfied=False)
            result['failure_reasons'].append('缺少涨幅占比数据')
            unqualified_patterns.append(result)
            continue
        
        # 检查所有中间红色柱子是否都<10%
        all_satisfied = all(ratio < 10 for ratio in trigger_ratios)
        
        if all_satisfied:
            qualified_patterns.append(format_pattern_result(pattern_info, satisfied=True))
        else:
            result = format_pattern_result(pattern_info, satisfied=False)
            ratios_str = ', '.join([f'{r:.2f}%' for r in trigger_ratios])
            result['failure_reasons'].append(f'中间红色柱子上涨占比 [{ratios_str}] 存在 >= 10.00% 的情况 (需要全部 < 10.00%)')
            unqualified_patterns.append(result)
    
    return qualified_patterns, unqualified_patterns

def main():
    print("=" * 80)
    print("📊 今日模式检测详细分析（满足和不满足条件的都列出）")
    print("=" * 80)
    
    # 获取今日数据（已经是处理好的10分钟柱子）
    bars = fetch_today_data()
    if not bars:
        print("❌ 未获取到今日数据")
        return
    
    # 🔧 获取原始数据（包含total_change）
    import requests
    beijing_tz = pytz.timezone('Asia/Shanghai')
    today_str = datetime.now(beijing_tz).strftime('%Y-%m-%d')
    
    try:
        url = f'http://localhost:9002/api/coin-change-tracker/history?date={today_str}&limit=1440'
        response = requests.get(url, timeout=30)
        result = response.json()
        
        records = []
        if result.get('success') and result.get('data'):
            records = result['data']
            print(f"[{datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')}] ✅ 获取到 {len(records)} 条数据记录")
    except Exception as e:
        print(f"⚠️ 无法获取原始数据: {e}")
        records = []
    
    print(f"\n✅ 获取到 {len(bars)} 个10分钟柱子")
    
    # 显示最近10根柱子
    print(f"\n📊 最近10根柱子:")
    for bar in bars[-10:]:
        emoji_map = {'green': '🟢', 'yellow': '🟡', 'red': '🔴', 'blank': '⚪'}
        emoji = emoji_map.get(bar['color'], '❓')
        print(f"  {bar['time']} {emoji} {bar['up_ratio']}%")
    
    # 计算总涨跌幅 (这里简单求和所有非空白柱子的差异)
    total_change = sum(bar['up_ratio'] - 50 for bar in bars if bar['color'] != 'blank')
    print(f"✅ 当日涨跌幅总和: {total_change:.2f}%")
    
    # 获取当日预判
    daily_prediction_str = get_daily_prediction(today_str)
    daily_prediction = {'signal': daily_prediction_str} if daily_prediction_str else None
    print(f"✅ 当日预判: {daily_prediction_str or '未知'}")
    
    print("\n" + "=" * 80)
    print("🔍 开始检测所有模式...")
    print("=" * 80)
    
    # 检测所有模式（传入原始records数据）
    qualified, unqualified = check_pattern_with_conditions(bars, total_change, daily_prediction, records)
    
    # 输出结果
    print(f"\n{'=' * 80}")
    print(f"✅ 满足触发条件的模式 ({len(qualified)} 个)")
    print(f"{'=' * 80}")
    
    if qualified:
        for i, pattern in enumerate(qualified, 1):
            print(f"\n【模式 {i}】{pattern['pattern_name']}")
            print(f"  类型: {pattern.get('bar_type', pattern.get('pattern_type', 'unknown'))}")
            print(f"  时间范围: {pattern['time_range']}")
            print(f"  信号类型: {pattern['signal']}")
            
            # 格式化柱子信息
            bars_info = []
            for bar in pattern['bars']:
                if isinstance(bar, dict):
                    bars_info.append(f"{bar.get('emoji', '❓')}{bar['time']} {bar['up_ratio']:.1f}%")
                else:
                    bars_info.append(str(bar))
            print(f"  柱子序列: {' → '.join(bars_info)}")
            
            if 'trigger_ratio' in pattern:
                if isinstance(pattern['trigger_ratio'], list):
                    print(f"  触发占比: {pattern['trigger_ratio']}")
                else:
                    print(f"  触发占比: {pattern['trigger_ratio']:.2f}%")
            if 'threshold' in pattern:
                print(f"  阈值要求: {pattern['threshold']:.2f}%")
            if 'total_change' in pattern:
                print(f"  当日总和: {pattern['total_change']:.2f}%")
    else:
        print("\n  无")
    
    print(f"\n{'=' * 80}")
    print(f"⚠️ 不满足触发条件的模式 ({len(unqualified)} 个)")
    print(f"{'=' * 80}")
    
    if unqualified:
        for i, pattern in enumerate(unqualified, 1):
            print(f"\n【模式 {i}】{pattern['pattern_name']}")
            print(f"  类型: {pattern.get('bar_type', pattern.get('pattern_type', 'unknown'))}")
            print(f"  时间范围: {pattern['time_range']}")
            print(f"  信号类型: {pattern['signal']}")
            
            # 格式化柱子信息
            bars_info = []
            for bar in pattern['bars']:
                if isinstance(bar, dict):
                    bars_info.append(f"{bar.get('emoji', '❓')}{bar['time']} {bar['up_ratio']:.1f}%")
                else:
                    bars_info.append(str(bar))
            print(f"  柱子序列: {' → '.join(bars_info)}")
            
            if 'trigger_ratio' in pattern:
                if isinstance(pattern['trigger_ratio'], list):
                    print(f"  触发占比: {pattern['trigger_ratio']}")
                else:
                    print(f"  触发占比: {pattern['trigger_ratio']:.2f}%")
            if 'threshold' in pattern:
                print(f"  阈值要求: {pattern['threshold']:.2f}%")
            if 'total_change' in pattern:
                print(f"  当日总和: {pattern['total_change']:.2f}%")
            
            # 🆕 显示开仓点时间
            if 'entry_time' in pattern and pattern['entry_time']:
                print(f"  ✅ 开仓点时间: {pattern['entry_time']} (27币涨幅之和达到 {pattern.get('entry_total_change', '?'):.2f}%)")
            elif 'total_change_at_trigger' in pattern and 'threshold' in pattern:
                print(f"  ⏳ 等待开仓: 当前27币涨幅之和 {pattern['total_change_at_trigger']:.2f}%，未达到 {pattern['threshold']:.2f}% 阈值")
            
            print(f"  ❌ 不满足原因:")
            for reason in pattern['failure_reasons']:
                print(f"     • {reason}")
    else:
        print("\n  无")
    
    # 保存到JSON文件（包含两类模式）
    beijing_tz = pytz.timezone('Asia/Shanghai')
    beijing_now = datetime.now(beijing_tz)
    date_str = beijing_now.strftime('%Y-%m-%d')
    
    output_file = Path(f'/tmp/all_patterns_detailed_{date_str}.json')
    result_data = {
        'date': date_str,
        'timestamp': beijing_now.strftime('%Y-%m-%d %H:%M:%S'),
        'total_bars': len(bars),
        'total_change': round(total_change, 2),
        'daily_prediction': daily_prediction_str,
        'qualified_patterns': qualified,
        'unqualified_patterns': unqualified,
        'summary': {
            'qualified_count': len(qualified),
            'unqualified_count': len(unqualified),
            'total_count': len(qualified) + len(unqualified)
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 80}")
    print(f"✅ 检测结果已保存到: {output_file}")
    print(f"{'=' * 80}\n")

def check_all_patterns_for_date(date_str):
    """
    检测指定日期的所有模式（满足和不满足条件的）
    
    Args:
        date_str: 日期字符串，格式为 'YYYY-MM-DD'
    
    Returns:
        dict: 包含检测结果的字典
    """
    try:
        beijing_tz = pytz.timezone('Asia/Shanghai')
        today_str = datetime.now(beijing_tz).strftime('%Y-%m-%d')
        
        # 判断是否为今天
        is_today = (date_str == today_str)
        
        if is_today:
            # 今天的数据：使用API获取bars和原始records
            bars = fetch_today_data()
            if not bars:
                return {
                    'success': False,
                    'error': '无法获取今日数据'
                }
            
            # 同时获取原始records（包含total_change字段）
            import requests
            url = f'http://localhost:9002/api/coin-change-tracker/history?date={date_str}&limit=1440'
            response = requests.get(url, timeout=30)
            result = response.json()
            
            if not result.get('success') or not result.get('data'):
                records = []
            else:
                records = result['data']
            
            # 计算总涨跌幅（简单求和所有非空白柱子与50%的差异）
            total_change = sum(bar['up_ratio'] - 50 for bar in bars if bar['color'] != 'blank')
        else:
            # 历史数据：从JSONL文件读取
            date_no_dash = date_str.replace('-', '')
            file_path = Path(f'data/coin_change_tracker/coin_change_{date_no_dash}.jsonl')
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'数据文件不存在: {file_path}'
                }
            
            # 读取所有记录
            records = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
            
            if not records:
                return {
                    'success': False,
                    'error': '数据文件为空'
                }
            
            # 转换为10分钟柱子
            bars = convert_to_10min_bars(records, date_str)
            
            # 计算当日总涨跌幅
            total_change = calculate_total_change(records)
        
        # 获取当日预判（字符串）
        daily_prediction_str = get_daily_prediction(date_str)
        
        # 构造daily_prediction字典（check_pattern函数期望的格式）
        daily_prediction_dict = {'signal': daily_prediction_str or ''}
        
        # 检测所有模式（传入records用于查询27币涨幅之和）
        qualified, unqualified = check_pattern_with_conditions(bars, total_change, daily_prediction_dict, records)
        
        return {
            'success': True,
            'date': date_str,
            'total_bars': len(bars),
            'total_change': round(total_change, 2),
            'daily_prediction': daily_prediction_str or '',
            'qualified_patterns': qualified,
            'unqualified_patterns': unqualified,
            'summary': {
                'total_count': len(qualified) + len(unqualified),
                'qualified_count': len(qualified),
                'unqualified_count': len(unqualified)
            }
        }
    
    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }


if __name__ == '__main__':
    main()
