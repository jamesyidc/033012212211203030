#!/usr/bin/env python3
"""
SAR JSONL Collector - SAR指标数据采集器
实时采集SAR指标数据并写入JSONL
"""
import sys
sys.path.insert(0, '/home/user/webapp/source_code')

import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
import pytz
import numpy as np

# 配置
DATA_DIR = Path('/home/user/webapp/data/sar_jsonl')
DATA_DIR.mkdir(parents=True, exist_ok=True)

BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 交易对列表 (29个币种)
# 注: 已移除MATIC（更名为POL，交易所不支持），添加OKB
SYMBOLS = [
    'AAVE', 'APT', 'BCH', 'BNB', 'BTC', 'CFX', 'CRO', 'CRV', 
    'DOGE', 'DOT', 'ETC', 'ETH', 'FIL', 'HBAR', 'LDO', 'LINK', 
    'LTC', 'NEAR', 'OKB', 'SOL', 'STX', 'SUI', 'TAO', 'TON', 
    'TRX', 'UNI', 'XLM', 'XRP', 'ADA'
]

# SAR参数
SAR_AF_START = 0.02  # 加速因子起始值
SAR_AF_INCREMENT = 0.02  # 加速因子增量
SAR_AF_MAX = 0.2  # 加速因子最大值


def calculate_sar(high, low, close, af_start=0.02, af_increment=0.02, af_max=0.2):
    """
    计算抛物线转向指标 (SAR)
    
    Args:
        high: 最高价数组
        low: 最低价数组
        close: 收盘价数组
        af_start: 加速因子起始值
        af_increment: 加速因子增量
        af_max: 加速因子最大值
    
    Returns:
        tuple: (sar值数组, 趋势数组, ep数组, af数组)
    """
    length = len(high)
    sar = np.zeros(length)
    trend = np.zeros(length)  # 1 = bullish, -1 = bearish
    ep = np.zeros(length)  # extreme point
    af = np.zeros(length)  # acceleration factor
    
    # 初始化
    sar[0] = low[0]
    trend[0] = 1  # 假设初始为上升趋势
    ep[0] = high[0]
    af[0] = af_start
    
    for i in range(1, length):
        # 计算当前SAR
        sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
        
        # 判断趋势是否反转
        if trend[i-1] == 1:  # 上升趋势
            # 检查是否需要反转
            if low[i] < sar[i]:
                # 反转为下降趋势
                trend[i] = -1
                sar[i] = ep[i-1]  # SAR设为前期最高点
                ep[i] = low[i]
                af[i] = af_start
            else:
                # 继续上升趋势
                trend[i] = 1
                # 更新EP
                if high[i] > ep[i-1]:
                    ep[i] = high[i]
                    af[i] = min(af[i-1] + af_increment, af_max)
                else:
                    ep[i] = ep[i-1]
                    af[i] = af[i-1]
                
                # SAR不能高于前两期的最低价
                sar[i] = min(sar[i], low[i-1])
                if i > 1:
                    sar[i] = min(sar[i], low[i-2])
        else:  # 下降趋势
            # 检查是否需要反转
            if high[i] > sar[i]:
                # 反转为上升趋势
                trend[i] = 1
                sar[i] = ep[i-1]  # SAR设为前期最低点
                ep[i] = high[i]
                af[i] = af_start
            else:
                # 继续下降趋势
                trend[i] = -1
                # 更新EP
                if low[i] < ep[i-1]:
                    ep[i] = low[i]
                    af[i] = min(af[i-1] + af_increment, af_max)
                else:
                    ep[i] = ep[i-1]
                    af[i] = af[i-1]
                
                # SAR不能低于前两期的最高价
                sar[i] = max(sar[i], high[i-1])
                if i > 1:
                    sar[i] = max(sar[i], high[i-2])
    
    return sar, trend, ep, af


