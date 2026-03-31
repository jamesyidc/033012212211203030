#!/usr/bin/env python3
"""
分析正数占比突破40%阈值时的后续表现
- 从<40%突破到>40%：看涨信号
- 从>40%跌破到<40%：看跌信号
"""
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

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

def find_threshold_crossings(data_points):
    """
    找出正数占比突破40%阈值的时刻
    返回：
    - up_crossings: 从<40%突破到>40%的时刻
    - down_crossings: 从>40%跌破到<40%的时刻
    """
    up_crossings = []
    down_crossings = []
    
    for i in range(len(data_points) - 1):
        current = data_points[i]
        next_point = data_points[i + 1]
        
        current_ratio = current.get('up_ratio', 0)
        next_ratio = next_point.get('up_ratio', 0)
        
        # 从<40%突破到>=40%
        if current_ratio < 40 and next_ratio >= 40:
            up_crossings.append({
                'index': i + 1,
                'time': next_point.get('beijing_time'),
                'up_ratio': next_ratio,
                'cumulative_pct': next_point.get('cumulative_pct', 0)
            })
        
        # 从>=40%跌破到<40%
        if current_ratio >= 40 and next_ratio < 40:
            down_crossings.append({
                'index': i + 1,
                'time': next_point.get('beijing_time'),
                'up_ratio': next_ratio,
                'cumulative_pct': next_point.get('cumulative_pct', 0)
            })
    
    return up_crossings, down_crossings

def get_change_after_hours(data_points, index, hours=4):
    """获取指定小时后的涨跌幅"""
    if index >= len(data_points):
        return None
    
    current_time_str = data_points[index].get('beijing_time', '')
    if not current_time_str:
        return None
    
    try:
        current_time = datetime.strptime(current_time_str, '%Y-%m-%d %H:%M:%S')
        target_time = current_time + timedelta(hours=hours)
        
        current_change = data_points[index].get('cumulative_pct', 0)
        
        # 查找指定小时后最接近的数据点
        for i in range(index + 1, len(data_points)):
            point_time_str = data_points[i].get('beijing_time', '')
            if point_time_str:
                point_time = datetime.strptime(point_time_str, '%Y-%m-%d %H:%M:%S')
                
                if point_time >= target_time:
                    future_change = data_points[i].get('cumulative_pct', 0)
                    return future_change - current_change
        
        # 如果找不到指定小时后的数据，返回最后一个数据点
        if len(data_points) > index + 20:  # 至少要有20个数据点（约20分钟）
            last_change = data_points[-1].get('cumulative_pct', 0)
            return last_change - current_change
            
    except Exception as e:
        pass
    
    return None

def analyze_threshold_crossings():
    """分析正数占比突破40%阈值的情况"""
    predictions = load_daily_predictions()
    
    if not predictions:
        print("❌ 没有找到预测数据")
        return None
    
    print(f"✅ 加载了 {len(predictions)} 个预测数据")
    
    # 按预测类型分类结果
    results = defaultdict(lambda: {
        'up_crossings': [],  # 向上突破
        'down_crossings': []  # 向下跌破
    })
    
    all_up_crossings = []
    all_down_crossings = []
    
    for date, pred in predictions.items():
        signal = pred['signal']
        category = classify_signal(signal)
        
        # 加载该日期的币种变化数据
        data_points = load_coin_change_data(date)
        
        if not data_points or len(data_points) < 50:
            continue
        
        # 找出阈值突破点
        up_crossings, down_crossings = find_threshold_crossings(data_points)
        
        # 只取第一次突破
        if up_crossings:
            first_up = up_crossings[0]
            change_4h = get_change_after_hours(data_points, first_up['index'], hours=4)
            
            if change_4h is not None:
                crossing_data = {
                    'date': date,
                    'signal': signal,
                    'time': first_up['time'],
                    'up_ratio': first_up['up_ratio'],
                    'start_pct': first_up['cumulative_pct'],
                    'change_4h': change_4h
                }
                results[category]['up_crossings'].append(crossing_data)
                all_up_crossings.append(crossing_data)
        
        if down_crossings:
            first_down = down_crossings[0]
            change_4h = get_change_after_hours(data_points, first_down['index'], hours=4)
            
            if change_4h is not None:
                crossing_data = {
                    'date': date,
                    'signal': signal,
                    'time': first_down['time'],
                    'up_ratio': first_down['up_ratio'],
                    'start_pct': first_down['cumulative_pct'],
                    'change_4h': change_4h
                }
                results[category]['down_crossings'].append(crossing_data)
                all_down_crossings.append(crossing_data)
    
    return {
        'by_category': results,
        'all_up': all_up_crossings,
        'all_down': all_down_crossings
    }

