#!/usr/bin/env python3
"""
5分钟涨速止盈监控器 v2.0 - 内置API凭证版本
每30秒检查一次5分钟涨速，触发条件时执行平仓
"""
import sys
import os
import time
import json
import requests
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, '/home/user/webapp')

# 配置
CHECK_INTERVAL = 30  # 检查间隔(秒)
API_BASE_URL = 'http://localhost:9002'

# 📋 账户配置 - 直接内置API凭证（更可靠）
ACCOUNTS = {
    'account_main': {
        'name': '主账户',
        'apiKey': 'd6b272da-b59e-4ca3-97bd-663102f981b3',
        'apiSecret': '5D76ACDE6D74CF07842661385E12C61E',
        'passphrase': 'Tencent@123'
    },
    'account_fangfang12': {
        'name': 'Fangfang12',
        'apiKey': 'e5867a9a-93b7-476f-81ce-093c3aacae0d',
        'apiSecret': '4624EE63A9BF3F84250AC71C9A37F47D',
        'passphrase': 'Tencent@123'
    },
    'account_anchor': {
        'name': '锚点账号',
        'apiKey': '0b05a729-40eb-4809-b3eb-eb2de75b7e9e',
        'apiSecret': '4E4DA8BE3B18D01AA07185A006BF9F8E',
        'passphrase': 'Tencent@123'
    },
    'account_poit': {
        'name': 'POIT',
        'apiKey': '8650e46c-059b-431d-93cf-55f8c79babdb',
        'apiSecret': '4C2BD2AC6A08615EA7F36A6251857FCE',
        'passphrase': 'Wu666666.'
    },
    'account_poit_main': {
        'name': 'POIT主账户',
        'apiKey': '8650e46c-059b-431d-93cf-55f8c79babdb',
        'apiSecret': '4C2BD2AC6A08615EA7F36A6251857FCE',
        'passphrase': 'Wu666666.'
    },
    'account_dadanini': {
        'name': 'Dadanini',
        'apiKey': '1463198a-fad0-46ac-9ad8-2a386461782c',
        'apiSecret': '1D112283B7456290056C253C56E9F3A6',
        'passphrase': 'Tencent@123'
    }
}

# Telegram配置
TG_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TG_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

def log(message):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

