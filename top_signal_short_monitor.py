#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
见顶信号自动做空监控器
监控市场情绪见顶信号，当满足条件时自动开空单

策略1: 见顶信号 + RSI>1800 + 涨幅前8 → 做空
策略2: 见顶信号 + RSI>1800 + 涨幅后8 → 做空

每份账户可用余额的1.5%，开8份，每份限额5U

JSONL执行许可机制：
- 每个账户每个策略有独立的execution.jsonl文件
- 开关开启时，写入allowed=true到文件头
- 执行后，写入allowed=false，并记录执行详情
- 防止重复触发
"""

import json
import os
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

# 项目根目录
BASE_DIR = Path('/home/user/webapp')
sys.path.insert(0, str(BASE_DIR))

# 数据目录
DATA_DIR = BASE_DIR / 'data' / 'okx_auto_strategy'

# API基础URL
API_BASE = 'http://localhost:9002'

# 配置
CHECK_INTERVAL = 60  # 检查间隔（秒）= 1分钟
COOLDOWN_TIME = 3600  # 冷却时间（秒）= 1小时，防止重复触发

# Telegram配置
TELEGRAM_BOT_TOKEN = "8437045462:AAFePnwdC21cqeWhZISMQHGGgjmroVqE2H0"
TELEGRAM_CHAT_ID = "-1003227444260"

# 策略配置
STRATEGY_CONFIG = {
    'top8_short': {
        'name': '见顶信号+前8做空',
        'enabled_key': 'top_signal_top8_short_enabled',
        'threshold_key': 'top_signal_top8_short_threshold',
        'coin_selection': 'top8',  # 涨幅前8
        'rsi_threshold': 1800,
        'balance_percent': 0.015,  # 1.5%
        'num_coins': 8,
        'max_per_coin': 5.0  # 每份最大5U
    },
    'bottom8_short': {
        'name': '见顶信号+后8做空',
        'enabled_key': 'top_signal_bottom8_short_enabled',
        'threshold_key': 'top_signal_bottom8_short_threshold',
        'coin_selection': 'bottom8',  # 涨幅后8
        'rsi_threshold': 1800,
        'balance_percent': 0.015,  # 1.5%
        'num_coins': 8,
        'max_per_coin': 5.0  # 每份最大5U
    }
}

# 存储上次触发时间（防止重复）
last_trigger_times = {
    'top8_short': {},
    'bottom8_short': {}
}


def log(message):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)


def get_execution_file_path(account_id, strategy_key):
    """获取执行许可文件路径"""
    # top8_short -> top_signal_top8_short_execution.jsonl
    # bottom8_short -> top_signal_bottom8_short_execution.jsonl
    filename = f"{account_id}_top_signal_{strategy_key}_execution.jsonl"
    return DATA_DIR / filename


def check_allowed_execution(account_id, strategy_key):
    """检查是否允许执行（从JSONL文件头读取）"""
    execution_file = get_execution_file_path(account_id, strategy_key)
    
    if not execution_file.exists():
        # 文件不存在，创建并默认不允许执行（需要用户手动开启）
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(execution_file, 'w', encoding='utf-8') as f:
                record = {
                    'allowed': False,  # 🔧 修复：默认不允许执行，需用户手动开启
                    'timestamp': datetime.now().isoformat(),
                    'reason': '初始化，默认关闭（需用户手动开启）'
                }
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            log(f"✅ [{account_id}] 创建执行许可文件（默认关闭）: {strategy_key}")
            return False  # 🔧 返回False
        except Exception as e:
            log(f"❌ [{account_id}] 创建执行许可文件失败: {e}")
            return False
    
    try:
        with open(execution_file, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if first_line:
                record = json.loads(first_line)
                allowed = record.get('allowed', False)
                return allowed
    except Exception as e:
        log(f"❌ [{account_id}] 读取执行许可失败: {e}")
    
    return False


def set_allowed_execution(account_id, strategy_key, allowed, reason='', rsi_value=None, coins=None, result=None):
    """设置执行许可（更新JSONL文件头）"""
    execution_file = get_execution_file_path(account_id, strategy_key)
    
    try:
        # 读取现有记录（除了第一行）
        existing_records = []
        if execution_file.exists():
            with open(execution_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    existing_records = lines[1:]  # 跳过第一行
        
        # 写入新的文件头
        with open(execution_file, 'w', encoding='utf-8') as f:
            header = {
                'allowed': allowed,
                'timestamp': datetime.now().isoformat(),
                'reason': reason
            }
            
            if rsi_value is not None:
                header['rsi_value'] = rsi_value
            
            if coins:
                header['coins'] = coins
            
            if result:
                header['result'] = result
            
            f.write(json.dumps(header, ensure_ascii=False) + '\n')
            
            # 写回其他记录
            for line in existing_records:
                f.write(line)
        
        log(f"✅ [{account_id}] 执行许可已更新: {strategy_key} = {allowed}")
        return True
    except Exception as e:
        log(f"❌ [{account_id}] 更新执行许可失败: {e}")
        return False


def record_execution(account_id, strategy_key, coins, total_amount, amount_per_coin, success_count, failed_count, success_coins, failed_coins):
    """记录执行详情（追加到JSONL文件）"""
    execution_file = get_execution_file_path(account_id, strategy_key)
    
    try:
        with open(execution_file, 'a', encoding='utf-8') as f:
            record = {
                'timestamp': datetime.now().isoformat(),
                'account_id': account_id,
                'strategy_key': strategy_key,
                'coins': coins,
                'total_amount': total_amount,
                'amount_per_coin': amount_per_coin,
                'success_count': success_count,
                'failed_count': failed_count,
                'success_coins': success_coins,
                'failed_coins': failed_coins
            }
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        log(f"✅ [{account_id}] 执行记录已保存: {strategy_key}")
        return True
    except Exception as e:
        log(f"❌ [{account_id}] 保存执行记录失败: {e}")
        return False


def send_telegram(message):
    """发送Telegram通知"""
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
        response = requests.post(url, json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }, timeout=10)
        return response.status_code == 200
    except Exception as e:
        log(f"❌ Telegram通知失败: {str(e)}")
        return False


def get_accounts():
    """获取所有账户列表"""
    try:
        response = requests.get(f"{API_BASE}/api/okx-accounts/list-with-credentials", timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('success'):
            return result.get('accounts', [])
        return []
    except Exception as e:
        log(f"❌ 获取账户列表异常: {str(e)}")
        return []


def get_tpsl_settings(account_id):
    """获取账户的策略设置"""
    try:
        response = requests.get(f"{API_BASE}/api/okx-trading/tpsl-settings/{account_id}", timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('success'):
            return result.get('settings', {})
        return {}
    except Exception as e:
        log(f"❌ 获取账户 {account_id} 设置异常: {str(e)}")
        return {}


def check_market_sentiment():
    """检查市场情绪是否出现见顶信号"""
    try:
        response = requests.get(f"{API_BASE}/api/market-sentiment/latest", timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('success') and result.get('data'):
            sentiment = result['data'].get('sentiment', '')
            return '见顶信号' in sentiment, sentiment
        return False, None
    except Exception as e:
        log(f"❌ 获取市场情绪异常: {str(e)}")
        return False, None


def get_current_rsi():
    """获取当前RSI总和"""
    try:
        response = requests.get(f"{API_BASE}/api/coin-change-tracker/latest", timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('success') and result.get('data'):
            return result['data'].get('total_rsi', 0)
        return None
    except Exception as e:
        log(f"❌ 获取RSI数据异常: {str(e)}")
        return None


def get_coin_list(coin_selection):
    """获取币种列表（前8或后8）"""
    try:
        response = requests.get(f"{API_BASE}/api/coin-change-tracker/latest", timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if not result.get('success') or not result.get('data'):
            return []
        
        changes = result['data'].get('changes', {})
        if not changes:
            return []
        
        # 转换为数组并排序
        coins_array = [(symbol, data['change_pct']) for symbol, data in changes.items()]
        coins_array.sort(key=lambda x: x[1], reverse=True)
        
        if coin_selection == 'top8':
            # 涨幅前8
            return [c[0] for c in coins_array[:8]]
        else:
            # 涨幅后8
            return [c[0] for c in coins_array[-8:]]
    except Exception as e:
        log(f"❌ 获取币种列表异常: {str(e)}")
        return []


def get_account_balance(account):
    """获取账户可用余额"""
    try:
        data = {
            'apiKey': account['apiKey'],
            'apiSecret': account['apiSecret'],
            'passphrase': account['passphrase']
        }
        response = requests.post(f"{API_BASE}/api/okx-trading/balance", json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('success'):
            return result.get('availableBalance', 0)
        return 0
    except Exception as e:
        log(f"❌ 获取账户余额异常: {str(e)}")
        return 0


def place_short_order(account, symbol, amount):
    """下空单"""
    try:
        order_data = {
            'symbol': f'{symbol}-USDT-SWAP',
            'direction': 'short',
            'orderType': 'market',
            'amount': amount,
            'leverage': account.get('leverage', 10)
        }
        
        data = {
            'apiKey': account['apiKey'],
            'apiSecret': account['apiSecret'],
            'passphrase': account['passphrase'],
            'order': order_data
        }
        
        response = requests.post(f"{API_BASE}/api/okx-trading/place-order", json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        return result.get('success', False), result.get('message', '')
    except Exception as e:
        log(f"❌ 下单异常: {str(e)}")
        return False, str(e)


def execute_strategy(account, strategy_key, config):
    """执行做空策略"""
    account_id = account['id']
    account_name = account.get('name', account_id)
    
    # 🔒 检查JSONL执行许可
    allowed = check_allowed_execution(account_id, strategy_key)
    if not allowed:
        log(f"🔒 [{account_name}] 策略 {config['name']} 执行许可已禁用，跳过")
        return
    
    log(f"✅ [{account_name}] 策略 {config['name']} 执行许可已启用，继续检查...")
    
    # 检查冷却时间
    current_time = time.time()
    last_trigger = last_trigger_times[strategy_key].get(account_id, 0)
    if current_time - last_trigger < COOLDOWN_TIME:
        remaining = int(COOLDOWN_TIME - (current_time - last_trigger))
        log(f"⏳ [{account_name}] 策略 {config['name']} 冷却中，剩余 {remaining} 秒")
        return
    
    # 获取设置
    settings = get_tpsl_settings(account_id)
    if not settings:
        log(f"⚠️ [{account_name}] 无法获取设置")
        return
    
    # 检查策略是否启用
    if not settings.get(config['enabled_key'], False):
        log(f"⏭️ [{account_name}] 策略 {config['name']} 未启用")
        return
    
    log(f"✅ [{account_name}] 策略 {config['name']} 已启用，开始执行...")
    
    # 获取账户余额
    balance = get_account_balance(account)
    if balance <= 0:
        log(f"❌ [{account_name}] 余额不足")
        return
    
    # 计算总投入金额（余额的1.5%）
    total_amount = balance * config['balance_percent']
    log(f"💰 [{account_name}] 账户余额: {balance:.2f} USDT, 总投入: {total_amount:.2f} USDT ({config['balance_percent']*100}%)")
    
    # 获取币种列表
    coins = get_coin_list(config['coin_selection'])
    if not coins:
        log(f"❌ [{account_name}] 无法获取币种列表")
        return
    
    log(f"📋 [{account_name}] 目标币种({len(coins)}个): {', '.join(coins)}")
    
    # 计算每个币种的金额
    amount_per_coin = total_amount / config['num_coins']
    
    # 应用每份最大限额
    if amount_per_coin > config['max_per_coin']:
        amount_per_coin = config['max_per_coin']
        log(f"⚠️ [{account_name}] 单币金额超限，调整为: {amount_per_coin:.2f} USDT")
    
    log(f"💵 [{account_name}] 每个币种金额: {amount_per_coin:.2f} USDT")
    
    # 🔒 立即禁用执行许可（防止重复触发）
    current_rsi = get_current_rsi()
    set_allowed_execution(
        account_id, 
        strategy_key, 
        False, 
        f"{config['name']}已触发，执行中...",
        rsi_value=current_rsi,
        coins=coins
    )
    log(f"🔒 [{account_name}] 已禁用执行许可，防止重复触发")
    
    # 批量下空单
    success_count = 0
    failed_count = 0
    success_coins = []
    failed_coins = []
    
    for symbol in coins:
        log(f"📤 [{account_name}] 正在为 {symbol} 下空单...")
        success, message = place_short_order(account, symbol, amount_per_coin)
        
        if success:
            success_count += 1
            success_coins.append(symbol)
            log(f"✅ [{account_name}] {symbol} 下单成功")
        else:
            failed_count += 1
            failed_coins.append(f"{symbol}({message})")
            log(f"❌ [{account_name}] {symbol} 下单失败: {message}")
        
        time.sleep(0.5)  # 避免频率限制
    
    # 更新触发时间
    last_trigger_times[strategy_key][account_id] = current_time
    
    # 📝 记录执行详情
    record_execution(
        account_id,
        strategy_key,
        coins,
        total_amount,
        amount_per_coin,
        success_count,
        failed_count,
        success_coins,
        failed_coins
    )
    
    # 发送Telegram通知
    message = f"""
