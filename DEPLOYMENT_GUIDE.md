# 完整系统部署指南

## 一、系统要求

### 硬件要求
- CPU: 2核心以上
- 内存: 4GB (推荐8GB)
- 磁盘: 20GB可用空间 (推荐50GB)

### 软件要求
- 操作系统: Ubuntu 20.04+ / Debian 10+
- Python: 3.8+
- Node.js: 14+
- PM2: 全局安装
- Git: 2.0+

## 二、快速部署步骤

### 1. 解压备份
```bash
cd /tmp
tar -xzf webapp_full_backup_YYYYMMDD_HHMMSS.tar.gz
cd webapp_full_backup_YYYYMMDD_HHMMSS
```

### 2. 复制文件到目标目录
```bash
# 创建目标目录
sudo mkdir -p /home/user/webapp
sudo chown -R $USER:$USER /home/user/webapp

# 复制所有文件
cp -r core_code/* /home/user/webapp/
cp -r special_systems/* /home/user/webapp/
cp -r scripts/* /home/user/webapp/
cp -r web_assets/* /home/user/webapp/
cp -r configs/* /home/user/webapp/
cp -r data /home/user/webapp/
cp -r docs/* /home/user/webapp/
```

### 3. 安装系统依赖
```bash
# 更新系统
sudo apt update

# 安装Python
sudo apt install -y python3 python3-pip python3-venv

# 安装Node.js (使用NodeSource)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 验证安装
python3 --version
node --version
npm --version
```

### 4. 安装Python依赖
```bash
cd /home/user/webapp
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

### 5. 安装PM2
```bash
sudo npm install -g pm2
pm2 startup
# 按照提示执行命令
```

### 6. 恢复PM2进程
```bash
cd /home/user/webapp

# 方式1: 使用保存的dump文件
cp pm2_config/dump.pm2 ~/.pm2/dump.pm2
pm2 resurrect

# 方式2: 使用ecosystem配置
pm2 start ecosystem.config.js

# 保存PM2配置
pm2 save
```

### 7. 验证部署
```bash
# 检查PM2进程
pm2 list

# 检查Flask应用
curl http://localhost:9002/

# 检查数据文件
ls -lh /home/user/webapp/data/
```

## 三、详细配置说明

### 3.1 Flask应用 (app.py)
- **端口**: 9002
- **说明**: 主Web应用，提供API和Web界面
- **启动命令**: `pm2 start ecosystem.config.js --only flask-app`

### 3.2 数据采集服务 (13个)
| 服务名称 | 脚本位置 | 说明 |
|---------|---------|------|
| signal-collector | code/python/signal_collector.py | 交易信号采集 |
| liquidation-1h-collector | code/python/liquidation_1h_collector.py | 1小时爆仓数据 |
| crypto-index-collector | code/python/crypto_index_collector.py | 加密指数 |
| v1v2-collector | code/python/v1v2_collector.py | V1V2数据 |
| price-speed-collector | code/python/price_speed_collector.py | 价格速度 |
| sar-slope-collector | code/python/sar_slope_collector.py | SAR斜率 |
| price-comparison-collector | code/python/price_comparison_collector.py | 价格对比 |
| financial-indicators-collector | code/python/financial_indicators_collector.py | 财务指标 |
| okx-day-change-collector | code/python/okx_day_change_collector.py | OKX日变化 |
| price-baseline-collector | code/python/price_baseline_collector.py | 价格基线 |
| sar-bias-stats-collector | code/python/sar_bias_stats_collector.py | SAR偏差统计 |
| panic-wash-collector | code/python/panic_wash_collector.py | 恐慌洗盘 |
| coin-change-tracker | source_code/coin_change_tracker.py | 币种变化追踪 |

### 3.3 交易监控服务 (8个)
| 服务名称 | 脚本位置 | 说明 |
|---------|---------|------|
| coin-price-tracker | source_code/coin_price_tracker.py | 币价追踪 |
| okx-tpsl-monitor | code/python/okx_tpsl_monitor.py | OKX止盈止损监控 |
| okx-percent-tpsl-monitor | code/python/okx_percent_tpsl_monitor.py | OKX百分比止盈止损 |
| okx-coin-change-tpsl-main | code/python/okx_coin_change_tpsl_main.py | 主账户止盈止损 |
| okx-coin-change-tpsl-fangfang12 | code/python/okx_coin_change_tpsl_fangfang12.py | fangfang12账户 |
| okx-coin-change-tpsl-poit | code/python/okx_coin_change_tpsl_poit.py | poit账户 |
| okx-coin-change-tpsl-poit-main | code/python/okx_coin_change_tpsl_poit_main.py | poit主账户 |
| okx-coin-change-tpsl-anchor | code/python/okx_coin_change_tpsl_anchor.py | anchor账户 |

### 3.4 系统服务 (7个)
| 服务名称 | 脚本位置 | 说明 |
|---------|---------|------|
| data-health-monitor | code/python/data_health_monitor.py | 数据健康监控 |
| system-health-monitor | code/python/system_health_monitor.py | 系统健康监控 |
| dashboard-jsonl-manager | code/python/dashboard_jsonl_manager.py | Dashboard JSONL管理 |
| gdrive-jsonl-manager | code/python/gdrive_jsonl_manager.py | Google Drive JSONL管理 |
| bottom-signal-long-monitor | code/python/bottom_signal_long_monitor.py | 底部信号监控 |
| coin-change-predictor | source_code/coin_change_predictor.py | 币种变化预测 |
| new-high-low-collector | code/python/new_high_low_collector.py | 新高新低采集 |

### 3.5 市场分析服务 (4个)
| 服务名称 | 脚本位置 | 说明 |
|---------|---------|------|
| okx-trade-history | code/python/okx_trade_history.py | OKX交易历史 |
| market-sentiment-collector | code/python/market_sentiment_collector.py | 市场情绪采集 |
| price-position-collector | code/python/price_position_collector.py | 价格位置采集 |
| rsi-takeprofit-monitor | code/python/rsi_takeprofit_monitor.py | RSI止盈监控 |

## 四、数据目录结构

```
/home/user/webapp/data/
├── coin_change_tracker/
│   ├── coin_change_YYYYMMDD.jsonl  (每日币种变化数据)
│   └── aggregated/
│       ├── 10min_up_ratio_YYYYMMDD.json
│       ├── positive_ratio_stats_YYYYMMDD.json
│       └── velocity_stats_YYYYMMDD.json
├── btc_daily_range/
│   └── btc_range_YYYYMMDD.jsonl
├── crypto_index/
│   └── crypto_index_YYYYMMDD.jsonl
├── panic_index/
│   └── panic_index_YYYYMMDD.jsonl
├── signals/
│   └── signals_YYYYMMDD.jsonl
└── okx_*/
    └── okx_*_YYYYMMDD.jsonl
