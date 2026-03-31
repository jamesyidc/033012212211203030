#!/usr/bin/env python3
"""
ABC开仓系统数据追踪器
功能：追踪4个账户的ABC开仓和平仓逻辑
"""

import json
import os
import time
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/abc_position_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据目录
DATA_DIR = Path("data/abc_position")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# OKX API配置
OKX_API_BASE = "http://localhost:9002"

# 账户映射配置
ACCOUNT_MAPPING = {
    'A': {
        'name': '主账户',
        'okx_account': 'account_main',
        'account_id': 'main'
    },
    'B': {
        'name': 'POIT',
        'okx_account': 'account_poit_main', 
        'account_id': 'poit_main'
    },
    'C': {
        'name': 'fangfang12',
        'okx_account': 'account_fangfang12',
        'account_id': 'fangfang12'
    },
    'D': {
        'name': 'dadanini',
        'okx_account': 'account_dadanini',
        'account_id': 'dadanini'
    }
}

# 仓位阈值配置（每个账户的A/B/C仓位触发条件）
POSITION_THRESHOLDS = {
    'A': {  # 主账户
        'A': {'loss_trigger': 0, 'profit_target': 80},      # A仓：初始开仓，盈利80%平仓
        'B': {'loss_trigger': -16, 'profit_target': 50},    # B仓：亏损-16%触发，盈利50%平仓
        'C': {'loss_trigger': -32, 'profit_target': 50}     # C仓：亏损-32%触发，盈利50%平仓
    },
    'B': {  # POIT
        'A': {'loss_trigger': 0, 'profit_target': 80},
        'B': {'loss_trigger': -16, 'profit_target': 50},
        'C': {'loss_trigger': -32, 'profit_target': 50}
    },
    'C': {  # fangfang12
        'A': {'loss_trigger': -8, 'profit_target': 80},     # C账户的A仓：当AB账户亏损-8%时触发
        'B': {'loss_trigger': -24, 'profit_target': 50},    # C账户的B仓：亏损-24%触发
        'C': {'loss_trigger': -40, 'profit_target': 50}     # C账户的C仓：亏损-40%触发
    },
    'D': {  # dadanini
        'A': {'loss_trigger': -8, 'profit_target': 80},
        'B': {'loss_trigger': -24, 'profit_target': 50},
        'C': {'loss_trigger': -40, 'profit_target': 50}
    }
}

