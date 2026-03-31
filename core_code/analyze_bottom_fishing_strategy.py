#!/usr/bin/env python3
"""
分析正数占比>60%且最低涨速<-15%时的抄底做多策略
买入点：最低涨速<-15%时
卖出点：下一次最高涨速时
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

def find_trading_opportunities(data_points, up_ratio_threshold=60, speed_threshold=-15):
    """
    找出正数占比>60%且5分钟涨速<-15%的交易机会
    买入点：出现最低涨速<-15%时
    卖出点：下一次出现最高涨速时
    """
    trades = []
    
    for i in range(len(data_points) - 20):  # 保留后面至少20个数据点
        point = data_points[i]
        up_ratio = point.get('up_ratio', 0)
        
        # 检查正数占比是否>60%
        if up_ratio > up_ratio_threshold:
            # 计算5分钟涨速
            speed_5min = calculate_5min_speed(data_points, i)
            
            if speed_5min is not None and speed_5min < speed_threshold:
                # 找到买入点，现在寻找卖出点（下一次最高涨速）
                buy_time = point.get('beijing_time')
                buy_price = point.get('cumulative_pct', 0)
                buy_speed = speed_5min
                buy_ratio = up_ratio
                
                # 从买入点之后查找最高涨速作为卖出点
                max_speed = None
                max_speed_index = None
                
                # 扫描后续数据点，找到最高涨速
                for j in range(i + 1, min(i + 200, len(data_points))):  # 最多扫描200个点（约200分钟）
                    next_speed = calculate_5min_speed(data_points, j)
                    
                    if next_speed is not None:
                        if max_speed is None or next_speed > max_speed:
                            max_speed = next_speed
                            max_speed_index = j
                
                if max_speed_index is not None and max_speed > 0:  # 只有当最高涨速为正时才卖出
                    sell_point = data_points[max_speed_index]
                    sell_time = sell_point.get('beijing_time')
                    sell_price = sell_point.get('cumulative_pct', 0)
                    sell_speed = max_speed
                    sell_ratio = sell_point.get('up_ratio', 0)
                    
                    # 计算收益（卖出价 - 买入价）
                    profit = sell_price - buy_price
                    
                    # 计算持仓时长
                    try:
                        buy_dt = datetime.strptime(buy_time, '%Y-%m-%d %H:%M:%S')
                        sell_dt = datetime.strptime(sell_time, '%Y-%m-%d %H:%M:%S')
                        hold_duration = (sell_dt - buy_dt).total_seconds() / 60  # 转换为分钟
                    except:
                        hold_duration = 0
                    
                    trades.append({
                        'buy_time': buy_time,
                        'buy_price': buy_price,
                        'buy_speed': buy_speed,
                        'buy_ratio': buy_ratio,
                        'sell_time': sell_time,
                        'sell_price': sell_price,
                        'sell_speed': sell_speed,
                        'sell_ratio': sell_ratio,
                        'profit': profit,
                        'hold_duration': hold_duration
                    })
    
    return trades

def analyze_trading_strategy():
    """分析抄底做多策略"""
    predictions = load_daily_predictions()
    
    if not predictions:
        print("❌ 没有找到预测数据")
        return None
    
    print(f"✅ 加载了 {len(predictions)} 个预测数据")
    
    # 按预测类型分类结果
    results = defaultdict(list)
    all_trades = []
    
    for date, pred in predictions.items():
        signal = pred['signal']
        category = classify_signal(signal)
        
        # 加载该日期的币种变化数据
        data_points = load_coin_change_data(date)
        
        if not data_points or len(data_points) < 50:
            continue
        
        # 找出交易机会
        trades = find_trading_opportunities(data_points)
        
        for trade in trades:
            trade_data = {
                'date': date,
                'signal': signal,
                'category': category,
                **trade
            }
            results[category].append(trade_data)
            all_trades.append(trade_data)
    
    return {
        'by_category': results,
        'all_trades': all_trades
    }

def generate_markdown_report(results):
    """生成Markdown报告"""
    if not results or not results['all_trades']:
        return "# 暂无符合条件的交易数据\n\n未找到正数占比>60%且5分钟涨速<-15%的交易机会。\n"
    
    md = "# 📊 抄底做多策略回测报告\n\n"
    md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += "---\n\n"
    
    md += "## 📋 策略说明\n\n"
    md += "本报告回测以下抄底做多策略：\n\n"
    md += "- **交易条件**: 正数占比 >60% + 5分钟涨速 <-15%\n"
    md += "- **买入点**: 出现最低涨速<-15%时立即买入\n"
    md += "- **卖出点**: 下一次出现最高涨速时平仓\n"
    md += "- **收益计算**: 卖出价 - 买入价（基于累计涨跌幅）\n\n"
    md += "---\n\n"
    
    all_trades = results['all_trades']
    by_category = results['by_category']
    
    # 过滤有效交易（收益不为0）
    valid_trades = [t for t in all_trades if abs(t['profit']) >= 0.5]
    
    # 统计概览
    md += "## 📈 策略表现概览\n\n"
    md += f"- **总交易次数**: {len(all_trades)}次\n"
    md += f"- **有效交易（|收益| ≥ 0.5%）**: {len(valid_trades)}次\n"
    
    if valid_trades:
        avg_profit = sum(t['profit'] for t in valid_trades) / len(valid_trades)
        profitable_trades = [t for t in valid_trades if t['profit'] > 0]
        losing_trades = [t for t in valid_trades if t['profit'] < 0]
        
        md += f"- **平均收益**: {avg_profit:.2f}%\n"
        md += f"- **盈利次数**: {len(profitable_trades)}次（{(len(profitable_trades)/len(valid_trades)*100):.1f}%）\n"
        md += f"- **亏损次数**: {len(losing_trades)}次（{(len(losing_trades)/len(valid_trades)*100):.1f}%）\n"
        
        if profitable_trades:
            max_profit = max(t['profit'] for t in valid_trades)
            max_loss = min(t['profit'] for t in valid_trades)
            avg_hold = sum(t['hold_duration'] for t in valid_trades) / len(valid_trades)
            
            md += f"- **最大盈利**: {max_profit:.2f}%\n"
            md += f"- **最大亏损**: {max_loss:.2f}%\n"
            md += f"- **平均持仓时长**: {avg_hold:.1f}分钟（{avg_hold/60:.2f}小时）\n"
            
            # 胜率和盈亏比
            win_rate = len(profitable_trades) / len(valid_trades) * 100
            avg_win = sum(t['profit'] for t in profitable_trades) / len(profitable_trades) if profitable_trades else 0
            avg_loss = abs(sum(t['profit'] for t in losing_trades) / len(losing_trades)) if losing_trades else 0
            profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
            
            md += f"- **胜率**: {win_rate:.1f}%\n"
            md += f"- **平均盈利**: {avg_win:.2f}%\n"
            md += f"- **平均亏损**: {avg_loss:.2f}%\n"
            md += f"- **盈亏比**: {profit_loss_ratio:.2f}\n"
            
            # 策略评价
            if avg_profit > 5 and win_rate > 60:
                strategy_eval = "✅ 优秀策略"
            elif avg_profit > 2 and win_rate > 50:
                strategy_eval = "⭐ 良好策略"
            elif avg_profit > 0:
                strategy_eval = "⚡ 可行策略"
            else:
                strategy_eval = "⚠️ 亏损策略"
            
            md += f"- **策略评价**: {strategy_eval}\n"
    
    md += "\n---\n\n"
    
    # 按预测类型统计
    md += "## 📊 按预测类型统计\n\n"
    md += "| 预测类型 | 交易次数 | 有效交易 | 平均收益 | 胜率 | 盈亏比 | 平均持仓 |\n"
    md += "|---------|---------|---------|---------|------|-------|----------|\n"
    
    for category in ['低吸', '等待新低', '做空', '诱多', '空头强控盘', '观望']:
        if category in by_category:
            cat_trades = by_category[category]
            cat_valid = [t for t in cat_trades if abs(t['profit']) >= 0.5]
            
            if cat_valid:
                avg_profit = sum(t['profit'] for t in cat_valid) / len(cat_valid)
                profitable = [t for t in cat_valid if t['profit'] > 0]
                losing = [t for t in cat_valid if t['profit'] < 0]
                win_rate = len(profitable) / len(cat_valid) * 100 if cat_valid else 0
                
                avg_win = sum(t['profit'] for t in profitable) / len(profitable) if profitable else 0
                avg_loss = abs(sum(t['profit'] for t in losing) / len(losing)) if losing else 0
                pl_ratio = avg_win / avg_loss if avg_loss > 0 else 0
                
                avg_hold = sum(t['hold_duration'] for t in cat_valid) / len(cat_valid)
                
                md += f"| {category} | {len(cat_trades)} | {len(cat_valid)} | {avg_profit:.2f}% | {win_rate:.1f}% | {pl_ratio:.2f} | {avg_hold:.0f}分钟 |\n"
    
    md += "\n---\n\n"
    
    # 详细交易记录（只显示有效交易）
    md += "## 🔍 详细交易记录（有效交易，|收益| ≥ 0.5%）\n\n"
    
    for category in ['低吸', '等待新低', '做空', '诱多', '空头强控盘', '观望']:
        if category not in by_category:
            continue
        
        cat_valid = [t for t in by_category[category] if abs(t['profit']) >= 0.5]
        
        if not cat_valid:
            continue
        
        md += f"### {category}\n\n"
        md += "| 日期 | 预测 | 买入时间 | 买入涨速 | 卖出时间 | 卖出涨速 | 持仓时长 | 收益 |\n"
        md += "|------|-----|---------|---------|---------|---------|---------|------|\n"
        
        for trade in cat_valid:
            date = trade['date']
            signal = trade['signal']
            buy_time = trade['buy_time'].split(' ')[1]
            buy_speed = f"{trade['buy_speed']:.2f}%"
            sell_time = trade['sell_time'].split(' ')[1]
            sell_speed = f"{trade['sell_speed']:.2f}%"
            hold_duration = f"{trade['hold_duration']:.0f}分钟"
            profit = f"{trade['profit']:.2f}%"
            
            # 收益颜色标记
            if trade['profit'] > 5:
                profit = f"**{profit}** 🟢"
            elif trade['profit'] > 0:
                profit = f"{profit} 🟢"
            elif trade['profit'] < -5:
                profit = f"**{profit}** 🔴"
            else:
                profit = f"{profit} 🔴"
            
            md += f"| {date} | {signal} | {buy_time} | {buy_speed} | {sell_time} | {sell_speed} | {hold_duration} | {profit} |\n"
        
        md += "\n"
    
    md += "---\n\n"
    
    # 分析总结
    md += "## 💡 策略分析总结\n\n"
    
    if valid_trades:
        avg_profit = sum(t['profit'] for t in valid_trades) / len(valid_trades)
        win_rate = len([t for t in valid_trades if t['profit'] > 0]) / len(valid_trades) * 100
        
        md += f"### 整体表现\n\n"
        md += f"- **有效交易数量**: {len(valid_trades)}次\n"
        md += f"- **平均收益**: {avg_profit:.2f}%\n"
        md += f"- **胜率**: {win_rate:.1f}%\n\n"
        
        if avg_profit > 0 and win_rate > 50:
            md += "**结论**: 该策略在正数占比>60%且出现急速下跌时抄底做多，等待反弹至最高涨速时平仓，总体表现为**盈利策略**。\n\n"
        else:
            md += "**结论**: 该策略在正数占比>60%且出现急速下跌时抄底做多，总体表现为**亏损策略**，不建议使用。\n\n"
        
        md += "### 各预测类型表现\n\n"
        
        for category in ['低吸', '等待新低', '做空', '诱多', '空头强控盘', '观望']:
            if category in by_category:
                cat_valid = [t for t in by_category[category] if abs(t['profit']) >= 0.5]
                
                if cat_valid:
                    avg_profit = sum(t['profit'] for t in cat_valid) / len(cat_valid)
                    win_rate = len([t for t in cat_valid if t['profit'] > 0]) / len(cat_valid) * 100
                    
                    md += f"#### {category}\n\n"
                    md += f"- 交易次数: {len(cat_valid)}次\n"
                    md += f"- 平均收益: {avg_profit:.2f}%\n"
                    md += f"- 胜率: {win_rate:.1f}%\n"
                    
                    if avg_profit > 5 and win_rate > 60:
                        md += f"- **推荐操作**: ✅ 强烈推荐该策略\n\n"
                    elif avg_profit > 2 and win_rate > 50:
                        md += f"- **推荐操作**: ⭐ 推荐该策略\n\n"
                    elif avg_profit > 0:
                        md += f"- **推荐操作**: ⚡ 可以尝试该策略\n\n"
                    else:
                        md += f"- **推荐操作**: ⚠️ 不推荐该策略\n\n"
    
    md += "---\n\n"
    md += "*注: 本策略在正数占比>60%且5分钟涨速<-15%时买入，等待下一次最高涨速时卖出。回测数据基于历史表现，不保证未来收益。*\n"
    
    return md

def main():
    print("🚀 开始分析抄底做多策略（正数占比>60% + 涨速<-15%）...")
    print()
    
    results = analyze_trading_strategy()
    
    if not results:
        print("❌ 分析失败，没有有效数据")
        return
    
    all_trades = results['all_trades']
    valid_trades = [t for t in all_trades if abs(t['profit']) >= 0.5]
    
    print(f"✅ 分析完成！")
    print(f"   总交易次数: {len(all_trades)} 次")
    print(f"   有效交易: {len(valid_trades)} 次")
    
    if valid_trades:
        avg_profit = sum(t['profit'] for t in valid_trades) / len(valid_trades)
        profitable_count = len([t for t in valid_trades if t['profit'] > 0])
        win_rate = (profitable_count / len(valid_trades)) * 100
        
        print(f"   平均收益: {avg_profit:.2f}%")
        print(f"   胜率: {win_rate:.1f}% ({profitable_count}/{len(valid_trades)})")
    
    print()
    
    # 生成Markdown报告
    md_content = generate_markdown_report(results)
    
    # 保存报告
    output_file = 'BOTTOM_FISHING_STRATEGY_ANALYSIS.md'
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
