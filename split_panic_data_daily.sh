#!/bin/bash
# Panic Data Daily Split - 每日分割恐慌数据的定时任务脚本

cd /home/user/webapp
python3 source_code/split_panic_data_daily.py >> logs/panic_data_split.log 2>&1

echo "[$(date)] Panic data split completed" >> logs/panic_data_split.log
