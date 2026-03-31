#!/usr/bin/env python3
"""
分析首页没有JSONL数据的系统原因
"""
import os
import json
from pathlib import Path

# 没有JSONL数据的6个系统
MISSING_SYSTEMS = {
    "OKX利润分析": {
        "expected_dirs": ["okx_profit_analysis", "profit_analysis", "okx_profit"],
        "description": "OKX交易利润分析系统"
    },
    "数据管理与备份": {
        "expected_dirs": ["data_management", "backup", "data_backup"],
        "description": "数据管理和备份功能页面"
    },
    "重大事件监控": {
        "expected_dirs": ["major_events", "events_monitor", "major_events_monitor"],
        "description": "重大事件监控系统"
    },
    "数据健康监控": {
        "expected_dirs": ["data_health", "health_monitor", "data_monitor"],
        "description": "数据健康状态监控"
    },
    "ZT行高跌盘预警系统": {
        "expected_dirs": ["zt_alert", "zt_warning", "high_low_alert"],
        "description": "涨停跌停预警系统"
    },
    "支撑压力系统配置": {
        "expected_dirs": ["support_resistance_config", "sr_config", "system_config"],
        "description": "支撑压力系统配置页面"
    }
}

def check_system(system_name, info):
    """检查单个系统的数据情况"""
    print(f"\n{'='*60}")
    print(f"系统: {system_name}")
    print(f"说明: {info['description']}")
    print(f"{'='*60}")
    
    # 检查可能的数据目录
    data_base = Path("/home/user/webapp/data")
    found_dirs = []
    
    for expected_dir in info['expected_dirs']:
        dir_path = data_base / expected_dir
        if dir_path.exists():
            found_dirs.append(expected_dir)
            files = list(dir_path.glob("*.jsonl"))
            print(f"✓ 找到目录: {expected_dir}")
            print(f"  - 文件数: {len(files)}")
            if files:
                total_size = sum(f.stat().st_size for f in files)
                print(f"  - 总大小: {total_size / 1024 / 1024:.2f} MB")
                print(f"  - 文件列表:")
                for f in sorted(files)[:5]:
                    print(f"    • {f.name} ({f.stat().st_size / 1024:.2f} KB)")
    
    if not found_dirs:
        print(f"✗ 未找到任何相关数据目录")
        print(f"  可能原因:")
        print(f"  1. 这是一个纯Web功能页面，不需要JSONL数据")
        print(f"  2. 数据采集器尚未启动或未配置")
        print(f"  3. 目录命名与预期不同")
    
    # 检查app.py中的路由
    print(f"\n检查Flask路由:")
    try:
        with open("/home/user/webapp/app.py", "r", encoding="utf-8") as f:
            app_content = f.read()
            
        # 搜索相关路由
        route_keywords = [
            system_name.lower().replace(" ", "-"),
            system_name.lower().replace(" ", "_"),
        ]
        
        found_routes = []
        for line_num, line in enumerate(app_content.split('\n'), 1):
            if '@app.route' in line:
                for keyword in route_keywords:
                    if keyword in line.lower() or system_name[:4] in line:
                        found_routes.append((line_num, line.strip()))
        
        if found_routes:
            print(f"  ✓ 找到相关路由:")
            for line_num, route in found_routes[:3]:
                print(f"    Line {line_num}: {route}")
        else:
            print(f"  ✗ 未找到明确的路由定义")
            print(f"  可能原因: 该系统可能使用通用路由或前端直接调用API")
    
    except Exception as e:
        print(f"  ✗ 检查路由时出错: {e}")
    
    # 检查PM2进程
    print(f"\n检查相关数据采集进程:")
    try:
        import subprocess
        result = subprocess.run(
            ["pm2", "jlist"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            processes = json.loads(result.stdout)
            related_processes = []
            
            for proc in processes:
                proc_name = proc.get('name', '').lower()
                # 搜索相关进程
                for expected_dir in info['expected_dirs']:
                    if expected_dir.replace('_', '-') in proc_name or \
                       system_name[:5].lower() in proc_name:
                        related_processes.append({
                            'name': proc.get('name'),
                            'status': proc.get('pm2_env', {}).get('status'),
                            'pid': proc.get('pid')
                        })
            
            if related_processes:
                print(f"  ✓ 找到相关进程:")
                for proc in related_processes:
                    print(f"    • {proc['name']}: {proc['status']} (PID: {proc['pid']})")
            else:
                print(f"  ✗ 未找到相关数据采集进程")
                print(f"  说明: 该系统可能不需要独立的采集进程")
        
    except Exception as e:
        print(f"  ✗ 检查进程时出错: {e}")
    
    return found_dirs

def main():
    print("="*60)
    print("首页缺少JSONL数据系统分析报告")
    print(f"扫描时间: 2026-02-16")
    print("="*60)
    
    results = {}
    for system_name, info in MISSING_SYSTEMS.items():
        found = check_system(system_name, info)
        results[system_name] = {
            "has_data": len(found) > 0,
            "found_dirs": found
        }
    
    # 总结
    print(f"\n{'='*60}")
    print("总结分析")
    print(f"{'='*60}")
    
    has_data = [k for k, v in results.items() if v['has_data']]
    no_data = [k for k, v in results.items() if not v['has_data']]
    
    print(f"\n✓ 实际有数据目录的系统 ({len(has_data)}):")
    for sys in has_data:
        print(f"  • {sys}: {', '.join(results[sys]['found_dirs'])}")
    
    print(f"\n✗ 确实没有JSONL数据的系统 ({len(no_data)}):")
    for sys in no_data:
        print(f"  • {sys}")
    
    print(f"\n原因分析:")
    print(f"1. 纯Web功能页面 (不需要JSONL数据):")
    print(f"   • 数据管理与备份 - 管理现有数据的工具页面")
    print(f"   • 支撑压力系统配置 - 配置参数页面")
    print(f"\n2. 依赖其他系统数据 (不存储独立JSONL):")
    print(f"   • OKX利润分析 - 基于OKX交易数据计算")
    print(f"   • 重大事件监控 - 聚合多个系统的事件")
    print(f"   • 数据健康监控 - 监控其他系统的数据状态")
    print(f"\n3. 待开发系统:")
    print(f"   • ZT行高跌盘预警系统 - 可能尚未实现数据采集")
    
    print(f"\n建议:")
    print(f"• 纯Web功能页面: 首页可标记为'管理工具'而非'数据系统'")
    print(f"• 依赖其他系统的: 首页显示'基于XX系统数据'说明")
    print(f"• 待开发系统: 首页标记'开发中'或移除链接")

if __name__ == "__main__":
    main()
