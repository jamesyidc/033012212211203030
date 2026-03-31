#!/usr/bin/env python3
"""
OKX 百分比止盈止损自动监控服务
- 基于持仓保证金的百分比触发止盈/止损
- 按账户分别配置JSONL文件
- 检查JSONL抬头是否允许执行
- 每个持仓只允许执行一次止盈或止损
- 执行记录写入execution JSONL文件
- 平仓完成后发送Telegram通知
"""

import json
import os
import sys
import time
import hmac
import base64
import requests
from datetime import datetime, timezone
from pathlib import Path

# 配置
WEBAPP_DIR = Path(__file__).resolve().parent.parent
SETTINGS_DIR = WEBAPP_DIR / 'data' / 'okx_tpsl_settings'
ACCOUNTS_CONFIG = WEBAPP_DIR / 'data' / 'okx_auto_strategy'

# OKX API
OKX_BASE_URL = 'https://www.okx.com'
CHECK_INTERVAL = 10  # 每10秒检查一次（百分比止盈止损需要更频繁的检查）

# Telegram配置
try:
    sys.path.insert(0, str(WEBAPP_DIR / 'config'))
    from telegram_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
    if TELEGRAM_ENABLED:
        print(f"✅ Telegram已配置")
    else:
        print(f"⚠️  Telegram未配置，通知功能已禁用")
except Exception as e:
    print(f"⚠️  加载Telegram配置失败: {e}")
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


