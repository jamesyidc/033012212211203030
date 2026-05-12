#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立备份调度守护进程 - 不依赖 Flask 进程，独立运行
每5分钟检查一次，距上次备份超过12小时则自动执行备份

【修复记录 2026-04-16】
1. last_backup_time() 增加完整性检查：残缺文件（<354MB）不计入"已备份"
2. 所有日志同时写入 /tmp/backup_scheduler.log 文件，方便排查
3. run_backup() 超时后强制 kill 子进程，不让僵尸进程占用资源
4. 备份前检查 /tmp 可用空间，不足时跳过并警告
5. 启动时立即检查（不等60s），让页面关闭后重启也能快速备份
"""

import os
import sys
import time
import subprocess
import signal
from datetime import datetime, timezone, timedelta
from pathlib import Path

BACKUP_INTERVAL_SEC  = 12 * 3600          # 12小时
BACKUP_SCRIPT        = '/home/user/webapp/auto_backup_system.py'
CHECK_INTERVAL_SEC   = 300                 # 每5分钟检查一次
BJ_TZ                = timezone(timedelta(hours=8))
LOG_FILE             = Path('/tmp/backup_scheduler.log')
MIN_VALID_SIZE_BYTES = 354 * 1024 * 1024  # 354MB，低于此为残缺文件
MIN_FREE_SPACE_MB    = 600                 # /tmp 至少需要600MB空闲才启动备份


def now_bj():
    return datetime.now(BJ_TZ)


def log(msg):
    ts = now_bj().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[BackupScheduler] {ts} {msg}"
    print(line, flush=True)
    # 同时写入日志文件
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
        # 日志文件超过5MB时截断，只保留最新2MB
        if LOG_FILE.stat().st_size > 5 * 1024 * 1024:
            content = LOG_FILE.read_text(encoding='utf-8')
            LOG_FILE.write_text(content[-2 * 1024 * 1024:], encoding='utf-8')
    except Exception:
        pass


def is_valid_backup(path: Path) -> bool:
    """判断备份文件是否完整（大于354MB）"""
    try:
        return path.stat().st_size >= MIN_VALID_SIZE_BYTES
    except Exception:
        return False


def last_backup_time():
    """
    从 /tmp 和 aidrive 中取最新【完整】备份文件的修改时间。
    残缺文件（<354MB）不计入，避免误判为"已备份"。
    """
    candidates = []

    # 扫描 /tmp
    for p in Path('/tmp').glob('webapp_backup_*.tar.gz'):
        if is_valid_backup(p):
            candidates.append(p)
        else:
            size_mb = p.stat().st_size / 1024 / 1024
            log(f"⚠️  跳过残缺文件 {p.name}（{size_mb:.1f}MB < 354MB）")

    # 也扫描 aidrive 做参考（aidrive文件有效则说明曾经备份成功过）
    for aidrive_dir in [Path('/home/user/aidrive'), Path('/mnt/aidrive')]:
        if aidrive_dir.exists():
            for p in aidrive_dir.glob('webapp_backup_*.tar.gz'):
                if is_valid_backup(p):
                    candidates.append(p)

    if not candidates:
        return None, None

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    best = candidates[0]
    return datetime.fromtimestamp(best.stat().st_mtime, tz=BJ_TZ), best.name


def check_free_space_mb():
    """检查 / 文件系统剩余空间（MB）"""
    try:
        stat = os.statvfs('/tmp')
        return stat.f_bavail * stat.f_frsize / 1024 / 1024
    except Exception:
        return 9999


def cleanup_stale_backups():
    """清理残缺的 /tmp 备份文件（防止它们阻碍判断）"""
    removed = []
    for p in Path('/tmp').glob('webapp_backup_*.tar.gz'):
        if not is_valid_backup(p):
            try:
                size_mb = p.stat().st_size / 1024 / 1024
                p.unlink()
                removed.append(f"{p.name}({size_mb:.1f}MB)")
            except Exception as e:
                log(f"⚠️  无法删除残缺文件 {p.name}: {e}")
    if removed:
        log(f"🗑️  已清理残缺备份文件: {', '.join(removed)}")


def run_backup():
    log("🚀 开始执行备份...")

    # 先清理残缺文件
    cleanup_stale_backups()

    # 检查磁盘空间
    free_mb = check_free_space_mb()
    log(f"💾 当前可用磁盘空间: {free_mb:.0f} MB")
    if free_mb < MIN_FREE_SPACE_MB:
        log(f"❌ 磁盘空间不足（{free_mb:.0f}MB < {MIN_FREE_SPACE_MB}MB），跳过本次备份")
        return

    proc = None
    try:
        proc = subprocess.Popen(
            [sys.executable, BACKUP_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        log(f"📋 备份进程已启动 PID={proc.pid}")

        # 流式读取输出并写日志，同时等待完成（最多40分钟）
        timeout_sec = 40 * 60
        start = time.time()
        output_lines = []

        while True:
            elapsed = time.time() - start
            if elapsed > timeout_sec:
                log(f"❌ 备份超时（>{timeout_sec/60:.0f}分钟），强制终止进程 PID={proc.pid}")
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except Exception:
                    proc.kill()
                proc.wait()
                # 清理超时产生的残缺文件
                cleanup_stale_backups()
                return

            # 非阻塞读一行
            try:
                line = proc.stdout.readline()
            except Exception:
                break

            if line:
                line = line.rstrip()
                output_lines.append(line)
                # 只把关键行写进日志（减少噪音）
                if any(kw in line for kw in ['✅', '❌', '⚠️', '🚀', '☁️', '📦', '备份']):
                    log(f"  [backup] {line}")
            elif proc.poll() is not None:
                break
            else:
                time.sleep(0.5)

        # 读取剩余输出
        try:
            remaining = proc.stdout.read()
            if remaining:
                for line in remaining.strip().splitlines():
                    output_lines.append(line)
        except Exception:
            pass

        returncode = proc.wait()

        if returncode == 0:
            log("✅ 备份脚本执行成功")
        elif returncode == 1:
            log("⚠️  备份脚本退出码=1（某些文件被修改，但通常备份仍然成功）")
        else:
            tail = '\n'.join(output_lines[-15:])
            log(f"❌ 备份失败 (returncode={returncode})\n最后输出:\n{tail}")

        # 验证备份是否真的成功了
        valid_files = [p for p in Path('/tmp').glob('webapp_backup_*.tar.gz') if is_valid_backup(p)]
        if valid_files:
            latest = max(valid_files, key=lambda p: p.stat().st_mtime)
            size_mb = latest.stat().st_size / 1024 / 1024
            log(f"✅ 最新完整备份: {latest.name} ({size_mb:.1f}MB)")
        else:
            log("❌ 备份后没有找到有效的完整备份文件！")

    except Exception as e:
        log(f"❌ 备份异常: {e}")
        import traceback
        log(traceback.format_exc())
        if proc:
            try:
                proc.kill()
                proc.wait()
            except Exception:
                pass
        cleanup_stale_backups()


def main():
    log("=" * 60)
    log("备份调度守护进程已启动（每12小时备份，每5分钟检查）")
    log(f"备份脚本: {BACKUP_SCRIPT}")
    log(f"日志文件: {LOG_FILE}")
    log(f"最小有效备份大小: {MIN_VALID_SIZE_BYTES/1024/1024:.0f} MB")
    log("=" * 60)

    while True:
        try:
            last_t, last_name = last_backup_time()
            now_t = now_bj()

            if last_t is None:
                log("从未成功备份过（或所有备份文件残缺），立即执行首次备份")
                run_backup()
            else:
                elapsed = (now_t - last_t).total_seconds()
                if elapsed >= BACKUP_INTERVAL_SEC:
                    log(f"距上次完整备份 ({last_name}) 已过 {elapsed/3600:.1f}h，触发自动备份")
                    run_backup()
                else:
                    wait_sec = BACKUP_INTERVAL_SEC - elapsed
                    next_t   = now_t + timedelta(seconds=wait_sec)
                    log(f"上次完整备份 {last_t.strftime('%H:%M')} ({last_name})，"
                        f"下次 {next_t.strftime('%Y-%m-%d %H:%M')}（{wait_sec/3600:.1f}h后）")
        except Exception as e:
            log(f"检查循环异常: {e}")
            import traceback
            log(traceback.format_exc())

        time.sleep(CHECK_INTERVAL_SEC)


if __name__ == '__main__':
    main()
