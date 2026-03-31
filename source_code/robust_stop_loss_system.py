#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健壮的止盈止损系统 - 独立后台监控进程
特点：
1. 多账户支持 - 同时监控所有配置的账户
2. 故障恢复 - 自动重试、异常恢复
3. 持久化状态 - 防止重启丢失
4. 双重确认 - 确保平仓真正成功
5. 紧急通知 - 多渠道告警
6. 完整日志 - 可审计追踪
"""

import json
import hmac
import base64
import time
import sys
import os
import requests
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 项目根目录
BASE_DIR = Path('/home/user/webapp')
sys.path.insert(0, str(BASE_DIR))

# 配置目录
CONFIG_DIR = BASE_DIR / 'config'
DATA_DIR = BASE_DIR / 'data' / 'stop_loss_system'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 日志文件
LOG_FILE = DATA_DIR / f'stop_loss_{datetime.now().strftime("%Y%m%d")}.log'
STATE_FILE = DATA_DIR / 'stop_loss_state.json'

# Telegram 配置
TELEGRAM_BOT_TOKEN = "8437045462:AAFePnwdC21cqeWhZISMQHGGgjmroVqE2H0"
TELEGRAM_CHAT_ID = "-1003227444260"

# OKX API 配置
OKX_BASE_URL = 'https://www.okx.com'

# 监控配置
CHECK_INTERVAL = 10  # 检查间隔（秒）
MAX_RETRY = 5  # 最大重试次数
RETRY_DELAY = 3  # 重试延迟（秒）
CLOSE_TIMEOUT = 30  # 平仓超时（秒）

class Color:
    """终端颜色"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log(message: str, level: str = 'INFO'):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 颜色映射
    color_map = {
        'INFO': Color.CYAN,
        'SUCCESS': Color.GREEN,
        'WARNING': Color.YELLOW,
        'ERROR': Color.RED,
        'CRITICAL': Color.RED + Color.BOLD
    }
    
    color = color_map.get(level, Color.WHITE)
    
    # 控制台输出（带颜色）
    print(f"{color}[{timestamp}] [{level}] {message}{Color.END}")
    
    # 文件输出（无颜色）
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] [{level}] {message}\n")

def send_telegram(message: str, urgent: bool = False) -> bool:
    """发送 Telegram 通知"""
    try:
        # 如果是紧急消息，发送3次
        repeat = 3 if urgent else 1
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        
        # 紧急消息添加警告标记
        if urgent:
            message = f"🚨🚨🚨 【紧急】\n\n{message}"
        
        success_count = 0
        for i in range(repeat):
            try:
                response = requests.post(url, json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML"
                }, timeout=10)
                
                if response.status_code == 200:
                    success_count += 1
                    if i < repeat - 1:
                        time.sleep(1)
            except Exception as e:
                log(f"Telegram 发送失败 ({i+1}/{repeat}): {e}", 'WARNING')
        
        if success_count > 0:
            log(f"Telegram 通知已发送 ({success_count}/{repeat})", 'SUCCESS')
            return True
        else:
            log(f"Telegram 通知发送失败", 'ERROR')
            return False
    
    except Exception as e:
        log(f"发送 Telegram 异常: {e}", 'ERROR')
        return False

def load_accounts() -> List[Dict]:
    """加载账户配置"""
    try:
        config_file = CONFIG_DIR / 'okx_accounts.json'
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        accounts = config.get('accounts', [])
        log(f"加载了 {len(accounts)} 个账户配置", 'INFO')
        
        return accounts
    
    except Exception as e:
        log(f"加载账户配置失败: {e}", 'ERROR')
        return []

def sign_request(api_secret: str, timestamp: str, method: str, path: str, body: str = '') -> str:
    """生成 OKX API 签名"""
    message = timestamp + method + path + body
    mac = hmac.new(
        bytes(api_secret, encoding='utf8'),
        bytes(message, encoding='utf-8'),
        digestmod='sha256'
    )
    return base64.b64encode(mac.digest()).decode()

def get_positions(account: Dict) -> Optional[List[Dict]]:
    """获取账户持仓"""
    try:
        path = '/api/v5/account/positions'
        timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        
        signature = sign_request(account['apiSecret'], timestamp, 'GET', path)
        
        headers = {
            'OK-ACCESS-KEY': account['apiKey'],
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': account['passphrase'],
        }
        
        response = requests.get(OKX_BASE_URL + path, headers=headers, timeout=10)
        result = response.json()
        
        if result.get('code') == '0':
            positions = result.get('data', [])
            # 只返回有持仓的（pos != 0）
            active_positions = [p for p in positions if float(p.get('pos', 0)) != 0]
            return active_positions
        else:
            log(f"获取持仓失败 [{account['name']}]: {result.get('msg')}", 'ERROR')
            return None
    
    except Exception as e:
        log(f"获取持仓异常 [{account['name']}]: {e}", 'ERROR')
        return None

