#!/usr/bin/env python3
"""
OKX 止盈止损自动监控服务
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
SENTIMENT_DIR = WEBAPP_DIR / 'data' / 'market_sentiment'  # 市场情绪数据目录

# OKX API
OKX_BASE_URL = 'https://www.okx.com'
CHECK_INTERVAL = 60  # 每60秒检查一次

# Telegram配置 - 从config文件读取（全系统统一）
try:
    import sys
    sys.path.insert(0, str(WEBAPP_DIR / 'config'))
    from telegram_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
    if TELEGRAM_ENABLED:
        print(f"✅ Telegram已配置: Bot Token = {TELEGRAM_BOT_TOKEN[:10]}..., Chat ID = {TELEGRAM_CHAT_ID}")
    else:
        print(f"⚠️  Telegram未配置，通知功能已禁用")
except Exception as e:
    print(f"⚠️  加载Telegram配置失败: {e}")
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

def get_latest_market_sentiment():
    """获取最新的市场情绪信号"""
    try:
        from datetime import datetime as dt, timezone, timedelta
        today = dt.now(timezone(timedelta(hours=8))).strftime('%Y%m%d')
        sentiment_file = SENTIMENT_DIR / f'market_sentiment_{today}.jsonl'
        
        if not sentiment_file.exists():
            return None
        
        # 读取最后一条记录
        with open(sentiment_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                last_record = json.loads(lines[-1].strip())
                return last_record
    except Exception as e:
        print(f"⚠️  获取市场情绪失败: {e}")
    return None

class TPSLMonitor:
    def __init__(self, account_id):
        self.account_id = account_id
        self.settings_file = SETTINGS_DIR / f'{account_id}_tpsl.jsonl'
        self.execution_file = SETTINGS_DIR / f'{account_id}_tpsl_execution.jsonl'
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
        """加载止盈止损配置（从JSONL抬头）"""
        if not self.settings_file.exists():
            return None
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                # 只读取第一行（抬头）
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
    
    def record_execution(self, inst_id, pos_side, trigger_type, result):
        """记录执行结果"""
        try:
            record = {
                'timestamp': datetime.now().isoformat(),
                'account_id': self.account_id,
                'instId': inst_id,
                'posSide': pos_side,
                'triggerType': trigger_type,  # 'take_profit' or 'stop_loss'
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
                print(f"[{self.account_id}] ⚠️  获取持仓失败: {result.get('msg', '未知错误')}")
                return []
                
        except Exception as e:
            print(f"[{self.account_id}] ⚠️  获取持仓异常: {e}")
            return []
    
    def _execute_market_close(self, credentials, position, sentiment_data=None):
        """执行市价平仓（用于市场情绪止盈）"""
        inst_id = position.get('instId', '')
        pos_side = position.get('posSide', '')
        avg_px = float(position.get('avgPx', 0))
        mark_px = float(position.get('markPx', avg_px))
        pos_size = abs(float(position.get('pos', 0)))
        
        try:
            path = '/api/v5/trade/order'
            timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
            
            # 市价平仓参数
            order_params = {
                'instId': inst_id,
                'tdMode': 'isolated',
                'side': 'sell' if pos_side == 'long' else 'buy',
                'posSide': pos_side,
                'ordType': 'market',
                'sz': str(pos_size),
                'reduceOnly': True
            }
            
            body = json.dumps(order_params)
            message = timestamp + 'POST' + path + body
            
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
            
            response = requests.post(OKX_BASE_URL + path, headers=headers, data=body, timeout=10)
            result = response.json()
            
            if result.get('code') == '0':
                print(f"[{self.account_id}] ✅ 市价平仓成功: {inst_id} {pos_side}")
                
                # 计算当前盈亏
                if pos_side == 'long':
                    current_pnl = ((mark_px - avg_px) / avg_px) * 100
                else:
                    current_pnl = ((avg_px - mark_px) / avg_px) * 100
                
                # 构建Telegram消息
                side_name = '多单' if pos_side == 'long' else '空单'
                sentiment_text = sentiment_data.get('sentiment', '') if sentiment_data else ''
                sentiment_reason = sentiment_data.get('reason', '') if sentiment_data else ''
                sentiment_time = sentiment_data.get('beijing_time', '') if sentiment_data else ''
                
                tg_message = (
                    f"🔥 <b>市场情绪止盈触发</b>\n\n"
                    f"📊 账户: <code>{self.account_id}</code>\n"
                    f"💰 交易对: <code>{inst_id}</code>\n"
                    f"📈 方向: {side_name}\n"
                    f"💵 开仓价: {avg_px:.4f}\n"
                    f"💵 当前价: {mark_px:.4f}\n"
                    f"📊 盈亏: {current_pnl:+.2f}%\n"
                    f"✅ 状态: 市价平仓成功\n\n"
                    f"⚠️ 触发信号: {sentiment_text}\n"
                    f"📝 理由: {sentiment_reason}\n"
                    f"⏰ 时间: {sentiment_time}\n\n"
                    f"🔥 市场情绪止盈已执行！"
                )
                self.send_telegram(tg_message)
                
                return {'success': True, 'message': '市价平仓成功'}
            else:
                error_msg = result.get('msg', '未知错误')
                print(f"[{self.account_id}] ❌ 市价平仓失败: {error_msg}")
                
                tg_message = (
                    f"❌ <b>市场情绪止盈失败</b>\n\n"
                    f"📊 账户: <code>{self.account_id}</code>\n"
                    f"💰 交易对: <code>{inst_id}</code>\n"
                    f"📈 方向: {side_name}\n"
                    f"❌ 错误: {error_msg}\n\n"
                    f"请手动检查并处理！"
                )
                self.send_telegram(tg_message)
                
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            print(f"[{self.account_id}] ❌ 市价平仓异常: {e}")
            return {'success': False, 'error': str(e)}
    
    def execute_tpsl(self, credentials, position, trigger_type, settings, sentiment_data=None):
        """执行止盈或止损"""
        inst_id = position.get('instId', '')
        pos_side = position.get('posSide', '')
        avg_px = float(position.get('avgPx', 0))
        pos_size = position.get('pos', '0')
        
        if avg_px <= 0:
            return {'success': False, 'error': '无法获取开仓均价'}
        
        # 🔥 市场情绪止盈：立即市价平仓（不需要触发价格）
        if trigger_type == 'sentiment_take_profit':
            print(f"[{self.account_id}] 🔥 市场情绪止盈: {inst_id} {pos_side}, 立即市价平仓")
            return self._execute_market_close(credentials, position, sentiment_data)
        
        # 计算触发价格（常规止盈止损）
        trigger_px = None
        if trigger_type == 'take_profit':
            tp_percent = float(settings.get('take_profit_threshold', 0)) / 100
            if pos_side == 'long':
                trigger_px = avg_px * (1 + tp_percent)
            else:
                trigger_px = avg_px * (1 - tp_percent)
            print(f"[{self.account_id}] 📈 触发止盈: {inst_id} {pos_side}, 开仓价={avg_px}, 止盈价={trigger_px}")
        
        elif trigger_type == 'stop_loss':
            sl_percent = abs(float(settings.get('stop_loss_threshold', 0))) / 100
            if pos_side == 'long':
                trigger_px = avg_px * (1 - sl_percent)
            else:
                trigger_px = avg_px * (1 + sl_percent)
            print(f"[{self.account_id}] 📉 触发止损: {inst_id} {pos_side}, 开仓价={avg_px}, 止损价={trigger_px}")
        
        if not trigger_px:
            return {'success': False, 'error': '无法计算触发价格'}
        
        # 调用OKX API设置止盈止损
        try:
            path = '/api/v5/trade/order-algo'
            timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
            
            algo_params = {
                'instId': inst_id,
                'tdMode': 'isolated',
                'side': 'sell' if pos_side == 'long' else 'buy',
                'posSide': pos_side,
                'ordType': 'conditional',
                'sz': pos_size,
                'reduceOnly': 'true'
            }
            
            if trigger_type == 'take_profit':
                algo_params['tpTriggerPx'] = str(round(trigger_px, 2))
                algo_params['tpOrdPx'] = '-1'  # 市价
            else:
                algo_params['slTriggerPx'] = str(round(trigger_px, 2))
                algo_params['slOrdPx'] = '-1'  # 市价
            
            body = json.dumps(algo_params)
            message = timestamp + 'POST' + path + body
            
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
            
            response = requests.post(OKX_BASE_URL + path, headers=headers, data=body, timeout=10)
            result = response.json()
            
            if result.get('code') == '0':
                success_msg = f'{trigger_type}设置成功'
                print(f"[{self.account_id}] ✅ {success_msg}: {inst_id} {pos_side}")
                
                # 计算当前盈亏
                mark_px = float(position.get('markPx', avg_px))
                if pos_side == 'long':
                    current_pnl = ((mark_px - avg_px) / avg_px) * 100
                else:
                    current_pnl = ((avg_px - mark_px) / avg_px) * 100
                
                # 发送Telegram通知
                if trigger_type == 'sentiment_take_profit':
                    trigger_name = '市场情绪止盈'
                    emoji = '🔥'
                else:
                    trigger_name = '止盈' if trigger_type == 'take_profit' else '止损'
                    emoji = '🎯' if trigger_type == 'take_profit' else '🛑'
                
                side_name = '多单' if pos_side == 'long' else '空单'
                
                tg_message = (
                    f"{emoji} <b>OKX {trigger_name}触发</b>\n\n"
                    f"📊 账户: <code>{self.account_id}</code>\n"
                    f"💰 交易对: <code>{inst_id}</code>\n"
                    f"📈 方向: {side_name}\n"
                    f"💵 开仓价: <b>{avg_px:.2f} USDT</b>\n"
                    f"🎲 触发价: <b>{trigger_px:.2f} USDT</b>\n"
                    f"📊 当前价: <b>{mark_px:.2f} USDT</b>\n"
                    f"💹 当前盈亏: <b>{current_pnl:+.2f}%</b>\n"
                )
                
                # 如果是市场情绪止盈，添加情绪信息
                if trigger_type == 'sentiment_take_profit' and sentiment_data:
                    tg_message += (
                        f"\n🔥 <b>市场情绪信号</b>\n"
                        f"📊 信号: <b>{sentiment_data.get('sentiment', '')}</b>\n"
                        f"⏰ 时间: {sentiment_data.get('beijing_time', '')}\n"
                        f"💡 理由: {sentiment_data.get('reason', '')}\n"
                        f"📉 币涨跌: {sentiment_data.get('coin_data', {}).get('change_pct', 0):.2f}%\n"
                        f"📊 RSI变化: {sentiment_data.get('rsi_data', {}).get('change_pct', 0):.2f}%\n\n"
                    )
                
                tg_message += (
                    f"✅ 状态: <b>{trigger_name}订单已设置</b>\n\n"
                    f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"ℹ️ 等待市场价格触发平仓..."
                )
                self.send_telegram(tg_message)
                
                return {'success': True, 'message': success_msg}
            else:
                error_msg = result.get('msg', '未知错误')
                print(f"[{self.account_id}] ❌ {trigger_type} 设置失败: {error_msg}")
                
                # 发送失败通知
                trigger_name = '止盈' if trigger_type == 'take_profit' else '止损'
                side_name = '多单' if pos_side == 'long' else '空单'
                tg_message = (
                    f"⚠️ <b>OKX 止盈止损失败</b>\n\n"
                    f"账户: <code>{self.account_id}</code>\n"
                    f"交易对: <code>{inst_id}</code>\n"
                    f"方向: {side_name}\n"
                    f"类型: <b>{trigger_name}</b>\n"
                    f"状态: ❌ <b>设置失败</b>\n"
                    f"错误: {error_msg}\n\n"
                    f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                self.send_telegram(tg_message)
                
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            print(f"[{self.account_id}] ❌ {trigger_type} 执行异常: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_and_execute(self):
        """检查并执行止盈止损"""
        # 1. 加载配置
        settings = self.load_settings()
        if not settings:
            print(f"[{self.account_id}] ℹ️  未找到配置文件")
            return
        
        # 2. 检查是否启用
        if not settings.get('enabled', False):
            print(f"[{self.account_id}] ℹ️  止盈止损未启用")
            return
        
        # 3. 加载凭证
        credentials = self.load_account_credentials()
        if not credentials:
            print(f"[{self.account_id}] ⚠️  未找到账户凭证")
            return
        
        # 4. 获取持仓
        positions = self.get_positions(credentials)
        if not positions:
            print(f"[{self.account_id}] ℹ️  当前无持仓")
            return
        
        print(f"[{self.account_id}] 📊 当前持仓数: {len(positions)}")
        
        # 🔥 检查市场情绪止盈
        sentiment_triggered = False
        latest_sentiment = None
        if settings.get('sentiment_take_profit_enabled', False):
            latest_sentiment = get_latest_market_sentiment()
            if latest_sentiment:
                sentiment_text = latest_sentiment.get('sentiment', '')
                trigger_signals = settings.get('sentiment_signals', ['见顶信号', '顶部背离'])
                
                # 检查是否匹配触发信号
                if any(signal in sentiment_text for signal in trigger_signals):
                    sentiment_triggered = True
                    print(f"[{self.account_id}] 🔥 市场情绪止盈触发: {sentiment_text}")
                    print(f"[{self.account_id}]    时间: {latest_sentiment.get('beijing_time')}")
                    print(f"[{self.account_id}]    理由: {latest_sentiment.get('reason', '')}")
                else:
                    print(f"[{self.account_id}] 💚 市场情绪正常: {sentiment_text}")
            else:
                print(f"[{self.account_id}] ⚠️  未获取到市场情绪数据")
        
        # 5. 检查每个持仓
        for pos in positions:
            inst_id = pos.get('instId', '')
            pos_side = pos.get('posSide', '')
            avg_px = float(pos.get('avgPx', 0))
            mark_px = float(pos.get('markPx', 0))
            pos_size = abs(float(pos.get('pos', 0)))  # 持仓数量（绝对值）
            
            if avg_px <= 0 or mark_px <= 0:
                continue
            
            # 计算持仓价值（USDT）
            position_value_usdt = pos_size * mark_px
            
            # 🔥 优先检查市场情绪止盈（仅对多单有效）
            # 市场情绪止盈是紧急风控措施，无论持仓大小都应执行
            # ⚠️ 注意：这里只检查pos_side == 'long'，不会平空单
            if sentiment_triggered and pos_side == 'long':
                target_position_side = settings.get('sentiment_position_side', 'long')
                if pos_side == target_position_side:
                    if not self.check_executed(inst_id, pos_side, 'sentiment_take_profit'):
                        print(f"[{self.account_id}] 🔥 触发市场情绪止盈: {latest_sentiment.get('sentiment')} - 平掉多单 {inst_id} (价值{position_value_usdt:.2f}U)")
                        result = self.execute_tpsl(credentials, pos, 'sentiment_take_profit', settings, latest_sentiment)
                        self.record_execution(inst_id, pos_side, 'sentiment_take_profit', result)
                        continue  # 已执行市场情绪止盈，跳过后续检查
            
            # 计算当前盈亏百分比
            if pos_side == 'long':
                pnl_percent = ((mark_px - avg_px) / avg_px) * 100
            else:
                pnl_percent = ((avg_px - mark_px) / avg_px) * 100
            
            print(f"[{self.account_id}] 📊 {inst_id} {pos_side}: 开仓={avg_px}, 当前={mark_px}, 价值={position_value_usdt:.2f}U, 盈亏={pnl_percent:.2f}%")
            
            # 检查止盈
            if settings.get('take_profit_enabled', False):
                tp_threshold = float(settings.get('take_profit_threshold', 0))
                if pnl_percent >= tp_threshold:
                    if not self.check_executed(inst_id, pos_side, 'take_profit'):
                        print(f"[{self.account_id}] 🎯 触发止盈条件: {pnl_percent:.2f}% >= {tp_threshold}%")
                        result = self.execute_tpsl(credentials, pos, 'take_profit', settings)
                        self.record_execution(inst_id, pos_side, 'take_profit', result)
            
            # 检查止损
            if settings.get('stop_loss_enabled', False):
                sl_threshold = float(settings.get('stop_loss_threshold', 0))
                if pnl_percent <= sl_threshold:
                    if not self.check_executed(inst_id, pos_side, 'stop_loss'):
                        print(f"[{self.account_id}] 🛑 触发止损条件: {pnl_percent:.2f}% <= {sl_threshold}%")
                        result = self.execute_tpsl(credentials, pos, 'stop_loss', settings)
                        self.record_execution(inst_id, pos_side, 'stop_loss', result)

def main():
    """主函数"""
    print("=" * 60)
    print("OKX 止盈止损自动监控服务启动")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 扫描所有账户配置
    account_ids = []
    for account_file in ACCOUNTS_CONFIG.glob('account_*.json'):
        account_id = account_file.stem
        account_ids.append(account_id)
    
    print(f"✓ 发现账户数: {len(account_ids)}")
    print(f"  账户列表: {', '.join(account_ids)}")
    print()
    
    # 创建监控器
    monitors = [TPSLMonitor(account_id) for account_id in account_ids]
    
    # 主循环
    iteration = 0
    try:
        while True:
            iteration += 1
            print(f"\n{'='*60}")
            print(f"第 {iteration} 次检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}\n")
            
            for monitor in monitors:
                try:
                    monitor.check_and_execute()
                except Exception as e:
                    print(f"[{monitor.account_id}] ❌ 检查失败: {e}")
            
            print(f"\n{'='*60}")
            print(f"等待 {CHECK_INTERVAL} 秒后继续...")
            print(f"{'='*60}")
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n收到中断信号，服务停止")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 服务异常: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
