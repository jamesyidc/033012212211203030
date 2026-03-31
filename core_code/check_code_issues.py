#!/usr/bin/env python3
"""
检查代码中的潜在问题：
1. 无限循环
2. 内存泄漏
3. 递归调用
4. 大对象创建
"""

import os
import re
from pathlib import Path

def check_file(file_path):
    """检查单个文件"""
    issues = []
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        lines = content.split('\n')
    
    # 检查无限循环
    for i, line in enumerate(lines, 1):
        # while True 没有 break
        if 'while True' in line or 'while 1' in line:
            # 检查接下来的20行是否有break
            has_break = False
            for j in range(i, min(i+20, len(lines))):
                if 'break' in lines[j] or 'return' in lines[j]:
                    has_break = True
                    break
            if not has_break:
                issues.append({
                    'type': '⚠️  潜在无限循环',
                    'line': i,
                    'content': line.strip(),
                    'severity': 'high'
                })
        
        # 检查大列表/字典创建
        if re.search(r'\[\s*\].*for.*in.*range\s*\(\s*\d{5,}', line):
            issues.append({
                'type': '⚠️  大对象创建',
                'line': i,
                'content': line.strip()[:80],
                'severity': 'medium'
            })
        
        # 检查递归调用（可能导致栈溢出）
        if re.search(r'def\s+(\w+).*:', line):
            func_name = re.search(r'def\s+(\w+)', line).group(1)
            # 检查函数体内是否调用自己
            for j in range(i, min(i+50, len(lines))):
                if func_name + '(' in lines[j] and 'def ' not in lines[j]:
                    issues.append({
                        'type': 'ℹ️  递归调用',
                        'line': i,
                        'content': f'函数 {func_name} 可能递归调用',
                        'severity': 'low'
                    })
                    break
    
    return issues

def main():
    print("=" * 60)
    print("🔍 代码问题检查报告")
    print("=" * 60)
    print()
    
    # 检查主要的Python文件
    files_to_check = [
        'code/python/app.py',
        'source_code/panic_wash_collector.py',
    ]
    
    # 查找所有collector文件
    for pattern in ['*collector*.py', '**/collector*.py']:
        for file in Path('.').glob(pattern):
            if str(file) not in files_to_check:
                files_to_check.append(str(file))
    
    total_issues = 0
    critical_issues = 0
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            continue
            
        print(f"📄 检查文件: {file_path}")
        print("-" * 60)
        
        issues = check_file(file_path)
        
        if not issues:
            print("  ✅ 未发现问题")
        else:
            for issue in issues:
                print(f"  {issue['type']} (行{issue['line']})")
                print(f"     内容: {issue['content']}")
                print(f"     严重程度: {issue['severity']}")
                print()
                total_issues += 1
                if issue['severity'] == 'high':
                    critical_issues += 1
        
        print()
    
    print("=" * 60)
    print(f"📊 检查总结")
    print("=" * 60)
    print(f"总问题数: {total_issues}")
    print(f"严重问题: {critical_issues}")
    
    if critical_issues > 0:
        print()
        print("⚠️  发现严重问题，建议立即修复！")
    elif total_issues > 0:
        print()
        print("ℹ️  发现一些潜在问题，建议review代码")
    else:
        print()
        print("✅ 代码检查通过，未发现明显问题")

if __name__ == '__main__':
    main()
