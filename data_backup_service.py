#!/usr/bin/env python3
"""
数据备份恢复服务
支持增量备份、压缩备份、远程备份
"""
import os
import json
import tarfile
import shutil
from datetime import datetime
from pathlib import Path
import subprocess

class DataBackupService:
    def __init__(self, data_dir='data', backup_dir='backups'):
        self.data_dir = Path(data_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self, backup_name=None, compress=True):
        """创建完整备份"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"🔄 开始创建备份: {backup_name}")
        
        if compress:
            backup_file = self.backup_dir / f"{backup_name}.tar.gz"
            print(f"📦 压缩备份到: {backup_file}")
            
            with tarfile.open(backup_file, "w:gz") as tar:
                tar.add(self.data_dir, arcname='data')
            
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            print(f"✅ 备份完成！大小: {size_mb:.2f} MB")
            
            return {
                'success': True,
                'backup_file': str(backup_file),
                'size_mb': round(size_mb, 2),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            backup_path = self.backup_dir / backup_name
            print(f"📁 复制备份到: {backup_path}")
            
            shutil.copytree(self.data_dir, backup_path, dirs_exist_ok=True)
            
            # 计算大小
            total_size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
            size_mb = total_size / (1024 * 1024)
            
            print(f"✅ 备份完成！大小: {size_mb:.2f} MB")
            
            return {
                'success': True,
                'backup_path': str(backup_path),
                'size_mb': round(size_mb, 2),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def create_incremental_backup(self, reference_backup=None):
        """创建增量备份（只备份修改的文件）"""
        backup_name = f"incremental_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        print(f"🔄 开始创建增量备份: {backup_name}")
        
        # 获取参考时间
        if reference_backup:
            ref_path = Path(reference_backup)
            if ref_path.exists():
                ref_time = ref_path.stat().st_mtime
            else:
                print("⚠️ 参考备份不存在，创建完整备份")
                return self.create_backup(backup_name=backup_name, compress=False)
        else:
            # 使用最后一次完整备份作为参考
            backups = sorted(self.backup_dir.glob('backup_*'), key=lambda x: x.stat().st_mtime)
            if backups:
                ref_time = backups[-1].stat().st_mtime
                print(f"📌 参考备份: {backups[-1].name}")
            else:
                print("⚠️ 没有找到参考备份，创建完整备份")
                return self.create_backup(backup_name=backup_name, compress=False)
        
        # 复制修改过的文件
        copied_files = 0
        total_size = 0
        
        for src_file in self.data_dir.rglob('*'):
            if src_file.is_file():
                if src_file.stat().st_mtime > ref_time:
                    # 文件已修改，需要备份
                    rel_path = src_file.relative_to(self.data_dir)
                    dest_file = backup_path / rel_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    shutil.copy2(src_file, dest_file)
                    copied_files += 1
                    total_size += src_file.stat().st_size
        
        size_mb = total_size / (1024 * 1024)
        print(f"✅ 增量备份完成！")
        print(f"   复制文件: {copied_files} 个")
        print(f"   大小: {size_mb:.2f} MB")
        
        # 保存元数据
        metadata = {
            'type': 'incremental',
            'reference_time': datetime.fromtimestamp(ref_time).strftime('%Y-%m-%d %H:%M:%S'),
            'files_count': copied_files,
            'size_mb': round(size_mb, 2),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(backup_path / 'backup_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            'success': True,
            'backup_path': str(backup_path),
            'files_count': copied_files,
            'size_mb': round(size_mb, 2),
            'timestamp': metadata['timestamp']
        }
    
    def restore_backup(self, backup_source, target_dir=None):
        """恢复备份"""
        if not target_dir:
            target_dir = self.data_dir
        else:
            target_dir = Path(target_dir)
        
        backup_path = Path(backup_source)
        
        if not backup_path.exists():
            return {'success': False, 'error': '备份文件不存在'}
        
        print(f"🔄 开始恢复备份: {backup_source}")
        print(f"📁 目标目录: {target_dir}")
        
        # 创建备份当前数据（以防万一）
        if target_dir.exists():
            safety_backup = self.backup_dir / f"before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"💾 创建安全备份到: {safety_backup}")
            shutil.copytree(target_dir, safety_backup, dirs_exist_ok=True)
        
        # 解压或复制
        if backup_path.suffix == '.gz':
            print("📦 解压备份文件...")
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(target_dir.parent)
        else:
            print("📁 复制备份文件...")
            shutil.copytree(backup_path, target_dir, dirs_exist_ok=True)
        
        print("✅ 恢复完成！")
        
        return {
            'success': True,
            'restored_to': str(target_dir),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def list_backups(self):
        """列出所有备份"""
        backups = []
        
        # 压缩备份
        for backup_file in sorted(self.backup_dir.glob('*.tar.gz'), key=lambda x: x.stat().st_mtime, reverse=True):
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            backups.append({
                'name': backup_file.name,
                'path': str(backup_file),
                'type': 'compressed',
                'size_mb': round(size_mb, 2),
                'modified': mtime.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # 目录备份
        for backup_dir in sorted(self.backup_dir.glob('backup_*'), key=lambda x: x.stat().st_mtime, reverse=True):
            if backup_dir.is_dir():
                total_size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
                size_mb = total_size / (1024 * 1024)
                mtime = datetime.fromtimestamp(backup_dir.stat().st_mtime)
                
                backups.append({
                    'name': backup_dir.name,
                    'path': str(backup_dir),
                    'type': 'directory',
                    'size_mb': round(size_mb, 2),
                    'modified': mtime.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # 增量备份
        for backup_dir in sorted(self.backup_dir.glob('incremental_*'), key=lambda x: x.stat().st_mtime, reverse=True):
            if backup_dir.is_dir():
                metadata_file = backup_dir / 'backup_metadata.json'
                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                    backups.append({
                        'name': backup_dir.name,
                        'path': str(backup_dir),
                        'type': 'incremental',
                        'size_mb': metadata.get('size_mb', 0),
                        'files_count': metadata.get('files_count', 0),
                        'modified': metadata.get('timestamp', 'unknown')
                    })
        
        return backups
    
    def delete_backup(self, backup_name):
        """删除备份"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            return {'success': False, 'error': '备份不存在'}
        
        print(f"🗑️ 删除备份: {backup_name}")
        
        if backup_path.is_file():
            backup_path.unlink()
        else:
            shutil.rmtree(backup_path)
        
        print("✅ 删除完成")
        
        return {
            'success': True,
            'deleted': backup_name,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

if __name__ == '__main__':
    import sys
    
    service = DataBackupService(data_dir='data', backup_dir='backups')
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 data_backup_service.py backup          # 创建完整备份")
        print("  python3 data_backup_service.py incremental     # 创建增量备份")
        print("  python3 data_backup_service.py list            # 列出所有备份")
        print("  python3 data_backup_service.py restore <name>  # 恢复备份")
        print("  python3 data_backup_service.py delete <name>   # 删除备份")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'backup':
        result = service.create_backup()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    elif command == 'incremental':
        result = service.create_incremental_backup()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    elif command == 'list':
        backups = service.list_backups()
        print(f"\n📦 找到 {len(backups)} 个备份:")
        for backup in backups:
            print(f"\n  • {backup['name']}")
            print(f"    类型: {backup['type']}")
            print(f"    大小: {backup['size_mb']} MB")
            if 'files_count' in backup:
                print(f"    文件数: {backup['files_count']}")
            print(f"    修改时间: {backup['modified']}")
        
    elif command == 'restore' and len(sys.argv) > 2:
        backup_name = sys.argv[2]
        backup_path = Path('backups') / backup_name
        result = service.restore_backup(backup_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    elif command == 'delete' and len(sys.argv) > 2:
        backup_name = sys.argv[2]
        result = service.delete_backup(backup_name)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    else:
        print("❌ 未知命令或缺少参数")
        sys.exit(1)