```

## 五、常用管理命令

### PM2管理
```bash
# 查看所有进程
pm2 list

# 查看特定进程日志
pm2 logs flask-app
pm2 logs coin-change-tracker

# 重启所有进程
pm2 restart all

# 重启特定进程
pm2 restart flask-app

# 停止所有进程
pm2 stop all

# 查看进程详情
pm2 info flask-app

# 监控资源使用
pm2 monit
```

### 数据管理
```bash
# 查看数据目录大小
du -sh /home/user/webapp/data/

# 查看各子目录大小
du -sh /home/user/webapp/data/*/

# 清理旧数据 (谨慎操作)
find /home/user/webapp/data/ -name "*.jsonl" -mtime +30 -delete
```

### 系统维护
```bash
# 更新Python依赖
cd /home/user/webapp
pip3 list --outdated
pip3 install --upgrade -r requirements.txt

# 更新Node.js依赖
npm outdated
npm update

# 查看磁盘空间
df -h /home/user/webapp
```

## 六、故障排查

### 问题1: PM2进程无法启动
**症状**: `pm2 start` 后进程显示errored  
**排查**:
```bash
# 查看错误日志
pm2 logs [app-name] --err

# 检查Python环境
which python3
python3 --version

# 检查依赖
pip3 list | grep [package-name]

# 手动运行脚本测试
cd /home/user/webapp
python3 app.py
```

### 问题2: Flask应用无法访问
**症状**: `curl http://localhost:9002` 无响应  
**排查**:
```bash
# 检查Flask进程
pm2 list | grep flask

# 检查端口占用
netstat -tlnp | grep 9002
lsof -i :9002

# 查看Flask日志
pm2 logs flask-app

# 检查防火墙
sudo ufw status
```

### 问题3: 数据采集器不更新数据
**症状**: JSONL文件很久没有更新  
**排查**:
```bash
# 检查采集器进程状态
pm2 list | grep collector

# 查看采集器日志
pm2 logs coin-change-tracker

# 检查数据文件权限
ls -l /home/user/webapp/data/

# 手动运行采集器测试
python3 source_code/coin_change_tracker.py
```

### 问题4: 磁盘空间不足
**症状**: 无法写入新数据  
**解决**:
```bash
# 查看磁盘使用
df -h

# 查找大文件
find /home/user/webapp -type f -size +100M

# 清理日志 (谨慎操作)
pm2 flush  # 清空PM2日志
find /home/user/webapp/logs -name "*.log" -mtime +7 -delete
```

## 七、性能优化建议

### 7.1 数据库优化
- 定期归档历史数据
- 建立索引提高查询速度
- 使用分区表管理大量数据

### 7.2 PM2优化
```bash
# 配置日志轮转
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
```

### 7.3 系统资源
- 监控内存使用，必要时增加swap
- 使用SSD提高I/O性能
- 配置定时任务清理旧数据

## 八、备份策略

### 每日备份
```bash
# 自动备份脚本
crontab -e
# 添加：0 2 * * * /home/user/webapp/create_full_backup.sh
```

### 备份验证
- 定期测试恢复流程
- 验证备份文件完整性
- 保留多个版本备份

## 九、安全建议

1. 使用防火墙限制端口访问
2. 配置SSH密钥认证
3. 定期更新系统和依赖
4. 使用环境变量存储敏感信息
5. 定期审计系统日志

## 十、联系支持

- **文档**: /home/user/webapp/docs/
- **日志**: /home/user/webapp/logs/
- **配置**: /home/user/webapp/configs/

---
**最后更新**: $(date +"%Y-%m-%d")
