#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
页面定时截图系统
- 每1分钟截图一次
- 保存为JPG格式
- 提供HTTP访问接口
- 30分钟延迟展示（显示30分钟前的截图）
- 只保留3小时的数据，自动清理旧截图
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright
import shutil

# 项目根目录
BASE_DIR = Path('/home/user/webapp')
sys.path.insert(0, str(BASE_DIR))

# 截图保存目录
SCREENSHOTS_DIR = BASE_DIR / 'data' / 'screenshots'
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# 配置
TARGET_URL = "http://localhost:9002/coin-change-tracker"  # 要截图的页面URL
SCREENSHOT_INTERVAL = 60  # 截图间隔（秒）
KEEP_HOURS = 3  # 保留3小时的数据
DISPLAY_DELAY_MINUTES = 30  # 延迟30分钟展示

def get_beijing_time():
    """获取北京时间"""
    from datetime import timezone
    utc_now = datetime.now(timezone.utc)
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time

def take_screenshot(page, output_path):
    """截取页面并保存为JPG
    
    Args:
        page: Playwright页面对象
        output_path: 输出文件路径
    """
    try:
        # 截取整个页面
        page.screenshot(path=str(output_path), full_page=True, type='jpeg', quality=85)
        print(f"✅ 截图成功: {output_path.name}")
        return True
    except Exception as e:
        print(f"❌ 截图失败: {e}")
        return False

def cleanup_old_screenshots():
    """清理3小时以前的截图"""
    beijing_now = get_beijing_time()
    cutoff_time = beijing_now - timedelta(hours=KEEP_HOURS)
    
    deleted_count = 0
    
    for file_path in SCREENSHOTS_DIR.glob("screenshot_*.jpg"):
        try:
            # 从文件名提取时间戳
            # 格式: screenshot_20260224_223045.jpg
            filename = file_path.stem
            timestamp_str = filename.replace('screenshot_', '')
            file_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            
            # 如果文件时间早于截止时间，删除
            if file_time < cutoff_time:
                file_path.unlink()
                deleted_count += 1
                print(f"🗑️  删除旧截图: {file_path.name}")
        except Exception as e:
            print(f"⚠️ 清理文件失败 {file_path.name}: {e}")
    
    if deleted_count > 0:
        print(f"✅ 清理完成，删除了 {deleted_count} 个旧截图")
    
    return deleted_count

def get_screenshot_list():
    """获取所有截图列表（按时间倒序）"""
    screenshots = []
    
    for file_path in SCREENSHOTS_DIR.glob("screenshot_*.jpg"):
        try:
            filename = file_path.stem
            timestamp_str = filename.replace('screenshot_', '')
            file_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            
            screenshots.append({
                'filename': file_path.name,
                'timestamp': file_time.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp_raw': file_time,
                'size': file_path.stat().st_size,
                'path': str(file_path)
            })
        except Exception as e:
            print(f"⚠️ 解析文件失败 {file_path.name}: {e}")
    
    # 按时间倒序排序
    screenshots.sort(key=lambda x: x['timestamp_raw'], reverse=True)
    
    return screenshots

def get_delayed_screenshot():
    """获取30分钟前的截图
    
    Returns:
        截图信息字典，如果没有则返回None
    """
    beijing_now = get_beijing_time()
    target_time = beijing_now - timedelta(minutes=DISPLAY_DELAY_MINUTES)
    
    # 获取所有截图
    screenshots = get_screenshot_list()
    
    if not screenshots:
        return None
    
    # 找到最接近30分钟前的截图
    best_match = None
    min_diff = float('inf')
    
    for screenshot in screenshots:
        time_diff = abs((screenshot['timestamp_raw'] - target_time).total_seconds())
        
        if time_diff < min_diff:
            min_diff = time_diff
            best_match = screenshot
    
    return best_match

def save_metadata():
    """保存截图元数据（用于快速查询）"""
    screenshots = get_screenshot_list()
    
    metadata = {
        'update_time': get_beijing_time().strftime('%Y-%m-%d %H:%M:%S'),
        'total_count': len(screenshots),
        'screenshots': [
            {
                'filename': s['filename'],
                'timestamp': s['timestamp'],
                'size': s['size']
            }
            for s in screenshots
        ]
    }
    
    metadata_file = SCREENSHOTS_DIR / 'metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return metadata

def run_screenshot_loop():
    """运行截图循环"""
    print("=" * 60)
    print("🖼️  页面定时截图系统")
    print("=" * 60)
    print(f"📍 目标URL: {TARGET_URL}")
    print(f"⏱️  截图间隔: {SCREENSHOT_INTERVAL} 秒")
    print(f"🕐 保留时长: {KEEP_HOURS} 小时")
    print(f"⏰ 延迟展示: {DISPLAY_DELAY_MINUTES} 分钟")
    print(f"💾 存储目录: {SCREENSHOTS_DIR}")
    print("=" * 60)
    print()
    
    with sync_playwright() as p:
        # 启动浏览器
        print("🚀 启动浏览器...")
        browser = p.chromium.launch(headless=True)
        
        try:
            # 创建浏览器上下文
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = context.new_page()
            
            print(f"📄 打开页面: {TARGET_URL}")
            page.goto(TARGET_URL, wait_until='networkidle', timeout=30000)
            
            print("✅ 页面加载完成")
            print(f"⏰ 开始定时截图循环...\n")
            
            screenshot_count = 0
            
            while True:
                beijing_now = get_beijing_time()
                timestamp_str = beijing_now.strftime('%Y%m%d_%H%M%S')
                
                # 生成截图文件名
                screenshot_filename = f"screenshot_{timestamp_str}.jpg"
                screenshot_path = SCREENSHOTS_DIR / screenshot_filename
                
                print(f"[{beijing_now.strftime('%Y-%m-%d %H:%M:%S')}] 📸 开始截图...")
                
                # 刷新页面（获取最新数据）
                page.reload(wait_until='networkidle', timeout=30000)
                
                # 等待1秒确保数据加载完成
                time.sleep(1)
                
                # 截图
                success = take_screenshot(page, screenshot_path)
                
                if success:
                    screenshot_count += 1
                    file_size = screenshot_path.stat().st_size / 1024  # KB
                    print(f"   文件大小: {file_size:.1f} KB")
                    print(f"   累计截图: {screenshot_count} 张")
                    
                    # 每10次截图清理一次旧文件
                    if screenshot_count % 10 == 0:
                        print(f"\n🗑️  执行清理任务...")
                        cleanup_old_screenshots()
                        print()
                    
                    # 保存元数据
                    save_metadata()
                    
                    # 显示当前可显示的截图（30分钟前）
                    delayed = get_delayed_screenshot()
                    if delayed:
                        print(f"   📺 当前可展示: {delayed['filename']}")
                    else:
                        print(f"   ⏳ 等待数据积累（需要30分钟后才能展示）")
                
                print()
                
                # 等待下次截图
                print(f"⏳ 等待 {SCREENSHOT_INTERVAL} 秒后进行下次截图...\n")
                time.sleep(SCREENSHOT_INTERVAL)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  收到中断信号，正在停止...")
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("🔄 关闭浏览器...")
            browser.close()
            print("✅ 截图系统已停止")

def main():
    """主函数"""
    try:
        run_screenshot_loop()
    except Exception as e:
        print(f"❌ 系统错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