def send_telegram(message):
    """发送Telegram通知"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return False
    
    try:
        url = f'https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage'
        data = {
            'chat_id': TG_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=data, timeout=10)
        return response.json().get('ok', False)
    except Exception as e:
        log(f"❌ TG发送失败: {e}")
        return False

def get_velocity_config(account_id):
    """获取账户的涨速配置"""
    try:
        response = requests.get(
            f'{API_BASE_URL}/api/okx-trading/velocity-takeprofit/config/{account_id}',
            timeout=5
        )
        data = response.json()
        if data.get('success'):
            return data.get('config', {})  # 返回config字段
        return None
    except Exception as e:
        log(f"❌ [{account_id}] 获取配置失败: {e}")
        return None

def get_current_velocity():
    """获取当前5分钟涨速"""
    try:
        response = requests.get(
            f'{API_BASE_URL}/api/coin-change-tracker/velocity-history?limit=1',
            timeout=5
        )
        data = response.json()
        if data.get('success') and data.get('data'):
            latest = data['data'][0]
            return float(latest.get('velocity_5min', 0))
        return 0.0
    except Exception as e:
        log(f"❌ 获取涨速失败: {e}")
        return 0.0

def get_positions(account_id):
    """获取账户持仓"""
    if account_id not in ACCOUNTS:
        log(f"❌ [{account_id}] 账户不存在")
        return []
    
    account = ACCOUNTS[account_id]
    
    try:
        response = requests.post(
            f'{API_BASE_URL}/api/okx-trading/positions',
            json={
                'apiKey': account['apiKey'],
                'apiSecret': account['apiSecret'],
                'passphrase': account['passphrase']
            },
            timeout=10
        )
        
        data = response.json()
        if data.get('success'):
            return data.get('data', [])
        else:
            log(f"❌ [{account_id}] 获取持仓失败: {data.get('error', '未知错误')}")
        return []
    except Exception as e:
        log(f"❌ [{account_id}] 获取持仓异常: {e}")
        return []

def close_positions(account_id, positions, side):
    """平仓"""
    if account_id not in ACCOUNTS:
        log(f"❌ [{account_id}] 账户不存在")
        return False
    
    account = ACCOUNTS[account_id]
    log(f"🔧 [{account['name']}] 开始平仓 {len(positions)} 个 {side} 持仓")
    success_count = 0
    total_count = 0
    
    try:
        for pos in positions:
            if pos.get('posSide') != side:
                continue
            
            total_count += 1
            inst_id = pos.get('instId')
            pos_size = abs(float(pos.get('pos', 0)))
            
            if pos_size == 0:
                continue
            
            log(f"📤 [{account['name']}] 平仓 {inst_id} {side} {pos_size}张")
            
            response = requests.post(
                f'{API_BASE_URL}/api/okx-trading/close-position',
                json={
                    'apiKey': account['apiKey'],
                    'apiSecret': account['apiSecret'],
                    'passphrase': account['passphrase'],
                    'instId': inst_id,
                    'posSide': side,
                    'closeSize': str(pos_size)
                },
                timeout=10
            )
            
            result = response.json()
            if result.get('success'):
                log(f"✅ [{account['name']}] {inst_id} 平仓成功")
                success_count += 1
            else:
                log(f"❌ [{account['name']}] {inst_id} 平仓失败: {result.get('message')}")
        
        log(f"📊 [{account['name']}] 平仓完成: 成功 {success_count}/{total_count}")
        return success_count > 0
    except Exception as e:
        log(f"❌ [{account['name']}] 平仓异常: {e}")
        return False

def check_account(account_id):
    """检查单个账户"""
    if account_id not in ACCOUNTS:
        return
    
    account = ACCOUNTS[account_id]
    
    # 获取配置
    config = get_velocity_config(account_id)
    if not config:
        return
    
    long_enabled = config.get('long_enabled', False)
    short_enabled = config.get('short_enabled', False)
    long_permission = config.get('long_permission', False)
    short_permission = config.get('short_permission', False)
    max_threshold = float(config.get('max_velocity_threshold', 15.0))
    min_threshold = float(config.get('min_velocity_threshold', -15.0))
    
    # 获取当前涨速
    current_velocity = get_current_velocity()
    
    # 打印状态
    log(f"📊 [{account['name']}] 当前涨速: {current_velocity:.2f}% | "
        f"做多阈值: {max_threshold:.1f}% (启用:{long_enabled}, 权限:{long_permission}) | "
        f"做空阈值: {min_threshold:.1f}% (启用:{short_enabled}, 权限:{short_permission})")
    
    # 检查做多止盈
    if long_enabled and long_permission and current_velocity >= max_threshold:
        log(f"🎯 [{account['name']}] 触发做多止盈: {current_velocity:.2f}% >= {max_threshold:.1f}%")
        
        # 获取持仓
        positions = get_positions(account_id)
        long_positions = [p for p in positions if p.get('posSide') == 'long']
        
        if long_positions:
            log(f"📋 [{account['name']}] 发现 {len(long_positions)} 个多单持仓")
            
            # 平仓
            success = close_positions(account_id, long_positions, 'long')
            
            if success:
                # 发送TG通知
                message = (
                    f"🚀 <b>涨速止盈平仓</b>\n\n"
                    f"交易账户: {account['name']}\n"
                    f"当前涨速: +{current_velocity:.2f}%\n"
                    f"触发阈值: +{max_threshold:.1f}%\n"
                    f"平仓方向: 多单\n"
                    f"平仓数量: {len(long_positions)}个"
                )
                send_telegram(message)
        else:
            log(f"⚠️ [{account['name']}] 没有多单持仓，跳过")
    
    # 检查做空止盈
    if short_enabled and short_permission and current_velocity <= min_threshold:
        log(f"🎯 [{account['name']}] 触发做空止盈: {current_velocity:.2f}% <= {min_threshold:.1f}%")
        
        # 获取持仓
        positions = get_positions(account_id)
        short_positions = [p for p in positions if p.get('posSide') == 'short']
        
        if short_positions:
            log(f"📋 [{account['name']}] 发现 {len(short_positions)} 个空单持仓")
            
            # 平仓
            success = close_positions(account_id, short_positions, 'short')
            
            if success:
                # 发送TG通知
                message = (
                    f"🔻 <b>跌速止盈平仓</b>\n\n"
                    f"交易账户: {account['name']}\n"
                    f"当前跌速: {current_velocity:.2f}%\n"
                    f"触发阈值: {min_threshold:.1f}%\n"
                    f"平仓方向: 空单\n"
                    f"平仓数量: {len(short_positions)}个"
                )
                send_telegram(message)
        else:
            log(f"⚠️ [{account['name']}] 没有空单持仓，跳过")

def main():
    """主函数"""
    log("🚀 5分钟涨速止盈监控器启动 v2.0 (内置API凭证)")
    log(f"📋 监控账户 ({len(ACCOUNTS)}个):")
    for account_id, account in ACCOUNTS.items():
        log(f"   - {account_id}: {account['name']}")
    log(f"⏰ 检查间隔: {CHECK_INTERVAL}秒")
    log("=" * 60)
    
    try:
        while True:
            log("")
            log("🔄 开始检查...")
            
            # 检查所有账户
            for account_id in ACCOUNTS.keys():
                check_account(account_id)
            
            log("")
            log(f"⏰ 等待 {CHECK_INTERVAL} 秒后继续...")
            time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        log("")
        log("👋 监控器已停止")

if __name__ == '__main__':
    main()