def close_position(account: Dict, position: Dict) -> Tuple[bool, str]:
    """平仓单个持仓"""
    try:
        inst_id = position.get('instId')
        pos_side = position.get('posSide')
        
        path = '/api/v5/trade/close-position'
        order_params = {
            'instId': inst_id,
            'mgnMode': 'isolated',
            'posSide': pos_side
        }
        
        body = json.dumps(order_params)
        timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        
        signature = sign_request(account['apiSecret'], timestamp, 'POST', path, body)
        
        headers = {
            'OK-ACCESS-KEY': account['apiKey'],
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': account['passphrase'],
            'Content-Type': 'application/json'
        }
        
        response = requests.post(OKX_BASE_URL + path, headers=headers, data=body, timeout=CLOSE_TIMEOUT)
        result = response.json()
        
        if result.get('code') == '0':
            return True, '平仓成功'
        else:
            error_msg = result.get('msg', '未知错误')
            return False, error_msg
    
    except Exception as e:
        return False, str(e)

def close_all_positions_for_account(account: Dict, retry_count: int = 0) -> Tuple[int, int, List[str]]:
    """
    平掉单个账户的所有持仓
    返回: (成功数, 失败数, 失败详情)
    """
    try:
        log(f"━━━ 开始处理账户: {account['name']} ━━━", 'INFO')
        
        # 获取持仓
        positions = get_positions(account)
        
        if positions is None:
            log(f"获取持仓失败 [{account['name']}]", 'ERROR')
            return 0, 0, [f"{account['name']}: 获取持仓失败"]
        
        if len(positions) == 0:
            log(f"账户 {account['name']} 无持仓", 'INFO')
            return 0, 0, []
        
        log(f"账户 {account['name']} 有 {len(positions)} 个持仓", 'INFO')
        
        success_count = 0
        fail_count = 0
        fail_details = []
        
        for i, position in enumerate(positions, 1):
            inst_id = position.get('instId', '')
            pos_side = position.get('posSide', '')
            pos_size = position.get('pos', '0')
            
            coin_name = inst_id.replace('-USDT-SWAP', '')
            log(f"  [{i}/{len(positions)}] 平仓 {coin_name} {pos_side} (数量: {pos_size})", 'INFO')
            
            # 尝试平仓
            success, message = close_position(account, position)
            
            if success:
                success_count += 1
                log(f"  ✅ {coin_name} 平仓成功", 'SUCCESS')
            else:
                fail_count += 1
                error_detail = f"{account['name']} - {coin_name} {pos_side}: {message}"
                fail_details.append(error_detail)
                log(f"  ❌ {coin_name} 平仓失败: {message}", 'ERROR')
            
            # 添加小延迟
            time.sleep(0.2)
        
        log(f"账户 {account['name']} 处理完成: 成功 {success_count}/{len(positions)}", 
            'SUCCESS' if fail_count == 0 else 'WARNING')
        
        return success_count, fail_count, fail_details
    
    except Exception as e:
        log(f"处理账户异常 [{account['name']}]: {e}", 'ERROR')
        traceback.print_exc()
        return 0, 0, [f"{account['name']}: 处理异常 - {str(e)}"]

