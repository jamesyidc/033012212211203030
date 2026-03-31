#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSI止盈后台监控器
独立于前端页面运行，每60秒检查一次所有账户的RSI止盈条件
当条件满足时自动执行平仓操作
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

# API基础URL
API_BASE = 'http://localhost:9002'

# 配置
CHECK_INTERVAL = 60  # 检查间隔（秒）
RSI_CHECK_COOLDOWN = 300000  # 冷却时间（毫秒）= 5分钟

# 存储上次检查的RSI值和时间（防止重复触发）
last_trigger_times = {}
last_rsi_values = {}


def log(message):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)


def get_accounts():
    """获取所有账户列表"""
    try:
        response = requests.get(f"{API_BASE}/api/okx-accounts/list-with-credentials", timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('success'):
            accounts = result.get('accounts', [])
            log(f"✅ 获取到 {len(accounts)} 个账户")
            return accounts
        else:
            log(f"❌ 获取账户列表失败: {result.get('error', '未知错误')}")
            return []
    except Exception as e:
        log(f"❌ 获取账户列表异常: {str(e)}")
        return []


def get_current_rsi():
    """获取当前RSI总和"""
    try:
        response = requests.get(f"{API_BASE}/api/coin-change-tracker/latest", timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('success') and result.get('data'):
            total_rsi = result['data'].get('total_rsi', 0)
            return total_rsi
        else:
            log(f"⚠️ 获取RSI数据失败")
            return None
    except Exception as e:
        log(f"❌ 获取RSI数据异常: {str(e)}")
        return None


def get_tpsl_settings(account_id):
    """获取账户的止盈止损设置"""
    try:
        response = requests.get(f"{API_BASE}/api/okx-trading/tpsl-settings/{account_id}", timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('success'):
            return result.get('settings', {})
        else:
            return {}
    except Exception as e:
        log(f"❌ 获取账户 {account_id} 设置异常: {str(e)}")
        return {}


def check_allowed_takeprofit(account_id, pos_side='all'):
    """检查执行许可
    Args:
        account_id: 账户ID
        pos_side: 持仓方向 'long', 'short', 'all'
    """
    try:
        url = f"{API_BASE}/api/okx-trading/check-allowed-takeprofit/{account_id}"
        if pos_side != 'all':
            url += f"?posSide={pos_side}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        return result.get('success', False) and result.get('allowed', False)
    except Exception as e:
        log(f"❌ 检查账户 {account_id} ({pos_side}) 执行许可异常: {str(e)}")
        return False


def set_allowed_takeprofit(account_id, allowed, reason, rsi_value, pos_side='all'):
    """设置执行许可
    Args:
        account_id: 账户ID
        allowed: 是否允许
        reason: 原因
        rsi_value: RSI值
        pos_side: 持仓方向 'long', 'short', 'all'
    """
    try:
        data = {
            'allowed': allowed,
            'reason': reason,
            'takeprofitType': 'rsi',
            'rsiValue': rsi_value,
            'posSide': pos_side
        }
        response = requests.post(
            f"{API_BASE}/api/okx-trading/set-allowed-takeprofit/{account_id}",
            json=data,
            timeout=10
        )
        response.raise_for_status()
        return response.json().get('success', False)
    except Exception as e:
        log(f"❌ 设置账户 {account_id} ({pos_side}) 执行许可异常: {str(e)}")
        return False


def close_all_positions(account, pos_side='all'):
    """执行一键平仓
    Args:
        account: 账户信息
        pos_side: 持仓方向 'long', 'short', 'all'
    """
    try:
        data = {
            'apiKey': account['apiKey'],
            'apiSecret': account['apiSecret'],
            'passphrase': account['passphrase'],
            'accountId': account['id'],
            'posSide': pos_side  # 添加持仓方向过滤
        }
        response = requests.post(
            f"{API_BASE}/api/okx-trading/close-all-positions",
            json=data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log(f"❌ 账户 {account['name']} 平仓请求异常: {str(e)}")
        return {'success': False, 'error': str(e)}


def send_telegram_message(message):
    """发送Telegram通知"""
    try:
        response = requests.post(
            f"{API_BASE}/api/telegram/send-message",
            json={'message': message},
            timeout=10
        )
        response.raise_for_status()
        return response.json().get('success', False)
    except Exception as e:
        log(f"❌ 发送Telegram通知异常: {str(e)}")
        return False


def check_rsi_takeprofit():
    """检查所有账户的RSI止盈条件 (包括多单和空单)"""
    log("=" * 60)
    log("🔍 开始RSI止盈检查...")
    
    # 获取当前RSI
    total_rsi = get_current_rsi()
    if total_rsi is None:
        log("⚠️ 无法获取RSI数据，跳过本次检查")
        return
    
    log(f"📊 当前RSI总和: {total_rsi:.2f}")
    
    # 获取所有账户
    accounts = get_accounts()
    if not accounts:
        log("⚠️ 没有可用账户，跳过本次检查")
        return
    
    # 遍历所有账户
    for account in accounts:
        account_id = account['id']
        account_name = account['name']
        
        try:
            # 获取止盈止损设置
            settings = get_tpsl_settings(account_id)
            
            # ===== 1. 检查多单RSI止盈 =====
            rsi_long_enabled = settings.get('rsiTakeProfitEnabled', False)
            rsi_long_threshold = float(settings.get('rsiTakeProfitThreshold', 1900))
            
            if rsi_long_enabled:
                log(f"🎯 [{account_name}] RSI多单监控 - 当前: {total_rsi:.2f}, 阈值: {rsi_long_threshold}")
                
                # 检查多单执行许可（独立）
                allowed = check_allowed_takeprofit(account_id, pos_side='long')
                if allowed and total_rsi >= rsi_long_threshold:
                    # 防止短时间内重复触发
                    now = int(time.time() * 1000)
                    last_trigger = last_trigger_times.get(f"{account_id}_long", 0)
                    last_value = last_rsi_values.get(f"{account_id}_long", 0)
                    
                    if last_value != total_rsi and (now - last_trigger) >= RSI_CHECK_COOLDOWN:
                        # 更新触发记录
                        last_trigger_times[f"{account_id}_long"] = now
                        last_rsi_values[f"{account_id}_long"] = total_rsi
                        
                        log(f"🚨 [{account_name}] RSI多单止盈触发！RSI={total_rsi:.2f} >= {rsi_long_threshold}")
                        
                        # 立即禁用多单执行许可
                        set_allowed_takeprofit(
                            account_id,
                            False,
                            f"RSI多单止盈已触发，RSI={total_rsi:.2f}",
                            total_rsi,
                            pos_side='long'
                        )
                        
                        # 执行多单平仓
                        log(f"🔄 [{account_name}] 开始平掉所有多单...")
                        close_result = close_all_positions(account, pos_side='long')
                        
                        # 构建通知消息
                        message = f"🎯 RSI多单止盈触发（后台监控）\n账户：{account_name}\nRSI之和：{total_rsi:.2f}\n阈值：{rsi_long_threshold}\n\n"
                        
                        if close_result.get('success'):
                            total_pos = close_result.get('totalPositions', 0)
                            closed = close_result.get('closedCount', 0)
                            failed = close_result.get('failedCount', 0)
                            
                            message += f"✅ 多单平仓完成\n总持仓：{total_pos} 个\n成功平仓：{closed} 个\n失败：{failed} 个"
                            log(f"✅ [{account_name}] 多单平仓完成 - 成功: {closed}/{total_pos}")
                        else:
                            error_msg = close_result.get('message') or close_result.get('error', '未知错误')
                            message += f"❌ 平仓失败：{error_msg}"
                            log(f"❌ [{account_name}] 多单平仓失败: {error_msg}")
                        
                        # 发送Telegram通知
                        log(f"📱 发送Telegram通知...")
                        send_telegram_message(message)
                        log(f"✅ [{account_name}] RSI多单止盈处理完成")
                    else:
                        log(f"⏳ [{account_name}] 多单冷却期内或相同RSI值，跳过")
                elif not allowed:
                    log(f"⏸️ [{account_name}] 多单执行许可已禁用，跳过")
            else:
                log(f"⏭️ [{account_name}] RSI多单止盈未启用")
            
            # ===== 2. 检查空单RSI止盈 =====
            rsi_short_enabled = settings.get('rsiShortTakeProfitEnabled', False)
            rsi_short_threshold = float(settings.get('rsiShortTakeProfitThreshold', 810))
            
            if rsi_short_enabled:
                log(f"📉 [{account_name}] RSI空单监控 - 当前: {total_rsi:.2f}, 阈值: {rsi_short_threshold}")
                
                # 检查空单执行许可（独立）
                allowed_short = check_allowed_takeprofit(account_id, pos_side='short')
                
                if allowed_short and total_rsi <= rsi_short_threshold:
                    # 防止短时间内重复触发
                    now = int(time.time() * 1000)
                    last_trigger = last_trigger_times.get(f"{account_id}_short", 0)
                    last_value = last_rsi_values.get(f"{account_id}_short", 0)
                    
                    if last_value != total_rsi and (now - last_trigger) >= RSI_CHECK_COOLDOWN:
                        # 更新触发记录
                        last_trigger_times[f"{account_id}_short"] = now
                        last_rsi_values[f"{account_id}_short"] = total_rsi
                        
                        log(f"🚨 [{account_name}] RSI空单止盈触发！RSI={total_rsi:.2f} <= {rsi_short_threshold}")
                        
                        # 立即禁用空单执行许可（独立）
                        set_allowed_takeprofit(
                            account_id,
                            False,
                            f"RSI空单止盈已触发，RSI={total_rsi:.2f}",
                            total_rsi,
                            pos_side='short'
                        )
                        
                        # 执行空单平仓
                        log(f"🔄 [{account_name}] 开始平掉所有空单...")
                        close_result = close_all_positions(account, pos_side='short')
                        
                        # 构建通知消息
                        message = f"📉 RSI空单止盈触发（后台监控）\n账户：{account_name}\nRSI之和：{total_rsi:.2f}\n阈值：{rsi_short_threshold}\n\n"
                        
                        if close_result.get('success'):
                            total_pos = close_result.get('totalPositions', 0)
                            closed = close_result.get('closedCount', 0)
                            failed = close_result.get('failedCount', 0)
                            
                            message += f"✅ 空单平仓完成\n总持仓：{total_pos} 个\n成功平仓：{closed} 个\n失败：{failed} 个"
                            log(f"✅ [{account_name}] 空单平仓完成 - 成功: {closed}/{total_pos}")
                        else:
                            error_msg = close_result.get('message') or close_result.get('error', '未知错误')
                            message += f"❌ 平仓失败：{error_msg}"
                            log(f"❌ [{account_name}] 空单平仓失败: {error_msg}")
                        
                        # 发送Telegram通知
                        log(f"📱 发送Telegram通知...")
                        send_telegram_message(message)
                        log(f"✅ [{account_name}] RSI空单止盈处理完成")
                    else:
                        log(f"⏳ [{account_name}] 空单冷却期内或相同RSI值，跳过")
                elif not allowed_short:
                    log(f"⏸️ [{account_name}] 空单执行许可已禁用，跳过")
            else:
                log(f"⏭️ [{account_name}] RSI空单止盈未启用")
                
        except Exception as e:
            log(f"❌ [{account_name}] 检查失败: {str(e)}")
            continue
    
    log("✅ RSI止盈检查完成")


def main():
    """主函数"""
    log("=" * 60)
    log("🚀 RSI止盈后台监控器启动")
    log(f"📍 检查间隔: {CHECK_INTERVAL}秒")
    log(f"⏱️ 冷却时间: {RSI_CHECK_COOLDOWN/1000/60:.0f}分钟")
    log(f"🌐 API地址: {API_BASE}")
    log("=" * 60)
    
    # 首次检查
    check_rsi_takeprofit()
    
    # 定时检查
    while True:
        try:
            # 计算到下一个整分钟的等待时间
            now = datetime.now()
            next_minute = (now.minute + 1) % 60
            next_check = now.replace(second=0, microsecond=0)
            if next_minute == 0:
                next_check = next_check.replace(hour=(now.hour + 1) % 24, minute=0)
            else:
                next_check = next_check.replace(minute=next_minute)
            
            wait_seconds = (next_check - now).total_seconds()
            
            log(f"⏰ 下次检查时间: {next_check.strftime('%H:%M:%S')}, 等待 {wait_seconds:.0f} 秒...")
            time.sleep(wait_seconds)
            
            # 执行检查
            check_rsi_takeprofit()
            
        except KeyboardInterrupt:
            log("⚠️ 收到停止信号，退出...")
            break
        except Exception as e:
            log(f"❌ 主循环异常: {str(e)}")
            log(f"⏰ 等待 {CHECK_INTERVAL} 秒后重试...")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