class ABCPositionTracker:
    """ABC开仓系统追踪器"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.state_file = self.data_dir / "abc_position_state.json"
        # 历史记录按日期存储
        # self.history_file = self.data_dir / "abc_position_history.jsonl"  # 废弃
        
        # 账户映射
        self.account_mapping = ACCOUNT_MAPPING
        self.position_thresholds = POSITION_THRESHOLDS
        
        # 加载状态
        self.state = self.load_state()
    
    def get_history_file(self, date_str=None):
        """获取历史文件路径（按日期）"""
        if date_str is None:
            date_str = self.get_beijing_time().strftime('%Y%m%d')
        return self.data_dir / f"abc_position_{date_str}.jsonl"
        
    def get_beijing_time(self):
        """获取北京时间"""
        beijing_tz = timezone(timedelta(hours=8))
        return datetime.now(beijing_tz)
    
    def load_state(self):
        """加载状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载状态失败: {e}")
        
        # 默认状态：4个账户（A、B、C、D），每个账户3个仓位（A、B、C）
        return {
            'accounts': {
                'A': {'positions': {'A': None, 'B': None, 'C': None}, 'total_cost': 0, 'unrealized_pnl': 0},
                'B': {'positions': {'A': None, 'B': None, 'C': None}, 'total_cost': 0, 'unrealized_pnl': 0},
                'C': {'positions': {'A': None, 'B': None, 'C': None}, 'total_cost': 0, 'unrealized_pnl': 0},
                'D': {'positions': {'A': None, 'B': None, 'C': None}, 'total_cost': 0, 'unrealized_pnl': 0}
            },
            'trading_permission': {
                'enabled': False,  # 是否允许开单
                'direction': 'none',  # 允许方向：'long'(多单)/'short'(空单)/'none'(不允许)
                'last_update': None
            },
            'current_direction': 'none',  # 当前持仓方向：'long'/'short'/'none'
            'last_update': None,
            'trigger_history': []
        }
    
    def save_state(self):
        """保存状态"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
            logger.info("状态已保存")
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    def append_history(self, record, date_str=None):
        """追加历史记录（按日期存储）"""
        try:
            history_file = self.get_history_file(date_str)
            with open(history_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"追加历史记录失败: {e}")
    
    def fetch_okx_positions(self):
        """获取OKX持仓数据（使用真实API）"""
        try:
            # 调用新的real-positions API获取真实持仓数据
            response = requests.get(
                f"{OKX_API_BASE}/abc-position/api/real-positions",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('data', {})
            
            logger.error(f"获取真实持仓失败: {response.text}")
            return {}
            
        except requests.exceptions.Timeout:
            logger.warning(f"获取真实持仓超时")
            return {}
        except Exception as e:
            logger.error(f"获取真实持仓异常: {e}")
            return {}
            
        except Exception as e:
            logger.error(f"获取OKX持仓数据异常: {e}")
            return {}
    
    def set_trading_permission(self, enabled, direction='none'):
        """设置开单权限
        
        Args:
            enabled: 是否允许开单
            direction: 允许方向 'long'(多单)/'short'(空单)/'none'(不允许)
        """
        beijing_time = self.get_beijing_time()
        
        self.state['trading_permission'] = {
            'enabled': enabled,
            'direction': direction,
            'last_update': beijing_time.isoformat()
        }
        
        self.save_state()
        logger.info(f"开单权限已更新: enabled={enabled}, direction={direction}")
        
        return {
            'success': True,
            'enabled': enabled,
            'direction': direction,
            'timestamp': beijing_time.isoformat()
        }
    
    def get_trading_permission(self):
        """获取当前开单权限"""
        return self.state.get('trading_permission', {
            'enabled': False,
            'direction': 'none',
            'last_update': None
        })
    
    def can_open_position(self, direction):
        """检查是否可以开仓
        
        Args:
            direction: 开仓方向 'long'或'short'
            
        Returns:
            (bool, str): (是否允许, 原因)
        """
        permission = self.get_trading_permission()
        
        # 检查是否启用开单
        if not permission['enabled']:
            return False, "开单功能未启用"
        
        # 检查当前是否有持仓
        current_dir = self.state.get('current_direction', 'none')
        if current_dir != 'none' and current_dir != direction:
            return False, f"当前已有{current_dir}方向持仓，不能开{direction}方向"
        
        # 检查是否允许该方向
        if permission['direction'] != direction and permission['direction'] != 'both':
            return False, f"当前只允许开{permission['direction']}方向"
        
        return True, "允许开仓"
    
    def calculate_account_pnl(self, account_label, positions):
        """计算账户的持仓收益率
        
        Args:
            account_label: 账户标签 (A/B/C/D)
            positions: 持仓列表
            
        Returns:
            dict: {
                'total_cost': 建仓总成本,
                'unrealized_pnl': 未实现盈亏,
                'pnl_pct': 收益率百分比,
                'position_count': 持仓数量
            }
        """
        if not positions or len(positions) == 0:
            return {
                'total_cost': 0,
                'unrealized_pnl': 0,
                'pnl_pct': 0,
                'position_count': 0
            }
        
        total_cost = 0
        total_pnl = 0
        
        for pos in positions:
            # 计算建仓成本
            avg_price = float(pos.get('avgPx', 0))
            pos_size = abs(float(pos.get('pos', 0)))
            cost = avg_price * pos_size
            total_cost += cost
            
            # 计算未实现盈亏
            upl = float(pos.get('upl', 0))
            total_pnl += upl
        
        # 计算收益率
        pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'total_cost': total_cost,
            'unrealized_pnl': total_pnl,
            'pnl_pct': pnl_pct,
            'position_count': len(positions)
        }
    
    def calculate_position_pnl_pct(self, account_id):
        """计算账户持仓盈亏百分比"""
        account = self.state['accounts'][account_id]
        
        if account['total_cost'] == 0:
            return 0.0
        
        return (account['unrealized_pnl'] / account['total_cost']) * 100
    
    def get_position_color(self, account_id):
        """获取账户持仓颜色标识（基于USDT成本和阈值）"""
        account = self.state['accounts'][account_id]
        total_cost = account.get('total_cost', 0)
        
        logger.info(f"计算颜色 - 账户{account_id}: 成本={total_cost} USDT")
        
        # 尝试读取设置文件获取阈值
        try:
            settings_file = self.data_dir / "abc_position_settings.json"
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    if 'accounts' in settings and account_id in settings['accounts']:
                        thresholds = settings['accounts'][account_id].get('thresholds', {})
                        threshold_a = thresholds.get('A', 20)  # 默认20 USDT
                        threshold_b = thresholds.get('B', 40)  # 默认40 USDT
                        threshold_c = thresholds.get('C', 55)  # 默认55 USDT
                        
                        logger.info(f"账户{account_id} - 阈值A={threshold_a}U, 阈值B={threshold_b}U, 阈值C={threshold_c}U")
                        
                        # 根据USDT成本判断颜色
                        if total_cost == 0:
                            color = 'none'  # 无持仓：灰色
                        elif total_cost <= threshold_a:
                            color = 'green'  # A仓成本：绿色
                        elif total_cost <= threshold_b:
                            color = 'yellow'  # AB仓成本：黄色
                        elif total_cost <= threshold_c:
                            color = 'red'  # ABC仓成本：红色
                        else:
                            color = 'orange'  # 超过ABC仓：橙色
                        
                        logger.info(f"账户{account_id} - 颜色={color}")
                        return color
        except Exception as e:
            logger.warning(f"读取设置文件失败，使用默认阈值: {e}")
        
        # 默认阈值：20U以下绿色，40U以下黄色，55U以下红色，超过橙色
        if total_cost == 0:
            color = 'none'
        elif total_cost <= 20:
            color = 'green'
        elif total_cost <= 40:
            color = 'yellow'
        elif total_cost <= 55:
            color = 'red'
        else:
            color = 'orange'
        
        logger.info(f"账户{account_id} - 使用默认阈值，颜色={color}")
        return color
    
    def check_open_conditions(self):
        """检查开仓条件"""
        actions = []
        
        # 获取各账户的盈亏百分比
        pnl_pcts = {
            acc_id: self.calculate_position_pnl_pct(acc_id)
            for acc_id in ['A', 'B', 'C', 'D']
        }
        
        # 第一步：满足条件开A/B账户的A仓；亏损到-8%开C/D账户的A仓
        for acc_id in ['A', 'B']:
            if self.state['accounts'][acc_id]['positions']['A'] is None:
                # 检查是否满足开仓条件（这里需要根据实际条件判断）
                trigger_result, direction = self._check_initial_trigger()
                if trigger_result:
                    # 检查是否允许该方向开仓
                    can_open, reason = self.can_open_position(direction)
                    if can_open:
                        actions.append({
                            'action': 'open',
                            'account': acc_id,
                            'position': 'A',
                            'direction': direction,
                            'reason': f'满足初始开仓条件（{direction}）'
                        })
                    else:
                        logger.info(f"跳过开仓: {reason}")
        
        # 检查C/D账户A仓：需要A/B账户有仓位且亏损-8%
        ab_has_positions = any(
            self.state['accounts'][acc]['positions']['A'] is not None
            for acc in ['A', 'B']
        )
        ab_avg_pnl = sum(pnl_pcts[acc] for acc in ['A', 'B']) / 2 if ab_has_positions else 0
        
        # 获取当前持仓方向
        current_direction = self.state.get('current_direction', 'none')
        
        if ab_has_positions and ab_avg_pnl <= -8.0:
            for acc_id in ['C', 'D']:
                if self.state['accounts'][acc_id]['positions']['A'] is None:
                    # 使用当前持仓方向
                    if current_direction != 'none':
                        actions.append({
                            'action': 'open',
                            'account': acc_id,
                            'position': 'A',
                            'direction': current_direction,
                            'reason': f'A/B账户亏损{ab_avg_pnl:.2f}%，触发C/D账户A仓开仓'
                        })
        
        # 第二步：再亏损-8%，开A/B账户的B仓
        if ab_has_positions and ab_avg_pnl <= -16.0:
            for acc_id in ['A', 'B']:
                if self.state['accounts'][acc_id]['positions']['B'] is None:
                    if current_direction != 'none':
                        actions.append({
                            'action': 'open',
                            'account': acc_id,
                            'position': 'B',
                            'direction': current_direction,
                            'reason': f'A/B账户亏损{ab_avg_pnl:.2f}%，触发B仓开仓'
                        })
        
        # 再亏损-8%，开C/D账户的B仓
        if ab_avg_pnl <= -24.0:
            for acc_id in ['C', 'D']:
                if self.state['accounts'][acc_id]['positions']['B'] is None:
                    if current_direction != 'none':
                        actions.append({
                            'action': 'open',
                            'account': acc_id,
                            'position': 'B',
                            'direction': current_direction,
                            'reason': f'亏损{ab_avg_pnl:.2f}%，触发C/D账户B仓开仓'
                        })
        
        # 第三步：再亏损-8%，开A/B账户的C仓
        if ab_avg_pnl <= -32.0:
            for acc_id in ['A', 'B']:
                if self.state['accounts'][acc_id]['positions']['C'] is None:
                    if current_direction != 'none':
                        actions.append({
                            'action': 'open',
                            'account': acc_id,
                            'position': 'C',
                            'direction': current_direction,
                            'reason': f'亏损{ab_avg_pnl:.2f}%，触发A/B账户C仓开仓'
                        })
        
        # 再亏损-8%，开C/D账户的C仓
        if ab_avg_pnl <= -40.0:
            for acc_id in ['C', 'D']:
                if self.state['accounts'][acc_id]['positions']['C'] is None:
                    if current_direction != 'none':
                        actions.append({
                            'action': 'open',
                            'account': acc_id,
                            'position': 'C',
                            'direction': current_direction,
                            'reason': f'亏损{ab_avg_pnl:.2f}%，触发C/D账户C仓开仓'
                        })
        
        return actions
    
    def check_close_conditions(self):
        """检查平仓条件"""
        actions = []
        
        for acc_id in ['A', 'B', 'C', 'D']:
            account = self.state['accounts'][acc_id]
            pnl_pct = self.calculate_position_pnl_pct(acc_id)
            positions = account['positions']
            
            # A仓：上涨80%平仓
            if positions['A'] is not None and pnl_pct >= 80.0:
                actions.append({
                    'action': 'close',
                    'account': acc_id,
                    'position': 'A',
                    'ratio': 1.0,
                    'reason': f'A仓盈利{pnl_pct:.2f}%，达到80%止盈条件'
                })
            
            # AB仓：上涨50%平B仓（1/2仓位）
            if positions['A'] is not None and positions['B'] is not None and positions['C'] is None:
                if pnl_pct >= 50.0:
                    actions.append({
                        'action': 'close',
                        'account': acc_id,
                        'position': 'B',
                        'ratio': 0.5,
                        'reason': f'AB仓盈利{pnl_pct:.2f}%，平B仓（1/2仓位）'
                    })
            
            # ABC仓：上涨50%平BC仓（2/3仓位）
            if positions['A'] is not None and positions['B'] is not None and positions['C'] is not None:
                if pnl_pct >= 50.0:
                    actions.append({
                        'action': 'close',
                        'account': acc_id,
                        'position': 'BC',
                        'ratio': 2/3,
                        'reason': f'ABC仓盈利{pnl_pct:.2f}%，平BC仓（2/3仓位）'
                    })
        
        return actions
    
    def _check_initial_trigger(self):
        """检查初始触发条件（需要根据实际信号判断）
        
        Returns:
            (bool, str): (是否触发, 方向'long'/'short')
        """
        # 这里需要接入实际的触发信号逻辑
        # 暂时返回False，避免自动开仓
        # 实际应该调用信号检测API，判断是否满足开仓条件
        
        # 示例：从OKX交易信号判断
        # signal = self.fetch_trading_signal()
        # if signal:
        #     return True, signal['direction']
        
        return False, 'none'
    
    def update_positions(self):
        """更新持仓数据"""
        beijing_time = self.get_beijing_time()
        
        # 获取OKX持仓数据（新格式：直接返回账户数据）
        okx_positions = self.fetch_okx_positions()
        
        # 账户标签到 OKX API 账户 ID 的映射
        label_to_api_id = {
            'A': 'main',
            'B': 'poit_main',
            'C': 'fangfang12',
            'D': 'dadanini'
        }
        
        # 更新各账户数据
        for acc_label in ['A', 'B', 'C', 'D']:
            # 获取对应的 API 账户 ID
            api_account_id = label_to_api_id.get(acc_label)
            acc_data = okx_positions.get(api_account_id, {})
            
            if acc_data and acc_data.get('position_count', 0) > 0:
                # 使用 API 返回的真实数据
                # total_margin 是成本，total_upl 是未实现盈亏，profit_ratio 是盈亏百分比
                self.state['accounts'][acc_label]['total_cost'] = acc_data.get('total_margin', 0)
                self.state['accounts'][acc_label]['unrealized_pnl'] = acc_data.get('total_upl', 0)
                self.state['accounts'][acc_label]['pnl_pct'] = acc_data.get('profit_ratio', 0)
                self.state['accounts'][acc_label]['position_count'] = acc_data.get('position_count', 0)
            else:
                # 无持仓或API失败，使用默认值
                self.state['accounts'][acc_label]['total_cost'] = 0
                self.state['accounts'][acc_label]['unrealized_pnl'] = 0
                self.state['accounts'][acc_label]['pnl_pct'] = 0
                self.state['accounts'][acc_label]['position_count'] = 0
            
            # 记录账户名称
            acc_info = self.account_mapping[acc_label]
            self.state['accounts'][acc_label]['account_name'] = acc_info['name']
            self.state['accounts'][acc_label]['okx_account'] = acc_info['okx_account']
            
            # 更新颜色（基于持仓数量和阈值）
            self.state['accounts'][acc_label]['color'] = self.get_position_color(acc_label)
        
        # ⚠️ 暂时注释开仓平仓功能，先实现曲线显示
        # 检查开仓条件
        # open_actions = self.check_open_conditions()
        # for action in open_actions:
        #     logger.info(f"触发开仓: {action}")
        #     self.state['trigger_history'].append({
        #         'time': beijing_time.isoformat(),
        #         'action': action
        #     })
        
        # 检查平仓条件
        # close_actions = self.check_close_conditions()
        # for action in close_actions:
        #     logger.info(f"触发平仓: {action}")
        #     self.state['trigger_history'].append({
        #         'time': beijing_time.isoformat(),
        #         'action': action
        #     })
        
        # 更新状态
        self.state['last_update'] = beijing_time.isoformat()
        
        # 生成当前快照
        snapshot = {
            'timestamp': beijing_time.isoformat(),
            'accounts': {}
        }
        
        for acc_id in ['A', 'B', 'C', 'D']:
            acc_info = self.account_mapping[acc_id]
            snapshot['accounts'][acc_id] = {
                'account_name': acc_info['name'],
                'pnl_pct': self.state['accounts'][acc_id].get('pnl_pct', 0),
                'color': self.get_position_color(acc_id),
                'positions': self.state['accounts'][acc_id]['positions'],
                'unrealized_pnl': self.state['accounts'][acc_id]['unrealized_pnl'],
                'total_cost': self.state['accounts'][acc_id]['total_cost'],
                'position_count': self.state['accounts'][acc_id].get('position_count', 0)
            }
        
        # 追加历史记录
        self.append_history(snapshot)
        
        # 保存状态
        self.save_state()
        
        # 记录账户盈亏情况
        logger.info(f"数据更新完成 - " + 
                   f"A({self.account_mapping['A']['name']}): {self.state['accounts']['A'].get('pnl_pct', 0):.2f}%, " +
                   f"B({self.account_mapping['B']['name']}): {self.state['accounts']['B'].get('pnl_pct', 0):.2f}%, " +
                   f"C({self.account_mapping['C']['name']}): {self.state['accounts']['C'].get('pnl_pct', 0):.2f}%, " +
                   f"D({self.account_mapping['D']['name']}): {self.state['accounts']['D'].get('pnl_pct', 0):.2f}%")
        
        return snapshot
    
    def run_continuous(self, interval=60):
        """持续运行"""
        logger.info("启动ABC开仓系统追踪器...")
        logger.info(f"更新间隔: {interval} 秒")
        
        while True:
            try:
                self.update_positions()
                logger.info(f"等待 {interval} 秒后再次更新...")
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("收到中断信号，停止服务...")
                break
            except Exception as e:
                logger.error(f"更新过程中出错: {e}", exc_info=True)
                logger.info(f"等待 {interval} 秒后重试...")
                time.sleep(interval)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ABC开仓系统追踪器')
    parser.add_argument('--continuous', action='store_true', help='持续运行模式')
    parser.add_argument('--interval', type=int, default=60, help='持续模式下的更新间隔（秒）')
    
    args = parser.parse_args()
    
    tracker = ABCPositionTracker()
    
    if args.continuous:
        tracker.run_continuous(interval=args.interval)
    else:
        tracker.update_positions()

if __name__ == '__main__':
    main()