def calculate_slope(sar_values, window=5):
    """
    计算SAR斜率
    
    Args:
        sar_values: SAR值数组
        window: 计算斜率的窗口大小
    
    Returns:
        float: 斜率值
    """
    if len(sar_values) < window:
        return 0.0
    
    recent_sar = sar_values[-window:]
    x = np.arange(len(recent_sar))
    
    # 线性拟合
    coefficients = np.polyfit(x, recent_sar, 1)
    slope = coefficients[0]
    
    return float(slope)


def get_quadrant(price, sar, trend):
    """
    确定象限
    
    Args:
        price: 当前价格
        sar: SAR值
        trend: 趋势 (1=bullish, -1=bearish)
    
    Returns:
        str: 象限 (Q1, Q2, Q3, Q4)
    """
    if trend == 1:  # bullish
        if price > sar:
            return "Q1"  # 价格在SAR上方，上升趋势
        else:
            return "Q2"  # 价格在SAR下方，但趋势上升（即将反转）
    else:  # bearish
        if price < sar:
            return "Q3"  # 价格在SAR下方，下降趋势
        else:
            return "Q4"  # 价格在SAR上方，但趋势下降（即将反转）


def get_klines(symbol, limit=100):
    """
    从OKX获取K线数据
    
    Args:
        symbol: 交易对符号
        limit: 获取的K线数量
    
    Returns:
        dict: K线数据 {timestamp, open, high, low, close, volume}
    """
    try:
        # 优先使用永续合约
        url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}-USDT-SWAP&bar=1m&limit={limit}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # 如果永续合约失败，尝试现货
        if data.get('code') != '0' or not data.get('data'):
            url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}-USDT&bar=1m&limit={limit}"
            response = requests.get(url, timeout=10)
            data = response.json()
        
        if data.get('code') == '0' and data.get('data'):
            # OKX K线格式: [时间戳, 开盘价, 最高价, 最低价, 收盘价, 成交量, ...]
            klines = []
            for candle in reversed(data['data']):  # 反转为升序
                klines.append({
                    'timestamp': int(candle[0]),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                })
            
            return klines
        else:
            print(f"[警告] {symbol} K线数据获取失败: {data.get('msg', 'Unknown error')}")
            return []
            
    except Exception as e:
        print(f"[错误] {symbol} 获取K线失败: {e}")
        return []


def load_last_position(symbol):
    """
    加载上一次的持仓状态
    
    Args:
        symbol: 交易对符号
    
    Returns:
        dict: 上一次的状态 {position, duration_minutes}
    """
    jsonl_file = DATA_DIR / f"{symbol}.jsonl"
    
    if jsonl_file.exists():
        try:
            with open(jsonl_file, 'rb') as f:
                # 从文件末尾读取最后一行
                try:
                    f.seek(-2, 2)  # 跳过最后的换行符
                    while f.read(1) != b'\n':
                        f.seek(-2, 1)
                except OSError:
                    f.seek(0)
                
                last_line = f.readline().decode('utf-8')
                
                if last_line.strip():
                    last_record = json.loads(last_line)
                    return {
                        'position': last_record.get('position', 'unknown'),
                        'duration_minutes': last_record.get('duration_minutes', 0)
                    }
        except Exception as e:
            print(f"[错误] {symbol} 加载上次状态失败: {e}")
    
    return {'position': 'unknown', 'duration_minutes': 0}


