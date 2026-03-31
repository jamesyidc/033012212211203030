#!/usr/bin/env python3
"""
手动生成今天的预判数据
使用后端API的逻辑
"""
import json
import requests
from datetime import datetime
from pathlib import Path
import os

def send_telegram_message(message):
    """发送Telegram消息"""
    try:
        # 读取Telegram配置
        config_path = Path('/home/user/webapp/config/configs/telegram_config.json')
        if not config_path.exists():
            print(f"⚠️ Telegram配置文件不存在: {config_path}")
            return False
        
        with open(config_path, 'r', encoding='utf-8') as f:
            tg_config = json.load(f)
        
        bot_token = tg_config.get('bot_token')
        chat_id = tg_config.get('chat_id')
        
        if not bot_token or not chat_id:
            print("⚠️ Telegram配置不完整")
            return False
        
        # 发送消息
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Telegram消息发送成功")
            return True
        else:
            print(f"❌ Telegram消息发送失败: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"❌ 发送Telegram消息异常: {e}")
        return False

def generate_prediction_for_today():
    """生成今天的预判数据"""
    # 自动获取今天的日期（北京时间）
    from datetime import datetime, timedelta
    beijing_time = datetime.utcnow() + timedelta(hours=8)
    date = beijing_time.strftime('%Y-%m-%d')
    
    # 1. 获取0-2点的历史数据
    print(f"📊 正在获取 {date} 的0-2点数据...")
    url = f"http://localhost:9002/api/coin-change-tracker/history?date={date}&lite=true"
    response = requests.get(url, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ API请求失败: {response.status_code}")
        return False
    
    result = response.json()
    all_records = result.get('data', [])
    
    # 2. 筛选0-2点的数据
    morning_records = []
    for record in all_records:
        time_str = record.get('beijing_time', '')
        if not time_str:
            continue
        
        try:
            dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            hour = dt.hour
            
            if 0 <= hour < 2:
                morning_records.append({
                    'time': time_str,
                    'up_ratio': record.get('up_ratio', 0)
                })
        except Exception as e:
            continue
    
    print(f"✅ 找到 {len(morning_records)} 条0-2点数据")
    
    if len(morning_records) == 0:
        print("❌ 没有0-2点的数据")
        return False
    
    # 3. 分析10分钟柱状图颜色
    grouped = {}
    for record in morning_records:
        time_str = record['time']
        try:
            dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            total_minutes = dt.hour * 60 + dt.minute
            group_index = total_minutes // 10
            
            if group_index not in grouped:
                grouped[group_index] = []
            
            grouped[group_index].append(record['up_ratio'])
        except Exception as e:
            continue
    
    # 4. 计算每个10分钟区间的颜色
    color_counts = {'green': 0, 'red': 0, 'yellow': 0, 'blank': 0}
    
    for group_idx in range(12):  # 0-2点有12个10分钟区间
        if group_idx not in grouped or len(grouped[group_idx]) == 0:
            continue
        
        ratios = grouped[group_idx]
        avg_ratio = sum(ratios) / len(ratios)
        
        # 判断颜色
        if avg_ratio == 0:
            color = 'blank'
        elif avg_ratio >= 55:
            color = 'green'
        elif avg_ratio > 45:
            color = 'yellow'
        else:
            color = 'red'
        
        color_counts[color] += 1
    
    print(f"🎨 柱状图颜色统计: {color_counts}")
    
    # 5. 判断信号（使用后端逻辑）
    green = color_counts['green']
    red = color_counts['red']
    yellow = color_counts['yellow']
    blank = color_counts['blank']
    
    # 使用后端的 determine_market_signal_v2 逻辑
    if blank > 0 and green == 0 and red == 0 and yellow == 0:
        signal = "空头强控盘"
        description = "⚪⚪⚪ 0点-2点全部为空白，空头强控盘，建议观望。操作提示：不参与"
    elif green > 0 and red == 0 and yellow == 0 and blank == 0:
        signal = "诱多不参与"
        description = "🟢 全部绿色柱子，单边诱多行情，不参与操作。操作提示：不参与"
    elif red > 0 and green == 0 and yellow == 0:
        signal = "做空"
        description = f"🔴 只有红色柱子，预判下跌行情，建议做空。操作提示：相对高点做空"
    elif green > 0 and red > 0 and yellow == 0:
        signal = "低吸"
        description = "🟢🔴 有绿有红无黄，红色区间为低吸机会。操作提示：低点做多"
    elif green > 0 and red > 0 and yellow >= 2:
        signal = "等待新低"
        description = f"🟢🔴🟡 有绿有红有黄（黄色{yellow}根>=2根），可能还有新低，建议等待。操作提示：高点做空"
    elif green > 0 and red > 0 and yellow > 0:
        if (red + yellow) < 3 or yellow == 1:
            signal = "低吸"
            description = f"🟢🔴🟡 有绿有红有黄（红{red}+黄{yellow}共{red+yellow}根），红色区间为低吸机会。操作提示：低点做多"
        else:
            signal = "观望"
            description = "柱状图混合分布，建议观望"
    elif green >= 3 and (red > 0 or blank > 0):
        signal = "低吸"
        description = f"🟢🔴⚪ 绿色{green}根+红色{red}根+空白{blank}根，绿色柱子>=3根为主导，红色区间为低吸机会。操作提示：低点做多"
    elif red > 0 and yellow > 0 and green == 0:
        signal = "观望"
        description = "🔴🟡 红色柱子+黄色柱子，没有绿色柱子，多空博弈方向不明。操作提示：无，不参与"
    elif green > 0 and yellow > 0 and red == 0:
        if green >= 3:
            signal = "低吸"
            description = f"🟢🟡 绿色{green}根+黄色{yellow}根，绿色柱子>=3根为主导，黄色区间为低吸机会。操作提示：低点做多"
        else:
            signal = "观望"
            description = f"🟢🟡 只有绿色{green}根和黄色{yellow}根，绿色不足3根，无法判断低吸或新低。操作提示：观望"
    else:
        signal = "观望"
        description = "⚪ 柱状图混合分布，建议观望"
    
    print(f"\n🔮 预判信号: {signal}")
    print(f"💬 描述: {description}")
    
    # 6. 保存到文件
    output_dir = Path('data/daily_predictions')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    date_short = date.replace('-', '')  # 20260310
    output_file = output_dir / f'prediction_{date_short}.jsonl'
    
    prediction_data = {
        'date': date,
        'signal': signal,
        'description': description,
        'color_counts': color_counts,
        'green': green,
        'red': red,
        'yellow': yellow,
        'blank': blank,
        'is_final': True,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'analysis_time': '02:00:00'  # 标记为2点分析
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(prediction_data, f, ensure_ascii=False)
        f.write('\n')
    
    print(f"\n✅ 预判数据已保存到: {output_file}")
    
    # 📱 发送3次Telegram通知
    print("\n📱 正在发送Telegram通知...")
    
    # 构建通知消息
    message = f"""<b>🔮 币圈行情预判 ({date})</b>

📊 <b>柱状图统计 (0-2点)</b>
🟢 绿色: {green}根
🔴 红色: {red}根
🟡 黄色: {yellow}根
⚪ 空白: {blank}根

🎯 <b>预判信号: {signal}</b>

💬 <b>操作建议:</b>
{description}

⏰ 分析时间: {prediction_data['timestamp']}
"""
    
    # 发送3次消息
    success_count = 0
    for i in range(3):
        print(f"\n📤 发送第 {i+1} 次消息...")
        if send_telegram_message(message):
            success_count += 1
        else:
            print(f"⚠️ 第 {i+1} 次消息发送失败")
        
        # 避免发送太快，间隔1秒
        if i < 2:
            import time
            time.sleep(1)
    
    print(f"\n✅ Telegram通知完成: {success_count}/3 条消息发送成功")
    
    return True

if __name__ == '__main__':
    success = generate_prediction_for_today()
    exit(0 if success else 1)
