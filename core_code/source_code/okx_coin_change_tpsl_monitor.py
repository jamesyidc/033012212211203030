#!/usr/bin/env python3
"""
OKX 27币涨跌幅之和止盈监控服务
- 基于27币涨跌幅之和触发止盈
- 空单止盈：跌破设定阈值时止盈（total_change < -threshold）
- 多单止盈：突破设定阈值时止盈（total_change > threshold）
- 按账户分别配置JSONL文件
- 检查JSONL抬头是否允许执行
- 每个持仓只允许执行一次止盈
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
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 配置
WEBAPP_DIR = Path(__file__).resolve().parent.parent
SETTINGS_DIR = WEBAPP_DIR / 'data' / 'okx_tpsl_settings'
ACCOUNTS_CONFIG = WEBAPP_DIR / 'data' / 'okx_auto_strategy'
COIN_CHANGE_DIR = WEBAPP_DIR / 'data' / 'coin_change_tracker'

# OKX API
OKX_BASE_URL = 'https://www.okx.com'
CHECK_INTERVAL = 30  # 每30秒检查一次

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


class CoinChangeTakeProfitMonitor:
    def __init__(self, account_id):
        self.account_id = account_id
        self.settings_file = SETTINGS_DIR / f'{account_id}_coin_change_tpsl.jsonl'
        self.execution_file = SETTINGS_DIR / f'{account_id}_coin_change_tpsl_execution.jsonl'
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
        """加载27币涨跌幅止盈配置（从JSONL抬头）"""
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
    
    def get_latest_coin_change(self):
        """获取最新的27币涨跌幅之和"""
        try:
            # 获取今天日期（北京时间）
            beijing_tz = timezone(timedelta(hours=8))
            beijing_date = datetime.now(timezone.utc).astimezone(beijing_tz).strftime('%Y%m%d')
            coin_change_file = COIN_CHANGE_DIR / f'coin_change_{beijing_date}.jsonl'
            
            if not coin_change_file.exists():
                print(f"[{self.account_id}] ⚠️  今日币种涨跌数据文件不存在: {coin_change_file}")
                return None
            
            # 读取最后一行
            with open(coin_change_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if last_line:
                        data = json.loads(last_line)
                        total_change = data.get('total_change', 0)
                        beijing_time = data.get('beijing_time', '')
                        return {
                            'total_change': total_change,
                            'beijing_time': beijing_time,
                            'up_coins': data.get('up_coins', 0),
                            'down_coins': data.get('down_coins', 0)
                        }
        except Exception as e:
            print(f"[{self.account_id}] ❌ 获取币种涨跌数据异常: {e}")
        
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
    
    def record_execution(self, inst_id, pos_side, trigger_type, result, total_change, threshold):
        """记录执行结果"""
        try:
            record = {
                'timestamp': datetime.now().isoformat(),
                'account_id': self.account_id,
                'instId': inst_id,
                'posSide': pos_side,
                'triggerType': trigger_type,
                'totalChange': total_change,
                'threshold': threshold,
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
                return {'success': True, 'message': '平仓成功', 'data': result.get('data', [])}
            else:
                error_msg = result.get('msg', 'Unknown error')
                print(f"[{self.account_id}] ❌ 平仓失败: {error_msg}")
                return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = str(e)
            print(f"[{self.account_id}] ❌ 平仓异常: {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def check_and_execute(self):
        """检查并执行止盈"""
        # 1. 加载配置
        settings = self.load_settings()
        if not settings:
            print(f"[{self.account_id}] ⚠️  配置文件不存在或为空")
            return
        
        # 2. 检查是否启用
        short_tp_enabled = settings.get('shortTakeProfitEnabled', False)
        long_tp_enabled = settings.get('longTakeProfitEnabled', False)
        
        if not short_tp_enabled and not long_tp_enabled:
            print(f"[{self.account_id}] ℹ️  27币涨跌幅止盈未启用")
            return
        
        # 3. 获取阈值
        short_tp_threshold = settings.get('shortTakeProfitThreshold', 0)
        long_tp_threshold = settings.get('longTakeProfitThreshold', 0)
        
        # 4. 获取最新27币涨跌幅之和
        coin_change_data = self.get_latest_coin_change()
        if not coin_change_data:
            print(f"[{self.account_id}] ⚠️  无法获取币种涨跌数据")
            return
        
        total_change = coin_change_data['total_change']
        beijing_time = coin_change_data['beijing_time']
        
        print(f"[{self.account_id}] 📊 当前27币涨跌幅之和: {total_change:.2f}% (时间: {beijing_time})")
        
        # 5. 加载API凭证
        credentials = self.load_account_credentials()
        if not credentials:
            print(f"[{self.account_id}] ⚠️  无法加载API凭证")
            return
        
        # 6. 获取持仓
        positions = self.get_positions(credentials)
        if not positions:
            print(f"[{self.account_id}] ℹ️  当前无持仓")
            return
        
        # 7. 检查每个持仓是否需要止盈
        for pos in positions:
            inst_id = pos.get('instId', '')
            pos_side = pos.get('posSide', '')
            pos_amt = float(pos.get('pos', 0))
            
            # 跳过已平仓的
            if pos_amt == 0:
                continue
            
            print(f"[{self.account_id}] 📌 检查持仓: {inst_id} {pos_side} 数量: {pos_amt}")
            
            # 空单止盈检查（跌破阈值）
            if pos_side == 'short' and short_tp_enabled:
                # 空单止盈：total_change < -threshold（负值跌破）
                if total_change < -abs(short_tp_threshold):
                    trigger_type = 'short_take_profit'
                    
                    # 检查是否已执行过
                    if self.check_executed(inst_id, pos_side, trigger_type):
                        continue
                    
                    print(f"[{self.account_id}] 🔔 触发空单止盈: {inst_id} 涨跌幅{total_change:.2f}% < -{abs(short_tp_threshold):.2f}%")
                    
                    # 平仓
                    result = self.close_position(credentials, inst_id, pos_side)
                    
                    # 记录执行
                    self.record_execution(inst_id, pos_side, trigger_type, result, total_change, short_tp_threshold)
                    
                    # 发送通知
                    if result.get('success'):
                        msg = f"🎉 <b>空单止盈成功</b>\n\n"
                        msg += f"账户: {self.account_id}\n"
                        msg += f"币对: {inst_id}\n"
                        msg += f"方向: 空单\n"
                        msg += f"27币涨跌幅: {total_change:.2f}%\n"
                        msg += f"止盈阈值: -{abs(short_tp_threshold):.2f}%\n"
                        msg += f"时间: {beijing_time}"
                        self.send_telegram(msg)
            
            # 多单止盈检查（突破阈值）
            elif pos_side == 'long' and long_tp_enabled:
                # 多单止盈：total_change > threshold（正值突破）
                if total_change > abs(long_tp_threshold):
                    trigger_type = 'long_take_profit'
                    
                    # 检查是否已执行过
                    if self.check_executed(inst_id, pos_side, trigger_type):
                        continue
                    
                    print(f"[{self.account_id}] 🔔 触发多单止盈: {inst_id} 涨跌幅{total_change:.2f}% > {abs(long_tp_threshold):.2f}%")
                    
                    # 平仓
                    result = self.close_position(credentials, inst_id, pos_side)
                    
                    # 记录执行
                    self.record_execution(inst_id, pos_side, trigger_type, result, total_change, long_tp_threshold)
                    
                    # 发送通知
                    if result.get('success'):
                        msg = f"🎉 <b>多单止盈成功</b>\n\n"
                        msg += f"账户: {self.account_id}\n"
                        msg += f"币对: {inst_id}\n"
                        msg += f"方向: 多单\n"
                        msg += f"27币涨跌幅: {total_change:.2f}%\n"
                        msg += f"止盈阈值: +{abs(long_tp_threshold):.2f}%\n"
                        msg += f"时间: {beijing_time}"
                        self.send_telegram(msg)
    
    def run(self):
        """运行监控循环"""
        print(f"[{self.account_id}] 🚀 启动27币涨跌幅止盈监控")
        print(f"[{self.account_id}] 📊 监控间隔: {CHECK_INTERVAL}秒")
        
        while True:
            try:
                self.check_and_execute()
            except Exception as e:
                print(f"[{self.account_id}] ❌ 监控异常: {e}")
            
            time.sleep(CHECK_INTERVAL)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python okx_coin_change_tpsl_monitor.py <account_id>")
        sys.exit(1)
    
    account_id = sys.argv[1]
    monitor = CoinChangeTakeProfitMonitor(account_id)
    monitor.run()


if __name__ == '__main__':
    main()
