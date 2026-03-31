#!/usr/bin/env python3
"""
修复OKX Trading下单金额问题
问题：sz传递的是contractValuePerCoin(合约价值=保证金×10)，应该传递marginPerCoin(保证金)
"""

import re

html_file = '/home/user/webapp/templates/okx_trading.html'

# 读取文件
with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 统计修改前的信息
before_count = content.count('sz: contractValuePerCoin')
print(f"🔍 发现 {before_count} 处需要修复的代码")

# 修复1: batchOrder函数（第5111行附近）
# 需要添加maxOrderSize参数并改用marginPerCoin
pattern1 = r'(// sz传递合约价值，后端会根据当前价格计算合约张数\s+const orderData = \{\s+instId: symbolData\.symbol,\s+side: direction === \'long\' \? \'buy\' : \'sell\',\s+posSide: direction,\s+ordType: \'market\',\s+)sz: contractValuePerCoin,  // 传递合约价值（保证金 × 10）(\s+lever: \'10\'\s+\};)'

replacement1 = r'\1sz: marginPerCoin,  // 🔴 修复：使用保证金而不是合约价值\n                        maxOrderSize: maxOrderSize  // 🔴 新增：传递单笔限额用于后端风控检查\2'

content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE)

# 修复2和3: batchOrderTop8和batchOrderBottom8函数（第5297行和5502行附近）
# 同样需要添加maxOrderSize参数并改用marginPerCoin
pattern2 = r'(const orderData = \{\s+instId: symbolData\.symbol,\s+side: direction === \'long\' \? \'buy\' : \'sell\',\s+posSide: direction,\s+ordType: \'market\',\s+)sz: contractValuePerCoin,(\s+lever: \'10\'\s+\};)'

replacement2 = r'\1sz: marginPerCoin,  // 🔴 修复：使用保证金而不是合约价值\n                        maxOrderSize: maxOrderSize  // 🔴 新增：传递单笔限额用于后端风控检查\2'

content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE)

# 统计修改后的信息
after_count = content.count('sz: contractValuePerCoin')
fixed_count = before_count - after_count
print(f"✅ 成功修复 {fixed_count} 处代码")
print(f"❌ 剩余 {after_count} 处（应该为0）")

# 验证修复
margin_count = content.count('sz: marginPerCoin,  // 🔴 修复')
max_order_count = content.count('maxOrderSize: maxOrderSize  // 🔴 新增')
print(f"✅ 新增 sz: marginPerCoin 代码: {margin_count} 处")
print(f"✅ 新增 maxOrderSize 参数: {max_order_count} 处")

if fixed_count == before_count and after_count == 0 and margin_count == 3 and max_order_count == 3:
    # 写回文件
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n🎉 修复完成！已写入 {html_file}")
else:
    print(f"\n⚠️  修复结果异常，未写入文件，请检查：")
    print(f"   - before_count: {before_count}")
    print(f"   - fixed_count: {fixed_count}")
    print(f"   - after_count: {after_count}")
    print(f"   - margin_count: {margin_count}")
    print(f"   - max_order_count: {max_order_count}")
