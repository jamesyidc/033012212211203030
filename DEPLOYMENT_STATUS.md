# 系统部署状态报告

**部署时间**: 2026-03-15 17:09 UTC  
**部署位置**: /home/user/webapp  
**Python版本**: 3.12.11  
**PM2版本**: 6.0.14

---

## ✅ 部署成功！

### 🌐 Web应用访问地址

**Flask Web应用**: https://9002-izdl7i89gq7ib3tbi6fq1-82b888ba.sandbox.novita.ai

- 端口: 9002
- 状态: ✅ 运行中
- 内存使用: ~85MB

---

## 📊 服务运行状态

### 核心服务 (4个)

| 服务名称 | 状态 | 说明 |
|---------|------|------|
| flask-app | ✅ online | Flask Web应用主服务 |
| data-health-monitor | ✅ online | 数据健康监控 |
| system-health-monitor | ✅ online | 系统健康监控 |
| signal-collector | ✅ online | 交易信号采集 |

### 数据采集服务 (14个)

| 服务名称 | 状态 | 说明 |
|---------|------|------|
| liquidation-1h-collector | ✅ online | 1小时爆仓数据采集 |
| crypto-index-collector | ✅ online | 加密货币指数采集 |
| price-speed-collector | ✅ online | 价格速度采集 |
| sar-jsonl-collector | ✅ online | SAR指标采集 |
| price-comparison-collector | ✅ online | 价格对比采集 |
| financial-indicators-collector | ✅ online | 金融指标采集 |
| okx-day-change-collector | ✅ online | OKX日变化采集 |
| price-baseline-collector | ✅ online | 价格基线采集 |
| sar-bias-stats-collector | ✅ online | SAR偏差统计采集 |
| panic-wash-collector | ✅ online | 恐慌洗盘数据采集 |
| coin-change-tracker | ✅ online | 币种变化追踪 |
| coin-price-tracker | ✅ online | 币价追踪 |
| market-sentiment-collector | ✅ online | 市场情绪采集 |
| new-high-low-collector | ✅ online | 新高新低采集 |

**总计运行服务**: 18个  
**全部在线**: ✅ 是

---

## 📁 目录结构

```
/home/user/webapp/
├── core_code/          # 核心代码(包含Flask应用)
├── source_code/        # 数据采集脚本
├── data/               # 数据存储目录
│   ├── coin_change_tracker/
│   ├── crypto_index_jsonl/
│   ├── panic_jsonl/
│   └── ...
├── logs/               # PM2日志目录
├── templates/          # Flask模板
├── static/             # 静态资源
└── *.html              # Web界面文件
```

---

## 🔧 配置文件

- **PM2配置**: ecosystem.full.config.json
- **PM2核心配置**: ecosystem.core.config.json  
- **Python依赖**: requirements.txt
- **PM2进程保存**: ~/.pm2/dump.pm2

---

## 📝 管理命令

### PM2进程管理
```bash
# 查看所有服务状态
pm2 list

# 查看特定服务日志
pm2 logs flask-app
pm2 logs coin-change-tracker

# 重启所有服务
pm2 restart all

# 重启特定服务
pm2 restart flask-app

# 停止所有服务
pm2 stop all

# 保存当前进程列表
pm2 save

# 监控资源使用
pm2 monit
```

### 数据管理
```bash
# 查看数据目录大小
du -sh /home/user/webapp/data/

# 查看各子目录
ls -lh /home/user/webapp/data/

# 检查JSONL文件
find /home/user/webapp -name "*.jsonl" -mtime -1
```

---

## 🚀 功能特性

### ✅ 已实现功能

1. **Flask Web应用** - 主Web服务运行在端口9002
2. **数据采集系统** - 14个数据采集器实时收集市场数据
3. **健康监控** - 系统和数据健康状态监控
4. **PM2进程管理** - 所有服务由PM2管理，自动重启
5. **日志系统** - 完整的日志记录和管理
6. **JSONL数据存储** - 高效的时序数据存储

### 🎯 核心系统

- **价格位置系统** - 价格位置分析和预警
- **SAR指标系统** - SAR偏差趋势分析
- **币种追踪系统** - 实时币种变化监控
- **市场情绪系统** - 市场情绪指标采集
- **恐慌指数系统** - 恐慌洗盘数据分析

---

## 📊 系统状态监控

### 实时监控命令
```bash
# 查看所有服务状态
pm2 list

# 查看系统资源使用
pm2 monit

# 查看Flask应用日志
pm2 logs flask-app --lines 50
```

### 健康检查
```bash
# 检查Flask服务
curl http://localhost:9002/

# 检查数据采集
ls -lt /home/user/webapp/data/*/

# 检查PM2状态
pm2 status
```

---

## ⚠️ 注意事项

1. **端口**: Flask应用运行在9002端口
2. **日志**: 所有日志保存在 `/home/user/webapp/logs/`
3. **数据**: JSONL数据保存在 `/home/user/webapp/data/`
4. **依赖**: 某些服务需要ccxt等Python库

---

## 🔄 路由和监控

### Web界面路由

- `/` - 主页
- `/index.html` - 系统首页
- `/control_center.html` - 控制中心
- `/coin_change_tracker.html` - 币种追踪
- `/panic_new.html` - 恐慌指数
- `/price_position_unified.html` - 价格位置统一界面
- `/sar_bias_trend.html` - SAR偏差趋势

所有HTML文件都可以通过Flask应用访问。

---

## 📈 下一步操作

### 可选优化

1. **添加更多采集器** - 根据需要添加其他数据源
2. **配置定时任务** - 设置数据清理和备份任务
3. **监控告警** - 配置系统异常告警
4. **性能优化** - 根据实际使用调整资源配置
5. **数据备份** - 定期备份重要数据

### 导入JSONL数据

如需导入历史数据:
```bash
# 将JSONL文件复制到对应目录
cp your_data.jsonl /home/user/webapp/data/target_directory/

# 重启相关服务
pm2 restart [service-name]
```

---

## ✅ 部署完成清单

- [x] Python环境配置
- [x] Flask应用启动
- [x] PM2进程管理配置
- [x] 18个服务全部启动
- [x] 日志系统配置
- [x] Web应用访问验证
- [x] 数据目录结构创建
- [x] PM2配置保存

**状态**: 🎉 **系统已完全部署并正常运行！**

---

*最后更新: 2026-03-15 17:09 UTC*
