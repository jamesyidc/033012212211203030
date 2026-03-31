#!/usr/bin/env python3
"""
分析各种市场条件下做多和做空的胜率
找出最佳做多条件和最佳做空条件
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
        if len(data_points) > index + 5:
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
        if len(data_points) > index + 20:
            last_change = data_points[-1].get('cumulative_pct', 0)
            return last_change - current_change
            
    except Exception as e:
        pass
    
    return None

def analyze_all_conditions():
    """分析所有市场条件下的做多/做空胜率"""
    predictions = load_daily_predictions()
    
    if not predictions:
        print("❌ 没有找到预测数据")
        return None
    
    print(f"✅ 加载了 {len(predictions)} 个预测数据")
    
    # 定义各种条件组合
    conditions = []
    
    # 1. 预测类型
    for pred_type in ['低吸', '等待新低', '做空', '诱多', '观望']:
        conditions.append({
            'name': f'预测={pred_type}',
            'category': pred_type,
            'check': lambda p, pt=pred_type: p['category'] == pt
        })
    
    # 2. 正数占比区间
    for threshold in [(0, 40), (40, 60), (60, 80), (80, 100)]:
        conditions.append({
            'name': f'正数占比{threshold[0]}-{threshold[1]}%',
            'category': 'ratio_range',
            'check': lambda p, t=threshold: t[0] < p['up_ratio'] <= t[1]
        })
    
    # 3. 5分钟涨速区间
    for threshold in [(-100, -15), (-15, -5), (-5, 0), (0, 5), (5, 15), (15, 100)]:
        conditions.append({
            'name': f'5分钟涨速{threshold[0]}%~{threshold[1]}%',
            'category': 'speed_range',
            'check': lambda p, t=threshold: t[0] < p['speed_5min'] <= t[1]
        })
    
    # 4. 预测类型 + 正数占比
    for pred_type in ['低吸', '做空', '诱多']:
        for ratio_range in [(40, 60), (60, 80), (80, 100)]:
            conditions.append({
                'name': f'预测={pred_type}+正数占比{ratio_range[0]}-{ratio_range[1]}%',
                'category': 'combined',
                'check': lambda p, pt=pred_type, rr=ratio_range: p['category'] == pt and rr[0] < p['up_ratio'] <= rr[1]
            })
    
    # 5. 预测类型 + 5分钟涨速
    for pred_type in ['低吸', '做空', '诱多']:
        for speed_range in [(-15, -5), (-5, 0), (0, 5), (5, 15)]:
            conditions.append({
                'name': f'预测={pred_type}+5分钟涨速{speed_range[0]}%~{speed_range[1]}%',
                'category': 'combined',
                'check': lambda p, pt=pred_type, sr=speed_range: p['category'] == pt and sr[0] < p['speed_5min'] <= sr[1]
            })
    
    # 收集所有数据点
    all_data_points = []
    
    for date, pred in predictions.items():
        signal = pred['signal']
        category = classify_signal(signal)
        
        # 加载该日期的币种变化数据
        data_points = load_coin_change_data(date)
        
        if not data_points or len(data_points) < 50:
            continue
        
        # 遍历每个数据点
        for i in range(len(data_points) - 20):
            point = data_points[i]
            up_ratio = point.get('up_ratio', 0)
            speed_5min = calculate_5min_speed(data_points, i)
            change_2h = get_change_after_hours(data_points, i, hours=2)
            
            if speed_5min is None or change_2h is None or abs(change_2h) < 0.5:
                continue
            
            data_point = {
                'date': date,
                'signal': signal,
                'category': category,
                'time': point.get('beijing_time'),
                'up_ratio': up_ratio,
                'speed_5min': speed_5min,
                'change_2h': change_2h
            }
            
            all_data_points.append(data_point)
    
    print(f"✅ 收集了 {len(all_data_points)} 个有效数据点")
    
    # 分析每个条件
    results = []
    
    for condition in conditions:
        # 筛选符合条件的数据点
        matching_points = [p for p in all_data_points if condition['check'](p)]
        
        if len(matching_points) < 5:  # 样本数太少，跳过
            continue
        
        # 计算做多胜率（2小时后上涨）
        long_wins = len([p for p in matching_points if p['change_2h'] > 0])
        long_win_rate = (long_wins / len(matching_points)) * 100 if matching_points else 0
        long_avg_profit = sum(p['change_2h'] for p in matching_points if p['change_2h'] > 0) / long_wins if long_wins > 0 else 0
        long_avg_loss = abs(sum(p['change_2h'] for p in matching_points if p['change_2h'] < 0) / (len(matching_points) - long_wins)) if (len(matching_points) - long_wins) > 0 else 0
        
        # 计算做空胜率（2小时后下跌）
        short_wins = len([p for p in matching_points if p['change_2h'] < 0])
        short_win_rate = (short_wins / len(matching_points)) * 100 if matching_points else 0
        short_avg_profit = abs(sum(p['change_2h'] for p in matching_points if p['change_2h'] < 0) / short_wins) if short_wins > 0 else 0
        short_avg_loss = sum(p['change_2h'] for p in matching_points if p['change_2h'] > 0) / long_wins if long_wins > 0 else 0
        
        # 平均收益
        avg_change = sum(p['change_2h'] for p in matching_points) / len(matching_points)
        
        results.append({
            'condition': condition['name'],
            'category_type': condition['category'],
            'sample_count': len(matching_points),
            'avg_change': avg_change,
            'long_win_rate': long_win_rate,
            'long_avg_profit': long_avg_profit,
            'long_avg_loss': long_avg_loss,
            'short_win_rate': short_win_rate,
            'short_avg_profit': short_avg_profit,
            'short_avg_loss': short_avg_loss
        })
    
    return results

def generate_markdown_report(results):
    """生成Markdown报告"""
    if not results:
        return "# 暂无数据\n"
    
    md = "# 📊 最佳做多/做空条件分析报告\n\n"
    md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += "---\n\n"
    
    md += "## 📋 分析说明\n\n"
    md += "本报告分析各种市场条件下做多和做空的胜率，找出最佳交易条件：\n\n"
    md += "- **做多胜率**: 2小时后上涨的概率\n"
    md += "- **做空胜率**: 2小时后下跌的概率\n"
    md += "- **平均收益**: 2小时后的平均涨跌幅\n"
    md += "- **样本要求**: 至少5个数据点\n\n"
    md += "---\n\n"
    
    # 按做多胜率排序
    long_sorted = sorted(results, key=lambda x: x['long_win_rate'], reverse=True)
    
    md += "## 🟢 最佳做多条件（按胜率排序）\n\n"
    md += "| 排名 | 条件 | 样本数 | 做多胜率 | 平均盈利 | 平均亏损 | 平均收益 |\n"
    md += "|-----|------|--------|---------|---------|---------|----------|\n"
    
    for i, item in enumerate(long_sorted[:20], 1):
        md += f"| {i} | {item['condition']} | {item['sample_count']} | **{item['long_win_rate']:.1f}%** | {item['long_avg_profit']:.2f}% | {item['long_avg_loss']:.2f}% | {item['avg_change']:.2f}% |\n"
    
    md += "\n---\n\n"
    
    # 按做空胜率排序
    short_sorted = sorted(results, key=lambda x: x['short_win_rate'], reverse=True)
    
    md += "## 🔴 最佳做空条件（按胜率排序）\n\n"
    md += "| 排名 | 条件 | 样本数 | 做空胜率 | 平均盈利 | 平均亏损 | 平均收益 |\n"
    md += "|-----|------|--------|---------|---------|---------|----------|\n"
    
    for i, item in enumerate(short_sorted[:20], 1):
        md += f"| {i} | {item['condition']} | {item['sample_count']} | **{item['short_win_rate']:.1f}%** | {item['short_avg_profit']:.2f}% | {item['short_avg_loss']:.2f}% | {item['avg_change']:.2f}% |\n"
    
    md += "\n---\n\n"
    
    # 综合推荐
    md += "## ⭐ 综合推荐\n\n"
    
    md += "### 🟢 最佳做多策略（胜率>60% + 平均收益>5%）\n\n"
    best_long = [r for r in results if r['long_win_rate'] > 60 and r['avg_change'] > 5]
    best_long_sorted = sorted(best_long, key=lambda x: (x['long_win_rate'], x['avg_change']), reverse=True)
    
    if best_long_sorted:
        md += "| 条件 | 样本数 | 做多胜率 | 平均收益 | 推荐度 |\n"
        md += "|------|--------|---------|---------|-------|\n"
        for item in best_long_sorted[:10]:
            stars = "⭐" * min(5, int(item['long_win_rate'] / 15))
            md += f"| {item['condition']} | {item['sample_count']} | **{item['long_win_rate']:.1f}%** | **{item['avg_change']:.2f}%** | {stars} |\n"
    else:
        md += "*暂无符合条件的策略（胜率>60% + 平均收益>5%）*\n"
    
    md += "\n### 🔴 最佳做空策略（胜率>60% + 平均收益<-5%）\n\n"
    best_short = [r for r in results if r['short_win_rate'] > 60 and r['avg_change'] < -5]
    best_short_sorted = sorted(best_short, key=lambda x: (x['short_win_rate'], -x['avg_change']), reverse=True)
    
    if best_short_sorted:
        md += "| 条件 | 样本数 | 做空胜率 | 平均收益 | 推荐度 |\n"
        md += "|------|--------|---------|---------|-------|\n"
        for item in best_short_sorted[:10]:
            stars = "⭐" * min(5, int(item['short_win_rate'] / 15))
            md += f"| {item['condition']} | {item['sample_count']} | **{item['short_win_rate']:.1f}%** | **{item['avg_change']:.2f}%** | {stars} |\n"
    else:
        md += "*暂无符合条件的策略（胜率>60% + 平均收益<-5%）*\n"
    
    md += "\n---\n\n"
    md += "*注: 本报告基于历史数据分析，不保证未来收益。建议结合其他指标和风险管理。*\n"
    
    return md

def main():
    print("🚀 开始分析最佳做多/做空条件...")
    print()
    
    results = analyze_all_conditions()
    
    if not results:
        print("❌ 分析失败，没有有效数据")
        return
    
    print(f"✅ 分析完成！共分析了 {len(results)} 个条件组合")
    
    # 找出最佳做多条件
    best_long = max(results, key=lambda x: x['long_win_rate'])
    print(f"\n🟢 最佳做多条件:")
    print(f"   条件: {best_long['condition']}")
    print(f"   样本数: {best_long['sample_count']}")
    print(f"   做多胜率: {best_long['long_win_rate']:.1f}%")
    print(f"   平均收益: {best_long['avg_change']:.2f}%")
    
    # 找出最佳做空条件
    best_short = max(results, key=lambda x: x['short_win_rate'])
    print(f"\n🔴 最佳做空条件:")
    print(f"   条件: {best_short['condition']}")
    print(f"   样本数: {best_short['sample_count']}")
    print(f"   做空胜率: {best_short['short_win_rate']:.1f}%")
    print(f"   平均收益: {best_short['avg_change']:.2f}%")
    
    print()
    
    # 生成Markdown报告
    md_content = generate_markdown_report(results)
    
    # 保存报告
    output_file = 'BEST_TRADING_CONDITIONS_ANALYSIS.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"📄 报告已生成: {output_file}")
    print(f"   总行数: {len(md_content.splitlines())}")

if __name__ == '__main__':
    main()
