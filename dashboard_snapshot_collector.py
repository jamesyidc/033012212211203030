#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪表板快照采集器
每分钟记录一次完整的仪表板数据，保存为 JSONL 格式
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import requests

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 数据存储目录
DATA_DIR = project_root / 'data' / 'dashboard_snapshots'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# API 基础 URL
BASE_URL = 'http://127.0.0.1:9002'

def get_beijing_time():
    """获取北京时间"""
    from datetime import timezone, timedelta
    utc_time = datetime.now(timezone.utc)
    beijing_time = utc_time.astimezone(timezone(timedelta(hours=8)))
    return beijing_time

def collect_dashboard_data():
    """采集仪表板数据"""
    try:
        beijing_time = get_beijing_time()
        timestamp = beijing_time.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f'📊 [{timestamp}] 开始采集仪表板数据...')
        
        snapshot = {
            'timestamp': timestamp,
            'beijing_timestamp': int(beijing_time.timestamp() * 1000),
            'date': beijing_time.strftime('%Y-%m-%d'),
            'time': beijing_time.strftime('%H:%M:%S'),
        }
        
        # 1. 获取最新数据（27币涨跌幅之和等）
        try:
            resp = requests.get(f'{BASE_URL}/api/coin-change-tracker/latest', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('success'):
                    latest = data.get('data', {})
                    snapshot['coin_change'] = {
                        'cumulative_pct': latest.get('cumulative_pct'),  # 27币涨跌幅之和
                        'total_rsi': latest.get('total_rsi'),  # RSI之和
                        'avg_rsi': latest.get('total_rsi', 0) / 27 if latest.get('total_rsi') else None,
                        'up_coins': latest.get('up_coins'),  # 上涨币数
                        'down_coins': latest.get('down_coins'),  # 下跌币数
                        'timestamp': latest.get('timestamp'),
                    }
                    print(f'  ✅ 27币涨跌幅: {latest.get("cumulative_pct")}%')
        except Exception as e:
            print(f'  ❌ 获取最新数据失败: {e}')
            snapshot['coin_change'] = None
        
        # 2. 获取阿比值（A/B 比值）
        try:
            # 这里需要找到阿比值的API，暂时预留
            # resp = requests.get(f'{BASE_URL}/api/ab-ratio/latest', timeout=5)
            # 暂时从其他地方获取
            snapshot['ab_ratio'] = {
                'value': None,  # 阿比值
                'trend': None,  # 趋势
            }
        except Exception as e:
            print(f'  ❌ 获取阿比值失败: {e}')
            snapshot['ab_ratio'] = None
        
        # 3. 获取正负占比
        try:
            resp = requests.get(f'{BASE_URL}/api/coin-change-tracker/positive-ratio-stats', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('success'):
                    stats = data.get('stats', {})
                    snapshot['positive_ratio'] = {
                        'positive_count': stats.get('positive_count'),  # 正数时段数
                        'total_count': stats.get('total_count'),  # 总时段数
                        'ratio': stats.get('positive_ratio'),  # 正数占比
                    }
                    print(f'  ✅ 正负占比: {stats.get("positive_count")}/{stats.get("total_count")}')
        except Exception as e:
            print(f'  ❌ 获取正负占比失败: {e}')
            snapshot['positive_ratio'] = None
        
        # 4. 获取上涨占比
        try:
            # 从最新数据计算
            if snapshot.get('coin_change'):
                up = snapshot['coin_change'].get('up_coins', 0)
                down = snapshot['coin_change'].get('down_coins', 0)
                total = up + down
                snapshot['up_ratio'] = {
                    'up_count': up,
                    'down_count': down,
                    'total_count': total,
                    'percentage': (up / total * 100) if total > 0 else 0,
                }
                print(f'  ✅ 上涨占比: {snapshot["up_ratio"]["percentage"]:.1f}%')
        except Exception as e:
            print(f'  ❌ 计算上涨占比失败: {e}')
            snapshot['up_ratio'] = None
        
        # 5. 获取单币涨跌幅
        try:
            resp = requests.get(f'{BASE_URL}/api/coin-change-tracker/latest', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('success'):
                    latest = data.get('data', {})
                    changes = latest.get('changes', {})
                    snapshot['individual_coins'] = []
                    for symbol, coin_data in changes.items():
                        snapshot['individual_coins'].append({
                            'symbol': symbol,
                            'change_pct': coin_data.get('change_pct'),
                            'price': coin_data.get('price'),
                        })
                    print(f'  ✅ 单币数据: {len(snapshot["individual_coins"])} 个')
        except Exception as e:
            print(f'  ❌ 获取单币数据失败: {e}')
            snapshot['individual_coins'] = []
        
        # 6. 获取SAR偏向统计
        try:
            resp = requests.get(f'{BASE_URL}/api/coin-change-tracker/sar-bias-stats', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('success'):
                    stats = data.get('stats', {})
                    snapshot['sar_bias'] = {
                        'bullish_count': stats.get('total_bullish'),  # 看涨数量
                        'bearish_count': stats.get('total_bearish'),  # 看跌数量
                        'total': stats.get('total_bullish', 0) + stats.get('total_bearish', 0),
                    }
                    print(f'  ✅ SAR统计: 看涨{stats.get("total_bullish")} 看跌{stats.get("total_bearish")}')
        except Exception as e:
            print(f'  ❌ 获取SAR统计失败: {e}')
            snapshot['sar_bias'] = None
        
        # 7. 获取5分钟涨速统计
        try:
            resp = requests.get(f'{BASE_URL}/api/coin-change-tracker/velocity-stats', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('success'):
                    stats = data.get('stats', {})
                    snapshot['velocity_stats'] = {
                        'max': stats.get('max'),
                        'min': stats.get('min'),
                        'avg': stats.get('avg'),
                        'data_start_time': stats.get('data_start_time'),
                    }
                    print(f'  ✅ 5分钟涨速: 最高{stats.get("max")}% 最低{stats.get("min")}% 平均{stats.get("avg")}%')
        except Exception as e:
            print(f'  ❌ 获取涨速统计失败: {e}')
            snapshot['velocity_stats'] = None
        
        # 8. 获取日内模式预测
        try:
            resp = requests.get(f'{BASE_URL}/api/coin-change-tracker/daily-prediction', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('success'):
                    prediction = data.get('data', {})  # 修复：使用'data'而不是'prediction'
                    color_counts = prediction.get('color_counts', {})
                    snapshot['daily_prediction'] = {
                        'signal': prediction.get('signal'),
                        'date': prediction.get('date'),
                        'timestamp': prediction.get('timestamp'),
                        'description': prediction.get('description'),
                        'green_count': color_counts.get('green', 0),
                        'red_count': color_counts.get('red', 0),
                        'yellow_count': color_counts.get('yellow', 0),
                        'blank_count': color_counts.get('blank', 0),
                        'is_final': prediction.get('is_final', False),
                    }
                    print(f'  ✅ 日内预测: {prediction.get("signal")} (绿{color_counts.get("green")}红{color_counts.get("red")}黄{color_counts.get("yellow")})')
            else:
                snapshot['daily_prediction'] = None
        except Exception as e:
            print(f'  ❌ 获取日内预测失败: {e}')
            snapshot['daily_prediction'] = None
        
        # 9. 获取BTC数据
        try:
            resp = requests.get(f'{BASE_URL}/api/coin-change-tracker/latest', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('success'):
                    changes = data.get('data', {}).get('changes', {})
                    btc = changes.get('BTC', {})
                    snapshot['btc'] = {
                        'change_pct': btc.get('change_pct'),
                        'price': btc.get('price'),
                    }
        except Exception as e:
            print(f'  ❌ 获取BTC数据失败: {e}')
            snapshot['btc'] = None
        
        # 10. 获取ETH数据
        try:
            resp = requests.get(f'{BASE_URL}/api/coin-change-tracker/latest', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('success'):
                    changes = data.get('data', {}).get('changes', {})
                    eth = changes.get('ETH', {})
                    snapshot['eth'] = {
                        'change_pct': eth.get('change_pct'),
                        'price': eth.get('price'),
                    }
        except Exception as e:
            print(f'  ❌ 获取ETH数据失败: {e}')
            snapshot['eth'] = None
        
        # 11. 获取BTC/ETH比率
        try:
            resp = requests.get(f'{BASE_URL}/api/btc-eth-ratio/latest', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('success'):
                    ratio_data = data.get('data', {})
                    snapshot['btc_eth_ratio'] = {
                        'ratio': ratio_data.get('ratio'),
                        'btc_dominance': ratio_data.get('btc_dominance'),
                    }
                    print(f'  ✅ BTC/ETH比率: {ratio_data.get("ratio")}')
        except Exception as e:
            print(f'  ❌ 获取BTC/ETH比率失败: {e}')
            snapshot['btc_eth_ratio'] = None
        
        return snapshot
        
    except Exception as e:
        print(f'❌ 采集数据异常: {e}')
        import traceback
        traceback.print_exc()
        return None

def save_snapshot(snapshot):
    """保存快照到 JSONL 文件"""
    if not snapshot:
        print('⚠️ 快照为空，跳过保存')
        return
    
    try:
        date = snapshot['date']
        filename = f'dashboard_snapshot_{date.replace("-", "")}.jsonl'
        filepath = DATA_DIR / filename
        
        # 追加写入 JSONL
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(snapshot, ensure_ascii=False) + '\n')
        
        print(f'✅ 快照已保存: {filepath}')
        
    except Exception as e:
        print(f'❌ 保存快照失败: {e}')
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print('=' * 60)
    print('仪表板快照采集器启动')
    print('=' * 60)
    
    while True:
        try:
            # 采集数据
            snapshot = collect_dashboard_data()
            
            # 保存数据
            if snapshot:
                save_snapshot(snapshot)
            
            # 等待60秒
            print(f'⏰ 等待60秒后进行下一次采集...\n')
            time.sleep(60)
            
        except KeyboardInterrupt:
            print('\n👋 收到退出信号，停止采集')
            break
        except Exception as e:
            print(f'❌ 主循环异常: {e}')
            import traceback
            traceback.print_exc()
            time.sleep(60)

if __name__ == '__main__':
    main()
