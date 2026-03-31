#!/usr/bin/env python3
"""
完整备份系统 - 备份所有内容，不排除任何文件
包含：代码、数据、logs、node_modules、依赖包、配置等所有内容
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 北京时区
beijing_tz = timezone(timedelta(hours=8))
beijing_time = datetime.now(beijing_tz)

# 配置
BACKUP_DIR = Path('/tmp')
WEBAPP_DIR = Path('/home/user/webapp')
BACKUP_LOG_FILE = WEBAPP_DIR / 'data' / 'backup_history.jsonl'

# 备份文件名（使用北京时间）
backup_filename = f'webapp_complete_backup_{beijing_time.strftime("%Y%m%d_%H%M%S")}.tar.gz'
backup_path = BACKUP_DIR / backup_filename

print("=" * 80)
print("🔄 完整备份系统")
print("=" * 80)
print(f"\n🚀 开始完整备份...")
print(f"📅 备份时间: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
print(f"📁 备份文件: {backup_path}")
print(f"⚠️ 备份策略: 包含所有内容（代码、数据、logs、node_modules、依赖包等）")

# 统计文件
print(f"\n📊 统计备份内容...")
file_stats = {
    'python': {'count': 0, 'size': 0},
    'markdown': {'count': 0, 'size': 0},
    'html': {'count': 0, 'size': 0},
    'config': {'count': 0, 'size': 0},
    'data': {'count': 0, 'size': 0},
    'logs': {'count': 0, 'size': 0},
    'node_modules': {'count': 0, 'size': 0},
    'dependencies': {'count': 0, 'size': 0},
    'other': {'count': 0, 'size': 0},
}

for root, dirs, files in os.walk(WEBAPP_DIR):
    # 跳过.git目录
    if '.git' in root:
        continue
    
    for file in files:
        file_path = Path(root) / file
        try:
            file_size = file_path.stat().st_size
            
            if file.endswith('.py'):
                file_stats['python']['count'] += 1
                file_stats['python']['size'] += file_size
            elif file.endswith(('.md', '.rst', '.txt')):
                file_stats['markdown']['count'] += 1
                file_stats['markdown']['size'] += file_size
            elif file.endswith('.html'):
                file_stats['html']['count'] += 1
                file_stats['html']['size'] += file_size
            elif file.endswith(('.json', '.js', '.env', '.yml', '.yaml', '.ini', '.cfg')):
                file_stats['config']['count'] += 1
                file_stats['config']['size'] += file_size
            elif file.endswith('.jsonl') or 'data' in root:
                file_stats['data']['count'] += 1
                file_stats['data']['size'] += file_size
            elif 'logs' in root or file.endswith('.log'):
                file_stats['logs']['count'] += 1
                file_stats['logs']['size'] += file_size
            elif 'node_modules' in root:
                file_stats['node_modules']['count'] += 1
                file_stats['node_modules']['size'] += file_size
            elif any(x in root for x in ['venv', 'env', '__pycache__', '.pyc']):
                file_stats['dependencies']['count'] += 1
                file_stats['dependencies']['size'] += file_size
            else:
                file_stats['other']['count'] += 1
                file_stats['other']['size'] += file_size
        except:
            pass

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

print(f"📦 使用tar命令创建完整备份（包含所有文件）...")

# 只排除.git目录，保留所有其他内容
tar_cmd = f'cd {WEBAPP_DIR.parent} && tar --exclude=.git -czf {backup_path} {WEBAPP_DIR.name}'
print(f"🔧 执行命令: tar --exclude=.git -czf {backup_path.name} webapp/")

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
    print(f"❌ tar命令失败 (退出码 {result.returncode}): {result.stderr}")
    sys.exit(1)
elif result.returncode == 1:
    print(f"⚠️ 警告: 某些文件在备份过程中被修改，但备份已完成")
    if result.stderr:
        print(f"⚠️ 错误输出:\n{result.stderr}")

print(f"✅ tar压缩完成")

backup_size = os.path.getsize(backup_path)

print(f"\n✅ 完整备份完成!")
print(f"📦 备份大小: {format_size(backup_size)}")

# 保存备份记录
backup_info = {
    'timestamp': beijing_time.isoformat(),
    'filename': backup_filename,
    'filepath': str(backup_path),
    'size_bytes': backup_size,
    'size_formatted': format_size(backup_size),
    'backup_type': 'complete',  # 完整备份
    'file_stats': {
        'python': {'count': file_stats['python']['count'], 'size': format_size(file_stats['python']['size'])},
        'markdown': {'count': file_stats['markdown']['count'], 'size': format_size(file_stats['markdown']['size'])},
        'html': {'count': file_stats['html']['count'], 'size': format_size(file_stats['html']['size'])},
        'config': {'count': file_stats['config']['count'], 'size': format_size(file_stats['config']['size'])},
        'data': {'count': file_stats['data']['count'], 'size': format_size(file_stats['data']['size'])},
        'logs': {'count': file_stats['logs']['count'], 'size': format_size(file_stats['logs']['size'])},
        'node_modules': {'count': file_stats['node_modules']['count'], 'size': format_size(file_stats['node_modules']['size'])},
        'dependencies': {'count': file_stats['dependencies']['count'], 'size': format_size(file_stats['dependencies']['size'])},
        'other': {'count': file_stats['other']['count'], 'size': format_size(file_stats['other']['size'])},
    },
    'status': 'success'
}

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

print(f"\n✅ 完整备份文件位置: {backup_path}")
print(f"📦 文件大小: {format_size(backup_size)}")
print("=" * 80)
