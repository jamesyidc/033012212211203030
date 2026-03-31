#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日预判生成器 - 在凌晨2点自动生成当天的涨跌预判
Daily Prediction Generator - Automatically generate predictions at 2 AM
"""

import json
import os
import time
import logging
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_prediction_generator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_beijing_time():
    """获取北京时间"""
    from datetime import timezone
    utc_now = datetime.now(timezone.utc)
    beijing_tz = timezone(timedelta(hours=8))
    return utc_now.astimezone(beijing_tz)

def generate_prediction_for_date(date_str):
    """为指定日期生成预判"""
    date_file = date_str.replace('-', '')
    data_file = f'data/coin_change_tracker/coin_change_{date_file}.jsonl'
    
    if not os.path.exists(data_file):
        logger.warning(f"数据文件不存在: {data_file}")
        return None
    
    try:
        # 读取0-2点数据
        records = []
        with open(data_file, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    time_str = record.get('beijing_time', '')
                    if not time_str:
                        continue
                    
                    dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    hour = dt.hour
                    
                    if 0 <= hour < 2:
                        changes = record.get('changes', {})
                        if changes:
                            total_coins = len(changes)
                            up_coins = sum(1 for coin_data in changes.values() 
                                         if coin_data.get('change_pct', 0) > 0)
                            up_ratio = (up_coins / total_coins * 100) if total_coins > 0 else 0
                            
                            records.append({
                                'time': time_str,
                                'up_ratio': up_ratio
                            })
                except json.JSONDecodeError:
                    continue
        
        if not records:
            logger.warning(f"没有找到0-2点的有效数据: {date_str}")
            return None
        
        logger.info(f"找到 {len(records)} 条0-2点数据记录")
        
        # 按10分钟分组
        interval = 10
        grouped = defaultdict(lambda: {'ratios': []})
        
        for record in records:
            time_str = record['time']
            up_ratio = record['up_ratio']
            
            dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            hour = dt.hour
            minute = dt.minute
            
            total_minutes = hour * 60 + minute
            group_index = total_minutes // interval
            
            grouped[group_index]['ratios'].append(up_ratio)
        
        # 判断颜色
        color_counts = {'green': 0, 'red': 0, 'yellow': 0, 'blank': 0}
        
        for group_idx in sorted(grouped.keys()):
            ratios = grouped[group_idx]['ratios']
            if not ratios:
                continue
            
            avg_up_ratio = sum(ratios) / len(ratios)
            
            if avg_up_ratio == 0:
                color_counts['blank'] += 1
            elif avg_up_ratio > 55:
                color_counts['green'] += 1
            elif avg_up_ratio >= 45:
                color_counts['yellow'] += 1
            else:
                color_counts['red'] += 1
        
        # 判断信号
        green = color_counts['green']
        red = color_counts['red']
        yellow = color_counts['yellow']
        blank = color_counts['blank']
        blank_ratio = (blank / (green + red + yellow + blank) * 100) if (green + red + yellow + blank) > 0 else 0
        
        color_counts['blank_ratio'] = blank_ratio
        
        # 情况6: 全部为空白（空头强控盘）
        if blank > 0 and green == 0 and red == 0 and yellow == 0:
            signal = "空头强控盘"
            description = "⚪⚪⚪ 0点-2点全部为空白，空头强控盘，建议观望。操作提示：不参与"
        # 情况4: 全部绿色（诱多）
        elif green > 0 and red == 0 and yellow == 0 and blank == 0:
            signal = "诱多不参与"
            description = "🟢 全部绿色柱子，单边诱多行情，不参与操作。操作提示：不参与"
        # 情况3: 只有红色或红色+空白（做空）
        elif red > 0 and green == 0 and yellow == 0:
            if blank == 0:
                signal = "做空"
                description = "🔴 只有红色柱子，预判下跌行情，建议做空。操作提示：相对高点做空"
            else:
                signal = "做空"
                description = f"🔴⚪ 红色+空白（空白占比{blank_ratio:.1f}%），预判下跌行情，建议做空。操作提示：相对高点做空"
        # 情况1: 有绿+有红+无黄 → 低吸（要求绿>=3根）
        elif green >= 3 and red > 0 and yellow == 0:
            signal = "低吸"
            description = f"🟢🔴 绿色{green}根+红色{red}根（绿色>=3根为主导，无黄色），红色区间为低吸机会。操作提示：低点做多"
        # 情况2优先: 有绿+有红+有黄，且黄柱子 >= 2根 → 等待新低
        elif green > 0 and red > 0 and yellow >= 2:
            signal = "等待新低"
            description = f"🟢🔴🟡 有绿有红有黄，黄色柱子{yellow}根(>=2根)，可能还有新低，建议等待。操作提示：高点做空"
        # 情况1扩展: 有绿+有红+有黄，但(红+黄) < 3根 OR 黄柱子只有1根 → 低吸
        elif green >= 3 and red > 0 and yellow > 0 and ((red + yellow) < 3 or yellow == 1):
            signal = "低吸"
            description = f"🟢🔴🟡 绿色{green}根+红色{red}根+黄色{yellow}根（绿色>=3根为主导，红+黄共{red+yellow}根），红色区间为低吸机会。操作提示：低点做多"
        # 情况7: 红色+黄色（无绿色）→ 观望
        elif red > 0 and yellow > 0 and green == 0:
            signal = "观望"
            description = "🔴🟡 红色柱子+黄色柱子，没有绿色柱子，多空博弈方向不明。操作提示：无，不参与"
        # 情况8: 只有绿色+黄色（无红色）→ 根据绿色数量判断
        elif green > 0 and yellow > 0 and red == 0:
            if green >= 3:
                signal = "低吸"
                description = f"🟢🟡 绿色{green}根+黄色{yellow}根（绿色>=3根为主导，无红色），黄色区间为低吸机会。操作提示：低点做多"
            else:
                signal = "观望"
                description = f"🟢🟡 绿色{green}根+黄色{yellow}根（绿色<3根，无红色），无法判断低吸或新低。操作提示：观望"
        # 其他情况
        else:
            signal = "观望"
            description = "⚪ 柱状图混合分布，建议观望"
        
        prediction = {
            'date': date_str,
            'timestamp': f'{date_str} 02:00:00',
            'analysis_time': '02:00:00',
            'color_counts': color_counts,
            'signal': signal,
            'description': description,
            'is_final': True,
            'is_temp': False
        }
        
        logger.info(f"生成预判: {date_str} - 绿{green} 红{red} 黄{yellow} 空{blank} - {signal}")
        return prediction
        
    except Exception as e:
        logger.error(f"生成预判失败 ({date_str}): {e}", exc_info=True)
        return None

def save_prediction(prediction):
    """保存预判到文件"""
    if not prediction:
        return False
    
    try:
        date_str = prediction['date']
        date_file = date_str.replace('-', '')
        
        # 创建目录
        pred_dir = 'data/daily_predictions'
        os.makedirs(pred_dir, exist_ok=True)
        
        # 使用JSONL格式（单行）
        pred_file = f'{pred_dir}/prediction_{date_file}.jsonl'
        
        with open(pred_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(prediction, ensure_ascii=False) + '\n')
        
        logger.info(f"✅ 预判文件已保存: {pred_file}")
        return True
        
    except Exception as e:
        logger.error(f"保存预判文件失败: {e}", exc_info=True)
        return False

def check_and_generate_prediction():
    """检查并生成当天的预判（在凌晨2点后运行）"""
    beijing_time = get_beijing_time()
    current_date = beijing_time.strftime('%Y-%m-%d')
    current_hour = beijing_time.hour
    
    logger.info(f"当前北京时间: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 只在凌晨2点到3点之间生成预判
    if current_hour < 2 or current_hour >= 3:
        logger.info(f"当前时间 {current_hour}:xx 不在生成时间窗口（02:00-03:00），跳过")
        return False
    
    # 检查今天的预判是否已存在
    date_file = current_date.replace('-', '')
    pred_file = f'data/daily_predictions/prediction_{date_file}.jsonl'
    
    if os.path.exists(pred_file):
        logger.info(f"今日预判已存在: {pred_file}，跳过生成")
        return False
    
    # 等待一段时间确保有足够的0-2点数据
    logger.info("开始生成今日预判...")
    
    # 生成预判
    prediction = generate_prediction_for_date(current_date)
    
    if prediction:
        if save_prediction(prediction):
            logger.info(f"🎉 成功生成今日预判: {current_date} - {prediction['signal']}")
            return True
        else:
            logger.error(f"保存预判失败: {current_date}")
            return False
    else:
        logger.warning(f"无法生成预判: {current_date}（可能数据不足）")
        return False

def main():
    """主循环"""
    logger.info("="*80)
    logger.info("📊 每日预判生成器启动")
    logger.info("="*80)
    
    check_count = 0
    
    while True:
        try:
            check_count += 1
            logger.info(f"🔄 第 {check_count} 次检查开始...")
            
            check_and_generate_prediction()
            
            logger.info(f"✅ 第 {check_count} 次检查完成，等待下次检查...")
            
            # 每5分钟检查一次
            time.sleep(300)
            
        except KeyboardInterrupt:
            logger.info("接收到退出信号，正在关闭...")
            break
        except Exception as e:
            logger.error(f"运行出错: {e}", exc_info=True)
            time.sleep(60)

if __name__ == "__main__":
    main()
