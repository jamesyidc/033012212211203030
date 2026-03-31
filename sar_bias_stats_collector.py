#!/usr/bin/env python3
"""
SAR偏多偏空统计历史记录采集器
定期记录符合"2小时周期占比>80%"条件的币种数量，用于绘制趋势图
"""
import json
import time
import requests
from datetime import datetime
from pathlib import Path
import pytz

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 数据目录
DATA_DIR = Path('/home/user/webapp/data/sar_bias_stats')
DATA_DIR.mkdir(parents=True, exist_ok=True)

# JSONL文件路径（按日期分文件）
def get_jsonl_file():
    beijing_now = datetime.now(BEIJING_TZ)
    date_str = beijing_now.strftime('%Y%m%d')
    return DATA_DIR / f'bias_stats_{date_str}.jsonl'

def collect_bias_stats():
    """采集当前的偏多偏空统计（后端API已完成所有计算）"""
    try:
        # 调用API获取所有币种的2小时周期占比（后端已筛选>80%）
        response = requests.get('http://localhost:9002/api/sar-slope/bias-ratios', timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('success'):
            print('❌ API返回数据无效')
            return None
        
        # 后端已经计算好了 >80% 的币种列表，直接使用
        bullish_symbols = data.get('bullish_symbols', [])
        bearish_symbols = data.get('bearish_symbols', [])
        bullish_count = data.get('bullish_count', 0)
        bearish_count = data.get('bearish_count', 0)
        
        # 统计有数据的币种总数
        total_monitored = sum(1 for stats in data.get('data', {}).values() 
                             if stats.get('data_available'))
        
        # 构建记录
        beijing_now = datetime.now(BEIJING_TZ)
        record = {
            'timestamp': int(beijing_now.timestamp() * 1000),  # 毫秒时间戳
            'beijing_time': beijing_now.strftime('%Y-%m-%d %H:%M:%S'),
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'bullish_symbols': bullish_symbols,
            'bearish_symbols': bearish_symbols,
            'total_monitored': total_monitored,
            '_computed_by': 'backend'  # 标记数据来源
        }
        
        print(f'✅ 采集成功: 偏多 {bullish_count}个, 偏空 {bearish_count}个 (后端已计算)')
        
        return record
        
    except Exception as e:
        print(f'❌ 采集失败: {e}')
        import traceback
        traceback.print_exc()
        return None

def save_record(record):
    """保存记录到JSONL文件"""
    if not record:
        return False
    
    try:
        jsonl_file = get_jsonl_file()
        with open(jsonl_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        return True
    except Exception as e:
        print(f'❌ 保存失败: {e}')
        return False

def main():
    """主循环"""
    print('='*60)
    print('SAR偏多偏空统计历史记录采集器')
    print('='*60)
    print(f'数据目录: {DATA_DIR}')
    print(f'采集间隔: 5分钟')
    print('='*60)
    print()
    
    cycle = 0
    
    while True:
        try:
            cycle += 1
            beijing_now = datetime.now(BEIJING_TZ)
            print(f'\n【第 {cycle} 轮采集】 {beijing_now.strftime("%Y-%m-%d %H:%M:%S")}')
            print('-' * 60)
            
            # 采集数据
            record = collect_bias_stats()
            
            if record:
                # 保存记录
                if save_record(record):
                    print(f'✅ 采集成功')
                    print(f'   偏多 >80%: {record["bullish_count"]}个')
                    if record['bullish_symbols']:
                        symbols_str = ', '.join([f'{s["symbol"]}({s["ratio"]}%)' for s in record['bullish_symbols']])
                        print(f'   币种: {symbols_str}')
                    print(f'   偏空 >80%: {record["bearish_count"]}个')
                    if record['bearish_symbols']:
                        symbols_str = ', '.join([f'{s["symbol"]}({s["ratio"]}%)' for s in record['bearish_symbols']])
                        print(f'   币种: {symbols_str}')
                    print(f'   总监控: {record["total_monitored"]}个')
                    print(f'   文件: {get_jsonl_file().name}')
                else:
                    print('❌ 保存失败')
            else:
                print('❌ 采集失败')
            
            # 等待5分钟
            next_time = beijing_now.replace(second=0, microsecond=0)
            # 计算下一个5分钟整点
            minute = next_time.minute
            next_minute = ((minute // 5) + 1) * 5
            if next_minute >= 60:
                next_time = next_time.replace(hour=next_time.hour+1, minute=0)
            else:
                next_time = next_time.replace(minute=next_minute)
            
            wait_seconds = (next_time - beijing_now).total_seconds()
            if wait_seconds < 0:
                wait_seconds = 300  # 默认5分钟
            
            print(f'\n下次采集: {next_time.strftime("%H:%M:%S")} (等待 {int(wait_seconds)} 秒)')
            print('='*60)
            
            time.sleep(wait_seconds)
            
        except KeyboardInterrupt:
            print('\n\n收到退出信号，停止采集...')
            break
        except Exception as e:
            print(f'\n❌ 发生错误: {e}')
            import traceback
            traceback.print_exc()
            print('等待60秒后重试...')
            time.sleep(60)

if __name__ == '__main__':
    main()
