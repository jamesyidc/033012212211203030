#!/usr/bin/env python3
"""
上传备份文件到 GenSpark AI 云盘
"""
import os
import sys
import requests
from pathlib import Path
from datetime import datetime

# GenSpark API 配置
GENSPARK_BASE_URL = os.getenv('GENSPARK_BASE_URL', 'https://www.genspark.ai')
GENSPARK_TOKEN = os.getenv('GENSPARK_TOKEN', '')

def upload_file_to_aidrive(file_path):
    """上传文件到 GenSpark AI 云盘"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    print(f"📤 准备上传文件到 AI 云盘...")
    print(f"   文件: {file_path.name}")
    print(f"   大小: {file_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    try:
        # 构建上传 URL
        upload_url = f"{GENSPARK_BASE_URL}/api/files/v1/upload"
        
        # 准备文件
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, 'application/gzip')
            }
            
            headers = {
                'Authorization': f'Bearer {GENSPARK_TOKEN}'
            }
            
            print(f"🚀 正在上传到: {upload_url}")
            
            # 发送请求
            response = requests.post(
                upload_url,
                files=files,
                headers=headers,
                timeout=600  # 10分钟超时
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 上传成功！")
                print(f"   文件 URL: {result.get('url', 'N/A')}")
                print(f"   文件 ID: {result.get('file_id', 'N/A')}")
                return True
            else:
                print(f"❌ 上传失败: HTTP {response.status_code}")
                print(f"   响应: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 上传出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def upload_latest_backup():
    """上传最新的备份文件"""
    backup_dir = Path('/tmp')
    
    # 查找所有备份文件
    backup_files = sorted(
        backup_dir.glob('webapp_backup_*.tar.gz'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not backup_files:
        print("❌ 没有找到备份文件")
        return False
    
    # 上传最新的备份
    latest_backup = backup_files[0]
    print(f"\n📦 最新备份: {latest_backup.name}")
    print(f"   修改时间: {datetime.fromtimestamp(latest_backup.stat().st_mtime)}")
    
    return upload_file_to_aidrive(latest_backup)

if __name__ == '__main__':
    print("=" * 80)
    print("📤 GenSpark AI 云盘上传工具")
    print("=" * 80)
    
    if len(sys.argv) > 1:
        # 上传指定文件
        file_path = sys.argv[1]
        success = upload_file_to_aidrive(file_path)
    else:
        # 上传最新备份
        success = upload_latest_backup()
    
    sys.exit(0 if success else 1)
