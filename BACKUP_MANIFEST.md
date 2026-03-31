# 完整系统备份清单

## 备份信息
- **备份日期**: $(date +"%Y-%m-%d %H:%M:%S")
- **备份类型**: 完整备份 (All Data)
- **备份位置**: /tmp/
- **源目录**: /home/user/webapp

## 包含内容

### 1. 核心代码 (core_code/)
- Flask主应用 app.py
- source_code/ 所有Python API文件
- 根目录所有.py文件

### 2. 特殊系统 (special_systems/)
- panic_paged_v2/ - 恐慌指数分页系统V2
- panic_v3/ - 恐慌指数系统V3
- major-events-system/ - 重大事件系统

### 3. 脚本和工具 (scripts/)
- 所有.sh脚本文件
- scripts/ 目录

### 4. Web资源 (web_assets/)
- templates/ - HTML模板 (~130个文件)
- static/ - 静态资源 (CSS, JS, images)

### 5. 配置文件 (configs/)
- ecosystem.config.js - PM2配置
- requirements.txt - Python依赖
- package.json - Node.js依赖
- config/ - 应用配置目录

### 6. 数据文件 (data/) - **完整数据**
- 所有JSONL数据文件 (~3.2GB)
- coin_change_tracker/ - 币种变化追踪
- btc_daily_range/ - BTC日K数据
- crypto_index/ - 加密货币指数
- panic_index/ - 恐慌指数
- signals/ - 交易信号
- okx_*/ - OKX交易数据
- aggregated/ - 聚合数据

### 7. 文档 (docs/)
- README.md
- 所有.md和.txt文档
- 修复报告、部署指南等

### 8. PM2配置 (pm2_config/)
- dump.pm2 - PM2进程快照
- pm2_list.txt - PM2进程列表

## 排除内容
- ❌ logs/ - 日志文件
- ❌ node_modules/ - Node.js依赖包
- ❌ __pycache__/ - Python缓存
- ❌ backups/ - 旧备份

## 恢复说明

详见 DEPLOYMENT_GUIDE.md
