#!/usr/bin/env python3
"""
创新高创新低统计采集器 v2.0
New High/Low Statistics Collector

核心逻辑：
1. 维护每个币种的历史最高价和最低价
2. 每次采集时比较当前价格：
   - 如果 当前价格 > 历史最高价 → 创新高事件，更新最高价
   - 如果 当前价格 < 历史最低价 → 创新低事件，更新最低价
3. 记录每次创新高/创新低事件到JSONL文件

数据文件：
1. coin_highs_lows_state.json - 每个币种的当前最高/最低价状态
2. new_high_low_events_YYYYMMDD.jsonl - 每日事件记录

状态文件格式：
{
    "BTC": {
        "highest_price": 69500.5,
        "highest_time": "2026-02-16 14:30:00",
        "lowest_price": 65000.2,
        "lowest_time": "2026-02-15 08:15:00"
    },
    ...
}

事件记录格式：
{
    "time": "2026-02-16 14:30:00",
    "timestamp": 1708070400,
    "symbol": "BTC",
    "event_type": "new_high",  # 或 "new_low"
    "price": 69500.5,
    "previous_high": 69200.0,  # 或 previous_low
    "previous_time": "2026-02-15 18:20:00"
}
"""

import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# 配置
BASE_DIR = Path(__file__).parent.parent
SOURCE_DATA_DIR = BASE_DIR / 'data' / 'price_position'
OUTPUT_DATA_DIR = BASE_DIR / 'data' / 'new_high_low'
STATE_FILE = OUTPUT_DATA_DIR / 'coin_highs_lows_state.json'
COLLECT_INTERVAL = 180  # 3分钟

# 创建输出目录
OUTPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def get_beijing_time():
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)

def load_state():
    """
    加载币种最高/最低价状态
    
    Returns:
        dict: 币种状态字典
    """
    if not STATE_FILE.exists():
        return {}
    
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载状态文件失败: {e}")
        return {}

def save_state(state):
    """
    保存币种最高/最低价状态
    
    Args:
        state: 币种状态字典
    """
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        print(f"✅ 状态文件已保存: {STATE_FILE}")
    except Exception as e:
        print(f"❌ 保存状态文件失败: {e}")

def save_event(event, date_str):
    """
    保存创新高/创新低事件
    
    Args:
        event: 事件字典
        date_str: 日期字符串 YYYYMMDD
    """
    file_path = OUTPUT_DATA_DIR / f'new_high_low_events_{date_str}.jsonl'
    
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    except Exception as e:
        print(f"❌ 保存事件失败: {e}")

def process_snapshot(snapshot, state):
    """
    处理一个快照，检测创新高/创新低
    
    Args:
        snapshot: 价格快照记录
        state: 当前状态字典
    
    Returns:
        list: 事件列表
    """
    events = []
    snapshot_time = snapshot.get('snapshot_time', '')
    
    if not snapshot_time:
        return events
    
    try:
        snapshot_dt = BEIJING_TZ.localize(datetime.strptime(snapshot_time, '%Y-%m-%d %H:%M:%S'))
        timestamp = snapshot_dt.timestamp()
    except Exception:
        return events
    
    # 检查每个币种
    for coin in snapshot.get('positions', []):
        symbol = coin.get('inst_id', '').replace('-USDT-SWAP', '')
        current_price = coin.get('current_price', 0)
        
        if current_price <= 0:
            continue
        
        # 初始化该币种的状态
        if symbol not in state:
            state[symbol] = {
                'highest_price': current_price,
                'highest_time': snapshot_time,
                'lowest_price': current_price,
                'lowest_time': snapshot_time
            }
            print(f"📊 初始化 {symbol}: 最高={current_price}, 最低={current_price}")
            continue
        
        coin_state = state[symbol]
        
        # 检测创新高
        if current_price > coin_state['highest_price']:
            event = {
                'time': snapshot_time,
                'timestamp': timestamp,
                'symbol': symbol,
                'event_type': 'new_high',
                'price': current_price,
                'previous_high': coin_state['highest_price'],
                'previous_time': coin_state['highest_time']
            }
            events.append(event)
            
            # 更新最高价
            coin_state['highest_price'] = current_price
            coin_state['highest_time'] = snapshot_time
            
            print(f"🔥 {symbol} 创新高: {current_price} (前高: {event['previous_high']})")
        
        # 检测创新低
        if current_price < coin_state['lowest_price']:
            event = {
                'time': snapshot_time,
                'timestamp': timestamp,
                'symbol': symbol,
                'event_type': 'new_low',
                'price': current_price,
                'previous_low': coin_state['lowest_price'],
                'previous_time': coin_state['lowest_time']
            }
            events.append(event)
            
            # 更新最低价
            coin_state['lowest_price'] = current_price
            coin_state['lowest_time'] = snapshot_time
            
            print(f"❄️  {symbol} 创新低: {current_price} (前低: {event['previous_low']})")
    
    return events

