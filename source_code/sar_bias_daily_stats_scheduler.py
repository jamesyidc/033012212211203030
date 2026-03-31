#!/usr/bin/env python3
"""
SAR偏离趋势每日统计定时任务
每天00:05执行，生成前一天的统计
"""
import time
import subprocess
from datetime import datetime, timedelta
import pytz

BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def run_daily_stats_generator():
    """执行每日统计生成"""
    try:
        print('='*60)
        beijing_now = datetime.now(BEIJING_TZ)
        print(f'执行每日统计生成: {beijing_now.strftime("%Y-%m-%d %H:%M:%S")}')
        print('='*60)
        
        # 执行统计生成脚本
        result = subprocess.run(
            ['python3', '/home/user/webapp/source_code/sar_bias_daily_stats_generator.py'],
            cwd='/home/user/webapp',
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        print(result.stdout)
        if result.stderr:
            print('STDERR:', result.stderr)
        
        if result.returncode == 0:
            print('✅ 统计生成成功')
        else:
            print(f'❌ 统计生成失败，退出码: {result.returncode}')
        
        return result.returncode == 0
        
    except Exception as e:
        print(f'❌ 执行失败: {e}')
        import traceback
        traceback.print_exc()
        return False

def calculate_next_run_time():
    """计算下次执行时间（明天00:05）"""
    beijing_now = datetime.now(BEIJING_TZ)
    
    # 明天00:05
    next_run = beijing_now.replace(hour=0, minute=5, second=0, microsecond=0) + timedelta(days=1)
    
    return next_run

def main():
    print('='*60)
    print('SAR偏离趋势每日统计定时任务')
    print('每天00:05执行，生成前一天的统计')
    print('='*60)
    print()
    
    # 首次启动时，如果是00:00-00:10之间，立即执行一次
    beijing_now = datetime.now(BEIJING_TZ)
    if beijing_now.hour == 0 and beijing_now.minute < 10:
        print('🚀 检测到启动时间在00:00-00:10之间，立即执行一次统计生成')
        run_daily_stats_generator()
    
    while True:
        try:
            beijing_now = datetime.now(BEIJING_TZ)
            next_run = calculate_next_run_time()
            
            wait_seconds = (next_run - beijing_now).total_seconds()
            
            print(f'\n⏰ 下次执行时间: {next_run.strftime("%Y-%m-%d %H:%M:%S")}')
            print(f'⏱️  等待时间: {int(wait_seconds/3600)}小时 {int((wait_seconds%3600)/60)}分钟')
            print('-'*60)
            
            # 等待到下次执行时间
            time.sleep(wait_seconds)
            
            # 执行统计生成
            run_daily_stats_generator()
            
        except KeyboardInterrupt:
            print('\n\n收到退出信号，停止定时任务...')
            break
        except Exception as e:
            print(f'\n❌ 发生错误: {e}')
            import traceback
            traceback.print_exc()
            print('等待60秒后继续...')
            time.sleep(60)

if __name__ == '__main__':
    main()
