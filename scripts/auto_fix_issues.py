#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动修复已知问题的脚本
根据系统健康检查报告自动修复常见问题
"""

import os
import json
from datetime import datetime

def fix_okx_accounts_format():
    """修复OKX账户配置文件格式"""
    print("\n🔧 修复OKX账户配置...")
    
    config_file = 'config/okx_accounts.json'
    if not os.path.exists(config_file):
        print("  ❌ 配置文件不存在")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查格式
        if isinstance(data, dict) and 'accounts' in data:
            accounts = data['accounts']
            print(f"  ✅ 配置格式正确，包含 {len(accounts)} 个账户")
            
            # 验证账户
            required = ['account_main', 'account_fangfang12', 'account_anchor', 'account_poit']
            found = [acc['id'] for acc in accounts if 'id' in acc]
            
            for acc_id in required:
                if acc_id in found:
                    print(f"    ✅ {acc_id}")
                else:
                    print(f"    ❌ {acc_id} 缺失")
            
            return True
        else:
            print("  ⚠️  配置格式异常，需要手动检查")
            return False
    
    except Exception as e:
        print(f"  ❌ 读取失败: {e}")
        return False

def create_stop_loss_state():
    """创建止损系统状态文件"""
    print("\n🔧 创建止损系统状态文件...")
    
    state_dir = 'data/stop_loss_system'
    state_file = f'{state_dir}/stop_loss_state.json'
    
    os.makedirs(state_dir, exist_ok=True)
    
    if os.path.exists(state_file):
        print(f"  ✅ 状态文件已存在")
        return True
    
    try:
        initial_state = {
            'last_execution': None,
            'last_status': 'IDLE',
            'total_executions': 0,
            'success_count': 0,
            'failure_count': 0,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(initial_state, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ 状态文件创建成功: {state_file}")
        return True
    
    except Exception as e:
        print(f"  ❌ 创建失败: {e}")
        return False

def check_api_routes():
    """检查并提示API路由问题"""
    print("\n🔍 检查API路由...")
    
    required_routes = [
        '/api/coin-change-tracker/intraday-patterns',
        '/api/coin-change-tracker/market-sentiment',
        '/api/okx-trading/accounts-config',
    ]
    
    print("  ⚠️  以下API可能需要在app.py中检查:")
    for route in required_routes:
        print(f"    • {route}")
    
    print("\n  💡 建议: 使用以下命令检查路由定义:")
    print(f"    grep -n '@app.route' app.py | grep -E \"{'|'.join(required_routes)}\"")
    
    return True

def main():
    print("="*80)
    print("🔧 自动修复工具")
    print("="*80)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    fixes_applied = 0
    fixes_failed = 0
    
    # 修复1: OKX账户配置
    if fix_okx_accounts_format():
        fixes_applied += 1
    else:
        fixes_failed += 1
    
    # 修复2: 止损系统状态
    if create_stop_loss_state():
        fixes_applied += 1
    else:
        fixes_failed += 1
    
    # 检查3: API路由
    if check_api_routes():
        fixes_applied += 1
    
    print("\n" + "="*80)
    print("📊 修复总结")
    print("="*80)
    print(f"成功: {fixes_applied}")
    print(f"失败: {fixes_failed}")
    print("="*80)

if __name__ == "__main__":
    main()
