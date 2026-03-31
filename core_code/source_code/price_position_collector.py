#!/usr/bin/env python3
"""
Price Position Data Collector
价格位置数据采集器

功能：
1. 从OKX获取27种币的实时价格
2. 计算48小时和7天的高低点
3. 计算价格位置（在高低区间的百分比）
4. 检测支撑位和压力位突破信号
5. 写入JSONL文件（按日期保存）

采集间隔：3分钟
数据存储：data/price_position/price_position_YYYYMMDD.jsonl
"""

import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

import ccxt

# 配置
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data' / 'price_position'
COLLECT_INTERVAL = 180  # 3分钟

# 确保数据目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 27种监控币种
SYMBOLS = [
    'BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'SOL-USDT-SWAP', 'BNB-USDT-SWAP',
    'XRP-USDT-SWAP', 'ADA-USDT-SWAP', 'DOGE-USDT-SWAP', 'TRX-USDT-SWAP',
    'DOT-USDT-SWAP', 'LTC-USDT-SWAP', 'BCH-USDT-SWAP', 'LINK-USDT-SWAP',
    'UNI-USDT-SWAP', 'FIL-USDT-SWAP', 'ETC-USDT-SWAP', 'AAVE-USDT-SWAP',
    'CRV-USDT-SWAP', 'NEAR-USDT-SWAP', 'APT-USDT-SWAP', 'STX-USDT-SWAP',
    'LDO-USDT-SWAP', 'OKB-USDT-SWAP', 'CRO-USDT-SWAP', 'HBAR-USDT-SWAP',
    'TON-USDT-SWAP', 'TAO-USDT-SWAP', 'SUI-USDT-SWAP', 'XLM-USDT-SWAP'
]

def get_okx_exchange():
    """创建OKX交易所实例"""
    return ccxt.okx({
        'enableRateLimit': True,
        'timeout': 30000,
    })

