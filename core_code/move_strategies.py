#!/usr/bin/env python3
"""
移动上涨占比0策略到BTC策略下方
"""

# 读取文件
with open('/home/user/webapp/templates/okx_trading.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到要移动的策略范围（行号从1开始，但列表索引从0开始）
# 策略A: 2374-2454 行 (索引 2373-2453)
# 策略B: 2456-2536 行 (索引 2455-2535)
strategy_a_start = 2373  # 行2374
strategy_a_end = 2454    # 行2454
strategy_b_start = 2455  # 行2456
strategy_b_end = 2536    # 行2536

# 提取两个策略
strategy_a_lines = lines[strategy_a_start:strategy_a_end]
strategy_b_lines = lines[strategy_b_start:strategy_b_end]

# 删除原位置的策略
del lines[strategy_a_start:strategy_b_end+1]

# 找到BTC涨幅前8名策略结束的位置（</div>之后）
# 在2273行之后插入（索引2272）
insert_pos = 2272

# 插入两个策略
lines[insert_pos:insert_pos] = strategy_a_lines + ['\n'] + strategy_b_lines + ['\n']

# 写回文件
with open('/home/user/webapp/templates/okx_trading.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ 策略移动完成！")
print(f"已将上涨占比0策略移动到第{insert_pos+1}行附近")
