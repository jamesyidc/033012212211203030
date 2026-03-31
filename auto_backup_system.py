#!/usr/bin/env python3
"""
自动备份系统

【重要要求】
1. 备份文件必须大于 260MB（压缩后）
2. 保留最近 3 个备份（自动删除更旧的备份）
3. 备份必须包含所有历史数据（绝对不允许删除历史数据）
4. 每12小时自动备份一次
5. 记录详细备份信息到 backup_history.jsonl

【备份策略】
- 备份目标：完整的 webapp 项目（约 3.6 GB）
- 压缩后大小：约 285 MB
- 如果压缩后小于 260MB，说明数据不完整，备份失败！
- 备份位置：/tmp 目录
- 备份格式：tar.gz

【数据保护】
- 绝对不允许删除任何历史 JSONL 数据
- 禁止运行任何数据清理脚本
- 所有历史数据都是宝贵资产，必须永久保留
"""

import os
import sys
import tarfile
import json
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
import subprocess

# 配置
BACKUP_DIR = Path('/tmp')
WEBAPP_DIR = Path('/home/user/webapp')
BACKUP_LOG_FILE = WEBAPP_DIR / 'data' / 'backup_history.jsonl'
MAX_BACKUPS = 3  # 保留最近3个备份
MIN_BACKUP_SIZE_MB = 260  # 备份文件最小大小（MB），低于此值视为备份失败

# 备份策略：复制整个webapp目录，包含所有内容
# 用户要求包含：logs/, node_modules/, backups/, __pycache__/, 所有数据文件
# 只排除临时备份目录本身和.git目录

# 排除的内容（最小化排除）
EXCLUDE_PATTERNS = [
    '.git',  # 不备份git仓库
    'webapp_backup_temp_*',  # 不备份临时备份目录
]

def get_beijing_time():
    """获取北京时间"""
    beijing_tz = timezone(timedelta(hours=8))
    return datetime.now(beijing_tz)