def generate_markdown_report(results):
    """生成Markdown报告"""
    if not results:
        return "# 暂无数据\n"
    
    md = "# 📊 正数占比40%阈值突破分析报告（剔除无效数据）\n\n"
    md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += "---\n\n"
    
    md += "## 📋 分析说明\n\n"
    md += "本报告分析正数占比突破40%阈值时的后续表现：\n\n"
    md += "- **向上突破**: 当天第一次从<40%突破到≥40%，看涨信号\n"
    md += "- **向下跌破**: 当天第一次从≥40%跌破到<40%，看跌信号\n"
    md += "- **观察周期**: 突破/跌破后的4小时涨跌幅\n"
    md += "- **预测分类**: 按6种预测类型分析\n"
    md += "- **数据过滤**: 已剔除涨跌幅为0或接近0（|change| < 0.5%）的无效数据\n\n"
    md += "---\n\n"
    
    all_up = results['all_up']
    all_down = results['all_down']
    by_category = results['by_category']
    
    # 过滤无效数据（涨跌幅接近0）
    all_up_filtered = [item for item in all_up if abs(item['change_4h']) >= 0.5]
    all_down_filtered = [item for item in all_down if abs(item['change_4h']) >= 0.5]
    
    # 统计概览
    md += "## 📈 统计概览\n\n"
    md += "### 总体统计（过滤后）\n\n"
    md += f"- **向上突破原始样本数**: {len(all_up)}个\n"
    md += f"- **向上突破有效样本数**: {len(all_up_filtered)}个\n"
    if all_up_filtered:
        avg_up_change = sum(item['change_4h'] for item in all_up_filtered) / len(all_up_filtered)
        md += f"- **向上突破后4小时平均涨跌**: {avg_up_change:.2f}%\n"
    else:
        md += f"- **向上突破后4小时平均涨跌**: N/A（无有效数据）\n"
    
    md += f"- **向下跌破原始样本数**: {len(all_down)}个\n"
    md += f"- **向下跌破有效样本数**: {len(all_down_filtered)}个\n"
    if all_down_filtered:
        avg_down_change = sum(item['change_4h'] for item in all_down_filtered) / len(all_down_filtered)
        md += f"- **向下跌破后4小时平均涨跌**: {avg_down_change:.2f}%\n"
    else:
        md += f"- **向下跌破后4小时平均涨跌**: N/A（无有效数据）\n"
    
    md += "\n### 按预测类型统计（过滤后）\n\n"
    md += "| 预测类型 | 向上突破次数 | 向上突破有效 | 向上突破后4h | 向下跌破次数 | 向下跌破有效 | 向下跌破后4h |\n"
    md += "|---------|------------|------------|------------|------------|------------|------------|\n"
    
    for category in ['低吸', '等待新低', '做空', '诱多', '空头强控盘', '观望']:
        if category in by_category:
            data = by_category[category]
            
            # 过滤向上突破数据
            up_filtered = [item for item in data['up_crossings'] if abs(item['change_4h']) >= 0.5]
            up_count = len(data['up_crossings'])
            up_valid_count = len(up_filtered)
            
            # 过滤向下跌破数据
            down_filtered = [item for item in data['down_crossings'] if abs(item['change_4h']) >= 0.5]
            down_count = len(data['down_crossings'])
            down_valid_count = len(down_filtered)
            
            avg_up = "N/A"
            if up_filtered:
                avg = sum(item['change_4h'] for item in up_filtered) / len(up_filtered)
                avg_up = f"{avg:.2f}%"
            
            avg_down = "N/A"
            if down_filtered:
                avg = sum(item['change_4h'] for item in down_filtered) / len(down_filtered)
                avg_down = f"{avg:.2f}%"
            
            md += f"| {category} | {up_count} | {up_valid_count} | {avg_up} | {down_count} | {down_valid_count} | {avg_down} |\n"
    
    md += "\n---\n\n"
    
    # 详细分析（仅显示有效数据）
    md += "## 🔍 详细分析（仅显示有效数据，|change| ≥ 0.5%）\n\n"
    
    # 向上突破分析
    md += "### 📈 向上突破（<40% → ≥40%）\n\n"
    
    for category in ['低吸', '等待新低', '做空', '诱多', '空头强控盘', '观望']:
        if category not in by_category:
            continue
        
        # 过滤有效数据
        valid_data = [item for item in by_category[category]['up_crossings'] if abs(item['change_4h']) >= 0.5]
        
        if not valid_data:
            continue
        
        md += f"#### {category}\n\n"
        md += "| 日期 | 预测信号 | 突破时间 | 突破时正数占比 | 4小时后涨跌 |\n"
        md += "|------|---------|---------|--------------|------------|\n"
        
        for item in valid_data:
            date = item['date']
            signal = item['signal']
            time = item['time'].split(' ')[1] if ' ' in item['time'] else item['time']
            ratio = f"{item['up_ratio']:.1f}%"
            change = f"{item['change_4h']:.2f}%"
            md += f"| {date} | {signal} | {time} | {ratio} | {change} |\n"
        
        md += "\n"
    
    # 向下跌破分析
    md += "### 📉 向下跌破（≥40% → <40%）\n\n"
    
    for category in ['低吸', '等待新低', '做空', '诱多', '空头强控盘', '观望']:
        if category not in by_category:
            continue
        
        # 过滤有效数据
        valid_data = [item for item in by_category[category]['down_crossings'] if abs(item['change_4h']) >= 0.5]
        
        if not valid_data:
            continue
        
        md += f"#### {category}\n\n"
        md += "| 日期 | 预测信号 | 跌破时间 | 跌破时正数占比 | 4小时后涨跌 |\n"
        md += "|------|---------|---------|--------------|------------|\n"
        
        for item in valid_data:
            date = item['date']
            signal = item['signal']
            time = item['time'].split(' ')[1] if ' ' in item['time'] else item['time']
            ratio = f"{item['up_ratio']:.1f}%"
            change = f"{item['change_4h']:.2f}%"
            md += f"| {date} | {signal} | {time} | {ratio} | {change} |\n"
        
        md += "\n"
    
    # 总结分析
    md += "---\n\n"
    md += "## 💡 分析总结（基于有效数据）\n\n"
    
    md += "### 向上突破信号效果\n\n"
    
    if all_up_filtered:
        avg_up = sum(item['change_4h'] for item in all_up_filtered) / len(all_up_filtered)
        positive_count = sum(1 for item in all_up_filtered if item['change_4h'] > 0)
        positive_rate = (positive_count / len(all_up_filtered)) * 100
        
        md += f"- **原始样本数**: {len(all_up)}个\n"
        md += f"- **有效样本数**: {len(all_up_filtered)}个（过滤率 {((len(all_up) - len(all_up_filtered)) / len(all_up) * 100):.1f}%）\n"
        md += f"- **平均涨跌幅**: {avg_up:.2f}%\n"
        md += f"- **上涨概率**: {positive_rate:.1f}% ({positive_count}/{len(all_up_filtered)})\n"
        
        if avg_up > 2:
            md += f"- **信号评价**: ✅ 有效看涨信号\n\n"
        elif avg_up > 0:
            md += f"- **信号评价**: ⚡ 弱看涨信号\n\n"
        else:
            md += f"- **信号评价**: ⚠️ 无效信号（可能有陷阱）\n\n"
    else:
        md += "- **样本数**: 无有效数据\n\n"
    
    md += "### 向下跌破信号效果\n\n"
    
    if all_down_filtered:
        avg_down = sum(item['change_4h'] for item in all_down_filtered) / len(all_down_filtered)
        negative_count = sum(1 for item in all_down_filtered if item['change_4h'] < 0)
        negative_rate = (negative_count / len(all_down_filtered)) * 100
        
        md += f"- **原始样本数**: {len(all_down)}个\n"
        md += f"- **有效样本数**: {len(all_down_filtered)}个（过滤率 {((len(all_down) - len(all_down_filtered)) / len(all_down) * 100):.1f}%）\n"
        md += f"- **平均涨跌幅**: {avg_down:.2f}%\n"
        md += f"- **下跌概率**: {negative_rate:.1f}% ({negative_count}/{len(all_down_filtered)})\n"
        
        if avg_down < -2:
            md += f"- **信号评价**: ✅ 有效看跌信号\n\n"
        elif avg_down < 0:
            md += f"- **信号评价**: ⚡ 弱看跌信号\n\n"
        else:
            md += f"- **信号评价**: ⚠️ 无效信号（可能反向）\n\n"
    else:
        md += "- **样本数**: 无有效数据\n\n"
    
    # 按预测类型总结
    md += "### 各预测类型表现（过滤后）\n\n"
    
    for category in ['低吸', '等待新低', '做空', '诱多', '空头强控盘', '观望']:
        if category not in by_category:
            continue
        
        data = by_category[category]
        
        # 过滤数据
        up_filtered = [item for item in data['up_crossings'] if abs(item['change_4h']) >= 0.5]
        down_filtered = [item for item in data['down_crossings'] if abs(item['change_4h']) >= 0.5]
        
        if not up_filtered and not down_filtered:
            continue
        
        md += f"#### {category}\n\n"
        
        if up_filtered:
            avg = sum(item['change_4h'] for item in up_filtered) / len(up_filtered)
            md += f"- **向上突破**: {len(data['up_crossings'])}次原始，{len(up_filtered)}次有效，4小时后平均{avg:.2f}%\n"
        
        if down_filtered:
            avg = sum(item['change_4h'] for item in down_filtered) / len(down_filtered)
            md += f"- **向下跌破**: {len(data['down_crossings'])}次原始，{len(down_filtered)}次有效，4小时后平均{avg:.2f}%\n"
        
        md += "\n"
    
    md += "---\n\n"
    md += "*注: 40%阈值为正数占比的关键分界线，突破和跌破该阈值往往预示市场情绪转变。本报告已过滤所有涨跌幅 < 0.5% 的无效数据。*\n"
    
    return md

def main():
    print("🚀 开始分析正数占比40%阈值突破情况...")
    print()
    
    results = analyze_threshold_crossings()
    
    if not results:
        print("❌ 分析失败，没有有效数据")
        return
    
    all_up = results['all_up']
    all_down = results['all_down']
    
    print(f"✅ 分析完成！")
    print(f"   向上突破样本: {len(all_up)} 个")
    print(f"   向下跌破样本: {len(all_down)} 个")
    
    if all_up:
        avg_up = sum(item['change_4h'] for item in all_up) / len(all_up)
        print(f"   向上突破后4小时平均: {avg_up:.2f}%")
    
    if all_down:
        avg_down = sum(item['change_4h'] for item in all_down) / len(all_down)
        print(f"   向下跌破后4小时平均: {avg_down:.2f}%")
    
    print()
    
    # 生成Markdown报告
    md_content = generate_markdown_report(results)
    
    # 保存报告
    output_file = 'THRESHOLD_40_CROSSING_ANALYSIS.md'
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
