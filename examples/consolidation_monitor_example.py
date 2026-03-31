#!/usr/bin/env python3
"""
横盘监控数据查询和分析示例

演示如何使用 API 和本地文件读取横盘监控数据
"""

import requests
import json
from datetime import datetime, timedelta
from pathlib import Path


# API 基础 URL
API_BASE = "http://localhost:9002"


def example_1_get_current_status():
    """示例 1: 获取当前实时状态"""
    print("\n" + "="*60)
    print("示例 1: 获取当前实时状态")
    print("="*60)
    
    url = f"{API_BASE}/api/consolidation-monitor/status"
    response = requests.get(url)
    data = response.json()
    
    if data['success']:
        print(f"更新时间: {data['update_time']}\n")
        
        for symbol in ['BTC', 'ETH']:
            if symbol in data['data']:
                info = data['data'][symbol]
                print(f"{symbol} 永续合约:")
                print(f"  时间: {info['datetime']}")
                print(f"  价格: ${info['price']:,.2f}")
                print(f"  涨跌幅: {info['change_percent_display']}")
                print(f"  是否横盘: {'是' if info['is_consolidation'] else '否'}")
                print(f"  连续次数: {info['consecutive_count']}")
                
                if info['consecutive_count'] >= 3:
                    print(f"  ⚠️ 告警: 连续{info['consecutive_count']}次横盘，要变盘了！")
                print()


def example_2_query_available_dates():
    """示例 2: 查询可用的历史日期"""
    print("\n" + "="*60)
    print("示例 2: 查询可用的历史日期")
    print("="*60)
    
    for symbol in ['BTC-USDT-SWAP', 'ETH-USDT-SWAP']:
        url = f"{API_BASE}/api/consolidation-monitor/dates"
        params = {'symbol': symbol}
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['success']:
            print(f"\n{symbol} 可用日期（共 {data['count']} 天）:")
            for date_info in data['dates'][:5]:  # 只显示最近5天
                print(f"  {date_info['formatted']} ({date_info['file']})")