def process_latest_data(state):
    """
    处理最新的价格位置数据
    
    Args:
        state: 当前状态字典
    
    Returns:
        int: 新增事件数量
    """
    now = get_beijing_time()
    date_str = now.strftime('%Y%m%d')
    
    # 读取今天的数据文件
    file_path = SOURCE_DATA_DIR / f'price_position_{date_str}.jsonl'
    
    if not file_path.exists():
        print(f"⚠️  数据文件不存在: {file_path}")
        return 0
    
    # 读取文件中最后一条记录（最新数据）
    last_record = None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        last_record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"❌ 读取数据文件失败: {e}")
        return 0
    
    if not last_record:
        print(f"⚠️  没有有效的数据记录")
        return 0
    
    print(f"📊 处理快照: {last_record.get('snapshot_time', 'unknown')}")
    
    # 处理快照，检测创新高/创新低
    events = process_snapshot(last_record, state)
    
    # 保存事件
    for event in events:
        save_event(event, date_str)
    
    if events:
        print(f"✅ 检测到 {len(events)} 个新事件")
    
    return len(events)

def display_state_summary(state):
    """
    显示状态摘要
    
    Args:
        state: 状态字典
    """
    if not state:
        print("📊 当前没有状态数据")
        return
    
    print(f"\n{'='*80}")
    print(f"📊 币种最高/最低价状态摘要 (共{len(state)}个币种)")
    print(f"{'='*80}")
    
    # 按最高价排序，显示前5名
    sorted_by_high = sorted(state.items(), key=lambda x: x[1]['highest_price'], reverse=True)[:5]
    print(f"\n🔥 最高价TOP5:")
    for symbol, data in sorted_by_high:
        print(f"   {symbol:6s}: ${data['highest_price']:>10.2f}  ({data['highest_time']})")
    
    # 按最低价排序，显示前5名
    sorted_by_low = sorted(state.items(), key=lambda x: x[1]['lowest_price'])[:5]
    print(f"\n❄️  最低价TOP5:")
    for symbol, data in sorted_by_low:
        print(f"   {symbol:6s}: ${data['lowest_price']:>10.2f}  ({data['lowest_time']})")
    
    print(f"{'='*80}\n")

def main():
    """主函数"""
    print("="*80)
    print("🚀 创新高创新低统计采集器 v2.0 启动")
    print("="*80)
    print(f"📂 源数据目录: {SOURCE_DATA_DIR}")
    print(f"📂 输出数据目录: {OUTPUT_DATA_DIR}")
    print(f"📄 状态文件: {STATE_FILE}")
    print(f"⏱️  采集间隔: {COLLECT_INTERVAL} 秒 ({COLLECT_INTERVAL // 60} 分钟)")
    print("="*80)
    
    # 加载状态
    state = load_state()
    print(f"📊 已加载 {len(state)} 个币种的历史状态")
    
    # 显示初始状态摘要
    if state:
        display_state_summary(state)
    
    # 🔥 冷启动优化：立即执行首次采集（不等待3分钟）
    print(f"\n{'='*80}")
    print("⚡ 冷启动优化：立即执行首次采集...")
    print(f"{'='*80}")
    try:
        new_events = process_latest_data(state)
        if new_events > 0:
            save_state(state)
            print(f"✅ 冷启动采集完成，检测到 {new_events} 个新事件")
        else:
            print("ℹ️  冷启动采集完成，未检测到新事件")
        print(f"   追踪币种: {len(state)} 个")
    except Exception as e:
        print(f"⚠️  冷启动采集失败: {e}")
        import traceback
        traceback.print_exc()
    print(f"{'='*80}\n")
    
    iteration = 0
    
    while True:
        try:
            iteration += 1
            now = get_beijing_time()
            
            print(f"\n{'='*80}")
            print(f"🔄 第 {iteration} 次采集 - {now.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*80}")
            
            # 处理最新数据
            new_events = process_latest_data(state)
            
            # 保存状态
            save_state(state)
            
            # 每10次迭代显示一次状态摘要
            if iteration % 10 == 0:
                display_state_summary(state)
            
            print(f"\n📊 本次统计:")
            print(f"   新增事件: {new_events} 个")
            print(f"   追踪币种: {len(state)} 个")
            
            # 等待下一次采集
            print(f"\n⏳ 等待 {COLLECT_INTERVAL} 秒后进行下一次采集...")
            time.sleep(COLLECT_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n👋 收到退出信号，正在停止...")
            print("💾 保存最终状态...")
            save_state(state)
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()
            print(f"\n⏳ 等待 {COLLECT_INTERVAL} 秒后重试...")
            time.sleep(COLLECT_INTERVAL)
    
    print("\n✅ 采集器已停止")

if __name__ == '__main__':
    main()