def save_to_jsonl(symbol, data):
    """
    保存数据到JSONL
    
    Args:
        symbol: 交易对符号
        data: 数据记录
    """
    jsonl_file = DATA_DIR / f"{symbol}.jsonl"
    
    try:
        with open(jsonl_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
    except Exception as e:
        print(f"[错误] {symbol} 保存JSONL失败: {e}")


def process_symbol(symbol):
    """
    处理单个交易对
    
    Args:
        symbol: 交易对符号
    
    Returns:
        bool: 是否成功
    """
    try:
        # 获取K线数据
        klines = get_klines(symbol, limit=100)
        
        if not klines or len(klines) < 10:
            print(f"[警告] {symbol} K线数据不足")
            return False
        
        # 准备数据
        high = np.array([k['high'] for k in klines])
        low = np.array([k['low'] for k in klines])
        close = np.array([k['close'] for k in klines])
        
        # 计算SAR
        sar_values, trends, eps, afs = calculate_sar(high, low, close)
        
        # 获取最新值
        current_sar = float(sar_values[-1])
        current_price = float(close[-1])
        current_trend = int(trends[-1])
        timestamp = klines[-1]['timestamp']
        
        # 确定持仓方向
        position = 'bullish' if current_trend == 1 else 'bearish'
        
        # 计算斜率
        slope_value = calculate_slope(sar_values, window=5)
        slope_direction = 'up' if slope_value > 0 else 'down'
        
        # 确定象限
        quadrant = get_quadrant(current_price, current_sar, current_trend)
        
        # 加载上次状态以计算持续时间
        last_state = load_last_position(symbol)
        
        if last_state['position'] == position:
            duration_minutes = last_state['duration_minutes'] + 1
        else:
            duration_minutes = 1  # 新周期开始
        
        # 转换时间戳为北京时间
        beijing_time = datetime.fromtimestamp(timestamp / 1000, BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        # 计算 SAR 差值（绝对值和百分比）
        sar_diff_abs = abs(current_price - current_sar)
        sar_diff_pct = (sar_diff_abs / current_price) * 100 if current_price > 0 else 0
        
        # 构建数据记录
        record = {
            'symbol': symbol,
            'timestamp': timestamp,
            'beijing_time': beijing_time,
            'close': round(current_price, 8),
            'sar': round(current_sar, 8),
            'position': position,
            'quadrant': quadrant,
            'duration_minutes': duration_minutes,
            'slope_value': round(slope_value, 4),
            'slope_direction': slope_direction,
            'sar_diff_abs': round(sar_diff_abs, 8),
            'sar_diff_pct': round(sar_diff_pct, 4)
        }
        
        # 保存到JSONL
        save_to_jsonl(symbol, record)
        
        print(f"[成功] {symbol}: {position} {quadrant} 持续{duration_minutes}分钟 斜率{slope_value:.4f}")
        
        return True
        
    except Exception as e:
        print(f"[错误] {symbol} 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主循环"""
    print("=" * 60)
    print("SAR JSONL 数据采集器启动")
    print(f"追踪币种: {len(SYMBOLS)}个")
    print("=" * 60)
    
    cycle_count = 0
    
    while True:
        try:
            now = datetime.now(BEIJING_TZ)
            cycle_count += 1
            
            print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] 开始第 {cycle_count} 次采集...")
            
            success_count = 0
            bullish_count = 0
            bearish_count = 0
            
            # 处理所有交易对
            for symbol in SYMBOLS:
                if process_symbol(symbol):
                    success_count += 1
                    
                    # 统计多空
                    last_state = load_last_position(symbol)
                    if last_state['position'] == 'bullish':
                        bullish_count += 1
                    elif last_state['position'] == 'bearish':
                        bearish_count += 1
                
                time.sleep(0.1)  # 避免请求过快
            
            print(f"\n[统计] 成功: {success_count}/{len(SYMBOLS)}")
            print(f"[多空] 多头: {bullish_count}, 空头: {bearish_count}")
            print(f"[已采集] {cycle_count} 次")
            
            # 每1分钟采集一次
            next_time = now + timedelta(minutes=1)
            print(f"\n[等待] 下次采集时间: {next_time.strftime('%H:%M:%S')} (300秒后)")
            time.sleep(300)  # 5分钟采集一次
            
        except KeyboardInterrupt:
            print("\n[退出] 采集器已停止")
            break
        except Exception as e:
            print(f"[错误] 采集循环失败: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(60)


if __name__ == '__main__':
    main()
