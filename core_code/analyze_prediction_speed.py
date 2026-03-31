#!/usr/bin/env python3
"""
分析每日预测下的5分钟涨速极值情况
按照6种预测类型分类：低吸、等待新低、做空、诱多、空头强控盘、观望
"""
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

# 数据目录
PREDICTION_DIR = 'data/daily_predictions'
COIN_CHANGE_DIR = 'data/coin_change_tracker'

# 预测类型映射
PREDICTION_TYPES = {
    '低吸': ['低吸', '做多', '相对低点做多'],
    '等待新低': ['等待新低'],
    '做空': ['做空', '相对高点做空'],
    '诱多': ['诱多'],
    '空头强控盘': ['空头强控盘'],
    '观望': ['观望', '震荡', '等待']
}

def load_daily_predictions():
    """加载所有每日预测"""
    predictions = {}
    
    if not os.path.exists(PREDICTION_DIR):
        print(f"❌ 预测目录不存在: {PREDICTION_DIR}")
        return predictions
    
    for file in sorted(os.listdir(PREDICTION_DIR)):
        if not file.endswith('.json'):
            continue
            
        file_path = os.path.join(PREDICTION_DIR, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                date = data.get('date')
                signal = data.get('signal', '')
                
                if date and signal:
                    predictions[date] = {
                        'signal': signal,
                        'description': data.get('description', ''),
                        'timestamp': data.get('timestamp', '')
                    }
        except Exception as e:
            print(f"⚠️  读取预测文件失败 {file}: {e}")
    
    return predictions

def classify_signal(signal):
    """分类信号到6种类型"""
    signal_lower = signal.lower()
    
    for category, keywords in PREDICTION_TYPES.items():
        for keyword in keywords:
            if keyword in signal:
                return category
    
    # 默认分类
    if '多' in signal or '涨' in signal:
        return '低吸'
    elif '空' in signal or '跌' in signal:
        return '做空'
    else:
        return '观望'

def load_coin_change_data(date_str):
    """加载指定日期的币种变化数据"""
    # 转换日期格式 2026-02-20 -> 20260220
    date_file = date_str.replace('-', '')
    file_path = os.path.join(COIN_CHANGE_DIR, f'coin_change_{date_file}.jsonl')
    
    if not os.path.exists(file_path):
        return []
    
    data_points = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    data_points.append(record)
    except Exception as e:
        print(f"⚠️  读取币种变化数据失败 {file_path}: {e}")
    
    return data_points

def calculate_5min_speeds(data_points):
    """计算5分钟涨速"""
    speeds = []
    
    for i in range(len(data_points) - 1):
        current = data_points[i]
        next_point = data_points[i + 1]
        
        # 获取时间戳
        current_time = current.get('beijing_time', '')
        next_time = next_point.get('beijing_time', '')
        
        # 获取正数占比（整数占比）
        up_ratio = current.get('up_ratio', 0)
        
        # 获取累计涨跌幅
        current_change = current.get('cumulative_pct', 0)
        next_change = next_point.get('cumulative_pct', 0)
        
        # 计算5分钟涨速（涨跌幅变化）
        speed = next_change - current_change
        
        speeds.append({
            'time': current_time,
            'speed': speed,
            'up_ratio': up_ratio,
            'current_change': current_change,
            'next_change': next_change
        })
    
    return speeds

def get_change_after_2hours(data_points, index):
    """获取2小时后的涨跌幅"""
    if index >= len(data_points):
        return None
    
    current_time_str = data_points[index].get('beijing_time', '')
    if not current_time_str:
        return None
    
    try:
        current_time = datetime.strptime(current_time_str, '%Y-%m-%d %H:%M:%S')
        target_time = current_time + timedelta(hours=2)
        
        # 查找2小时后最接近的数据点
        current_change = data_points[index].get('cumulative_pct', 0)
        
        for i in range(index + 1, len(data_points)):
            point_time_str = data_points[i].get('beijing_time', '')
            if point_time_str:
                point_time = datetime.strptime(point_time_str, '%Y-%m-%d %H:%M:%S')
                
                if point_time >= target_time:
                    future_change = data_points[i].get('cumulative_pct', 0)
                    return future_change - current_change
        
        # 如果找不到2小时后的数据，返回最后一个数据点
        if len(data_points) > index + 10:  # 至少要有10个数据点
            last_change = data_points[-1].get('cumulative_pct', 0)
            return last_change - current_change
            
    except Exception as e:
        pass
    
    return None

def analyze_prediction_speeds():
    """分析预测类型下的涨速情况"""
    predictions = load_daily_predictions()
    
    if not predictions:
        print("❌ 没有找到预测数据")
        return None
    
    print(f"✅ 加载了 {len(predictions)} 个预测数据")
    
    # 按类型分类结果
    results = defaultdict(list)
    
    for date, pred in predictions.items():
        signal = pred['signal']
        category = classify_signal(signal)
        
        # 加载该日期的币种变化数据
        data_points = load_coin_change_data(date)
        
        if not data_points or len(data_points) < 10:
            continue
        
        # 计算5分钟涨速
        speeds = calculate_5min_speeds(data_points)
        
        if not speeds:
            continue
        
        # 排序找出最高和最低涨速的前3名
        sorted_speeds = sorted(speeds, key=lambda x: x['speed'], reverse=True)
        
        top3_high = sorted_speeds[:3]
        top3_low = sorted_speeds[-3:]
        
        # 获取2小时后的涨跌幅
        for item in top3_high:
            time_str = item['time']
            # 找到对应的数据点索引
            for idx, point in enumerate(data_points):
                if point.get('beijing_time') == time_str:
                    change_2h = get_change_after_2hours(data_points, idx)
                    item['change_2h_later'] = change_2h
                    break
        
        for item in top3_low:
            time_str = item['time']
            for idx, point in enumerate(data_points):
                if point.get('beijing_time') == time_str:
                    change_2h = get_change_after_2hours(data_points, idx)
                    item['change_2h_later'] = change_2h
                    break
        
        results[category].append({
            'date': date,
            'signal': signal,
            'top3_high': top3_high,
            'top3_low': top3_low
        })
    
    return results

def is_valid_data(value):
    """检查数据是否有效（排除None、0等非正常数据）"""
    if value is None:
        return False
    if abs(value) < 0.01:  # 排除接近0的数据
        return False
    return True

def generate_markdown_report(results):
    """生成Markdown报告"""
    if not results:
        return "# 暂无数据\n"
    
    md = "# 📊 当天走势预测涨速分析报告\n\n"
    md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += "---\n\n"
    
    md += "## 📋 分析说明\n\n"
    md += "本报告分析了每日预测的6种情况下，5分钟涨速的极值表现：\n\n"
    md += "- **预测类型**: 低吸、等待新低、做空、诱多、空头强控盘、观望\n"
    md += "- **涨速指标**: 5分钟时间窗口内的累计涨跌幅变化\n"
    md += "- **极值取样**: 每个日期取最高涨速前3名和最低涨速前3名\n"
    md += "- **后续表现**: 记录当时的正数占比和2小时后的涨跌幅变化\n"
    md += "- **数据过滤**: 已排除N/A和接近0的非正常数据\n\n"
    md += "---\n\n"
    
    # 统计信息
    md += "## 📈 统计概览\n\n"
    md += "| 预测类型 | 样本日期数 | 高涨速样本 | 低涨速样本 |\n"
    md += "|---------|-----------|-----------|----------|\n"
    
    for category in ['低吸', '等待新低', '做空', '诱多', '空头强控盘', '观望']:
        if category in results:
            data = results[category]
            total_dates = len(data)
            total_high = sum(len(d['top3_high']) for d in data)
            total_low = sum(len(d['top3_low']) for d in data)
            md += f"| {category} | {total_dates} | {total_high} | {total_low} |\n"
    
    md += "\n---\n\n"
    
    # 详细分析
    for category in ['低吸', '等待新低', '做空', '诱多', '空头强控盘', '观望']:
        if category not in results:
            continue
        
        md += f"## 🎯 {category}\n\n"
        
        data_list = results[category]
        
        if not data_list:
            md += "*暂无数据*\n\n"
            continue
        
        for data in data_list:
            date = data['date']
            signal = data['signal']
            top3_high = data['top3_high']
            top3_low = data['top3_low']
            
            md += f"### 📅 {date} - {signal}\n\n"
            
            # 最高涨速前3名
            md += "#### 🔥 最高涨速 TOP 3\n\n"
            md += "| 时间 | 5分钟涨速 | 正数占比 | 2小时后涨跌 |\n"
            md += "|------|----------|---------|------------|\n"
            
            for item in top3_high:
                time_str = item['time'].split(' ')[1] if ' ' in item['time'] else item['time']
                speed = f"{item['speed']:.2f}%"
                up_ratio = f"{item['up_ratio']:.1f}%"
                change_2h = f"{item.get('change_2h_later', 0):.2f}%" if item.get('change_2h_later') is not None else "N/A"
                md += f"| {time_str} | {speed} | {up_ratio} | {change_2h} |\n"
            
            md += "\n"
            
            # 最低涨速前3名
            md += "#### ❄️ 最低涨速 TOP 3\n\n"
            md += "| 时间 | 5分钟涨速 | 正数占比 | 2小时后涨跌 |\n"
            md += "|------|----------|---------|------------|\n"
            
            for item in top3_low:
                time_str = item['time'].split(' ')[1] if ' ' in item['time'] else item['time']
                speed = f"{item['speed']:.2f}%"
                up_ratio = f"{item['up_ratio']:.1f}%"
                change_2h = f"{item.get('change_2h_later', 0):.2f}%" if item.get('change_2h_later') is not None else "N/A"
                md += f"| {time_str} | {speed} | {up_ratio} | {change_2h} |\n"
            
            md += "\n---\n\n"
    
    # 添加总结分析
    md += "## 💡 分析总结\n\n"
    md += "### 各预测类型特征（已过滤非正常数据）\n\n"
    
    for category in ['低吸', '等待新低', '做空', '诱多', '空头强控盘', '观望']:
        if category not in results:
            continue
        
        data_list = results[category]
        if not data_list:
            continue
        
        # 统计平均值 - 过滤非正常数据
        all_high_speeds = []
        all_low_speeds = []
        all_high_2h = []
        all_low_2h = []
        all_high_up_ratio = []
        all_low_up_ratio = []
        
        for data in data_list:
            for item in data['top3_high']:
                if is_valid_data(item['speed']):
                    all_high_speeds.append(item['speed'])
                if is_valid_data(item.get('change_2h_later')):
                    all_high_2h.append(item['change_2h_later'])
                if is_valid_data(item.get('up_ratio')):
                    all_high_up_ratio.append(item['up_ratio'])
            
            for item in data['top3_low']:
                if is_valid_data(item['speed']):
                    all_low_speeds.append(item['speed'])
                if is_valid_data(item.get('change_2h_later')):
                    all_low_2h.append(item['change_2h_later'])
                if is_valid_data(item.get('up_ratio')):
                    all_low_up_ratio.append(item['up_ratio'])
        
        md += f"#### {category}\n\n"
        
        if all_high_speeds:
            avg_high_speed = sum(all_high_speeds) / len(all_high_speeds)
            md += f"- **平均最高涨速**: {avg_high_speed:.2f}% (有效样本: {len(all_high_speeds)})\n"
        
        if all_high_2h:
            avg_high_2h = sum(all_high_2h) / len(all_high_2h)
            md += f"- **高涨速后2小时平均涨跌**: {avg_high_2h:.2f}% (有效样本: {len(all_high_2h)})\n"
        
        if all_high_up_ratio:
            avg_high_up_ratio = sum(all_high_up_ratio) / len(all_high_up_ratio)
            md += f"- **高涨速时平均正数占比**: {avg_high_up_ratio:.1f}%\n"
        
        if all_low_speeds:
            avg_low_speed = sum(all_low_speeds) / len(all_low_speeds)
            md += f"- **平均最低涨速**: {avg_low_speed:.2f}% (有效样本: {len(all_low_speeds)})\n"
        
        if all_low_2h:
            avg_low_2h = sum(all_low_2h) / len(all_low_2h)
            md += f"- **低涨速后2小时平均涨跌**: {avg_low_2h:.2f}% (有效样本: {len(all_low_2h)})\n"
        
        if all_low_up_ratio:
            avg_low_up_ratio = sum(all_low_up_ratio) / len(all_low_up_ratio)
            md += f"- **低涨速时平均正数占比**: {avg_low_up_ratio:.1f}%\n"
        
        md += "\n"
    
    md += "\n---\n\n"
    md += "*注: 5分钟涨速为该时间点后5分钟的累计涨跌幅变化；正数占比为上涨币种占比；2小时后涨跌为相对于当前时刻的涨跌幅变化*\n"
    md += "*数据已排除N/A和接近0（±0.01%以内）的非正常数据*\n"
    
    return md

def main():
    print("🚀 开始分析预测涨速数据...")
    print()
    
    results = analyze_prediction_speeds()
    
    if not results:
        print("❌ 分析失败，没有有效数据")
        return
    
    print(f"✅ 分析完成！")
    print(f"   找到 {len(results)} 个预测类型的数据")
    for category, data_list in results.items():
        print(f"   - {category}: {len(data_list)} 个日期")
    print()
    
    # 生成Markdown报告
    md_content = generate_markdown_report(results)
    
    # 保存报告
    output_file = 'PREDICTION_SPEED_ANALYSIS.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"📄 报告已生成: {output_file}")
    print(f"   总行数: {len(md_content.splitlines())}")
    
    # 显示部分内容
    print("\n" + "="*60)
    print("报告预览（前50行）:")
    print("="*60)
    for i, line in enumerate(md_content.splitlines()[:50], 1):
        print(line)
    
    if len(md_content.splitlines()) > 50:
        print("\n... (更多内容请查看完整报告文件) ...")

if __name__ == '__main__':
    main()
