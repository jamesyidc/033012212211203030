#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统健康检查脚本 - 自动发现潜在问题
执行全面的系统检查，生成问题报告
"""

import os
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime, timedelta, timezone
import requests

class SystemHealthChecker:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
        self.base_url = "http://localhost:9002"
        
    def add_issue(self, category, title, description, severity="HIGH"):
        self.issues.append({
            'category': category,
            'title': title,
            'description': description,
            'severity': severity,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def add_warning(self, category, title, description):
        self.warnings.append({
            'category': category,
            'title': title,
            'description': description,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def add_passed(self, category, title):
        self.passed.append({
            'category': category,
            'title': title,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def check_api_endpoints(self):
        """检查关键API端点"""
        print("\n🔍 检查API端点...")
        
        endpoints = [
            ('/api/coin-change-tracker/daily-prediction', '日常预判API'),
            ('/api/coin-change-tracker/intraday-patterns', '日内模式检测API'),
            ('/api/coin-change-tracker/market-sentiment', '市场情绪API'),
            ('/api/okx-trading/accounts-config', 'OKX账户配置API'),
            ('/api/okx-trading/positions', 'OKX持仓API'),
        ]
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.add_passed('API', f"{name} 正常")
                        print(f"  ✅ {name}")
                    else:
                        self.add_warning('API', f"{name} 返回失败", data.get('error', '未知错误'))
                        print(f"  ⚠️  {name} - {data.get('error')}")
                else:
                    self.add_issue('API', f"{name} HTTP错误", f"状态码: {response.status_code}")
                    print(f"  ❌ {name} - HTTP {response.status_code}")
            except Exception as e:
                self.add_issue('API', f"{name} 连接失败", str(e))
                print(f"  ❌ {name} - {e}")
    
    def check_data_files(self):
        """检查关键数据文件"""
        print("\n🔍 检查数据文件...")
        
        # 检查今天的数据
        now_beijing = datetime.now(timezone.utc) + timedelta(hours=8)
        today = now_beijing.strftime('%Y%m%d')
        today_dash = now_beijing.strftime('%Y-%m-%d')
        
        files_to_check = [
            (f'data/coin_change_tracker/coin_change_{today}.jsonl', '今日币价数据'),
            (f'data/daily_predictions/prediction_{today_dash}.json', '今日预判数据'),
            ('data/stop_loss_system/stop_loss_state.json', '止损系统状态'),
            ('config/okx_accounts.json', 'OKX账户配置'),
        ]
        
        for file_path, name in files_to_check:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                if size > 0:
                    self.add_passed('数据文件', f"{name} 存在且有数据")
                    print(f"  ✅ {name} ({size} bytes)")
                else:
                    self.add_warning('数据文件', f"{name} 文件为空", f"路径: {file_path}")
                    print(f"  ⚠️  {name} - 文件为空")
            else:
                self.add_issue('数据文件', f"{name} 不存在", f"路径: {file_path}", "MEDIUM")
                print(f"  ❌ {name} - 不存在")
    
    def check_okx_accounts(self):
        """检查OKX账户配置"""
        print("\n🔍 检查OKX账户配置...")
        
        config_file = 'config/okx_accounts.json'
        if not os.path.exists(config_file):
            self.add_issue('OKX配置', '账户配置文件不存在', f"路径: {config_file}")
            print("  ❌ 配置文件不存在")
            return
        
        try:
            with open(config_file, 'r') as f:
                accounts = json.load(f)
            
            required_accounts = ['account_main', 'account_fangfang12', 'account_anchor', 'account_poit']
            found_accounts = [acc['id'] for acc in accounts if 'id' in acc]
            
            for acc_id in required_accounts:
                if acc_id in found_accounts:
                    self.add_passed('OKX配置', f"{acc_id} 存在")
                    print(f"  ✅ {acc_id}")
                else:
                    self.add_issue('OKX配置', f"{acc_id} 缺失", "一键平仓可能无法作用于该账户")
                    print(f"  ❌ {acc_id} - 缺失")
            
            # 检查API凭证完整性
            for account in accounts:
                acc_id = account.get('id', 'unknown')
                has_key = bool(account.get('apiKey'))
                has_secret = bool(account.get('apiSecret'))
                has_passphrase = bool(account.get('passphrase'))
                
                if has_key and has_secret and has_passphrase:
                    self.add_passed('OKX配置', f"{acc_id} API凭证完整")
                else:
                    missing = []
                    if not has_key: missing.append('apiKey')
                    if not has_secret: missing.append('apiSecret')
                    if not has_passphrase: missing.append('passphrase')
                    self.add_warning('OKX配置', f"{acc_id} API凭证不完整", f"缺少: {', '.join(missing)}")
                    print(f"  ⚠️  {acc_id} - 缺少: {', '.join(missing)}")
        
        except Exception as e:
            self.add_issue('OKX配置', '读取配置文件失败', str(e))
            print(f"  ❌ 读取失败: {e}")
    
    def check_prediction_logic(self):
        """检查预判逻辑一致性"""
        print("\n🔍 检查预判逻辑...")
        
        script_file = 'scripts/regenerate_all_predictions.py'
        if not os.path.exists(script_file):
            self.add_issue('预判逻辑', '预判脚本不存在', f"路径: {script_file}")
            print("  ❌ 脚本不存在")
            return
        
        try:
            with open(script_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查关键逻辑是否存在
            checks = [
                ('red + yellow) >= 3', '情况2: 红+黄>=3根判断'),
                ('red + yellow) < 3', '情况1: 红+黄<3根判断'),
                ('yellow >= 3 and red == 0', '情况8: 只有绿+黄判断'),
            ]
            
            for pattern, desc in checks:
                if pattern in content:
                    self.add_passed('预判逻辑', desc)
                    print(f"  ✅ {desc}")
                else:
                    self.add_issue('预判逻辑', f"{desc} 缺失", f"未找到模式: {pattern}")
                    print(f"  ❌ {desc} - 缺失")
        
        except Exception as e:
            self.add_issue('预判逻辑', '检查脚本失败', str(e))
            print(f"  ❌ 检查失败: {e}")
    
    def check_stop_loss_system(self):
        """检查止损系统"""
        print("\n🔍 检查止损系统...")
        
        files_to_check = [
            ('scripts/robust_stop_loss_system.py', '健壮止损脚本'),
            ('templates/okx_accounts_diagnostic.html', '账户诊断页面'),
            ('scripts/test_accounts_config.py', '账户配置测试'),
        ]
        
        for file_path, name in files_to_check:
            if os.path.exists(file_path):
                self.add_passed('止损系统', f"{name} 存在")
                print(f"  ✅ {name}")
            else:
                self.add_warning('止损系统', f"{name} 不存在", f"路径: {file_path}")
                print(f"  ⚠️  {name} - 不存在")
        
        # 检查前端止损函数
        okx_trading_file = 'templates/okx_trading.html'
        if os.path.exists(okx_trading_file):
            with open(okx_trading_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'closeAllAccountsPositions()' in content:
                self.add_passed('止损系统', '前端调用closeAllAccountsPositions()')
                print("  ✅ 前端调用closeAllAccountsPositions()")
            else:
                self.add_issue('止损系统', '前端未调用closeAllAccountsPositions()', 
                             "止损可能只作用于单个账户", "HIGH")
                print("  ❌ 前端未调用closeAllAccountsPositions()")
    
    def check_intraday_patterns(self):
        """检查日内模式检测"""
        print("\n🔍 检查日内模式检测...")
        
        # 检查时间窗口过滤
        coin_tracker_file = 'templates/coin_change_tracker.html'
        if os.path.exists(coin_tracker_file):
            with open(coin_tracker_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查关键功能
            checks = [
                ('is_valid_time', '时间窗口过滤函数'),
                ('find_entry_point', '开仓点时间计算函数'),
                ('entry_time', '开仓点时间字段'),
                ('toggleIntradayMainContent', '可伸缩功能'),
            ]
            
            for pattern, desc in checks:
                if pattern in content:
                    self.add_passed('日内模式', desc)
                    print(f"  ✅ {desc}")
                else:
                    self.add_warning('日内模式', f"{desc} 可能缺失", f"未找到: {pattern}")
                    print(f"  ⚠️  {desc} - 可能缺失")
        else:
            self.add_issue('日内模式', '页面文件不存在', f"路径: {coin_tracker_file}")
            print("  ❌ 页面文件不存在")
    
    def generate_report(self):
        """生成检查报告"""
        print("\n" + "="*80)
        print("📊 系统健康检查报告")
        print("="*80)
        
        total = len(self.issues) + len(self.warnings) + len(self.passed)
        
        print(f"\n总检查项: {total}")
        print(f"  ✅ 通过: {len(self.passed)}")
        print(f"  ⚠️  警告: {len(self.warnings)}")
        print(f"  ❌ 问题: {len(self.issues)}")
        
        if self.issues:
            print("\n" + "="*80)
            print("❌ 发现的问题:")
            print("="*80)
            for i, issue in enumerate(self.issues, 1):
                print(f"\n{i}. [{issue['severity']}] {issue['category']}: {issue['title']}")
                print(f"   描述: {issue['description']}")
        
        if self.warnings:
            print("\n" + "="*80)
            print("⚠️  警告:")
            print("="*80)
            for i, warning in enumerate(self.warnings, 1):
                print(f"\n{i}. {warning['category']}: {warning['title']}")
                print(f"   描述: {warning['description']}")
        
        # 保存报告到文件
        report_file = f'data/system_health_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        os.makedirs('data', exist_ok=True)
        
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total': total,
                'passed': len(self.passed),
                'warnings': len(self.warnings),
                'issues': len(self.issues)
            },
            'issues': self.issues,
            'warnings': self.warnings,
            'passed': self.passed
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📁 报告已保存到: {report_file}")
        print("="*80)
        
        # 返回状态码
        if self.issues:
            return 1  # 有严重问题
        elif self.warnings:
            return 2  # 有警告
        else:
            return 0  # 全部通过

def main():
    print("="*80)
    print("🏥 系统健康检查工具")
    print("="*80)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    checker = SystemHealthChecker()
    
    try:
        checker.check_api_endpoints()
        checker.check_data_files()
        checker.check_okx_accounts()
        checker.check_prediction_logic()
        checker.check_stop_loss_system()
        checker.check_intraday_patterns()
        
        exit_code = checker.generate_report()
        sys.exit(exit_code)
    
    except Exception as e:
        print(f"\n❌ 检查过程出错: {e}")
        traceback.print_exc()
        sys.exit(3)

if __name__ == "__main__":
    main()
