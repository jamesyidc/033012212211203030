#!/usr/bin/env python3
"""
自动化测试脚本：验证tooltip显示的值是79还是189
"""
import asyncio
from playwright.async_api import async_playwright
import sys

async def test_tooltip():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 监听console日志
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"{msg.type()}: {msg.text()}"))
        
        print("🔄 正在加载页面...")
        await page.goto('https://9001-iou7okyaq15h840cyuitp-c07dda5e.sandbox.novita.ai/price-position')
        
        # 等待图表加载
        print("⏳ 等待图表加载...")
        await page.wait_for_selector('#chartSellSignals', timeout=30000)
        await asyncio.sleep(3)
        
        # 查找包含tooltip调试日志的关键信息
        print("\n📊 控制台日志中的关键信息：")
        for log in console_logs:
            if 'sell24hData最后5个值' in log or 'sell_24h' in log:
                print(f"  {log}")
        
        # 尝试触发tooltip
        print("\n🎯 尝试触发tooltip...")
        try:
            # 找到图表容器
            chart_element = await page.query_selector('#chartSellSignals')
            if chart_element:
                # 获取图表的位置和大小
                box = await chart_element.bounding_box()
                if box:
                    # 鼠标移动到图表右侧（最后一个数据点）
                    x = box['x'] + box['width'] - 50
                    y = box['y'] + box['height'] / 2
                    
                    print(f"  移动鼠标到坐标: ({x:.0f}, {y:.0f})")
                    await page.mouse.move(x, y)
                    await asyncio.sleep(1)
                    
                    # 再等待一下，看是否有tooltip日志
                    await asyncio.sleep(2)
                    
                    # 检查是否有tooltip日志
                    tooltip_logs = [log for log in console_logs if '🎯 Tooltip' in log]
                    if tooltip_logs:
                        print("\n✅ 捕获到Tooltip日志：")
                        for log in tooltip_logs[-5:]:  # 显示最后5条
                            print(f"  {log}")
                            
                            # 解析tooltip值
                            if '24h=' in log:
                                import re
                                match = re.search(r'24h=(\d+)', log)
                                if match:
                                    value_24h = int(match.group(1))
                                    print(f"\n{'='*60}")
                                    if value_24h == 79:
                                        print(f"❌ 错误！Tooltip显示 24h={value_24h} (期望值: 189)")
                                        print("   问题：tooltip仍然使用错误的数据")
                                    elif value_24h == 189 or value_24h == 190:
                                        print(f"✅ 正确！Tooltip显示 24h={value_24h}")
                                        print("   修复成功：tooltip使用了正确的数据")
                                    else:
                                        print(f"⚠️  Tooltip显示 24h={value_24h} (期望: ~189)")
                                        print("   需要进一步检查数值是否合理")
                                    print(f"{'='*60}")
                    else:
                        print("⚠️  未捕获到Tooltip日志，可能鼠标未悬停到数据点")
                        print("   让我尝试在图表上多个位置移动...")
                        
                        # 尝试多个位置
                        for offset in [100, 200, 300, 400]:
                            x = box['x'] + box['width'] - offset
                            await page.mouse.move(x, y)
                            await asyncio.sleep(0.5)
                        
                        await asyncio.sleep(1)
                        tooltip_logs = [log for log in console_logs if '🎯 Tooltip' in log]
                        if tooltip_logs:
                            print(f"\n✅ 在移动后捕获到 {len(tooltip_logs)} 条Tooltip日志")
                            print(f"  最后一条: {tooltip_logs[-1]}")
        except Exception as e:
            print(f"❌ 触发tooltip失败: {e}")
        
        # 显示所有tooltip相关日志
        print("\n📋 所有Tooltip相关日志：")
        tooltip_count = 0
        for log in console_logs:
            if '🎯' in log or 'Tooltip' in log:
                print(f"  {log}")
                tooltip_count += 1
        
        if tooltip_count == 0:
            print("  （无Tooltip日志）")
        
        await browser.close()
        
        return tooltip_count > 0

if __name__ == '__main__':
    try:
        result = asyncio.run(test_tooltip())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
