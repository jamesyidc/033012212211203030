#!/bin/bash
# OKX Angle Analyzer Daily Runner
# 每日自动运行OKX角度分析器

cd /home/user/webapp

# 获取昨天的日期（格式：YYYYMMDD）
yesterday=$(date -d "yesterday" +"%Y%m%d")

echo "[$(date)] Running OKX angle analyzer for $yesterday"

# 运行角度分析器
python3 code/python/collectors/okx_angle_analyzer_v3.py $yesterday >> logs/okx_angle_analyzer.log 2>&1

# 检查结果
if [ $? -eq 0 ]; then
    echo "[$(date)] ✅ OKX angle analysis completed for $yesterday" >> logs/okx_angle_analyzer.log
else
    echo "[$(date)] ❌ OKX angle analysis failed for $yesterday" >> logs/okx_angle_analyzer.log
fi
