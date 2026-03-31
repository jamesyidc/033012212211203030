#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回溯分析2月1日以来的日内模式检测
读取历史的10分钟上涨占比数据，重新运行模式检测逻辑
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import glob

# 项目根目录
BASE_DIR = Path('/home/user/webapp')
sys.path.insert(0, str(BASE_DIR))

# 数据目录
DATA_DIR = BASE_DIR / 'data' / 'intraday_patterns'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 历史数据目录
HISTORY_DIR = BASE_DIR / 'data' / 'coin_change_tracker'

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.utcnow()
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time

def load_daily_prediction(date_str):
    """加载指定日期的0-2点预判数据"""
    try:
        prediction_file = BASE_DIR / 'data' / 'daily_predictions' / f'prediction_{date_str}.json'
        if prediction_file.exists():
            with open(prediction_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    'signal': data.get('signal', ''),
                    'description': data.get('description', ''),
                    'date': data.get('date', date_str)
                }
    except Exception as e:
        print(f"⚠️ 加载预判数据失败 {date_str}: {e}")
    return None

def load_history_data(date_str):
    """加载指定日期的历史数据"""
    try:
        # 文件格式: coin_change_20260223.jsonl
        date_compact = date_str.replace("-", "")  # "2026-02-23" -> "20260223"
        file_path = HISTORY_DIR / f'coin_change_{date_compact}.jsonl'
        
        if file_path.exists():
            records = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
            print(f"✅ 加载历史数据: {file_path.name}, 记录数: {len(records)}")
            return records
        
        print(f"⚠️ 未找到历史数据文件: {file_path.name}")
        return []
    except Exception as e:
        print(f"❌ 加载历史数据失败 {date_str}: {e}")
        return []

def calculate_up_ratio(changes):
    """计算上涨占比"""
    if not changes:
        return 0.0
    up_count = sum(1 for c in changes if c > 0)
    return (up_count / len(changes)) * 100

def get_bar_color(ratio):
    """根据占比确定柱子颜色"""
    if ratio == 0:
        return '空白'
    elif ratio > 55:
        return '绿色'
    elif ratio >= 45:
        return '黄色'
    else:
        return '红色'