def get_historical_klines(exchange, symbol, timeframe, limit):
    """获取历史K线数据"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        return ohlcv
    except Exception as e:
        print(f"获取 {symbol} K线失败: {e}")
        return []

def calculate_high_low(klines):
    """计算K线的最高价和最低价"""
    if not klines:
        return None, None
    
    highs = [k[2] for k in klines]  # high
    lows = [k[3] for k in klines]   # low
    
    return max(highs), min(lows)

def calculate_position(current_price, high, low):
    """计算价格位置（百分比）"""
    if high == low:
        return 50.0
    
    position = ((current_price - low) / (high - low)) * 100
    return round(position, 2)

def check_alert(position):
    """检查是否触发预警
    
    低位预警：position ≤ 5%（接近最低点，支撑位）
    高位预警：position ≥ 95%（接近最高点，压力位）
    """
    alert_low = 1 if position <= 5 else 0
    alert_high = 1 if position >= 95 else 0
    return alert_low, alert_high

def collect_price_positions():
    """采集所有币种的价格位置数据"""
    print(f"\n{'='*60}")
    print(f"开始采集价格位置数据 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    exchange = get_okx_exchange()
    
    # 使用北京时间
    beijing_tz = pytz.timezone('Asia/Shanghai')
    snapshot_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    positions_data = []
    support_48h_list = []
    pressure_48h_list = []
    support_7d_list = []
    pressure_7d_list = []
    
    for symbol in SYMBOLS:
        try:
            # 获取当前价格
            ticker = exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # 获取48小时K线（5分钟级别，48h = 576根K线）
            klines_48h = get_historical_klines(exchange, symbol, '5m', 576)
            high_48h, low_48h = calculate_high_low(klines_48h)
            
            # 获取7天K线（1小时级别，7d = 168根K线）
            klines_7d = get_historical_klines(exchange, symbol, '1h', 168)
            high_7d, low_7d = calculate_high_low(klines_7d)
            
            if high_48h and low_48h and high_7d and low_7d:
                # 计算价格位置
                position_48h = calculate_position(current_price, high_48h, low_48h)
                position_7d = calculate_position(current_price, high_7d, low_7d)
                
                # 检查预警
                alert_48h_low, alert_48h_high = check_alert(position_48h)
                alert_7d_low, alert_7d_high = check_alert(position_7d)
                
                # 收集数据
                positions_data.append({
                    'inst_id': symbol,
                    'snapshot_time': snapshot_time,
                    'current_price': current_price,
                    'high_48h': high_48h,
                    'low_48h': low_48h,
                    'position_48h': position_48h,
                    'high_7d': high_7d,
                    'low_7d': low_7d,
                    'position_7d': position_7d,
                    'alert_48h_low': alert_48h_low,
                    'alert_48h_high': alert_48h_high,
                    'alert_7d_low': alert_7d_low,
                    'alert_7d_high': alert_7d_high,
                })
                
                # 收集支撑压力线数据
                support_48h_list.append(low_48h)
                pressure_48h_list.append(high_48h)
                support_7d_list.append(low_7d)
                pressure_7d_list.append(high_7d)
                
                symbol_name = symbol.replace('-USDT-SWAP', '')
                print(f"✓ {symbol_name:6s} | 价格: ${current_price:10.4f} | "
                      f"48h位置: {position_48h:5.1f}% | 7d位置: {position_7d:5.1f}% | "
                      f"预警: {'🔴低' if alert_48h_low else '  '} {'🔴高' if alert_48h_high else '  '}")
            
            time.sleep(0.1)  # 避免频率限制
            
        except Exception as e:
            print(f"✗ {symbol} 采集失败: {e}")
    
    print(f"\n采集完成: {len(positions_data)}/{len(SYMBOLS)} 个币种")
    
    # 写入数据库
    if positions_data:
        save_to_jsonl(positions_data, snapshot_time, 
                      support_48h_list, pressure_48h_list,
                      support_7d_list, pressure_7d_list)

def save_to_jsonl(positions_data, snapshot_time, 
                  support_48h_list, pressure_48h_list,
                  support_7d_list, pressure_7d_list):
    """保存数据到JSONL文件（按日期保存）"""
    try:
        # 使用北京时间获取日期
        beijing_tz = pytz.timezone('Asia/Shanghai')
        today = datetime.now(beijing_tz).strftime('%Y%m%d')
        
        # JSONL文件路径
        jsonl_file = DATA_DIR / f'price_position_{today}.jsonl'
        
        # 统计4个预警指标的币种数量
        support_line1_count = len([d for d in positions_data if d['alert_48h_low']])  # 48h低位预警（≤5%）
        support_line2_count = len([d for d in positions_data if d['alert_7d_low']])   # 7d低位预警（≤5%）
        pressure_line1_count = len([d for d in positions_data if d['alert_48h_high']]) # 48h高位预警（≥95%）
        pressure_line2_count = len([d for d in positions_data if d['alert_7d_high']])  # 7d高位预警（≥95%）
        
        # 判断信号类型
        signal_type = ''
        signal_triggered = 0
        trigger_reason = ''
        
        # 抄底信号：支撑线1+支撑线2 ≥ 20 且两者都≥1
        if (support_line1_count + support_line2_count >= 20 and 
            support_line1_count >= 1 and support_line2_count >= 1):
            signal_type = '抄底信号'
            signal_triggered = 1
            trigger_reason = f"支撑线1({support_line1_count}个) + 支撑线2({support_line2_count}个) ≥ 20"
        
        # 逃顶信号：压力线1+压力线2 ≥ 8 且两者都≥1
        elif (pressure_line1_count + pressure_line2_count >= 8 and 
              pressure_line1_count >= 1 and pressure_line2_count >= 1):
            signal_type = '逃顶信号'
            signal_triggered = 1
            trigger_reason = f"压力线1({pressure_line1_count}个) + 压力线2({pressure_line2_count}个) ≥ 8"
        
        # 构建要保存的数据
        data_entry = {
            'snapshot_time': snapshot_time,
            'positions': positions_data,
            'summary': {
                'total_coins': len(positions_data),
                'support_line1_count': support_line1_count,  # 48h低位
                'support_line2_count': support_line2_count,  # 7d低位
                'pressure_line1_count': pressure_line1_count, # 48h高位
                'pressure_line2_count': pressure_line2_count, # 7d高位
                'signal_type': signal_type,
                'signal_triggered': signal_triggered,
                'trigger_reason': trigger_reason
            }
        }
        
        # 追加写入JSONL文件
        with open(jsonl_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data_entry, ensure_ascii=False) + '\n')
        
        print(f"✓ 保存 {len(positions_data)} 条价格位置数据")
        print(f"✓ 保存信号时间轴数据 | 信号: {signal_type or '无'}")
        print(f"✓ 数据保存成功 -> {jsonl_file}")
        
    except Exception as e:
        print(f"✗ 数据保存失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("Price Position Collector 启动")
    print(f"数据目录: {DATA_DIR}")
    print(f"监控币种: {len(SYMBOLS)} 个")
    print(f"采集间隔: {COLLECT_INTERVAL} 秒")
    
    # 确保数据目录存在
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    while True:
        try:
            collect_price_positions()
            print(f"\n下次采集时间: {(datetime.now() + timedelta(seconds=COLLECT_INTERVAL)).strftime('%H:%M:%S')}")
            print("等待中...")
            time.sleep(COLLECT_INTERVAL)
        except KeyboardInterrupt:
            print("\n收到停止信号，退出...")
            break
        except Exception as e:
            print(f"采集出错: {e}")
            import traceback
            traceback.print_exc()
            print(f"等待 {COLLECT_INTERVAL} 秒后重试...")
            time.sleep(COLLECT_INTERVAL)

if __name__ == '__main__':
    main()
