#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正数占比自动平仓监控脚本
自动检查所有启用的账户，在正数占比突破阈值时自动平仓
"""

import os
import sys
import time
import json
import logging
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/home/user/webapp')

# 配置
CHECK_INTERVAL = 60  # 检查间隔：60秒
API_BASE_URL = "http://localhost:9002"
DATA_DIR = Path('/home/user/webapp/data/positive_ratio_stoploss')

# 硬编码API密钥
ACCOUNT_API_KEYS = {
    'account_main': {
        'apiKey': 'd6b272da-b59e-4ca3-97bd-663102f981b3',
        'apiSecret': '5D76ACDE6D74CF07842661385E12C61E',
        'passphrase': 'Tencent@123'
    },
    'account_fangfang12': {
        'apiKey': 'fbb2cb97-6d01-41ad-9c56-00ad03ba4ffe',
        'apiSecret': 'C8E82B23B1D7C6B6F3C0E0D5AD95DC6F',
        'passphrase': 'Tencent@123'
    },
    'account_poit_main': {
        'apiKey': '8650e46c-059b-431d-93cf-55f8c79babdb',
        'apiSecret': '4C2BD2AC6A08615EA7F36A6251857FCE',
        'passphrase': 'Wu666666.'
    },
    'account_dadanini': {
        'apiKey': '1463198a-fad0-46ac-9ad8-2a386461782c',
        'apiSecret': '1D112283B7456290056C253C56E9F3A6',
        'passphrase': 'Tencent@123'
    },
    'account_anchor': {
        'apiKey': '0b05a729-40eb-4806-9b53-c21db80a6d3a',
        'apiSecret': '4E4DA8BE3B18D01AA07185A006BF9F8E',
        'passphrase': 'Tencent@123'
    }
}

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class PositiveRatioAutoClose:
    """正数占比自动平仓监控器"""
    
    def __init__(self):
        self.accounts = self.load_all_accounts()
        self.load_telegram_config()
    
    def load_telegram_config(self):
        """加载Telegram配置"""
        try:
            config_file = Path('/home/user/webapp/config/configs/telegram_config.json')
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    tg_config = json.load(f)
                    self.tg_bot_token = tg_config.get('bot_token')
                    self.tg_chat_id = tg_config.get('chat_id')
                    logger.info(f"✅ Telegram配置加载成功")
            else:
                self.tg_bot_token = None
                self.tg_chat_id = None
                logger.warning(f"⚠️ Telegram配置文件不存在")
        except Exception as e:
            self.tg_bot_token = None
            self.tg_chat_id = None
            logger.error(f"❌ 加载Telegram配置失败: {e}")
    
    def send_telegram(self, message):
        """发送Telegram消息"""
        if not self.tg_bot_token or not self.tg_chat_id:
            logger.warning("⚠️ Telegram未配置，跳过发送")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.tg_bot_token}/sendMessage"
            data = {
                'chat_id': self.tg_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            logger.info("✅ Telegram消息发送成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ Telegram消息发送失败: {e}")
            return False
        
    def load_all_accounts(self):
        """加载所有启用的账户配置"""
        accounts = []
        
        if not DATA_DIR.exists():
            logger.warning(f"⚠️ 配置目录不存在: {DATA_DIR}")
            return accounts
        
        for config_file in DATA_DIR.glob('*_config.json'):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 只加载启用的账户
                if config.get('enabled', False):
                    account_id = config_file.stem.replace('_config', '')
                    accounts.append({
                        'id': account_id,
                        'config': config,
                        'config_file': config_file
                    })
                    logger.info(f"✅ 加载账户: {account_id} (阈值: {config.get('threshold', 40)}%)")
            
            except Exception as e:
                logger.error(f"❌ 加载配置失败 {config_file.name}: {e}")
        
        return accounts
    
    def check_account(self, account):
        """检查单个账户并执行平仓"""
        account_id = account['id']
        config = account['config']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 检查账户: {account_id}")
        logger.info(f"{'='*60}")
        
        try:
            # 调用检查API
            check_url = f"{API_BASE_URL}/api/okx-trading/positive-ratio-stoploss/check/{account_id}"
            response = requests.post(check_url, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if not result.get('success'):
                logger.error(f"❌ 检查失败: {result.get('error', '未知错误')}")
                return
            
            # 显示当前状态
            current_ratio = result.get('current_ratio', 0)
            threshold = result.get('threshold', 40)
            last_status = result.get('last_status', 'unknown')
            current_status = result.get('current_status', 'unknown')
            trigger = result.get('trigger', False)
            action = result.get('action', 'none')
            reason = result.get('reason', '')
            
            logger.info(f"📊 当前正数占比: {current_ratio:.2f}%")
            logger.info(f"⚡ 阈值: {threshold}%")
            logger.info(f"📈 上次状态: {last_status} → 当前状态: {current_status}")
            
            if trigger:
                logger.warning(f"🔥 触发平仓！动作: {action}")
                logger.warning(f"📝 原因: {reason}")
                
                # 执行平仓
                if action == 'close_long':
                    self.close_positions(account_id, 'long')
                elif action == 'close_short':
                    self.close_positions(account_id, 'short')
                
                # 重新加载账户配置（可能已被禁用）
                self.reload_account(account)
            else:
                logger.info(f"✅ 未触发，继续监控")
                
        except Exception as e:
            logger.error(f"❌ 检查账户失败: {e}")
    
    def close_positions(self, account_id, direction):
        """平仓"""
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"🚀 开始平仓: {account_id} - {'多单' if direction == 'long' else '空单'}")
            logger.info(f"{'='*60}")
            
            # 1. 获取API密钥（硬编码）
            if account_id not in ACCOUNT_API_KEYS:
                logger.error(f"❌ 账户 {account_id} 没有配置API密钥")
                return
            
            api_credentials = ACCOUNT_API_KEYS[account_id]
            api_key = api_credentials['apiKey']
            api_secret = api_credentials['apiSecret']
            passphrase = api_credentials['passphrase']
            
            logger.info(f"✅ 使用硬编码API密钥: {api_key[:8]}...")
            
            # 2. 获取持仓
            positions_url = f"{API_BASE_URL}/api/okx-trading/positions"
            positions_response = requests.post(
                positions_url,
                json={
                    'apiKey': api_key,
                    'apiSecret': api_secret,
                    'passphrase': passphrase
                },
                timeout=10
            )
            positions_response.raise_for_status()
            positions_data = positions_response.json()
            
            if not positions_data.get('success'):
                logger.error(f"❌ 获取持仓失败: {positions_data.get('error')}")
                return
            
            positions = positions_data.get('data', [])
            logger.info(f"📊 总持仓数: {len(positions)}")
            
            # 筛选需要平仓的持仓
            target_positions = []
            for pos in positions:
                pos_side = pos.get('posSide', '')
                # 尝试多个字段名
                pos_amt = float(pos.get('pos', pos.get('posSize', 0)))
                
                if pos_amt == 0:
                    continue
                
                if direction == 'long' and pos_side == 'long':
                    target_positions.append(pos)
                elif direction == 'short' and pos_side == 'short':
                    target_positions.append(pos)
            
            if not target_positions:
                logger.info(f"✅ 没有需要平仓的{'多单' if direction == 'long' else '空单'}")
                return
            
            logger.info(f"📋 找到 {len(target_positions)} 个持仓需要平仓")
            for pos in target_positions:
                inst_id = pos.get('instId')
                pos_amt = pos.get('pos', pos.get('posSize', 0))
                logger.info(f"  • {inst_id}: {pos_amt}")
            
            # 3. 批量平仓
            close_url = f"{API_BASE_URL}/api/okx-trading/close-position"
            success_count = 0
            fail_count = 0
            closed_positions = []
            
            for pos in target_positions:
                inst_id = pos.get('instId')
                pos_side = pos.get('posSide')
                pos_amt = pos.get('pos', pos.get('posSize', 0))
                
                try:
                    logger.info(f"\n🔄 平仓: {inst_id} {pos_side} {pos_amt}")
                    
                    close_response = requests.post(
                        close_url,
                        json={
                            'apiKey': api_key,
                            'apiSecret': api_secret,
                            'passphrase': passphrase,
                            'accountId': account_id,
                            'instId': inst_id,
                            'posSide': pos_side
                        },
                        timeout=10
                    )
                    close_response.raise_for_status()
                    close_result = close_response.json()
                    
                    logger.info(f"   响应: {json.dumps(close_result, ensure_ascii=False)}")
                    
                    if close_result.get('success'):
                        success_count += 1
                        closed_positions.append(inst_id)
                        logger.info(f"   ✅ {inst_id} 平仓成功")
                    else:
                        fail_count += 1
                        logger.error(f"   ❌ {inst_id} 平仓失败: {close_result.get('error')}")
                    
                    # 延迟避免请求过快
                    time.sleep(0.5)
                    
                except Exception as e:
                    fail_count += 1
                    logger.error(f"   ❌ {inst_id} 平仓异常: {e}")
            
            logger.info(f"\n{'='*60}")
            logger.info(f"📊 平仓完成: 成功 {success_count} 个，失败 {fail_count} 个")
            logger.info(f"   已平仓: {', '.join(closed_positions)}")
            logger.info(f"{'='*60}")
            
            # 发送Telegram通知
            if success_count > 0 or fail_count > 0:
                account_names = {
                    'account_main': '主账户',
                    'account_fangfang12': 'Fangfang12',
                    'account_anchor': '锚点账号',
                    'account_poit': 'POIT',
                    'account_poit_main': 'POIT主账户',
                    'account_dadanini': 'Dadanini'
                }
                account_name = account_names.get(account_id, account_id)
                direction_text = '多单' if direction == 'long' else '空单'
                
                # 获取当前正数占比
                try:
                    ratio_response = requests.get(f'{API_BASE_URL}/api/coin-change-tracker/positive-ratio-stats', timeout=5)
                    ratio_data = ratio_response.json()
                    current_ratio = ratio_data.get('stats', {}).get('positive_ratio', 0)
                except:
                    current_ratio = 0
                
                tg_message = f"""