def build_bars_from_history(records):
    """从历史记录构建10分钟柱子"""
    # 按时间排序
    records.sort(key=lambda x: x.get('beijing_time', ''))
    
    bars = []
    current_hour = None
    current_minute_start = None
    current_changes = []
    
    for record in records:
        beijing_time = record.get('beijing_time', '')
        if not beijing_time:
            continue
        
        # 解析时间 "2026-02-23 14:35:42"
        try:
            dt = datetime.strptime(beijing_time, '%Y-%m-%d %H:%M:%S')
            hour = dt.hour
            minute = dt.minute
            
            # 计算10分钟区间的起始分钟
            minute_start = (minute // 10) * 10
            
            # 如果是新的10分钟区间
            if hour != current_hour or minute_start != current_minute_start:
                # 保存上一个区间的数据
                if current_changes:
                    up_ratio = calculate_up_ratio(current_changes)
                    color = get_bar_color(up_ratio)
                    time_str = f"{current_hour:02d}:{current_minute_start:02d}"
                    
                    bars.append({
                        'time': time_str,
                        'hour': current_hour,
                        'up_ratio': round(up_ratio, 2),
                        'color': color
                    })
                
                # 开始新区间
                current_hour = hour
                current_minute_start = minute_start
                current_changes = []
            
            # 收集涨跌幅数据
            if 'changes' in record and record['changes']:
                # record['changes'] 是一个字典: {"BTC-USDT-SWAP": {"change_pct": -3.3}, ...}
                change_values = [coin_data.get('change_pct', 0) for coin_data in record['changes'].values()]
                current_changes.extend(change_values)
        except Exception as e:
            print(f"⚠️ 解析时间失败: {beijing_time}, {e}")
            continue
    
    # 保存最后一个区间
    if current_changes:
        up_ratio = calculate_up_ratio(current_changes)
        color = get_bar_color(up_ratio)
        time_str = f"{current_hour:02d}:{current_minute_start:02d}"
        bars.append({
            'time': time_str,
            'hour': current_hour,
            'up_ratio': round(up_ratio, 2),
            'color': color
        })
    
    return bars

def check_pattern_1(bars, daily_prediction=None):
    """检测模式1: 诱多等待新低
    
    连续3根：红→黄→绿 或 绿→黄→红
    连续4根：红→黄→黄→绿
    
    动态阈值（根据预测信号）：
    - "等待新低" → 触发后10分钟上涨占比平均 > 65%
    - "做空"或"观望" → 触发后10分钟上涨占比平均 > 50%
    """
    detections = []
    
    # 确定阈值
    signal = daily_prediction.get('signal', '') if daily_prediction else ''
    threshold = 65 if '等待新低' in signal else 50
    
    # 先检查4根柱子模式：红→黄→黄→绿
    if len(bars) >= 4:
        for i in range(len(bars) - 3):
            b1, b2, b3, b4 = bars[i], bars[i+1], bars[i+2], bars[i+3]
            
            if (b1['color'] == '红色' and b2['color'] == '黄色' and 
                b3['color'] == '黄色' and b4['color'] == '绿色'):
                # 检查触发后的上涨占比（最后一根柱子）
                trigger_ratio = b4['up_ratio']
                
                if trigger_ratio > threshold:
                    detections.append({
                        'pattern_id': 'pattern_1',
                        'pattern_name': '诱多等待新低',
                        'pattern_type': '红→黄→黄→绿',
                        'signal': '逢高做空',
                        'signal_type': 'short',
                        'time_range': f"{b1['time']} - {b4['time']}",
                        'bars': [b1, b2, b3, b4],
                        'threshold': threshold,
                        'trigger_ratio': trigger_ratio
                    })
    
    # 检查3根柱子模式
    for i in range(len(bars) - 2):
        b1, b2, b3 = bars[i], bars[i+1], bars[i+2]
        
        # 红→黄→绿
        if (b1['color'] == '红色' and b2['color'] == '黄色' and b3['color'] == '绿色'):
            trigger_ratio = b3['up_ratio']
            
            if trigger_ratio > threshold:
                detections.append({
                    'pattern_id': 'pattern_1',
                    'pattern_name': '诱多等待新低',
                    'pattern_type': '红→黄→绿',
                    'signal': '逢高做空',
                    'signal_type': 'short',
                    'time_range': f"{b1['time']} - {b3['time']}",
                    'bars': [b1, b2, b3],
                    'threshold': threshold,
                    'trigger_ratio': trigger_ratio
                })
        
        # 绿→黄→红
        elif (b1['color'] == '绿色' and b2['color'] == '黄色' and b3['color'] == '红色'):
            trigger_ratio = b3['up_ratio']
            
            if trigger_ratio > threshold:
                detections.append({
                    'pattern_id': 'pattern_1',
                    'pattern_name': '诱多等待新低',
                    'pattern_type': '绿→黄→红',
                    'signal': '逢高做空',
                    'signal_type': 'short',
                    'time_range': f"{b1['time']} - {b3['time']}",
                    'bars': [b1, b2, b3],
                    'threshold': threshold,
                    'trigger_ratio': trigger_ratio
                })
    
    return detections

def check_pattern_2(bars):
    """检测模式2: 诱空试仓抄底 (红+3空白)"""
    detections = []
    for i in range(len(bars) - 3):
        b1, b2, b3, b4 = bars[i], bars[i+1], bars[i+2], bars[i+3]
        
        # 红柱后连续3个空白
        if (b1['color'] == '红色' and 
            b2['color'] == '空白' and b3['color'] == '空白' and b4['color'] == '空白'):
            
            # 计算空白占比
            blank_ratio = (b2['up_ratio'] + b3['up_ratio'] + b4['up_ratio']) / 3
            
            if blank_ratio <= 25:
                detections.append({
                    'pattern_id': 'pattern_2',
                    'pattern_name': '诱空试仓抄底',
                    'pattern_type': '红+3空白',
                    'signal': '开多单试仓',
                    'signal_type': 'long',
                    'time_range': f"{b1['time']} - {b4['time']}",
                    'blank_ratio': round(blank_ratio, 2),
                    'bars': [b1, b2, b3, b4]
                })
    
    return detections

def check_pattern_3(bars, records):
    """检测模式3: 筑底信号 (黄→绿→黄)
    
    触发条件（双重验证）：
    1. 颜色模式：黄→绿→黄
    2. 触发后10分钟上涨占比 < 10%
    3. 总涨跌幅 < -50%
    
    Args:
        bars: 10分钟柱子数据
        records: 历史记录（用于获取总涨跌幅）
    """
    detections = []
    for i in range(len(bars) - 2):
        b1, b2, b3 = bars[i], bars[i+1], bars[i+2]
        
        if (b1['color'] == '黄色' and b2['color'] == '绿色' and b3['color'] == '黄色'):
            # 检查触发后的上涨占比（最后一根柱子）
            trigger_ratio = b3['up_ratio']
            
            # 条件1: 触发后上涨占比 < 10%
            if trigger_ratio >= 10:
                continue
            
            # 查找对应时间的总涨跌幅
            middle_time = b2['time']  # 使用中间柱子的时间
            total_change = None
            
            for record in records:
                beijing_time = record.get('beijing_time', '')
                if beijing_time.startswith(f"2026-") and middle_time in beijing_time:
                    total_change = record.get('total_change', 0)
                    break
            
            # 条件2: 总涨跌幅 < -50%
            if total_change is not None and total_change < -50:
                detections.append({
                    'pattern_id': 'pattern_3',
                    'pattern_name': '筑底信号',
                    'pattern_type': '黄→绿→黄',
                    'signal': '逢低做多',
                    'signal_type': 'long',
                    'time_range': f"{b1['time']} - {b3['time']}",
                    'trigger_ratio': trigger_ratio,
                    'total_change': round(total_change, 2),
                    'bars': [b1, b2, b3]
                })
    
    return detections

def check_pattern_4(bars):
    """检测模式4: 诱空信号
    
    连续4根：绿→红→红→绿
    或连续3根：绿→红→绿
    触发条件：中间柱上涨占比 < 10%
    """
    detections = []
    
    # 检测4根模式: 绿→红→红→绿
    for i in range(len(bars) - 3):
        b1, b2, b3, b4 = bars[i], bars[i+1], bars[i+2], bars[i+3]
        
        if (b1['color'] == '绿色' and b2['color'] == '红色' and 
            b3['color'] == '红色' and b4['color'] == '绿色'):
            # 检查中间两根红柱的上涨占比
            middle_ratio_1 = b2['up_ratio']
            middle_ratio_2 = b3['up_ratio']
            
            if middle_ratio_1 < 10 and middle_ratio_2 < 10:
                detections.append({
                    'pattern_id': 'pattern_4',
                    'pattern_name': '诱空信号',
                    'pattern_type': '绿→红→红→绿',
                    'signal': '逢低做多',
                    'signal_type': 'long',
                    'time_range': f"{b1['time']} - {b4['time']}",
                    'bars': [b1, b2, b3, b4],
                    'middle_ratios': [middle_ratio_1, middle_ratio_2]
                })
    
    # 检测3根模式: 绿→红→绿
    for i in range(len(bars) - 2):
        b1, b2, b3 = bars[i], bars[i+1], bars[i+2]
        
        if (b1['color'] == '绿色' and b2['color'] == '红色' and b3['color'] == '绿色'):
            # 检查中间红柱的上涨占比
            middle_ratio = b2['up_ratio']
            
            if middle_ratio < 10:
                detections.append({
                    'pattern_id': 'pattern_4',
                    'pattern_name': '诱空信号',
                    'pattern_type': '绿→红→绿',
                    'signal': '逢低做多',
                    'signal_type': 'long',
                    'time_range': f"{b1['time']} - {b3['time']}",
                    'bars': [b1, b2, b3],
                    'middle_ratios': [middle_ratio]
                })
    
    return detections

def is_signal_allowed(pattern_signal_type, daily_prediction, total_change=None):
    """判断信号是否被大周期允许
    
    Args:
        pattern_signal_type: 信号类型 ('long' 或 'short')
        daily_prediction: 日预测数据
        total_change: 当前27币总涨跌幅
    """
    if not daily_prediction:
        return True, "无预判数据，允许所有信号"
    
    daily_signal = daily_prediction.get('signal', '')
    
    # 定义明确的做空信号
    short_signals = ["做空", "等待新低"]
    # 定义明确的做多信号
    long_signals = ["低吸", "诱空试仓抄底"]
    # 中性信号（多空对决未分胜负）
    neutral_signals = ["观望"]
    # 禁止所有操作的信号
    no_trade_signals = ["诱多不参与", "单边诱多行情不参与"]
    
    # 判断大周期方向
    is_daily_short = any(s in daily_signal for s in short_signals)
    is_daily_long = any(s in daily_signal for s in long_signals)
    is_daily_neutral = any(s in daily_signal for s in neutral_signals)
    is_no_trade = any(s in daily_signal for s in no_trade_signals)
    
    # 如果是禁止交易信号，禁止所有操作
    if is_no_trade:
        return False, f"大周期为不参与信号({daily_signal})，禁止所有操作"
    
    # 如果是中性信号（观望），需要根据总涨跌幅判断
    if is_daily_neutral:
        if total_change is None:
            # 没有涨跌幅数据，允许操作
            return True, f"大周期为中性信号({daily_signal})，允许多空操作"
        
        # 观望信号的涨跌幅条件判断
        if pattern_signal_type == 'short':
            # 做空信号：总涨跌幅 > -15 (在-15以上)
            if total_change > -15:
                return True, f"观望且涨跌幅{total_change:.2f}% > -15，允许做空"
            else:
                return False, f"观望但涨跌幅{total_change:.2f}% ≤ -15，禁止做空"
        
        elif pattern_signal_type == 'long':
            # 做多信号：总涨跌幅 < -90 (在-90以下)
            if total_change < -90:
                return True, f"观望且涨跌幅{total_change:.2f}% < -90，允许做多"
            else:
                return False, f"观望但涨跌幅{total_change:.2f}% ≥ -90，禁止做多"
    
    # 如果大周期是做空系列，禁止做多
    if is_daily_short:
        if pattern_signal_type == 'long':
            return False, f"大周期为做空信号({daily_signal})，禁止做多"
    
    # 如果大周期是做多系列，禁止做空
    if is_daily_long:
        if pattern_signal_type == 'short':
            return False, f"大周期为做多信号({daily_signal})，禁止做空"
    
    return True, f"大周期信号({daily_signal})允许"

def deduplicate_detections(detections, time_window_minutes=30):
    """去重检测结果：30分钟内同类型信号只保留第一个
    
    Args:
        detections: 检测结果列表
        time_window_minutes: 时间窗口（分钟）
    
    Returns:
        去重后的检测结果列表
    """
    from datetime import datetime, timedelta
    
    if not detections:
        return []
    
    # 按时间排序
    sorted_detections = sorted(detections, key=lambda x: x['time_range'].split(' - ')[0])
    
    filtered = []
    last_signal_time = {}  # {signal_type: last_time_str}
    
    for detection in sorted_detections:
        signal_type = detection['signal_type']
        time_str = detection['time_range'].split(' - ')[0]  # 取开始时间 "06:30"
        
        # 解析时间
        try:
            hour, minute = map(int, time_str.split(':'))
            current_time = timedelta(hours=hour, minutes=minute)
            
            # 检查是否与上次同类型信号间隔超过30分钟
            if signal_type in last_signal_time:
                last_time_str = last_signal_time[signal_type]
                last_hour, last_minute = map(int, last_time_str.split(':'))
                last_time = timedelta(hours=last_hour, minutes=last_minute)
                
                time_diff = (current_time.total_seconds() - last_time.total_seconds()) / 60
                
                if time_diff < time_window_minutes:
                    print(f"   🔄 跳过重复信号: {detection['pattern_name']} @ {detection['time_range']} "
                          f"(距离上次 {signal_type} 信号仅 {time_diff:.0f} 分钟)")
                    continue
            
            # 添加到结果并更新时间
            filtered.append(detection)
            last_signal_time[signal_type] = time_str
            
        except Exception as e:
            print(f"   ⚠️ 解析时间失败: {time_str}, {e}")
            # 解析失败时保留该检测
            filtered.append(detection)
    
    return filtered

def analyze_single_day(date_str):
    """分析单日数据"""
    print(f"\n{'='*60}")
    print(f"📅 分析日期: {date_str}")
    print(f"{'='*60}")
    
    # 加载历史数据
    records = load_history_data(date_str)
    if not records:
        print(f"⚠️ {date_str} 无历史数据，跳过")
        return None
    
    # 构建10分钟柱子
    bars = build_bars_from_history(records)
    if not bars:
        print(f"⚠️ {date_str} 无法构建柱子数据，跳过")
        return None
    
    # 过滤2:00-23:59的柱子
    bars = [b for b in bars if 2 <= b['hour'] <= 23]
    
    print(f"📊 构建了 {len(bars)} 个10分钟柱子 (2:00-23:59)")
    
    # 统计颜色分布
    colors = {'绿色': 0, '黄色': 0, '红色': 0, '空白': 0}
    for bar in bars:
        colors[bar['color']] += 1
    print(f"🎨 颜色分布: 绿{colors['绿色']} 黄{colors['黄色']} 红{colors['红色']} 空{colors['空白']}")
    
    # 加载预判数据
    daily_prediction = load_daily_prediction(date_str)
    if daily_prediction:
        print(f"📊 大周期预判: {daily_prediction['signal']}")
    else:
        print(f"⚠️ 无大周期预判数据")
    
    # 获取当前总涨跌幅（用于观望信号判断）
    total_change = None
    if records:
        # 使用最新的记录
        total_change = records[-1].get('total_change', 0)
        print(f"📊 当前涨跌幅总和: {total_change:.2f}%")
    
    # 检测所有模式
    all_detections = []
    
    # 模式1
    pattern1_detections = check_pattern_1(bars, daily_prediction)
    for detection in pattern1_detections:
        allowed, reason = is_signal_allowed(detection['signal_type'], daily_prediction, total_change)
        detection['allowed'] = allowed
        detection['block_reason'] = reason if not allowed else None
        all_detections.append(detection)
    
    # 模式2
    pattern2_detections = check_pattern_2(bars)
    for detection in pattern2_detections:
        allowed, reason = is_signal_allowed(detection['signal_type'], daily_prediction, total_change)
        detection['allowed'] = allowed
        detection['block_reason'] = reason if not allowed else None
        all_detections.append(detection)
    
    # 模式3（需要传入records来检查总涨跌幅）
    pattern3_detections = check_pattern_3(bars, records)
    for detection in pattern3_detections:
        allowed, reason = is_signal_allowed(detection['signal_type'], daily_prediction, total_change)
        detection['allowed'] = allowed
        detection['block_reason'] = reason if not allowed else None
        all_detections.append(detection)
    
    # 模式4
    pattern4_detections = check_pattern_4(bars)
    for detection in pattern4_detections:
        allowed, reason = is_signal_allowed(detection['signal_type'], daily_prediction, total_change)
        detection['allowed'] = allowed
        detection['block_reason'] = reason if not allowed else None
        all_detections.append(detection)
    
    print(f"\n🔍 检测结果:")
    print(f"   模式1 (诱多等待新低): {len(pattern1_detections)} 个")
    print(f"   模式2 (诱空试仓抄底): {len(pattern2_detections)} 个")
    print(f"   模式3 (筑底信号): {len(pattern3_detections)} 个")
    print(f"   模式4 (诱空信号): {len(pattern4_detections)} 个")
    print(f"   总计: {len(all_detections)} 个")
    
    # 统计允许和被阻止的数量
    allowed_count = sum(1 for d in all_detections if d['allowed'])
    blocked_count = len(all_detections) - allowed_count
    print(f"   ✅ 允许: {allowed_count} 个")
    print(f"   ❌ 被阻止: {blocked_count} 个")
    
    # 去重：30分钟内同类型信号只保留第一个
    print(f"\n🔄 开始去重（30分钟窗口）...")
    all_detections = deduplicate_detections(all_detections, time_window_minutes=30)
    print(f"✅ 去重后剩余: {len(all_detections)} 个")
    
    # 重新统计
    allowed_count = sum(1 for d in all_detections if d['allowed'])
    blocked_count = len(all_detections) - allowed_count
    
    # 显示详细信息
    if all_detections:
        print(f"\n📋 检测详情:")
        for i, detection in enumerate(all_detections, 1):
            status = "✅" if detection['allowed'] else "❌"
            print(f"   {status} {i}. {detection['pattern_name']} @ {detection['time_range']}")
            print(f"      信号: {detection['signal']} ({detection['signal_type']})")
            if not detection['allowed']:
                print(f"      原因: {detection['block_reason']}")
    
    # 保存检测结果
    output_file = DATA_DIR / f'detections_{date_str}.jsonl'
    with open(output_file, 'w', encoding='utf-8') as f:
        for detection in all_detections:
            record = {
                'timestamp': datetime.now().isoformat(),
                'date': date_str,
                'detection_time': get_beijing_time().strftime('%Y-%m-%d %H:%M:%S'),
                **detection,
                'daily_prediction': daily_prediction
            }
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"\n💾 保存检测结果到: {output_file.name}")
    
    return {
        'date': date_str,
        'total_bars': len(bars),
        'total_detections': len(all_detections),
        'allowed_detections': allowed_count,
        'blocked_detections': blocked_count,
        'detections': all_detections
    }