class PercentTPSLMonitor:
    def __init__(self, account_id):
        self.account_id = account_id
        self.settings_file = SETTINGS_DIR / f'{account_id}_percent_tpsl.jsonl'
        self.execution_file = SETTINGS_DIR / f'{account_id}_percent_tpsl_execution.jsonl'
        self.account_config_file = ACCOUNTS_CONFIG / f'{account_id}.json'
    
    def send_telegram(self, message):
        """发送Telegram通知"""
        if not TELEGRAM_ENABLED:
            print(f"[{self.account_id}] [Telegram] 未配置，跳过通知")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"[{self.account_id}] [Telegram] ✅ 通知发送成功")
                return True
            else:
                print(f"[{self.account_id}] [Telegram] ❌ 通知发送失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"[{self.account_id}] [Telegram] ❌ 通知异常: {e}")
            return False
    
    def load_settings(self):
        """加载百分比止盈止损配置（从JSONL抬头）"""
        if not self.settings_file.exists():
            return None
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line:
                    settings = json.loads(first_line)
                    return settings
        except Exception as e:
            print(f"[{self.account_id}] ⚠️  加载配置失败: {e}")
        return None
    
    def load_account_credentials(self):
        """加载账户API凭证"""
        if not self.account_config_file.exists():
            return None
        
        try:
            with open(self.account_config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {
                    'api_key': config.get('apiKey', ''),
                    'secret_key': config.get('apiSecret', ''),
                    'passphrase': config.get('passphrase', '')
                }
        except Exception as e:
            print(f"[{self.account_id}] ⚠️  加载凭证失败: {e}")
        return None
    
    def check_executed(self, inst_id, pos_side, trigger_type):
        """检查是否已经执行过（防止重复执行）"""
        if not self.execution_file.exists():
            return False
        
        try:
            with open(self.execution_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        if (record.get('instId') == inst_id and 
                            record.get('posSide') == pos_side and
                            record.get('triggerType') == trigger_type):
                            print(f"[{self.account_id}] ℹ️  {inst_id} {pos_side} {trigger_type} 已经执行过")
                            return True
        except Exception as e:
            print(f"[{self.account_id}] ⚠️  检查执行记录失败: {e}")
        
        return False
    
    def record_execution(self, inst_id, pos_side, trigger_type, result, margin, unrealized_pnl, threshold_pct, threshold_amount):
        """记录执行结果"""
        try:
            record = {
                'timestamp': datetime.now().isoformat(),
                'account_id': self.account_id,
                'instId': inst_id,
                'posSide': pos_side,
                'triggerType': trigger_type,
                'margin': margin,
                'unrealizedPnl': unrealized_pnl,
                'thresholdPercent': threshold_pct,
                'thresholdAmount': threshold_amount,
                'success': result.get('success', False),
                'message': result.get('message', ''),
                'error': result.get('error', '')
            }
            
            with open(self.execution_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            
            print(f"[{self.account_id}] ✅ 执行记录已保存: {inst_id} {pos_side} {trigger_type}")
        except Exception as e:
            print(f"[{self.account_id}] ⚠️  保存执行记录失败: {e}")
    
    def get_positions(self, credentials):
        """获取当前持仓"""
        try:
            path = '/api/v5/account/positions'
            timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
            message = timestamp + 'GET' + path
            
            mac = hmac.new(
                bytes(credentials['secret_key'], encoding='utf8'),
                bytes(message, encoding='utf-8'),
                digestmod='sha256'
            )
            signature = base64.b64encode(mac.digest()).decode()
            
            headers = {
                'OK-ACCESS-KEY': credentials['api_key'],
                'OK-ACCESS-SIGN': signature,
                'OK-ACCESS-TIMESTAMP': timestamp,
                'OK-ACCESS-PASSPHRASE': credentials['passphrase'],
                'Content-Type': 'application/json'
            }
            
            response = requests.get(OKX_BASE_URL + path, headers=headers, timeout=10)
            result = response.json()
            
            if result.get('code') == '0':
                return result.get('data', [])
            else:
                print(f"[{self.account_id}] ❌ 获取持仓失败: {result.get('msg')}")
                return []
        except Exception as e:
            print(f"[{self.account_id}] ❌ 获取持仓异常: {e}")
            return []
    
    def close_position(self, credentials, inst_id, pos_side):
        """平仓"""
        try:
            path = '/api/v5/trade/close-position'
            timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
            
            body = {
                'instId': inst_id,
                'mgnMode': 'cross',
                'posSide': pos_side
            }
            body_str = json.dumps(body)
            
            message = timestamp + 'POST' + path + body_str
            mac = hmac.new(
                bytes(credentials['secret_key'], encoding='utf8'),
                bytes(message, encoding='utf-8'),
                digestmod='sha256'
            )
            signature = base64.b64encode(mac.digest()).decode()
            
            headers = {
                'OK-ACCESS-KEY': credentials['api_key'],
                'OK-ACCESS-SIGN': signature,
                'OK-ACCESS-TIMESTAMP': timestamp,
                'OK-ACCESS-PASSPHRASE': credentials['passphrase'],
                'Content-Type': 'application/json'
            }
            
            response = requests.post(OKX_BASE_URL + path, headers=headers, json=body, timeout=10)
            result = response.json()
            
            if result.get('code') == '0':
                print(f"[{self.account_id}] ✅ 平仓成功: {inst_id} {pos_side}")
                return {'success': True, 'message': '平仓成功'}
            else:
                error_msg = result.get('msg', '未知错误')
                print(f"[{self.account_id}] ❌ 平仓失败: {error_msg}")
                return {'success': False, 'error': error_msg}
        except Exception as e:
            print(f"[{self.account_id}] ❌ 平仓异常: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_and_execute(self):
        """检查并执行百分比止盈止损"""
        settings = self.load_settings()
        if not settings:
            return
        
        # 检查是否启用
        take_profit_enabled = settings.get('percentTakeProfitEnabled', False)
        stop_loss_enabled = settings.get('percentStopLossEnabled', False)
        
        if not take_profit_enabled and not stop_loss_enabled:
            return
        
        take_profit_pct = settings.get('percentTakeProfitThreshold', 5.0)
        stop_loss_pct = settings.get('percentStopLossThreshold', 7.0)
        
        # 加载API凭证
        credentials = self.load_account_credentials()
        if not credentials or not credentials['api_key']:
            return
        
        # 获取持仓
        positions = self.get_positions(credentials)
        if not positions:
            return
        
        # 计算总保证金和总盈亏
        total_margin = 0
        total_unrealized_pnl = 0
        
        for pos in positions:
            pos_size = float(pos.get('pos', 0))
            if pos_size == 0:
                continue
            
            margin = float(pos.get('margin', 0))
            unrealized_pnl = float(pos.get('upl', 0))
            
            total_margin += margin
            total_unrealized_pnl += unrealized_pnl
        
        if total_margin == 0:
            return
        
        # 计算百分比止盈止损阈值
        take_profit_amount = total_margin * take_profit_pct / 100
        stop_loss_amount = -(total_margin * stop_loss_pct / 100)
        
        print(f"[{self.account_id}] 📊 总保证金: {total_margin:.2f} USDT, 总盈亏: {total_unrealized_pnl:+.2f} USDT")
        print(f"[{self.account_id}] 📈 止盈: {take_profit_pct}% = +{take_profit_amount:.2f} USDT, 启用: {take_profit_enabled}")
        print(f"[{self.account_id}] 📉 止损: {stop_loss_pct}% = {stop_loss_amount:.2f} USDT, 启用: {stop_loss_enabled}")
        
        # 检查是否启用确认模式
        confirm_mode = settings.get('percentConfirmMode', False)
        print(f"[{self.account_id}] 🔔 确认模式: {'已启用' if confirm_mode else '未启用'}")
        
        # 检查止盈
        if take_profit_enabled and total_unrealized_pnl >= take_profit_amount:
            print(f"[{self.account_id}] 🎉 触发百分比止盈！")
            if confirm_mode:
                # 确认模式：创建待确认记录
                self.create_pending_confirmation(positions, 'percent_take_profit', 
                                                total_margin, total_unrealized_pnl, take_profit_pct, take_profit_amount)
            else:
                # 直接执行
                self.execute_close_all(credentials, positions, 'percent_take_profit', 
                                      total_margin, total_unrealized_pnl, take_profit_pct, take_profit_amount)
        
        # 检查止损
        elif stop_loss_enabled and total_unrealized_pnl <= stop_loss_amount:
            print(f"[{self.account_id}] ⚠️ 触发百分比止损！")
            if confirm_mode:
                # 确认模式：创建待确认记录
                self.create_pending_confirmation(positions, 'percent_stop_loss',
                                                total_margin, total_unrealized_pnl, stop_loss_pct, stop_loss_amount)
            else:
                # 直接执行
                self.execute_close_all(credentials, positions, 'percent_stop_loss',
                                      total_margin, total_unrealized_pnl, stop_loss_pct, stop_loss_amount)
        
        # 检查是否有待确认的记录需要执行
        if confirm_mode:
            self.check_confirmed_pending(credentials, positions)
    
    def create_pending_confirmation(self, positions, trigger_type, total_margin, total_unrealized_pnl, threshold_pct, threshold_amount):
        """创建待确认记录"""
        pending_file = SETTINGS_DIR / f'{self.account_id}_percent_tpsl_pending.jsonl'
        
        # 检查是否已有待确认记录
        if pending_file.exists():
            with open(pending_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    last_data = json.loads(lines[-1].strip())
                    if last_data.get('status') == 'pending':
                        print(f"[{self.account_id}] 🔔 已有待确认记录，跳过创建")
                        return
        
        # 创建新的待确认记录
        pending_data = {
            'account_id': self.account_id,
            'status': 'pending',
            'triggerType': trigger_type,
            'thresholdPercent': threshold_pct,
            'thresholdAmount': threshold_amount,
            'totalMargin': total_margin,
            'totalPnl': total_unrealized_pnl,
            'positionCount': len([p for p in positions if float(p.get('pos', 0)) != 0]),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'positions': [
                {
                    'instId': pos.get('instId'),
                    'posSide': pos.get('posSide'),
                    'pos': pos.get('pos')
                }
                for pos in positions if float(pos.get('pos', 0)) != 0
            ]
        }
        
        with open(pending_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(pending_data, ensure_ascii=False) + '\n')
        
        print(f"[{self.account_id}] 🔔 已创建待确认记录")
        
        # 发送Telegram通知
        emoji = "🎉" if trigger_type == 'percent_take_profit' else "⚠️"
        type_name = "百分比止盈" if trigger_type == 'percent_take_profit' else "百分比止损"
        message = f"{emoji} <b>{type_name}触发 - 等待确认</b>\n\n"
        message += f"📊 总保证金: {total_margin:.2f} USDT\n"
        message += f"💰 总盈亏: {total_unrealized_pnl:+.2f} USDT\n"
        message += f"🎯 触发阈值: {threshold_pct}% ({threshold_amount:+.2f} USDT)\n"
        message += f"📝 待平仓: {pending_data['positionCount']} 个持仓\n\n"
        message += f"⚠️ 请登录交易页面确认执行"
        self.send_telegram(message)
    
    def check_confirmed_pending(self, credentials, positions):
        """检查并执行已确认的待确认记录"""
        pending_file = SETTINGS_DIR / f'{self.account_id}_percent_tpsl_pending.jsonl'
        if not pending_file.exists():
            return
        
        with open(pending_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            return
        
        last_data = json.loads(lines[-1].strip())
        if last_data.get('status') == 'confirmed':
            print(f"[{self.account_id}] ✅ 发现已确认的待执行记录，开始执行")
            
            trigger_type = last_data['triggerType']
            total_margin = last_data['totalMargin']
            total_unrealized_pnl = last_data['totalPnl']
            threshold_pct = last_data['thresholdPercent']
            threshold_amount = last_data['thresholdAmount']
            
            # 执行平仓
            self.execute_close_all(credentials, positions, trigger_type,
                                  total_margin, total_unrealized_pnl, threshold_pct, threshold_amount)
            
            # 标记为已执行
            last_data['status'] = 'executed'
            last_data['execute_time'] = datetime.now(timezone.utc).isoformat()
            lines[-1] = json.dumps(last_data, ensure_ascii=False) + '\n'
            
            with open(pending_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
    
    def execute_close_all(self, credentials, positions, trigger_type, total_margin, total_unrealized_pnl, threshold_pct, threshold_amount):
        """执行全部平仓"""
        closed_positions = []
        failed_positions = []
        
        for pos in positions:
            pos_size = float(pos.get('pos', 0))
            if pos_size == 0:
                continue
            
            inst_id = pos.get('instId')
            pos_side = pos.get('posSide')
            
            # 检查是否已执行过
            if self.check_executed(inst_id, pos_side, trigger_type):
                continue
            
            # 执行平仓
            result = self.close_position(credentials, inst_id, pos_side)
            
            # 记录执行
            self.record_execution(inst_id, pos_side, trigger_type, result, 
                                total_margin, total_unrealized_pnl, threshold_pct, threshold_amount)
            
            if result.get('success'):
                closed_positions.append(f"{inst_id} {pos_side}")
            else:
                failed_positions.append(f"{inst_id} {pos_side}: {result.get('error', '未知')}")
        
        # 发送Telegram通知
        if closed_positions or failed_positions:
            if trigger_type == 'percent_take_profit':
                emoji = "🎉"
                type_name = "百分比止盈"
            else:
                emoji = "⚠️"
                type_name = "百分比止损"
            
            message = f"{emoji} <b>{type_name}触发</b>\n\n"
            message += f"📊 总保证金: {total_margin:.2f} USDT\n"
            message += f"💰 总盈亏: {total_unrealized_pnl:+.2f} USDT\n"
            message += f"🎯 触发阈值: {threshold_pct}% ({threshold_amount:+.2f} USDT)\n\n"
            
            if closed_positions:
                message += f"✅ 成功平仓 ({len(closed_positions)}):\n"
                for pos in closed_positions:
                    message += f"  • {pos}\n"
            
            if failed_positions:
                message += f"\n❌ 平仓失败 ({len(failed_positions)}):\n"
                for pos in failed_positions:
                    message += f"  • {pos}\n"
            
            self.send_telegram(message)


def main():
    """主循环"""
    print("="*60)
    print("📊 OKX 百分比止盈止损监控服务启动")
    print("="*60)
    
    # 获取所有账户
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    
    while True:
        try:
            # 查找所有百分比止盈止损配置文件
            print(f"🔍 扫描配置目录: {SETTINGS_DIR}")
            config_files = list(SETTINGS_DIR.glob('*_percent_tpsl.jsonl'))
            print(f"📁 找到 {len(config_files)} 个配置文件")
            
            if not config_files:
                print("⏳ 暂无百分比止盈止损配置，等待30秒...")
                time.sleep(30)
                continue
            
            for config_file in config_files:
                account_id = config_file.stem.replace('_percent_tpsl', '')
                monitor = PercentTPSLMonitor(account_id)
                
                try:
                    monitor.check_and_execute()
                except Exception as e:
                    print(f"[{account_id}] ❌ 监控异常: {e}")
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n⚠️  收到退出信号")
            break
        except Exception as e:
            print(f"❌ 主循环异常: {e}")
            time.sleep(30)


if __name__ == '__main__':
    main()
