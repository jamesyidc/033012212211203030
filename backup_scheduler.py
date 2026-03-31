#!/usr/bin/env python3
"""
备份调度器
每12小时自动执行一次备份
"""

import time
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BACKUP_INTERVAL = 12 * 60 * 60  # 12小时（秒）
BACKUP_SCRIPT = Path('/home/user/webapp/auto_backup_system.py')

def get_beijing_time():
    """获取北京时间"""
    beijing_tz = timezone(timedelta(hours=8))
    return datetime.now(beijing_tz)

def run_backup():
    """运行备份脚本"""
    beijing_time = get_beijing_time()
    print(f"\n{'='*80}")
    print(f"🔄 开始执行备份任务")
    print(f"⏰ 时间: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
    print(f"{'='*80}\n")
    
    try:
        # 执行备份脚本
        result = subprocess.run(
            [sys.executable, str(BACKUP_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )
        
        # 输出结果
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"⚠️ 错误输出:\n{result.stderr}", file=sys.stderr)
        
        if result.returncode == 0:
            print(f"\n✅ 备份任务完成 (退出码: {result.returncode})")
        else:
            print(f"\n❌ 备份任务失败 (退出码: {result.returncode})")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"❌ 备份超时（超过10分钟）")
        return False
    except Exception as e:
        print(f"❌ 备份执行出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主循环"""
    print("="*80)
    print("🚀 备份调度器已启动")
    print(f"⏱️  备份间隔: {BACKUP_INTERVAL / 3600} 小时")
    print(f"📜 备份脚本: {BACKUP_SCRIPT}")
    print("="*80)
    
    # 立即执行一次备份
    print("\n🎯 执行首次备份...")
    run_backup()
    
    # 定时执行
    while True:
        next_backup_time = get_beijing_time() + timedelta(seconds=BACKUP_INTERVAL)
        print(f"\n⏰ 下次备份时间: {next_backup_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
        print(f"😴 等待 {BACKUP_INTERVAL / 3600} 小时...")
        
        time.sleep(BACKUP_INTERVAL)
        
        # 执行备份
        run_backup()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ 备份调度器已停止")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 备份调度器出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