def main():
    """主函数"""
    print("🚀 开始回溯分析日内模式检测")
    print(f"📅 分析期间: 2026-02-01 至今")
    print(f"📂 数据目录: {HISTORY_DIR}")
    print(f"💾 输出目录: {DATA_DIR}")
    
    # 生成日期列表 (2026-02-01 至今)
    start_date = datetime(2026, 2, 1)
    end_date = get_beijing_time().date()
    
    date_list = []
    current_date = start_date
    while current_date.date() <= end_date:
        date_list.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    print(f"📊 待分析日期: {len(date_list)} 天")
    
    # 逐日分析
    results = []
    for date_str in date_list:
        result = analyze_single_day(date_str)
        if result:
            results.append(result)
    
    # 生成总结报告
    print(f"\n{'='*60}")
    print(f"📊 分析总结")
    print(f"{'='*60}")
    print(f"✅ 成功分析: {len(results)} 天")
    
    total_detections = sum(r['total_detections'] for r in results)
    total_allowed = sum(r['allowed_detections'] for r in results)
    total_blocked = sum(r['blocked_detections'] for r in results)
    
    print(f"🔍 总检测数: {total_detections} 个")
    print(f"✅ 允许执行: {total_allowed} 个 ({total_allowed/total_detections*100:.1f}%)" if total_detections > 0 else "")
    print(f"❌ 被阻止: {total_blocked} 个 ({total_blocked/total_detections*100:.1f}%)" if total_detections > 0 else "")
    
    # 保存总结
    summary_file = DATA_DIR / 'backfill_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'analysis_time': get_beijing_time().isoformat(),
            'start_date': date_list[0] if date_list else None,
            'end_date': date_list[-1] if date_list else None,
            'total_days': len(results),
            'total_detections': total_detections,
            'allowed_detections': total_allowed,
            'blocked_detections': total_blocked,
            'daily_results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 总结报告保存到: {summary_file.name}")
    print(f"✅ 回溯分析完成！")

if __name__ == '__main__':
    main()
