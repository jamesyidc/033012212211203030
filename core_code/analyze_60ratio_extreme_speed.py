#!/usr/bin/env python3
"""
分析正数占比>60%且最低涨速<-15%的情况下，2小时后的涨跌幅
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

def calculate_5min_speed(data_points, index):
    """计算5分钟涨速（未来5分钟的累计涨跌幅）"""
    if index >= len(data_points):
        return None
    
    current_time_str = data_points[index].get('beijing_time', '')
    if not current_time_str:
        return None
    
    try:
        current_time = datetime.strptime(current_time_str, '%Y-%m-%d %H:%M:%S')
        target_time = current_time + timedelta(minutes=5)
        
        current_change = data_points[index].get('cumulative_pct', 0)
        
        # 查找5分钟后最接近的数据点
        for i in range(index + 1, len(data_points)):
            point_time_str = data_points[i].get('beijing_time', '')
            if point_time_str:
                point_time = datetime.strptime(point_time_str, '%Y-%m-%d %H:%M:%S')
                
                if point_time >= target_time:
                    future_change = data_points[i].get('cumulative_pct', 0)
                    return future_change - current_change
        
        # 如果找不到5分钟后的数据，返回最后一个数据点（如果有足够数据）
        if len(data_points) > index + 5:  # 至少要有5个数据点
            last_change = data_points[-1].get('cumulative_pct', 0)
            return last_change - current_change
            
    except Exception as e:
        pass
    
    return None

def get_change_after_hours(data_points, index, hours=2):
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

def find_extreme_speed_points(data_points, up_ratio_threshold=60, speed_threshold=-15):
    """
    找出正数占比>60%且5分钟涨速<-15%的数据点
    """
    extreme_points = []
    
    for i in range(len(data_points) - 10):  # 保留后面至少10个数据点用于计算
        point = data_points[i]
        up_ratio = point.get('up_ratio', 0)
        
        # 检查正数占比是否>60%
        if up_ratio > up_ratio_threshold:
            # 计算5分钟涨速
            speed_5min = calculate_5min_speed(data_points, i)
            
            if speed_5min is not None and speed_5min < speed_threshold:
                # 计算2小时后涨跌幅
                change_2h = get_change_after_hours(data_points, i, hours=2)
                
                if change_2h is not None:
                    extreme_points.append({
                        'index': i,
                        'time': point.get('beijing_time'),
                        'up_ratio': up_ratio,
                        'cumulative_pct': point.get('cumulative_pct', 0),
                        'speed_5min': speed_5min,
                        'change_2h': change_2h
                    })
    
    return extreme_points

def analyze_extreme_conditions():
    """分析正数占比>60%且涨速<-15%的情况"""
    predictions = load_daily_predictions()
    
    if not predictions:
        print("❌ 没有找到预测数据")
        return None
    
    print(f"✅ 加载了 {len(predictions)} 个预测数据")
    
    # 按预测类型分类结果
    results = defaultdict(list)
    all_extreme_points = []
    
    for date, pred in predictions.items():
        signal = pred['signal']
        category = classify_signal(signal)
        
        # 加载该日期的币种变化数据
        data_points = load_coin_change_data(date)
        
        if not data_points or len(data_points) < 50:
            continue
        
        # 找出极端情况点
        extreme_points = find_extreme_speed_points(data_points)
        
        for point in extreme_points:
            point_data = {
                'date': date,
                'signal': signal,
                'category': category,
                'time': point['time'],
                'up_ratio': point['up_ratio'],
                'cumulative_pct': point['cumulative_pct'],
                'speed_5min': point['speed_5min'],
                'change_2h': point['change_2h']
            }
            results[category].append(point_data)
            all_extreme_points.append(point_data)
    
    return {
        'by_category': results,
        'all_points': all_extreme_points
    }

def generate_markdown_report(results):
    """生成Markdown报告"""
    if not results or not results['all_points']:
        return "# 暂无符合条件的数据\n\n未找到正数占比>60%且5分钟涨速<-15%的数据点。\n"
    
    md = "# 📊 极端市场条件分析报告\n\n"
    md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += "---\n\n"
    
    md += "## 📋 分析条件\n\n"
    md += "本报告分析以下极端市场条件下的后续表现：\n\n"
    md += "- **正数占比**: >60%（市场相对乐观）\n"
    md += "- **5分钟涨速**: <-15%（急速下跌）\n"
    md += "- **观察周期**: 2小时后的涨跌幅\n"
    md += "- **市场解读**: 高涨势下的急速回调，可能是获利回吐或恐慌抛售\n\n"
    md += "---\n\n"
    
    all_points = results['all_points']
    by_category = results['by_category']
    
    # 过滤有效数据（2小时后涨跌幅不为0）
    valid_points = [p for p in all_points if abs(p['change_2h']) >= 0.5]
    
    # 统计概览
    md += "## 📈 统计概览\n\n"
    md += f"- **符合条件的数据点总数**: {len(all_points)}个\n"
    md += f"- **有效数据点（|变化| ≥ 0.5%）**: {len(valid_points)}个\n"
    
    if valid_points:
        avg_change = sum(p['change_2h'] for p in valid_points) / len(valid_points)
        positive_count = sum(1 for p in valid_points if p['change_2h'] > 0)
        negative_count = sum(1 for p in valid_points if p['change_2h'] < 0)
        
        md += f"- **2小时后平均涨跌幅**: {avg_change:.2f}%\n"
        md += f"- **上涨次数**: {positive_count}次（{(positive_count/len(valid_points)*100):.1f}%）\n"
        md += f"- **下跌次数**: {negative_count}次（{(negative_count/len(valid_points)*100):.1f}%）\n"
        
        # 计算极值
        max_gain = max(p['change_2h'] for p in valid_points)
        max_loss = min(p['change_2h'] for p in valid_points)
        md += f"- **最大涨幅**: {max_gain:.2f}%\n"
        md += f"- **最大跌幅**: {max_loss:.2f}%\n"
        
        # 信号评价
        if avg_change > 5:
            signal_eval = "✅ 强烈反弹信号"
        elif avg_change > 2:
            signal_eval = "⭐ 反弹信号"
        elif avg_change > 0:
            signal_eval = "⚡ 弱反弹信号"
        elif avg_change > -5:
            signal_eval = "⚠️ 继续下跌"
        else:
            signal_eval = "🔴 暴跌风险"
        
        md += f"- **信号评价**: {signal_eval}\n"
    
    md += "\n---\n\n"
    
    # 按预测类型统计
    md += "## 📊 按预测类型统计\n\n"
    md += "| 预测类型 | 数据点数 | 有效数据 | 平均2h涨跌 | 上涨概率 | 最大涨幅 | 最大跌幅 |\n"
    md += "|---------|---------|---------|-----------|---------|---------|----------|\n"
    
    for category in ['低吸', '等待新低', '做空', '诱多', '空头强控盘', '观望']:
        if category in by_category:
            cat_points = by_category[category]
            cat_valid = [p for p in cat_points if abs(p['change_2h']) >= 0.5]
            
            if cat_valid:
                avg = sum(p['change_2h'] for p in cat_valid) / len(cat_valid)
                positive_rate = (sum(1 for p in cat_valid if p['change_2h'] > 0) / len(cat_valid)) * 100
                max_gain = max(p['change_2h'] for p in cat_valid)
                max_loss = min(p['change_2h'] for p in cat_valid)
                
                md += f"| {category} | {len(cat_points)} | {len(cat_valid)} | {avg:.2f}% | {positive_rate:.1f}% | {max_gain:.2f}% | {max_loss:.2f}% |\n"
    
    md += "\n---\n\n"
    
    # 详细数据列表（仅显示有效数据）
    md += "## 🔍 详细数据列表（仅显示有效数据，|变化| ≥ 0.5%）\n\n"
    
    for category in ['低吸', '等待新低', '做空', '诱多', '空头强控盘', '观望']:
        if category not in by_category:
            continue
        
        cat_valid = [p for p in by_category[category] if abs(p['change_2h']) >= 0.5]
        
        if not cat_valid:
            continue
        
        md += f"### {category}\n\n"
        md += "| 日期 | 预测信号 | 时间 | 正数占比 | 5分钟涨速 | 2小时后涨跌 |\n"
        md += "|------|---------|------|---------|----------|------------|\n"
        
        for point in cat_valid:
            date = point['date']
            signal = point['signal']
            time = point['time'].split(' ')[1] if ' ' in point['time'] else point['time']
            ratio = f"{point['up_ratio']:.1f}%"
            speed = f"{point['speed_5min']:.2f}%"
            change = f"{point['change_2h']:.2f}%"
            
            md += f"| {date} | {signal} | {time} | {ratio} | {speed} | {change} |\n"
        
        md += "\n"
    
    md += "---\n\n"
    
    # 分析总结
    md += "## 💡 分析总结\n\n"
    
    if valid_points:
        avg_change = sum(p['change_2h'] for p in valid_points) / len(valid_points)
        positive_rate = (sum(1 for p in valid_points if p['change_2h'] > 0) / len(valid_points)) * 100
        
        md += f"### 整体表现\n\n"
        md += f"- **样本数量**: {len(valid_points)}个有效样本\n"
        md += f"- **平均涨跌**: {avg_change:.2f}%\n"
        md += f"- **反弹概率**: {positive_rate:.1f}%\n\n"
        
        if avg_change > 0:
            md += "**结论**: 正数占比>60%时出现急速下跌（5分钟跌幅<-15%），2小时后平均出现反弹，可能是短期获利回吐后的恢复。\n\n"
        else:
            md += "**结论**: 正数占比>60%时出现急速下跌（5分钟跌幅<-15%），2小时后继续下跌，可能是市场转向的信号。\n\n"
        
        md += "### 各预测类型表现\n\n"
        
        for category in ['低吸', '等待新低', '做空', '诱多', '空头强控盘', '观望']:
            if category in by_category:
                cat_valid = [p for p in by_category[category] if abs(p['change_2h']) >= 0.5]
                
                if cat_valid:
                    avg = sum(p['change_2h'] for p in cat_valid) / len(cat_valid)
                    pos_rate = (sum(1 for p in cat_valid if p['change_2h'] > 0) / len(cat_valid)) * 100
                    
                    md += f"#### {category}\n\n"
                    md += f"- 样本数: {len(cat_valid)}个\n"
                    md += f"- 平均涨跌: {avg:.2f}%\n"
                    md += f"- 反弹概率: {pos_rate:.1f}%\n"
                    
                    if avg > 5:
                        md += f"- **推荐操作**: ✅ 强烈建议抄底\n\n"
                    elif avg > 2:
                        md += f"- **推荐操作**: ⭐ 可以抄底\n\n"
                    elif avg > 0:
                        md += f"- **推荐操作**: ⚡ 谨慎抄底\n\n"
                    else:
                        md += f"- **推荐操作**: ⚠️ 避免抄底，可能继续下跌\n\n"
    
    md += "---\n\n"
    md += "*注: 极端市场条件（正数占比>60% + 5分钟跌幅<-15%）通常代表短期恐慌或获利回吐，历史数据显示这种情况后的反弹概率较高。*\n"
    
    return md

def main():
    print("🚀 开始分析极端市场条件（正数占比>60% + 5分钟涨速<-15%）...")
    print()
    
    results = analyze_extreme_conditions()
    
    if not results:
        print("❌ 分析失败，没有有效数据")
        return
    
    all_points = results['all_points']
    valid_points = [p for p in all_points if abs(p['change_2h']) >= 0.5]
    
    print(f"✅ 分析完成！")
    print(f"   符合条件的数据点: {len(all_points)} 个")
    print(f"   有效数据点: {len(valid_points)} 个")
    
    if valid_points:
        avg_change = sum(p['change_2h'] for p in valid_points) / len(valid_points)
        positive_count = sum(1 for p in valid_points if p['change_2h'] > 0)
        positive_rate = (positive_count / len(valid_points)) * 100
        
        print(f"   2小时后平均涨跌: {avg_change:.2f}%")
        print(f"   反弹概率: {positive_rate:.1f}% ({positive_count}/{len(valid_points)})")
    
    print()
    
    # 生成Markdown报告
    md_content = generate_markdown_report(results)
    
    # 保存报告
    output_file = 'EXTREME_CONDITION_ANALYSIS.md'
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