def example_3_query_history_data():
    """示例 3: 查询历史数据"""
    print("\n" + "="*60)
    print("示例 3: 查询历史数据（最近10条）")
    print("="*60)
    
    symbol = 'BTC-USDT-SWAP'
    url = f"{API_BASE}/api/consolidation-monitor/history"
    params = {
        'symbol': symbol,
        'limit': 10
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    if data['success']:
        print(f"\n{symbol} 最近 {data['count']} 条记录:\n")
        
        for record in data['records']:
            status = "🟢 横盘" if record['is_consolidation'] else "🔴 波动"
            consecutive = f"[连续{record['consecutive_count']}]" if record['consecutive_count'] > 0 else ""
            
            print(f"{record['datetime']} - "
                  f"{status} {consecutive} - "
                  f"{record['change_percent_display']} - "
                  f"${record['price']:,.2f}")


def example_4_query_daily_stats():
    """示例 4: 查询每日统计数据"""
    print("\n" + "="*60)
    print("示例 4: 查询每日统计数据")
    print("="*60)
    
    for symbol in ['BTC-USDT-SWAP', 'ETH-USDT-SWAP']:
        url = f"{API_BASE}/api/consolidation-monitor/stats"
        params = {'symbol': symbol}
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['success']:
            stats = data['stats']
            print(f"\n{symbol} 统计数据:")
            print(f"  总记录数: {stats['total_count']}")
            print(f"  横盘记录数: {stats['consolidation_count']}")
            print(f"  横盘比例: {stats['consolidation_ratio']}%")
            print(f"  最大连续次数: {stats['max_consecutive']}")
            print(f"  告警次数: {stats['alert_count']}")
            print(f"  平均涨跌幅: {stats['avg_change_percent']}%")
            print(f"  价格范围: ${stats['price_range']['min']:,.2f} - ${stats['price_range']['max']:,.2f}")
            print(f"  时间范围: {stats['time_range']['first']} - {stats['time_range']['last']}")
            
            if data['alert_moments']:
                print(f"\n  告警时刻:")
                for alert in data['alert_moments']:
                    print(f"    {alert['datetime']}: 连续{alert['consecutive_count']}次 ({alert['change_percent_display']})")


def example_5_read_local_file():
    """示例 5: 直接读取本地 JSONL 文件"""
    print("\n" + "="*60)
    print("示例 5: 直接读取本地 JSONL 文件")
    print("="*60)
    
    data_dir = Path('/home/user/webapp/data/consolidation_monitor')
    today = datetime.now().strftime('%Y%m%d')
    
    for symbol in ['BTC_USDT_SWAP', 'ETH_USDT_SWAP']:
        jsonl_file = data_dir / f'consolidation_{symbol}_{today}.jsonl'
        
        if jsonl_file.exists():
            records = []
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            
            print(f"\n{symbol.replace('_', '-')} (文件读取):")
            print(f"  文件: {jsonl_file.name}")
            print(f"  记录数: {len(records)}")
            
            if records:
                latest = records[-1]
                print(f"  最新记录:")
                print(f"    时间: {latest['datetime']}")
                print(f"    涨跌幅: {latest['change_percent_display']}")
                print(f"    价格: ${latest['price']:,.2f}")
                print(f"    连续横盘: {latest['consecutive_count']}次")
                
                # 统计横盘记录
                consolidation_count = sum(1 for r in records if r['is_consolidation'])
                print(f"  横盘记录: {consolidation_count}/{len(records)} ({consolidation_count/len(records)*100:.1f}%)")


def example_6_find_consolidation_periods():
    """示例 6: 查找横盘周期"""
    print("\n" + "="*60)
    print("示例 6: 查找横盘周期")
    print("="*60)
    
    data_dir = Path('/home/user/webapp/data/consolidation_monitor')
    today = datetime.now().strftime('%Y%m%d')
    symbol = 'BTC_USDT_SWAP'
    jsonl_file = data_dir / f'consolidation_{symbol}_{today}.jsonl'
    
    if jsonl_file.exists():
        records = []
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        # 找出所有横盘周期（连续3次或以上）
        periods = []
        current_period = []
        
        for record in records:
            if record['is_consolidation']:
                current_period.append(record)
            else:
                if len(current_period) >= 3:
                    periods.append(current_period)
                current_period = []
        
        # 检查最后一个周期
        if len(current_period) >= 3:
            periods.append(current_period)
        
        print(f"\nBTC-USDT-SWAP 横盘周期（连续≥3次）:")
        print(f"找到 {len(periods)} 个横盘周期\n")
        
        for i, period in enumerate(periods, 1):
            start_time = period[0]['datetime']
            end_time = period[-1]['datetime']
            duration = len(period)
            avg_change = sum(abs(r['change_percent']) for r in period) / len(period) * 100
            
            print(f"周期 {i}:")
            print(f"  时间: {start_time} - {end_time}")
            print(f"  持续: {duration} 个5分钟 ({duration * 5} 分钟)")
            print(f"  平均涨跌幅: {avg_change:.3f}%")
            print()


def example_7_analyze_alert_effectiveness():
    """示例 7: 分析告警有效性"""
    print("\n" + "="*60)
    print("示例 7: 分析告警有效性（告警后价格变化）")
    print("="*60)
    
    url = f"{API_BASE}/api/consolidation-monitor/stats"
    params = {'symbol': 'BTC-USDT-SWAP'}
    response = requests.get(url, params=params)
    data = response.json()
    
    if data['success'] and data['alert_moments']:
        # 获取完整历史数据
        history_url = f"{API_BASE}/api/consolidation-monitor/history"
        history_response = requests.get(history_url, params={'symbol': 'BTC-USDT-SWAP'})
        history_data = history_response.json()
        
        if history_data['success']:
            records = {r['timestamp']: r for r in history_data['records']}
            
            print(f"\nBTC-USDT-SWAP 告警有效性分析:\n")
            
            for alert in data['alert_moments']:
                alert_time = alert['timestamp']
                
                # 查找告警后30分钟内的价格变化（6个5分钟K线）
                alert_record = records.get(alert_time)
                if alert_record:
                    alert_price = alert_record['price']
                    
                    # 找后续记录
                    future_records = [r for r in history_data['records'] 
                                    if r['timestamp'] > alert_time 
                                    and r['timestamp'] <= alert_time + 30*60*1000]
                    
                    if future_records:
                        max_price = max(r['price'] for r in future_records)
                        min_price = min(r['price'] for r in future_records)
                        
                        max_change = (max_price - alert_price) / alert_price * 100
                        min_change = (min_price - alert_price) / alert_price * 100
                        
                        print(f"告警时间: {alert['datetime']}")
                        print(f"  连续次数: {alert['consecutive_count']}")
                        print(f"  告警价格: ${alert_price:,.2f}")
                        print(f"  后续30分钟价格变化:")
                        print(f"    最高: ${max_price:,.2f} ({max_change:+.2f}%)")
                        print(f"    最低: ${min_price:,.2f} ({min_change:+.2f}%)")
                        
                        # 判断是否有效
                        max_abs_change = max(abs(max_change), abs(min_change))
                        if max_abs_change > 0.5:
                            print(f"    ✅ 有效告警 - 后续波动 {max_abs_change:.2f}%")
                        else:
                            print(f"    ⚠️ 继续横盘 - 波动仅 {max_abs_change:.2f}%")
                        print()


def main():
    """运行所有示例"""
    print("\n" + "🔍 横盘监控数据查询和分析示例".center(60, "="))
    
    try:
        # 运行各个示例
        example_1_get_current_status()
        example_2_query_available_dates()
        example_3_query_history_data()
        example_4_query_daily_stats()
        example_5_read_local_file()
        example_6_find_consolidation_periods()
        example_7_analyze_alert_effectiveness()
        
        print("\n" + "="*60)
        print("✅ 所有示例执行完成")
        print("="*60 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误: 无法连接到 API 服务器")
        print("请确保 Flask 应用正在运行: pm2 status flask-app")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