🚨 <b>见顶信号自动做空执行</b>

📊 <b>策略</b>: {config['name']}
👤 <b>账户</b>: {account_name}
💰 <b>投入</b>: {total_amount:.2f} USDT
📈 <b>单币</b>: {amount_per_coin:.2f} USDT

✅ <b>成功</b>: {success_count}/{len(coins)}
{f"  {', '.join(success_coins)}" if success_coins else ""}

{f"❌ <b>失败</b>: {failed_count}\\n  {', '.join(failed_coins)}" if failed_coins else ""}

⏰ <b>时间</b>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    send_telegram(message.strip())
    log(f"📊 执行完成: 成功 {success_count}, 失败 {failed_count}")


def check_and_execute():
    """检查条件并执行策略"""
    # 检查市场情绪
    has_top_signal, sentiment_text = check_market_sentiment()
    if not has_top_signal:
        return
    
    log(f"⚠️ 检测到见顶信号: {sentiment_text}")
    
    # 检查RSI
    current_rsi = get_current_rsi()
    if current_rsi is None:
        log(f"❌ 无法获取RSI数据")
        return
    
    log(f"📊 当前RSI: {current_rsi:.2f}")
    
    # 获取所有账户
    accounts = get_accounts()
    if not accounts:
        log(f"❌ 没有找到账户")
        return
    
    log(f"👥 找到 {len(accounts)} 个账户")
    
    # 遍历所有策略
    for strategy_key, config in STRATEGY_CONFIG.items():
        # 检查RSI阈值
        if current_rsi < config['rsi_threshold']:
            log(f"⏭️ RSI {current_rsi:.2f} < {config['rsi_threshold']}, 跳过策略 {config['name']}")
            continue
        
        log(f"✅ RSI {current_rsi:.2f} >= {config['rsi_threshold']}, 检查策略 {config['name']}")
        
        # 为每个账户执行策略
        for account in accounts:
            try:
                execute_strategy(account, strategy_key, config)
            except Exception as e:
                log(f"❌ 账户 {account.get('name', account['id'])} 执行策略异常: {str(e)}")
                import traceback
                traceback.print_exc()


def main():
    """主函数"""
    log("=" * 60)
    log("🚀 见顶信号自动做空监控器启动")
    log("=" * 60)
    log(f"📍 API地址: {API_BASE}")
    log(f"⏱️  检查间隔: {CHECK_INTERVAL}秒")
    log(f"🕐 冷却时间: {COOLDOWN_TIME}秒 ({COOLDOWN_TIME//60}分钟)")
    log(f"📊 策略数量: {len(STRATEGY_CONFIG)}")
    
    for key, config in STRATEGY_CONFIG.items():
        log(f"  - {config['name']}: RSI>{config['rsi_threshold']}, {config['coin_selection']}, {config['balance_percent']*100}%余额, 最大{config['max_per_coin']}U/币")
    
    log("=" * 60)
    
    while True:
        try:
            check_and_execute()
        except Exception as e:
            log(f"❌ 检查异常: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 等待下次检查
        next_check = datetime.now().strftime('%H:%M:%S')
        next_check_time = datetime.now().timestamp() + CHECK_INTERVAL
        next_check = datetime.fromtimestamp(next_check_time).strftime('%H:%M:%S')
        log(f"⏰ 下次检查时间: {next_check} (等待 {CHECK_INTERVAL} 秒)")
        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