🔥 <b>正数占比自动平仓通知</b>

━━━━━━━━━━━━━━━━━━
📋 <b>交易账户:</b> {account_name}
📊 <b>当前正数占比:</b> {current_ratio:.2f}%
⚡ <b>平仓方向:</b> {direction_text}
━━━━━━━━━━━━━━━━━━

📈 <b>平仓结果:</b>
  ✅ 成功: {success_count} 个
  ❌ 失败: {fail_count} 个

⏰ 时间: {datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                self.send_telegram(tg_message)
            
        except Exception as e:
            logger.error(f"❌ 平仓执行失败: {e}")
    
    def reload_account(self, account):
        """重新加载账户配置"""
        try:
            with open(account['config_file'], 'r', encoding='utf-8') as f:
                account['config'] = json.load(f)
        except Exception as e:
            logger.error(f"❌ 重新加载配置失败: {e}")
    
    def run(self):
        """主循环"""
        logger.info("=" * 60)
        logger.info("🚀 正数占比自动平仓监控启动")
        logger.info("=" * 60)
        logger.info(f"⚙️  配置:")
        logger.info(f"   - 检查间隔: {CHECK_INTERVAL}秒")
        logger.info(f"   - 监控账户数: {len(self.accounts)}")
        logger.info("=" * 60)
        
        if not self.accounts:
            logger.warning("⚠️ 没有启用的账户，监控退出")
            return
        
        check_count = 0
        
        while True:
            try:
                check_count += 1
                beijing_time = datetime.now(timezone(timedelta(hours=8)))
                
                logger.info(f"\n{'='*80}")
                logger.info(f"🔍 第 {check_count} 次检查 - {beijing_time.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*80}")
                
                # 检查所有账户
                for account in self.accounts:
                    if account['config'].get('enabled', False):
                        self.check_account(account)
                    else:
                        logger.info(f"⏭️  跳过已禁用账户: {account['id']}")
                
                # 重新加载账户列表（可能有新账户启用）
                self.accounts = self.load_all_accounts()
                
                logger.info(f"\n⏳ 等待 {CHECK_INTERVAL} 秒后进行下次检查...")
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("\n⚠️  收到中断信号，监控停止")
                break
            except Exception as e:
                logger.error(f"❌ 监控循环错误: {e}")
                logger.info(f"⏳ 等待 {CHECK_INTERVAL} 秒后重试...")
                time.sleep(CHECK_INTERVAL)
        
        logger.info("👋 监控已停止")


if __name__ == '__main__':
    monitor = PositiveRatioAutoClose()
    monitor.run()
