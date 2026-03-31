#!/usr/bin/env python3
"""
Coin Change Tracker Collector - 币种涨跌变化追踪采集器
实时采集27个币种的价格变化并写入JSONL
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
DATA_DIR = Path('/home/user/webapp/data/coin_change_tracker')
BASELINE_DIR = DATA_DIR
DATA_DIR.mkdir(parents=True, exist_ok=True)

BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 27个追踪的币种（2026-03-06更新）
SYMBOLS = [
    'BTC', 'ETH', 'XRP', 'BNB', 'SOL',
    'LTC', 'DOGE', 'SUI', 'TRX', 'TON',
    'ETC', 'BCH', 'HBAR', 'XLM', 'FIL',
    'LINK', 'CRO', 'DOT', 'AAVE', 'UNI',
    'NEAR', 'APT', 'CFX', 'CRV', 'STX',
    'LDO', 'TAO'
]


def calculate_rsi(prices, period=14):
    """
    计算RSI指标
    :param prices: 价格列表(从旧到新)
    :param period: RSI周期，默认14
    :return: RSI值 (0-100)
    """
    if len(prices) < period + 1:
        return None
    
    # 计算价格变化
    deltas = np.diff(prices)
    
    # 分离涨跌
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # 计算平均涨跌
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    # 避免除零
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)


def get_5min_candles(symbol, limit=20):
    """
    获取5分钟K线数据
    :param symbol: 币种符号
    :param limit: 获取K线数量，默认20根（足够计算RSI14）
    :return: 收盘价列表(从旧到新)
    """
    try:
        # 优先使用永续合约
        url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}-USDT-SWAP&bar=5m&limit={limit}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        # 如果永续合约失败，尝试现货
        if data.get('code') != '0' or not data.get('data'):
            url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}-USDT&bar=5m&limit={limit}"
            response = requests.get(url, timeout=5)
            data = response.json()
        
        if data.get('code') == '0' and data.get('data'):
            # K线数据格式: [时间戳, 开盘价, 最高价, 最低价, 收盘价, ...]
            # OKX返回的数据是从新到旧，需要反转
            candles = data['data']
            close_prices = [float(candle[4]) for candle in reversed(candles)]
            return close_prices
        else:
            print(f"[警告] {symbol} 5分钟K线获取失败")
            return None
            
    except Exception as e:
        print(f"[错误] {symbol} 获取5分钟K线失败: {e}")
        return None


def get_all_rsi_values():
    """
    获取所有27个币种的RSI值
    :return: 字典 {symbol: rsi_value}
    """
    rsi_values = {}
    
    for symbol in SYMBOLS:
        try:
            # 获取5分钟K线数据
            close_prices = get_5min_candles(symbol, limit=20)
            
            if close_prices and len(close_prices) >= 15:  # 至少需要15根K线来计算RSI14
                rsi = calculate_rsi(close_prices, period=14)
                if rsi is not None:
                    rsi_values[symbol] = rsi
                    print(f"[RSI] {symbol}: {rsi}")
            else:
                print(f"[警告] {symbol} K线数据不足，无法计算RSI")
            
            time.sleep(0.1)  # 避免请求过快
            
        except Exception as e:
            print(f"[错误] {symbol} 计算RSI失败: {e}")
            continue
    
    return rsi_values


def get_daily_open_prices():
    """从OKX获取今日开盘价（日线开盘价）"""
    try:
        open_prices = {}
        for symbol in SYMBOLS:
            try:
                # 优先使用永续合约，如果失败则使用现货
                # 永续合约后缀：-USDT-SWAP
                url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}-USDT-SWAP&bar=1D&limit=1"
                response = requests.get(url, timeout=5)
                data = response.json()
                
                # 如果永续合约失败，尝试现货
                if data.get('code') != '0' or not data.get('data'):
                    url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}-USDT&bar=1D&limit=1"
                    response = requests.get(url, timeout=5)
                    data = response.json()
                
                if data.get('code') == '0' and data.get('data'):
                    # 日线数据格式: [时间戳, 开盘价, 最高价, 最低价, 收盘价, ...]
                    candle = data['data'][0]
                    open_price = float(candle[1])  # 开盘价
                    open_prices[symbol] = open_price
                    print(f"[开盘价] {symbol}: {open_price}")
                else:
                    print(f"[警告] {symbol} 开盘价获取失败")
                    
                time.sleep(0.1)  # 避免请求过快
                
            except Exception as e:
                print(f"[错误] {symbol} 获取开盘价失败: {e}")
                continue
                
        return open_prices
        
    except Exception as e:
        print(f"[错误] 获取开盘价失败: {e}")
        return {}


def get_current_prices():
    """从OKX获取当前价格"""
    try:
        prices = {}
        for symbol in SYMBOLS:
            try:
                # 优先使用永续合约，如果失败则使用现货
                url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}-USDT-SWAP"
                response = requests.get(url, timeout=5)
                data = response.json()
                
                # 如果永续合约失败，尝试现货
                if data.get('code') != '0' or not data.get('data'):
                    url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}-USDT"
                    response = requests.get(url, timeout=5)
                    data = response.json()
                
                if data.get('code') == '0' and data.get('data'):
                    price = float(data['data'][0]['last'])
                    prices[symbol] = price
                    print(f"[价格] {symbol}: {price}")
                else:
                    print(f"[警告] {symbol} 价格获取失败")
                    
                time.sleep(0.1)  # 避免请求过快
                
            except Exception as e:
                print(f"[错误] {symbol} 获取价格失败: {e}")
                continue
                
        return prices
        
    except Exception as e:
        print(f"[错误] 获取价格失败: {e}")
        return {}


def load_baseline():
    """加载基准价格"""
    today = datetime.now(BEIJING_TZ).strftime('%Y%m%d')
    baseline_file = BASELINE_DIR / f"baseline_{today}.json"
    
    if baseline_file.exists():
        try:
            with open(baseline_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[错误] 加载基准价格失败: {e}")
    
    return {}


def save_baseline(prices):
    """保存基准价格"""
    today = datetime.now(BEIJING_TZ).strftime('%Y%m%d')
    baseline_file = BASELINE_DIR / f"baseline_{today}.json"
    
    try:
        with open(baseline_file, 'w', encoding='utf-8') as f:
            json.dump(prices, f, indent=2, ensure_ascii=False)
        print(f"[保存] 基准价格已保存到 {baseline_file}")
    except Exception as e:
        print(f"[错误] 保存基准价格失败: {e}")


def calculate_changes(current_prices, baseline_prices):
    """计算涨跌幅"""
    changes = {}
    
    for symbol in SYMBOLS:
        if symbol in current_prices and symbol in baseline_prices:
            current = current_prices[symbol]
            baseline = baseline_prices[symbol]
            
            if baseline > 0:
                change_pct = ((current - baseline) / baseline) * 100
                changes[symbol] = {
                    'current_price': current,
                    'baseline_price': baseline,
                    'change_pct': round(change_pct, 2)
                }
    
    return changes


def save_to_jsonl(data):
    """保存数据到JSONL"""
    today = datetime.now(BEIJING_TZ).strftime('%Y%m%d')
    jsonl_file = DATA_DIR / f"coin_change_{today}.jsonl"
    
    try:
        with open(jsonl_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
        print(f"[保存] 数据已写入 {jsonl_file}")
    except Exception as e:
        print(f"[错误] 保存JSONL失败: {e}")


def save_rsi_to_jsonl(rsi_data):
    """保存RSI数据到独立的JSONL文件"""
    today = datetime.now(BEIJING_TZ).strftime('%Y%m%d')
    rsi_file = DATA_DIR / f"rsi_{today}.jsonl"
    
    try:
        with open(rsi_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(rsi_data, ensure_ascii=False) + '\n')
        print(f"[保存] RSI数据已写入 {rsi_file}")
    except Exception as e:
        print(f"[错误] 保存RSI JSONL失败: {e}")


def save_velocity_to_jsonl(velocity_data):
    """保存5分钟涨速数据到独立的JSONL文件"""
    today = datetime.now(BEIJING_TZ).strftime('%Y%m%d')
    velocity_file = DATA_DIR / f"velocity_{today}.jsonl"
    
    try:
        with open(velocity_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(velocity_data, ensure_ascii=False) + '\n')
        print(f"[保存] 涨速数据已写入 {velocity_file}")
    except Exception as e:
        print(f"[错误] 保存涨速JSONL失败: {e}")


def get_total_change_5min_ago():
    """获取5分钟前的total_change值"""
    try:
        today = datetime.now(BEIJING_TZ).strftime('%Y%m%d')
        jsonl_file = DATA_DIR / f"coin_change_{today}.jsonl"
        
        if not jsonl_file.exists():
            return None
        
        # 读取今天的所有记录
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            return None
        
        # 获取最后一条记录的时间戳
        latest_record = json.loads(lines[-1].strip())
        latest_timestamp = latest_record.get('timestamp', 0)
        
        # 5分钟前的时间戳（5分钟 = 300秒 = 300000毫秒）
        target_timestamp = latest_timestamp - 300000
        
        # 查找最接近5分钟前的记录
        closest_record = None
        min_diff = float('inf')
        
        for line in lines:
            record = json.loads(line.strip())
            timestamp = record.get('timestamp', 0)
            diff = abs(timestamp - target_timestamp)
            
            if diff < min_diff:
                min_diff = diff
                closest_record = record
        
        if closest_record:
            return closest_record.get('total_change', 0)
        
        return None
        
    except Exception as e:
        print(f"[错误] 获取5分钟前的total_change失败: {e}")
        return None


def main():
    """主循环"""
    print("=" * 60)
    print("币种涨跌变化追踪采集器启动")
    print("=" * 60)
    
    # 加载或初始化基准价格
    baseline_prices = load_baseline()
    last_baseline_date = None
    last_rsi_collect_time = None  # 记录上次RSI采集时间
    
    # 如果没有基准价格，或者是新的一天，获取今日开盘价
    today = datetime.now(BEIJING_TZ).strftime('%Y%m%d')
    
    if not baseline_prices:
        print("[初始化] 获取今日开盘价作为基准...")
        baseline_prices = get_daily_open_prices()
        if baseline_prices:
            save_baseline(baseline_prices)
            last_baseline_date = today
    else:
        last_baseline_date = today
    
    while True:
        try:
            now = datetime.now(BEIJING_TZ)
            current_date = now.strftime('%Y%m%d')
            
            # 检查是否是新的一天，如果是则重置基准价格
            if current_date != last_baseline_date:
                print(f"\n[新的一天] {current_date} - 重置基准价格...")
                baseline_prices = get_daily_open_prices()
                if baseline_prices:
                    save_baseline(baseline_prices)
                    last_baseline_date = current_date
            
            print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] 开始采集...")
            
            # 获取当前价格
            current_prices = get_current_prices()
            
            # 检查是否需要采集RSI（每5分钟一次）
            should_collect_rsi = False
            if last_rsi_collect_time is None:
                should_collect_rsi = True
            else:
                minutes_since_last = (now - last_rsi_collect_time).total_seconds() / 60
                if minutes_since_last >= 5:
                    should_collect_rsi = True
            
            # 获取RSI数据
            rsi_values = {}
            total_rsi = None
            if should_collect_rsi:
                print("[RSI] 开始采集5分钟RSI数据...")
                rsi_values = get_all_rsi_values()
                
                # 确保获取到所有币种的RSI
                if rsi_values:
                    missing_symbols = [s for s in SYMBOLS if s not in rsi_values]
                    if missing_symbols:
                        print(f"[警告] 以下币种RSI获取失败: {', '.join(missing_symbols)}")
                    
                    # 只有当获取到足够多的RSI数据时才计算总和（至少20个币种）
                    if len(rsi_values) >= 20:
                        total_rsi = round(sum(rsi_values.values()), 2)
                        print(f"[RSI] 成功采集 {len(rsi_values)}/27 个币种，RSI之和: {total_rsi}")
                        last_rsi_collect_time = now
                        
                        # 单独保存RSI数据到独立文件
                        rsi_record = {
                            'timestamp': int(time.time() * 1000),
                            'beijing_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                            'rsi_values': rsi_values,
                            'total_rsi': total_rsi,
                            'count': len(rsi_values)
                        }
                        save_rsi_to_jsonl(rsi_record)
                    else:
                        print(f"[警告] RSI数据不足 ({len(rsi_values)}/27)，跳过本次记录")
                        rsi_values = {}
                        total_rsi = None
            
            if current_prices:
                # 🔴 强制检查：必须获取到全部27个币种的价格
                if len(current_prices) < 27:
                    missing_symbols = [s for s in SYMBOLS if s not in current_prices]
                    print(f"❌ [数据不完整] 只获取到 {len(current_prices)}/27 个币种，缺失: {', '.join(missing_symbols)}")
                    print(f"⚠️  [跳过保存] 数据不完整，跳过本次采集，等待下次重试...")
                    print(f"[等待] 下次采集时间: {(now + timedelta(minutes=1)).strftime('%H:%M:%S')}")
                    time.sleep(60)
                    continue
                
                # 计算涨跌幅
                changes = calculate_changes(current_prices, baseline_prices)
                
                # 再次检查：确保所有27个币种都有涨跌幅数据
                if len(changes) < 27:
                    missing_in_changes = [s for s in SYMBOLS if s not in changes]
                    print(f"❌ [数据不完整] 涨跌幅计算后只有 {len(changes)}/27 个币种，缺失: {', '.join(missing_in_changes)}")
                    print(f"⚠️  [跳过保存] 数据不完整，跳过本次采集，等待下次重试...")
                    print(f"[等待] 下次采集时间: {(now + timedelta(minutes=1)).strftime('%H:%M:%S')}")
                    time.sleep(60)
                    continue
                
                # ✅ 数据完整，可以保存
                print(f"✅ [数据完整] 成功获取全部 27/27 个币种的数据")
                
                # 计算总和
                total_change = sum(item['change_pct'] for item in changes.values())
                
                # 计算上涨占比（只统计有涨跌的币种，排除change_pct=0的币种）
                up_coins = sum(1 for item in changes.values() if item['change_pct'] > 0)
                down_coins = sum(1 for item in changes.values() if item['change_pct'] < 0)
                total_coins = up_coins + down_coins  # 只计算有涨跌的币种
                up_ratio = (up_coins / total_coins * 100) if total_coins > 0 else 0
                
                # 构建数据记录
                record = {
                    'timestamp': int(time.time() * 1000),
                    'beijing_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'cumulative_pct': round(total_change, 2),  # 使用cumulative_pct字段名
                    'total_change': round(total_change, 2),     # 保留兼容性
                    'up_ratio': round(up_ratio, 1),            # 上涨占比 (%)
                    'up_coins': up_coins,                      # 上涨币种数
                    'down_coins': down_coins,                  # 下跌币种数（已修正）
                    'changes': changes,
                    'count': len(changes)
                }
                
                # 如果有RSI数据，添加到记录中
                if rsi_values:
                    record['rsi_values'] = rsi_values
                    record['total_rsi'] = total_rsi
                
                # 保存到JSONL
                save_to_jsonl(record)
                
                # 计算5分钟涨速
                total_change_5min_ago = get_total_change_5min_ago()
                if total_change_5min_ago is not None:
                    velocity_5min = round(total_change - total_change_5min_ago, 2)
                    
                    # 保存涨速数据
                    velocity_record = {
                        'timestamp': int(time.time() * 1000),
                        'beijing_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                        'velocity_5min': velocity_5min,
                        'current_total_change': round(total_change, 2),
                        'total_change_5min_ago': round(total_change_5min_ago, 2)
                    }
                    save_velocity_to_jsonl(velocity_record)
                    
                    log_msg = f"[统计] 总涨跌幅: {total_change:.2f}%, 5分钟涨速: {velocity_5min:+.2f}%, 币种数: {len(changes)}, 上涨占比: {up_ratio:.1f}% ({up_coins}↑/{total_coins - up_coins}↓)"
                else:
                    log_msg = f"[统计] 总涨跌幅: {total_change:.2f}%, 币种数: {len(changes)}, 上涨占比: {up_ratio:.1f}% ({up_coins}↑/{total_coins - up_coins}↓)"
                
                if total_rsi is not None:
                    log_msg += f", RSI之和: {total_rsi}"
                print(log_msg)
            
            # 每1分钟采集一次
            print(f"[等待] 下次采集时间: {(now + timedelta(minutes=1)).strftime('%H:%M:%S')}")
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\n[退出] 采集器已停止")
            break
        except Exception as e:
            print(f"[错误] 采集失败: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(60)


if __name__ == '__main__':
    main()
