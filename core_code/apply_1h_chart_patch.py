#!/usr/bin/env python3
"""
应用1小时图表补丁：改为按日期显示+左右翻页
"""

# 读取原文件
with open('templates/panic_new.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 新的JavaScript代码（从patch文件读取）
with open('patch_panic_1h_chart.js', 'r', encoding='utf-8') as f:
    new_js_code = f.read()

# 找到需要替换的行号范围
# 从 "// ==================== 1小时爆仓金额图表 ====================" 开始
# 到 "function loadLiquidationPreviousPage()" 之前

start_marker = "// ==================== 1小时爆仓金额图表 ===================="
end_marker = "function loadLiquidationPreviousPage()"

start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if start_marker in line and start_idx is None:
        start_idx = i
    if end_marker in line and end_idx is None:
        end_idx = i
        break

if start_idx is None or end_idx is None:
    print(f"❌ 找不到标记：start={start_idx}, end={end_idx}")
    exit(1)

print(f"📍 找到替换范围：第{start_idx+1}行 到 第{end_idx+1}行")
print(f"   将删除 {end_idx - start_idx} 行旧代码")

# 构建新文件
new_lines = []
new_lines.extend(lines[:start_idx])  # 保留之前的内容
new_lines.append("        " + new_js_code + "\n")  # 插入新代码
new_lines.extend(lines[end_idx:])  # 保留之后的内容（包括loadLiquidationPreviousPage）

# 写入新文件
with open('templates/panic_new.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"✅ 替换完成！")
print(f"   原文件行数: {len(lines)}")
print(f"   新文件行数: {len(new_lines)}")
print(f"   变化: {len(new_lines) - len(lines):+d} 行")
