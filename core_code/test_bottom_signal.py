#!/usr/bin/env python3
"""测试见底信号的RSI<700条件"""

# 测试场景1: RSI<700，ratio>=10 → 应该触发见底信号
print("=== 测试场景1: RSI<700，ratio>=10 ===")
curr_total_rsi = 650
coin_change_pct = -2.0
rsi_change_pct = -25.0
ratio = abs(rsi_change_pct) / abs(coin_change_pct)

print(f"RSI总和: {curr_total_rsi}")
print(f"币价跌幅: {coin_change_pct}%")
print(f"RSI降幅: {rsi_change_pct}%")
print(f"比率: {ratio:.1f}")

if ratio >= 10 and curr_total_rsi < 700:
    print("✅ 结果: 触发见底信号")
else:
    print("❌ 结果: 不触发见底信号")

print()

# 测试场景2: RSI>700，ratio>=10 → 不应该触发见底信号
print("=== 测试场景2: RSI>700，ratio>=10 ===")
curr_total_rsi = 1190
coin_change_pct = -2.0
rsi_change_pct = -25.0
ratio = abs(rsi_change_pct) / abs(coin_change_pct)

print(f"RSI总和: {curr_total_rsi}")
print(f"币价跌幅: {coin_change_pct}%")
print(f"RSI降幅: {rsi_change_pct}%")
print(f"比率: {ratio:.1f}")

if ratio >= 10 and curr_total_rsi < 700:
    print("✅ 结果: 触发见底信号")
else:
    print("❌ 结果: 不触发见底信号（RSI过高）")

print()

# 测试场景3: RSI<700，ratio<10 → 不应该触发见底信号
print("=== 测试场景3: RSI<700，ratio<10 ===")
curr_total_rsi = 650
coin_change_pct = -5.0
rsi_change_pct = -8.0
ratio = abs(rsi_change_pct) / abs(coin_change_pct)

print(f"RSI总和: {curr_total_rsi}")
print(f"币价跌幅: {coin_change_pct}%")
print(f"RSI降幅: {rsi_change_pct}%")
print(f"比率: {ratio:.1f}")

if ratio >= 10 and curr_total_rsi < 700:
    print("✅ 结果: 触发见底信号")
else:
    print("❌ 结果: 不触发见底信号（ratio不够）")

print()
print("=== 修改总结 ===")
print("见底信号触发条件:")
print("1. 市场下跌（coin_change_delta < 0）")
print("2. RSI也下跌（rsi_change_delta < 0）")
print("3. RSI降幅 >= 币价跌幅 × 10")
print("4. 🆕 RSI总和 < 700")
print()
print("原因分析:")
print("- RSI高位（如1190）时出现的\"见底信号\"往往是假信号")
print("- RSI低位（如650以下）的恐慌才是真正的底部")
print("- 增加RSI<700条件可以过滤假信号，提高准确性")