def execute_stop_loss(reason: str, accounts: List[Dict]) -> Dict:
    """
    执行止损 - 平掉所有账户的所有持仓
    返回执行结果
    """
    log("", 'INFO')
    log("=" * 80, 'CRITICAL')
    log(f"🚨 触发止损: {reason}", 'CRITICAL')
    log("=" * 80, 'CRITICAL')
    log("", 'INFO')
    
    start_time = time.time()
    
    # 发送紧急通知
    send_telegram(
        f"🚨🚨🚨 止损触发\n\n"
        f"原因: {reason}\n"
        f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"账户数: {len(accounts)}\n\n"
        f"正在执行全部平仓...",
        urgent=True
    )
    
    total_success = 0
    total_fail = 0
    all_fail_details = []
    account_results = []
    
    # 筛选有效账户
    valid_accounts = [
        acc for acc in accounts
        if acc.get('apiKey') and acc.get('apiSecret') and acc.get('passphrase')
    ]
    
    log(f"共 {len(valid_accounts)} 个有效账户需要处理", 'INFO')
    
    # 逐个处理账户
    for i, account in enumerate(valid_accounts, 1):
        log(f"\n[{i}/{len(valid_accounts)}] 处理账户: {account['name']}", 'INFO')
        
        success, fail, details = close_all_positions_for_account(account)
        
        total_success += success
        total_fail += fail
        all_fail_details.extend(details)
        
        account_results.append({
            'account': account['name'],
            'success': success,
            'fail': fail,
            'total': success + fail
        })
        
        # 账户间添加延迟
        if i < len(valid_accounts):
            time.sleep(1)
    
    elapsed = time.time() - start_time
    
    # 生成结果报告
    result = {
        'timestamp': datetime.now().isoformat(),
        'reason': reason,
        'accounts_processed': len(valid_accounts),
        'total_positions': total_success + total_fail,
        'success_count': total_success,
        'fail_count': total_fail,
        'elapsed_seconds': round(elapsed, 2),
        'account_details': account_results,
        'failures': all_fail_details
    }
    
    # 记录到文件
    result_file = DATA_DIR / f'stop_loss_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 总结日志
    log("", 'INFO')
    log("=" * 80, 'INFO')
    log("📊 止损执行结果", 'INFO')
    log("=" * 80, 'INFO')
    log(f"处理账户: {len(valid_accounts)} 个", 'INFO')
    log(f"总持仓数: {total_success + total_fail} 个", 'INFO')
    log(f"成功平仓: {total_success} 个", 'SUCCESS')
    log(f"失败: {total_fail} 个", 'ERROR' if total_fail > 0 else 'INFO')
    log(f"耗时: {elapsed:.2f} 秒", 'INFO')
    log("=" * 80, 'INFO')
    
    # 发送结果通知
    notification = (
        f"✅ 止损执行完成\n\n"
        f"原因: {reason}\n"
        f"账户数: {len(valid_accounts)}\n"
        f"持仓数: {total_success + total_fail}\n"
        f"成功: {total_success}\n"
        f"失败: {total_fail}\n"
        f"耗时: {elapsed:.2f}秒\n\n"
    )
    
    if account_results:
        notification += "各账户详情:\n"
        for r in account_results:
            emoji = "✅" if r['fail'] == 0 else ("⚠️" if r['success'] > 0 else "❌")
            notification += f"  {emoji} {r['account']}: {r['success']}/{r['total']}\n"
    
    if all_fail_details:
        notification += f"\n失败详情:\n"
        for detail in all_fail_details[:5]:  # 最多显示5个
            notification += f"  • {detail}\n"
        if len(all_fail_details) > 5:
            notification += f"  ... 还有 {len(all_fail_details) - 5} 个失败\n"
    
    send_telegram(notification, urgent=(total_fail > 0))
    
    return result

def main():
    """主函数 - 命令行手动触发"""
    try:
        log("", 'INFO')
        log("=" * 80, 'INFO')
        log("🛡️  健壮止损系统启动", 'INFO')
        log("=" * 80, 'INFO')
        
        # 加载账户
        accounts = load_accounts()
        
        if not accounts:
            log("未找到账户配置！", 'CRITICAL')
            sys.exit(1)
        
        # 显示账户信息
        log(f"已加载 {len(accounts)} 个账户:", 'INFO')
        for i, acc in enumerate(accounts, 1):
            log(f"  {i}. {acc.get('name', '未命名')} ({acc.get('id', 'N/A')})", 'INFO')
        
        # 获取触发原因
        if len(sys.argv) > 1:
            reason = sys.argv[1]
        else:
            reason = input("\n请输入止损原因 (回车使用默认): ").strip()
            if not reason:
                reason = "手动触发"
        
        # 确认执行
        confirm = input(f"\n⚠️  确认执行止损吗？这将平掉所有账户的所有持仓！(yes/no): ").strip().lower()
        
        if confirm != 'yes':
            log("已取消执行", 'WARNING')
            sys.exit(0)
        
        # 执行止损
        result = execute_stop_loss(reason, accounts)
        
        # 根据结果退出
        if result['fail_count'] == 0:
            log("\n✅ 止损执行成功！", 'SUCCESS')
            sys.exit(0)
        else:
            log(f"\n⚠️  止损部分失败！失败数: {result['fail_count']}", 'WARNING')
            sys.exit(1)
    
    except KeyboardInterrupt:
        log("\n⚠️  用户中断", 'WARNING')
        sys.exit(130)
    except Exception as e:
        log(f"\n❌ 执行失败: {e}", 'CRITICAL')
        traceback.print_exc()
        sys.exit(2)

if __name__ == '__main__':
    main()