def get_directory_size(path):
    """计算目录大小（字节）- 包含所有文件"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            # 只排除.git和临时备份目录
            dirnames[:] = [d for d in dirnames if not (
                d == '.git' or d.startswith('webapp_backup_temp_')
            )]
            
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath) and os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception as e:
        print(f"⚠️ 计算大小时出错: {e}")
    return total_size

def format_size(bytes_size):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def count_files_by_type(root_path):
    """统计各类型文件数量和大小 - 包含所有文件类型"""
    stats = {
        'python': {'count': 0, 'size': 0, 'extensions': ['.py', '.pyc']},
        'markdown': {'count': 0, 'size': 0, 'extensions': ['.md']},
        'html': {'count': 0, 'size': 0, 'extensions': ['.html']},
        'config': {'count': 0, 'size': 0, 'extensions': ['.json', '.js', '.yaml', '.yml', '.conf', '.config', '.txt']},
        'data': {'count': 0, 'size': 0, 'extensions': ['.jsonl', '.csv']},
        'logs': {'count': 0, 'size': 0, 'extensions': ['.log']},
        'dependencies': {'count': 0, 'size': 0, 'extensions': []},  # node_modules计入这里
        'other': {'count': 0, 'size': 0, 'extensions': []},
    }
    
    try:
        for dirpath, dirnames, filenames in os.walk(root_path):
            # 只排除.git和临时备份目录
            dirnames[:] = [d for d in dirnames if not (
                d == '.git' or d.startswith('webapp_backup_temp_')
            )]
            
            # 统计node_modules目录
            if 'node_modules' in dirpath:
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath) and os.path.isfile(filepath):
                        file_size = os.path.getsize(filepath)
                        stats['dependencies']['count'] += 1
                        stats['dependencies']['size'] += file_size
                continue
            
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if not os.path.exists(filepath) or not os.path.isfile(filepath):
                    continue
                
                file_size = os.path.getsize(filepath)
                file_ext = os.path.splitext(filename)[1].lower()
                
                # 分类统计
                classified = False
                for category, info in stats.items():
                    if file_ext in info['extensions']:
                        info['count'] += 1
                        info['size'] += file_size
                        classified = True
                        break
                
                if not classified:
                    stats['other']['count'] += 1
                    stats['other']['size'] += file_size
    
    except Exception as e:
        print(f"⚠️ 统计文件时出错: {e}")
    
    return stats

def create_backup():
    """创建备份"""
    beijing_time = get_beijing_time()
    date_str = beijing_time.strftime('%Y%m%d')
    
    # 查找当天已有的备份数量，生成序号
    existing_backups = list(BACKUP_DIR.glob(f'webapp_backup_{date_str}_*.tar.gz'))
    sequence = len(existing_backups) + 1
    
    backup_filename = f'webapp_backup_{date_str}_{sequence}.tar.gz'
    backup_path = BACKUP_DIR / backup_filename
    
    print(f"\n🚀 开始备份...")
    print(f"📅 备份时间: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
    print(f"📁 备份文件: {backup_path}")
    print(f"🔢 今日第 {sequence} 次备份")
    
    # 统计备份前的信息
    print(f"\n📊 统计备份内容...")
    file_stats = count_files_by_type(WEBAPP_DIR)
    
    try:
        # 直接使用tar命令创建备份（更快更可靠，包含所有文件）
        print(f"📦 使用tar命令直接创建备份...")
        
        # 构建排除参数（只排除.git目录）
        exclude_opts = '--exclude=.git'
        
        # 使用tar命令直接创建压缩包
        tar_cmd = f'cd {WEBAPP_DIR.parent} && tar {exclude_opts} -czf {backup_path} {WEBAPP_DIR.name}'
        print(f"🔧 执行命令: tar ... -czf {backup_path.name} webapp/")
        
        result = subprocess.run(
            tar_cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        # tar退出码说明：
        # 0 = 成功
        # 1 = 文件在备份过程中被修改（警告，但备份已完成）
        # 2+ = 严重错误
        if result.returncode >= 2:
            raise Exception(f"tar命令失败 (退出码 {result.returncode}): {result.stderr}")
        elif result.returncode == 1:
            print(f"⚠️ 警告: 某些文件在备份过程中被修改，但备份已完成")
            if result.stderr:
                print(f"⚠️ 错误输出:\n{result.stderr}")
        
        print(f"✅ tar压缩完成")
        
        backup_size = os.path.getsize(backup_path)
        
        print(f"\n✅ 备份完成!")
        print(f"📦 备份大小: {format_size(backup_size)}")
        
        # 保存备份记录
        backup_info = {
            'timestamp': beijing_time.isoformat(),
            'filename': backup_filename,
            'filepath': str(backup_path),
            'size_bytes': backup_size,
            'size_formatted': format_size(backup_size),
            'file_stats': {
                'python': {'count': file_stats['python']['count'], 'size': format_size(file_stats['python']['size'])},
                'markdown': {'count': file_stats['markdown']['count'], 'size': format_size(file_stats['markdown']['size'])},
                'html': {'count': file_stats['html']['count'], 'size': format_size(file_stats['html']['size'])},
                'config': {'count': file_stats['config']['count'], 'size': format_size(file_stats['config']['size'])},
                'data': {'count': file_stats['data']['count'], 'size': format_size(file_stats['data']['size'])},
                'logs': {'count': file_stats['logs']['count'], 'size': format_size(file_stats['logs']['size'])},
                'dependencies': {'count': file_stats['dependencies']['count'], 'size': format_size(file_stats['dependencies']['size'])},
                'other': {'count': file_stats['other']['count'], 'size': format_size(file_stats['other']['size'])},
            },
            'status': 'success'
        }
        
        # 验证备份大小
        backup_size_mb = backup_size / (1024 * 1024)
        if backup_size_mb < MIN_BACKUP_SIZE_MB:
            print(f"\n❌ 备份失败：文件大小 {backup_size_mb:.2f} MB < 最小要求 {MIN_BACKUP_SIZE_MB} MB")
            print(f"⚠️  数据不完整！请检查是否有数据被清理或丢失")
            os.remove(backup_path)
            raise Exception(f"备份文件过小 ({backup_size_mb:.2f} MB < {MIN_BACKUP_SIZE_MB} MB)，数据不完整")
        
        print(f"✅ 备份大小验证通过：{backup_size_mb:.2f} MB > {MIN_BACKUP_SIZE_MB} MB")
        
        # 追加到备份历史文件
        BACKUP_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(BACKUP_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(backup_info, ensure_ascii=False) + '\n')
        
        print(f"📝 备份记录已保存到: {BACKUP_LOG_FILE}")
        
        # 显示文件统计
        print(f"\n📊 备份内容统计:")
        for category, info in file_stats.items():
            if info['count'] > 0:
                print(f"  - {category.upper()}: {info['count']} 文件, {format_size(info['size'])}")
        
        return backup_path
        
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 记录失败
        backup_info = {
            'timestamp': beijing_time.isoformat(),
            'filename': backup_filename,
            'error': str(e),
            'status': 'failed'
        }
        with open(BACKUP_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(backup_info, ensure_ascii=False) + '\n')
        
        return None

def copy_to_aidrive(backup_path):
    """将备份文件复制到 AI 云盘"""
    print(f"\n☁️  转存备份到 GenSpark AI 云盘...")
    
    try:
        # GenSpark AI 云盘路径（用户可访问的 Web AI 云盘）
        aidrive_dir = Path('/home/user/aidrive')
        
        # 创建目录（如果不存在）
        aidrive_dir.mkdir(parents=True, exist_ok=True)
        
        # 备用路径：沙箱本地挂载点
        backup_aidrive_dir = Path('/mnt/aidrive')
        
        print(f"📍 AI 云盘目录: {aidrive_dir}")
        
        if not aidrive_dir.exists():
            print(f"⚠️  AI 云盘目录不存在: {aidrive_dir}")
            return False
        
        backup_filename = Path(backup_path).name
        aidrive_backup_path = aidrive_dir / backup_filename
        
        # 复制文件到 GenSpark AI 云盘（不需要 sudo）
        print(f"📋 复制文件: {backup_path} -> {aidrive_backup_path}")
        result = subprocess.run(
            ['cp', '-v', str(backup_path), str(aidrive_backup_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        # 同时复制到备用位置（如果存在）
        if backup_aidrive_dir.exists():
            backup_aidrive_path = backup_aidrive_dir / backup_filename
            print(f"📋 同时备份到: {backup_aidrive_path}")
            subprocess.run(
                ['sudo', 'cp', '-v', str(backup_path), str(backup_aidrive_path)],
                capture_output=True,
                timeout=300
            )
        
        if result.returncode == 0:
            # 验证文件是否成功复制
            if aidrive_backup_path.exists():
                aidrive_size = aidrive_backup_path.stat().st_size
                original_size = Path(backup_path).stat().st_size
                
                if aidrive_size == original_size:
                    print(f"✅ 备份已成功转存到 GenSpark AI 云盘")
                    print(f"   位置: {aidrive_backup_path}")
                    print(f"   大小: {format_size(aidrive_size)}")
                    print(f"   提示: 文件将在您的 AI 云盘 Web 界面中显示")
                    print(f"   访问: https://www.genspark.ai 查看您的云盘")
                    
                    # 清理 GenSpark AI 云盘中的旧备份
                    cleanup_old_aidrive_backups()
                    
                    return True
                else:
                    print(f"⚠️  文件大小不匹配: AI云盘 {format_size(aidrive_size)} != 原始 {format_size(original_size)}")
                    return False
            else:
                print(f"⚠️  文件未找到: {aidrive_backup_path}")
                return False
        else:
            print(f"❌ 复制失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ 复制超时（超过5分钟）")
        return False
    except Exception as e:
        print(f"❌ 转存到 AI 云盘失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_old_aidrive_backups():
    """清理 GenSpark AI 云盘中的旧备份，只保留最近3个"""
    print(f"\n🧹 清理 GenSpark AI 云盘旧备份（保留最近{MAX_BACKUPS}个）...")
    
    try:
        # GenSpark AI 云盘目录
        aidrive_dir = Path('/home/user/aidrive')
        
        if not aidrive_dir.exists():
            print(f"⚠️  AI 云盘目录不存在")
            return
        
        # 获取所有备份文件
        backup_files = sorted(
            aidrive_dir.glob('webapp_backup_*.tar.gz'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # 同时清理备用位置
        backup_aidrive_dir = Path('/mnt/aidrive')
        if backup_aidrive_dir.exists():
            backup_files_alt = []
            result = subprocess.run(
                ['sudo', 'find', str(backup_aidrive_dir), '-name', 'webapp_backup_*.tar.gz', '-type', 'f'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        file_path = Path(line.strip())
                        if file_path.exists():
                            backup_files_alt.append(file_path)
                backup_files_alt.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        if len(backup_files) <= MAX_BACKUPS:
            print(f"✅ GenSpark AI 云盘当前备份数量 {len(backup_files)} <= {MAX_BACKUPS}，无需清理")
        else:
            # 删除超出数量的旧备份
            files_to_delete = backup_files[MAX_BACKUPS:]
            for backup_file in files_to_delete:
                try:
                    print(f"🗑️  删除 GenSpark AI 云盘旧备份: {backup_file.name}")
                    os.remove(backup_file)
                except Exception as e:
                    print(f"⚠️  删除失败 {backup_file.name}: {e}")
            
            print(f"✅ GenSpark AI 云盘清理完成，保留最近 {MAX_BACKUPS} 个备份")
        
        # 显示保留的备份
        remaining_backups = backup_files[:MAX_BACKUPS]
        print(f"\n☁️  GenSpark AI 云盘当前保留的备份:")
        for i, backup_file in enumerate(remaining_backups, 1):
            stat = backup_file.stat()
            size = format_size(stat.st_size)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            print(f"  {i}. {backup_file.name} - {size} - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 清理备用位置
        if backup_aidrive_dir.exists() and backup_files_alt:
            if len(backup_files_alt) > MAX_BACKUPS:
                files_to_delete_alt = backup_files_alt[MAX_BACKUPS:]
                for backup_file in files_to_delete_alt:
                    try:
                        subprocess.run(['sudo', 'rm', str(backup_file)], check=True, timeout=30)
                    except Exception:
                        pass
            
    except Exception as e:
        print(f"❌ 清理 AI 云盘备份失败: {e}")

def cleanup_old_backups():
    """清理旧备份，只保留最近3个"""
    print(f"\n🧹 清理旧备份（保留最近{MAX_BACKUPS}个）...")
    
    backup_files = sorted(
        BACKUP_DIR.glob('webapp_backup_*.tar.gz'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if len(backup_files) <= MAX_BACKUPS:
        print(f"✅ 当前备份数量 {len(backup_files)} <= {MAX_BACKUPS}，无需清理")
        return
    
    # 删除超出数量的旧备份
    files_to_delete = backup_files[MAX_BACKUPS:]
    for backup_file in files_to_delete:
        try:
            print(f"🗑️  删除旧备份: {backup_file.name}")
            os.remove(backup_file)
        except Exception as e:
            print(f"⚠️  删除失败 {backup_file.name}: {e}")
    
    print(f"✅ 清理完成，保留最近 {MAX_BACKUPS} 个备份")
    
    # 显示保留的备份
    remaining_backups = sorted(
        BACKUP_DIR.glob('webapp_backup_*.tar.gz'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    print(f"\n📦 当前保留的备份:")
    for i, backup_file in enumerate(remaining_backups, 1):
        stat = backup_file.stat()
        size = format_size(stat.st_size)
        mtime = datetime.fromtimestamp(stat.st_mtime)
        print(f"  {i}. {backup_file.name} - {size} - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")

def list_backups():
    """列出所有备份"""
    backup_files = sorted(
        BACKUP_DIR.glob('webapp_backup_*.tar.gz'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not backup_files:
        print("📭 没有找到备份文件")
        return
    
    print(f"\n📦 备份列表 (最近{MAX_BACKUPS}次):")
    print("=" * 80)
    for i, backup_file in enumerate(backup_files[:MAX_BACKUPS], 1):
        stat = backup_file.stat()
        size = format_size(stat.st_size)
        mtime = datetime.fromtimestamp(stat.st_mtime)
        print(f"{i}. {backup_file.name}")
        print(f"   大小: {size}")
        print(f"   时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

def get_backup_statistics():
    """获取备份统计信息"""
    stats = {
        'total_backups': 0,
        'total_size': 0,
        'latest_backup': None,
        'backups': []
    }
    
    backup_files = sorted(
        BACKUP_DIR.glob('webapp_backup_*.tar.gz'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    for backup_file in backup_files:
        stat = backup_file.stat()
        backup_info = {
            'filename': backup_file.name,
            'size': stat.st_size,
            'size_formatted': format_size(stat.st_size),
            'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
        stats['backups'].append(backup_info)
        stats['total_size'] += stat.st_size
    
    stats['total_backups'] = len(backup_files)
    stats['total_size_formatted'] = format_size(stats['total_size'])
    
    if backup_files:
        stats['latest_backup'] = stats['backups'][0]
    
    return stats

if __name__ == '__main__':
    print("=" * 80)
    print("🔄 自动备份系统")
    print("=" * 80)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'list':
            list_backups()
        elif command == 'stats':
            stats = get_backup_statistics()
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        else:
            print(f"❌ 未知命令: {command}")
            print("用法: python auto_backup_system.py [list|stats]")
    else:
        # 执行备份
        backup_path = create_backup()
        if backup_path:
            # 自动转存到 AI 云盘
            copy_to_aidrive(backup_path)
            
            # 清理旧备份
            cleanup_old_backups()
            
            # 显示备份列表
            list_backups()
        else:
            sys.exit(1)
