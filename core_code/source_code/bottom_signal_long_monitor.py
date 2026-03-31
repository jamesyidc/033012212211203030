#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
见底信号自动做多监控器
监控市场情绪见底信号，当满足条件时自动开多单

策略1: 见底信号(底部背离) + RSI<800 + 涨幅前8 → 10倍杠杆做多
策略2: 见底信号(底部背离) + RSI<800 + 涨幅后8 → 10倍杠杆做多

每份账户可用余额的1.5%，开8份，每份限额5U（可配置）

JSONL配置与执行记录：
- 每个账户每个策略有独立的配置文件和执行记录
- 配置文件存储: RSI阈值、单币限额、杠杆等参数
- 执行记录防止重复触发（1小时冷却期）
"""

import json
import os
import sys
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

# 项目根目录
BASE_DIR = Path('/home/user/webapp')
sys.path.insert(0, str(BASE_DIR))

# 数据目录
CONFIG_DIR = BASE_DIR / 'data' / 'okx_bottom_signal_strategies'
EXECUTION_DIR = BASE_DIR / 'data' / 'okx_bottom_signal_execution'

# API基础URL
API_BASE = 'http://localhost:9002'

# 配置
CHECK_INTERVAL = 60  # 检查间隔（秒）= 1分钟
COOLDOWN_TIME = 3600  # 冷却时间（秒）= 1小时，防止重复触发

# Telegram配置
TELEGRAM_BOT_TOKEN = "8437045462:AAFePnwdC21cqeWhZISMQHGGgjmroVqE2H0"
TELEGRAM_CHAT_ID = "-1003227444260"


def log(message):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)


def send_telegram_message(message):
    """发送Telegram消息"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            log("✅ Telegram消息发送成功")
        else:
            log(f"⚠️  Telegram消息发送失败: {response.status_code}")
    except Exception as e:
        log(f"❌ Telegram消息发送异常: {e}")


def load_strategy_config(account_id, strategy_type):
    """加载策略配置
    strategy_type: 'top8_long' 或 'bottom8_long'
    """
    config_file = CONFIG_DIR / f"{account_id}_bottom_signal_{strategy_type}.jsonl"
    
    # 默认配置
    default_config = {
        'enabled': False,
        'rsi_threshold': 800,
        'max_order_usdt': 5.0,
        'position_percent': 1.5,
        'leverage': 10
    }
    
    if not config_file.exists():
        log(f"⚠️  [{account_id}/{strategy_type}] 配置文件不存在，使用默认配置")
        return default_config
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                config = json.loads(lines[-1].strip())
                log(f"✅ [{account_id}/{strategy_type}] 加载配置成功: RSI<{config.get('rsi_threshold', 800)}, 限额{config.get('max_order_usdt', 5)}U")
                return config
    except Exception as e:
        log(f"❌ [{account_id}/{strategy_type}] 加载配置失败: {e}")
    
    return default_config


def check_last_execution(account_id, strategy_type):
    """检查上次执行时间，判断是否在冷却期内（支持按日期分文件）"""
    EXECUTION_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    
    # 优先检查今天的文件
    date_str = now.strftime('%Y%m%d')  # 20260226
    execution_file = EXECUTION_DIR / f"{account_id}_bottom_signal_{strategy_type}_execution_{date_str}.jsonl"
    
    # 如果今天的文件不存在，检查旧格式文件（兼容性）
    if not execution_file.exists():
        old_execution_file = EXECUTION_DIR / f"{account_id}_bottom_signal_{strategy_type}_execution.jsonl"
        if old_execution_file.exists():
            execution_file = old_execution_file
        else:
            return True  # 两个文件都不存在，可以执行
    
    try:
        with open(execution_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                # 从后往前查找最近的执行记录
                for line in reversed(lines):
                    line = line.strip()
                    if line:
                        last_record = json.loads(line)
                        last_time_str = last_record.get('timestamp')
                        if last_time_str:
                            last_time = datetime.fromisoformat(last_time_str)
                            time_diff = (now - last_time).total_seconds()
                            
                            if time_diff < COOLDOWN_TIME:
                                remaining = int(COOLDOWN_TIME - time_diff)
                                log(f"⏳ [{account_id}/{strategy_type}] 冷却期内，还需等待 {remaining}秒")
                                return False
                            break  # 找到最近的记录就退出
    except Exception as e:
        log(f"❌ [{account_id}/{strategy_type}] 检查执行记录失败: {e}")
    
    return True


def record_execution(account_id, strategy_type, coins, rsi_value, result):
    """记录执行信息（按日期分文件保存）"""
    EXECUTION_DIR.mkdir(parents=True, exist_ok=True)
    
    # 按日期分文件：account_main_bottom_signal_top8_long_execution_20260226.jsonl
    now = datetime.now()
    date_str = now.strftime('%Y%m%d')  # 20260226
    execution_file = EXECUTION_DIR / f"{account_id}_bottom_signal_{strategy_type}_execution_{date_str}.jsonl"
    
    try:
        record = {
            'timestamp': now.isoformat(),
            'time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'date': now.strftime('%Y-%m-%d'),
            'account_id': account_id,
            'strategy_type': strategy_type,
            'rsi_value': rsi_value,
            'coins': coins,
            'result': result
        }
        
        with open(execution_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        log(f"✅ [{account_id}/{strategy_type}] 执行记录已保存到: {execution_file.name}")
    except Exception as e:
        log(f"❌ [{account_id}/{strategy_type}] 保存执行记录失败: {e}")


def get_account_list():
    """获取账户列表"""
    try:
        response = requests.get(f"{API_BASE}/api/okx-accounts/list-with-credentials", timeout=10)
        result = response.json()
        if result.get('success'):
            accounts = result.get('accounts', [])
            log(f"✅ 获取账户列表成功: {len(accounts)} 个账户")
            return accounts
        else:
            log(f"❌ 获取账户列表失败: {result.get('error')}")
            return []
    except Exception as e:
        log(f"❌ 获取账户列表异常: {e}")
        return []


def get_market_sentiment():
    """获取当前市场情绪"""
    try:
        response = requests.get(f"{API_BASE}/api/market-sentiment", timeout=10)
        result = response.json()
        if result.get('success'):
            sentiment = result.get('sentiment', '')
            rsi_total = float(result.get('rsi_total', 0))
            log(f"📊 市场情绪: {sentiment}, RSI总和: {rsi_total}")
            return sentiment, rsi_total
        else:
            log(f"⚠️  获取市场情绪失败: {result.get('error')}")
            return None, 0
    except Exception as e:
        log(f"❌ 获取市场情绪异常: {e}")
        return None, 0


def get_favorite_symbols():
    """获取常用币列表"""
    try:
        response = requests.get(f"{API_BASE}/api/favorite-symbols", timeout=10)
        result = response.json()
        if result.get('success'):
            symbols = result.get('symbols', [])
            log(f"✅ 获取常用币列表成功: {len(symbols)} 个币种")
            return symbols
        else:
            log(f"❌ 获取常用币列表失败")
            return []
    except Exception as e:
        log(f"❌ 获取常用币列表异常: {e}")
        return []


def get_top_gainers(symbols, count=8, reverse=False):
    """获取涨幅前/后N名币种
    reverse=False: 涨幅前N (涨幅最大)
    reverse=True: 涨幅后N (涨幅最小)
    """
    try:
        response = requests.get(f"{API_BASE}/api/okx/market-tickers", timeout=10)
        result = response.json()
        
        if not result.get('success'):
            log(f"❌ 获取行情数据失败")
            return []
        
        tickers = result.get('tickers', [])
        
        # 筛选常用币种
        filtered_tickers = []
        for ticker in tickers:
            inst_id = ticker.get('instId', '')
            if any(inst_id.startswith(sym + '-USDT-SWAP') for sym in symbols):
                change = float(ticker.get('change', 0)) * 100  # 转换为百分比
                filtered_tickers.append({
                    'symbol': inst_id.split('-')[0],
                    'instId': inst_id,
                    'change': change
                })
        
        # 排序
        sorted_tickers = sorted(filtered_tickers, key=lambda x: x['change'], reverse=not reverse)
        top_coins = sorted_tickers[:count]
        
        type_name = '涨幅后' if reverse else '涨幅前'
        coins_str = ', '.join([f"{c['symbol']}({c['change']:.2f}%)" for c in top_coins])
        log(f"📈 {type_name}{count}名: {coins_str}")
        return top_coins
        
    except Exception as e:
        log(f"❌ 获取涨跌幅排名异常: {e}")
        return []


def execute_long_orders(account, coins, config):
    """执行多单开仓"""
    account_id = account['id']
    account_name = account['name']
    
    # 获取账户余额
    try:
        response = requests.get(f"{API_BASE}/api/okx-trading/account/{account_id}", timeout=10)
        result = response.json()
        if not result.get('success'):
            log(f"❌ [{account_name}] 获取账户信息失败")
            return None
        
        available_balance = float(result.get('data', {}).get('availBal', 0))
        log(f"💰 [{account_name}] 可用余额: {available_balance:.2f} USDT")
        
    except Exception as e:
        log(f"❌ [{account_name}] 获取账户信息异常: {e}")
        return None
    
    # 计算每个币种的开仓金额
    position_percent = config.get('position_percent', 1.5) / 100  # 1.5% -> 0.015
    max_per_coin = config.get('max_order_usdt', 5.0)
    leverage = config.get('leverage', 10)
    
    total_investment = available_balance * position_percent
    per_coin_amount = min(total_investment / len(coins), max_per_coin)
    
    log(f"💵 [{account_name}] 总投入: {total_investment:.2f} USDT, 单币: {per_coin_amount:.2f} USDT, 杠杆: {leverage}x")
    
    # 开仓
    success_count = 0
    failed_coins = []
    
    for coin in coins:
        symbol = coin['symbol']
        inst_id = coin['instId']
        
        try:
            # 调用开仓API
            payload = {
                'account_id': account_id,
                'instId': inst_id,
                'tdMode': 'cross',  # 全仓
                'side': 'buy',  # 做多
                'posSide': 'long',
                'ordType': 'market',
                'sz_usdt': per_coin_amount,
                'lever': leverage
            }
            
            response = requests.post(f"{API_BASE}/api/okx-trading/open-position-by-usdt", json=payload, timeout=15)
            result = response.json()
            
            if result.get('success'):
                success_count += 1
                log(f"✅ [{account_name}] {symbol} 多单开仓成功: {per_coin_amount:.2f} USDT @ {leverage}x")
            else:
                failed_coins.append(symbol)
                log(f"❌ [{account_name}] {symbol} 多单开仓失败: {result.get('error')}")
            
            time.sleep(0.5)  # 避免API限流
            
        except Exception as e:
            failed_coins.append(symbol)
            log(f"❌ [{account_name}] {symbol} 多单开仓异常: {e}")
    
    return {
        'success_count': success_count,
        'failed_coins': failed_coins,
        'total_investment': total_investment,
        'per_coin_amount': per_coin_amount
    }


def check_and_execute_strategy(account, strategy_type):
    """检查并执行见底信号策略
    strategy_type: 'top8_long' (涨幅前8) 或 'bottom8_long' (涨幅后8)
    """
    account_id = account['id']
    account_name = account['name']
    
    # 1. 加载策略配置
    config = load_strategy_config(account_id, strategy_type)
    
    if not config.get('enabled'):
        return  # 策略未启用
    
    # 2. 检查冷却期
    if not check_last_execution(account_id, strategy_type):
        return  # 在冷却期内
    
    # 3. 获取市场情绪和RSI
    sentiment, rsi_total = get_market_sentiment()
    
    if sentiment is None:
        return
    
    # 4. 判断是否为见底信号
    if '🎯见底信号' not in sentiment:
        return
    
    # 5. 检查RSI阈值
    rsi_threshold = config.get('rsi_threshold', 800)
    if rsi_total >= rsi_threshold:
        log(f"⚠️  [{account_name}/{strategy_type}] RSI总和({rsi_total:.0f}) >= 阈值({rsi_threshold})，不满足做多条件")
        return
    
    log(f"🎯 [{account_name}/{strategy_type}] 触发条件满足: {sentiment}, RSI={rsi_total:.0f} < {rsi_threshold}")
    
    # 6. 获取目标币种
    symbols = get_favorite_symbols()
    if not symbols:
        log(f"❌ [{account_name}/{strategy_type}] 获取常用币列表失败")
        return
    
    # reverse=False: 涨幅前8, reverse=True: 涨幅后8
    is_bottom8 = (strategy_type == 'bottom8_long')
    target_coins = get_top_gainers(symbols, count=8, reverse=is_bottom8)
    
    if not target_coins:
        log(f"❌ [{account_name}/{strategy_type}] 获取目标币种失败")
        return
    
    # 7. 执行开仓
    log(f"🚀 [{account_name}/{strategy_type}] 开始执行做多开仓...")
    result = execute_long_orders(account, target_coins, config)
    
    if result is None:
        log(f"❌ [{account_name}/{strategy_type}] 开仓失败")
        return
    
    # 8. 记录执行
    coins_list = [c['symbol'] for c in target_coins]
    record_execution(account_id, strategy_type, coins_list, rsi_total, result)
    
    # 9. 发送Telegram通知
    strategy_name = "见底信号+涨幅前8做多" if strategy_type == 'top8_long' else "见底信号+涨幅后8做多"
    message = f"""
🎯 <b>{strategy_name} - 已执行</b>

📌 账户: {account_name}
📊 市场情绪: {sentiment}
📈 RSI总和: {rsi_total:.0f} (阈值 < {rsi_threshold})

💰 总投入: {result['total_investment']:.2f} USDT
💵 单币: {result['per_coin_amount']:.2f} USDT
⚡️ 杠杆: {config.get('leverage', 10)}x

✅ 成功: {result['success_count']}/{len(target_coins)}
📊 币种: {', '.join(coins_list)}

⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔒 下次可触发: {(datetime.now() + timedelta(seconds=COOLDOWN_TIME)).strftime('%H:%M')}
"""
    
    if result['failed_coins']:
        message += f"\n❌ 失败: {', '.join(result['failed_coins'])}"
    
    send_telegram_message(message)
    log(f"✅ [{account_name}/{strategy_type}] 策略执行完成")


def main():
    """主循环"""
    log("=" * 80)
    log("🎯 见底信号自动做多监控器启动")
    log("=" * 80)
    log(f"检查间隔: {CHECK_INTERVAL}秒")
    log(f"冷却时间: {COOLDOWN_TIME}秒 ({COOLDOWN_TIME/3600:.1f}小时)")
    log("监控策略: 见底信号+涨幅前8做多, 见底信号+涨幅后8做多")
    log("=" * 80)
    
    while True:
        try:
            log("🔍 开始检查见底信号...")
            
            # 获取所有账户
            accounts = get_account_list()
            
            if not accounts:
                log("⚠️  未获取到账户列表，等待下次检查")
                time.sleep(CHECK_INTERVAL)
                continue
            
            # 遍历每个账户，检查两个策略
            for account in accounts:
                check_and_execute_strategy(account, 'top8_long')
                time.sleep(2)  # 账户间隔2秒
                check_and_execute_strategy(account, 'bottom8_long')
                time.sleep(2)  # 策略间隔2秒
            
            log(f"⏳ 等待 {CHECK_INTERVAL}秒 后下次检查...")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log("⚠️  收到退出信号，停止监控")
            break
        except Exception as e:
            log(f"❌ 主循环异常: {e}")
            import traceback
            log(traceback.format_exc())
            log(f"⏳ 等待 {CHECK_INTERVAL}秒 后重试...")
            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
