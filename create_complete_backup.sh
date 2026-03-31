#!/bin/bash
# 完整系统备份脚本
# 用途: 创建包含所有代码、配置、依赖和数据的完整备份
# 目标: /tmp/webapp_complete_backup_YYYYMMDD_HHMMSS.tar.gz

set -e  # 遇到错误立即退出

echo "=========================================="
echo "   完整系统备份脚本"
echo "=========================================="
echo ""

# 定义颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 记录开始时间
START_TIME=$(date +%s)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="webapp_complete_backup_${TIMESTAMP}"
BACKUP_DIR="/tmp/${BACKUP_NAME}"
BACKUP_FILE="/tmp/${BACKUP_NAME}.tar.gz"

echo -e "${BLUE}📦 备份名称: ${BACKUP_NAME}${NC}"
echo -e "${BLUE}📁 临时目录: ${BACKUP_DIR}${NC}"
echo -e "${BLUE}📦 目标文件: ${BACKUP_FILE}${NC}"
echo ""

# 创建临时备份目录
echo -e "${YELLOW}🔨 创建临时备份目录...${NC}"
mkdir -p "${BACKUP_DIR}"
cd /home/user/webapp

# ==========================================
# 1. 核心代码文件
# ==========================================
echo -e "${GREEN}📝 1. 备份核心代码文件...${NC}"
mkdir -p "${BACKUP_DIR}/core_code"

# 主应用文件
echo "   - 主应用文件 (app.py, start_flask.py, etc.)"
cp -p app.py start_flask.py "${BACKUP_DIR}/core_code/" 2>/dev/null || true

# source_code 目录
echo "   - source_code/ 目录 (所有Python API文件)"
if [ -d "source_code" ]; then
    cp -r source_code "${BACKUP_DIR}/core_code/"
fi

# panic系统
echo "   - panic_paged_v2/ 目录"
if [ -d "panic_paged_v2" ]; then
    cp -r panic_paged_v2 "${BACKUP_DIR}/core_code/"
fi

echo "   - panic_v3/ 目录"
if [ -d "panic_v3" ]; then
    cp -r panic_v3 "${BACKUP_DIR}/core_code/"
fi

# 根目录下的Python脚本
echo "   - 根目录Python脚本 (*.py)"
find . -maxdepth 1 -name "*.py" -type f -exec cp -p {} "${BACKUP_DIR}/core_code/" \;

# ==========================================
# 2. 监控和脚本
# ==========================================
echo -e "${GREEN}📊 2. 备份监控脚本和工具...${NC}"
mkdir -p "${BACKUP_DIR}/monitors_and_scripts"

if [ -d "monitors" ]; then
    echo "   - monitors/ 目录"
    cp -r monitors "${BACKUP_DIR}/monitors_and_scripts/"
fi

if [ -d "scripts" ]; then
    echo "   - scripts/ 目录"
    cp -r scripts "${BACKUP_DIR}/monitors_and_scripts/"
fi

# Shell脚本
echo "   - Shell脚本 (*.sh)"
find . -maxdepth 1 -name "*.sh" -type f -exec cp -p {} "${BACKUP_DIR}/monitors_and_scripts/" \;

# ==========================================
# 3. Web界面资源
# ==========================================
echo -e "${GREEN}🌐 3. 备份Web界面资源...${NC}"
mkdir -p "${BACKUP_DIR}/web_assets"

if [ -d "templates" ]; then
    echo "   - templates/ 目录 (HTML模板)"
    cp -r templates "${BACKUP_DIR}/web_assets/"
fi

if [ -d "static" ]; then
    echo "   - static/ 目录 (CSS/JS/图片)"
    cp -r static "${BACKUP_DIR}/web_assets/"
fi

# ==========================================
# 4. 配置文件
# ==========================================
echo -e "${GREEN}⚙️  4. 备份配置文件...${NC}"
mkdir -p "${BACKUP_DIR}/configs"

# PM2配置
if [ -d "pm2" ]; then
    echo "   - pm2/ 目录"
    cp -r pm2 "${BACKUP_DIR}/configs/"
fi

# Ecosystem配置
echo "   - PM2 ecosystem配置文件"
cp -p ecosystem*.js "${BACKUP_DIR}/configs/" 2>/dev/null || true
cp -p pm2_process_list.json "${BACKUP_DIR}/configs/" 2>/dev/null || true

# Git配置
echo "   - Git配置"
if [ -d ".git" ]; then
    cp -r .git "${BACKUP_DIR}/configs/"
fi

# Python依赖
echo "   - requirements.txt"
cp -p requirements.txt "${BACKUP_DIR}/configs/" 2>/dev/null || true

# JSON配置文件
echo "   - JSON配置文件"
cp -p *.json "${BACKUP_DIR}/configs/" 2>/dev/null || true

# JavaScript配置
echo "   - JavaScript配置文件"
find . -maxdepth 1 -name "*.js" -type f -exec cp -p {} "${BACKUP_DIR}/configs/" \;

# ==========================================
# 5. 文档
# ==========================================
echo -e "${GREEN}📚 5. 备份文档...${NC}"
mkdir -p "${BACKUP_DIR}/docs"

echo "   - Markdown文档 (*.md)"
find . -maxdepth 1 -name "*.md" -type f -exec cp -p {} "${BACKUP_DIR}/docs/" \;

echo "   - README文件"
cp -p README* "${BACKUP_DIR}/docs/" 2>/dev/null || true

echo "   - 文本文档 (*.txt)"
find . -maxdepth 1 -name "*.txt" -type f -exec cp -p {} "${BACKUP_DIR}/docs/" \;

# ==========================================
# 6. 数据文件 (完整备份)
# ==========================================
echo -e "${GREEN}💾 6. 备份数据文件 (完整备份，包含所有历史数据)...${NC}"
if [ -d "data" ]; then
    echo "   - data/ 目录 (完整备份)"
    echo "     警告: 这可能需要较长时间..."
    
    # 显示数据目录大小
    DATA_SIZE=$(du -sh data/ | cut -f1)
    echo "     数据目录大小: ${DATA_SIZE}"
    
    # 完整复制数据目录
    cp -r data "${BACKUP_DIR}/"
    
    echo "     ✅ 数据备份完成"
fi

# ==========================================
# 7. 交易子系统
# ==========================================
echo -e "${GREEN}💰 7. 备份交易子系统...${NC}"
if [ -d "trading_subsystems" ]; then
    echo "   - trading_subsystems/ 目录"
    cp -r trading_subsystems "${BACKUP_DIR}/"
fi

if [ -d "trading_signals_system" ]; then
    echo "   - trading_signals_system/ 目录"
    cp -r trading_signals_system "${BACKUP_DIR}/"
fi

# ==========================================
# 8. 系统依赖清单
# ==========================================
echo -e "${GREEN}📋 8. 导出系统依赖清单...${NC}"
mkdir -p "${BACKUP_DIR}/dependencies"

# Python依赖
echo "   - Python包列表 (pip freeze)"
pip freeze > "${BACKUP_DIR}/dependencies/python_requirements.txt" 2>/dev/null || true

# 系统包列表 (apt)
echo "   - 系统包列表 (dpkg)"
dpkg -l > "${BACKUP_DIR}/dependencies/system_packages.txt" 2>/dev/null || true

# PM2进程列表
echo "   - PM2进程列表"
pm2 list > "${BACKUP_DIR}/dependencies/pm2_processes.txt" 2>/dev/null || true
pm2 save 2>/dev/null || true
if [ -f ~/.pm2/dump.pm2 ]; then
    cp ~/.pm2/dump.pm2 "${BACKUP_DIR}/dependencies/pm2_dump.pm2"
fi

# Node.js版本
echo "   - Node.js和npm版本"
echo "Node.js: $(node --version 2>/dev/null || echo 'Not installed')" > "${BACKUP_DIR}/dependencies/nodejs_version.txt"
echo "npm: $(npm --version 2>/dev/null || echo 'Not installed')" >> "${BACKUP_DIR}/dependencies/nodejs_version.txt"
echo "PM2: $(pm2 --version 2>/dev/null || echo 'Not installed')" >> "${BACKUP_DIR}/dependencies/nodejs_version.txt"

# Python版本
echo "   - Python版本"
python3 --version > "${BACKUP_DIR}/dependencies/python_version.txt" 2>&1 || true

# ==========================================
# 9. 创建备份清单
# ==========================================
echo -e "${GREEN}📄 9. 创建备份清单...${NC}"

cat > "${BACKUP_DIR}/BACKUP_MANIFEST.md" << 'EOF'
# 完整系统备份清单

## 备份信息

- **备份时间**: {TIMESTAMP}
- **备份位置**: /tmp/webapp_complete_backup_{TIMESTAMP}.tar.gz
- **源目录**: /home/user/webapp

## 目录结构

```
webapp_complete_backup_YYYYMMDD_HHMMSS/
├── core_code/                    # 核心代码文件
│   ├── app.py                    # Flask主应用
│   ├── start_flask.py            # Flask启动脚本
│   ├── source_code/              # 所有Python API文件
│   ├── panic_paged_v2/           # Panic系统v2
│   ├── panic_v3/                 # Panic系统v3
│   └── *.py                      # 根目录Python脚本
├── monitors_and_scripts/         # 监控和工具脚本
│   ├── monitors/                 # 监控脚本
│   └── scripts/                  # 工具脚本
├── web_assets/                   # Web界面资源
│   ├── templates/                # HTML模板 (130+个)
│   └── static/                   # CSS/JS/图片
├── configs/                      # 配置文件
│   ├── pm2/                      # PM2配置
│   ├── ecosystem*.js             # PM2 ecosystem配置
│   ├── requirements.txt          # Python依赖
│   ├── .git/                     # Git仓库
│   └── *.json                    # JSON配置文件
├── docs/                         # 文档
│   └── *.md                      # Markdown文档
├── data/                         # 数据文件 (完整备份)
│   ├── coin_change_tracker/      # 币种变化追踪数据
│   │   ├── coin_change_*.jsonl   # 每日数据文件
│   │   └── aggregated/           # 聚合数据
│   │       ├── 10min_up_ratio_*.json
│   │       ├── positive_ratio_stats_*.json
│   │       └── velocity_stats_*.json
│   ├── btc_daily_range/          # BTC日内振幅数据
│   ├── crypto_index/             # 加密指数数据
│   ├── panic_index/              # 恐慌指数数据
│   ├── signals/                  # 信号数据
│   ├── liquidation/              # 爆仓数据
│   └── okx_trading_logs/         # OKX交易日志
├── trading_subsystems/           # 交易子系统
├── trading_signals_system/       # 交易信号系统
└── dependencies/                 # 依赖清单
    ├── python_requirements.txt   # Python包列表
    ├── system_packages.txt       # 系统包列表
    ├── pm2_processes.txt         # PM2进程列表
    ├── pm2_dump.pm2              # PM2进程快照
    ├── nodejs_version.txt        # Node.js版本
    └── python_version.txt        # Python版本
```

## 文件统计

- **Python文件**: ~88个
- **Markdown文档**: ~60个
- **HTML模板**: ~130个
- **配置文件**: ~15个
- **数据文件**: 完整备份，包含所有历史数据

## 排除项

以下内容**不包含**在备份中:

- ❌ `logs/` - 日志文件 (65MB)
- ❌ `node_modules/` - Node.js依赖 (34MB)
- ❌ `backups/` - 旧备份目录
- ❌ `__pycache__/` - Python缓存
- ❌ `*.pyc` - Python字节码文件
- ❌ `trading_system_complete_*.tar.gz` - 旧备份文件

## PM2 服务列表

1. **flask-app** - Flask主应用服务器 (端口: 9002)
2. **signal-collector** - 信号采集器
3. **crypto-index-collector** - 加密指数采集器
4. **coin-change-tracker** - 币种变化追踪器
5. **intraday-pattern-monitor** - 日内模式监控器
6. **coin-change-aggregator** - 币种变化聚合器
7. **btc-daily-range** - BTC日内振幅监控器

## 重新部署说明

详细的重新部署步骤请查看 `DEPLOYMENT_GUIDE.md` 文件。

快速恢复命令:
```bash
# 1. 解压备份
cd /tmp
tar -xzf webapp_complete_backup_YYYYMMDD_HHMMSS.tar.gz

# 2. 复制文件到目标目录
mkdir -p /home/user/webapp
cd webapp_complete_backup_YYYYMMDD_HHMMSS
cp -r core_code/* /home/user/webapp/
cp -r monitors_and_scripts/* /home/user/webapp/
cp -r web_assets/* /home/user/webapp/
cp -r configs/* /home/user/webapp/
cp -r data /home/user/webapp/
cp -r trading_subsystems /home/user/webapp/
cp -r trading_signals_system /home/user/webapp/

# 3. 安装依赖
cd /home/user/webapp
pip install -r requirements.txt

# 4. 恢复PM2服务
pm2 resurrect
# 或手动启动
pm2 start ecosystem.config.js
```

EOF

# 替换时间戳占位符
sed -i "s/{TIMESTAMP}/${TIMESTAMP}/g" "${BACKUP_DIR}/BACKUP_MANIFEST.md"

# ==========================================
# 10. 创建详细的部署指南
# ==========================================
echo -e "${GREEN}📖 10. 创建详细部署指南...${NC}"

cat > "${BACKUP_DIR}/DEPLOYMENT_GUIDE.md" << 'EOF'
# 完整系统重新部署指南

## 📋 目录

1. [系统要求](#系统要求)
2. [备份恢复](#备份恢复)
3. [依赖安装](#依赖安装)
4. [数据库和数据文件](#数据库和数据文件)
5. [服务配置](#服务配置)
6. [启动服务](#启动服务)
7. [验证部署](#验证部署)
8. [故障排除](#故障排除)

---

## 系统要求

### 操作系统
- Ubuntu 20.04 LTS 或更高版本
- Debian 10 或更高版本
- 其他基于Debian的Linux发行版

### 软件依赖
- **Python**: 3.8 或更高版本
- **Node.js**: 14.x 或更高版本
- **npm**: 6.x 或更高版本
- **PM2**: 最新版本 (npm install -g pm2)
- **Git**: 2.x 或更高版本

### 硬件要求
- **CPU**: 2核或以上
- **内存**: 4GB或以上 (推荐8GB)
- **磁盘**: 20GB可用空间 (推荐50GB)

---

## 备份恢复

### 1. 解压备份文件

```bash
# 进入备份目录
cd /tmp

# 解压备份 (这可能需要几分钟)
tar -xzf webapp_complete_backup_YYYYMMDD_HHMMSS.tar.gz

# 进入解压后的目录
cd webapp_complete_backup_YYYYMMDD_HHMMSS

# 查看备份清单
cat BACKUP_MANIFEST.md
```

### 2. 创建目标目录

```bash
# 创建主目录 (如果不存在)
sudo mkdir -p /home/user/webapp
sudo chown -R $USER:$USER /home/user/webapp
```

### 3. 复制文件

```bash
# 复制核心代码
cp -r core_code/* /home/user/webapp/

# 复制监控和脚本
cp -r monitors_and_scripts/monitors /home/user/webapp/ 2>/dev/null || true
cp -r monitors_and_scripts/scripts /home/user/webapp/ 2>/dev/null || true
cp monitors_and_scripts/*.sh /home/user/webapp/ 2>/dev/null || true

# 复制Web资源
cp -r web_assets/templates /home/user/webapp/
cp -r web_assets/static /home/user/webapp/

# 复制配置文件
cp -r configs/pm2 /home/user/webapp/ 2>/dev/null || true
cp configs/ecosystem*.js /home/user/webapp/ 2>/dev/null || true
cp configs/requirements.txt /home/user/webapp/
cp configs/*.json /home/user/webapp/ 2>/dev/null || true
cp -r configs/.git /home/user/webapp/ 2>/dev/null || true

# 复制文档
cp docs/*.md /home/user/webapp/ 2>/dev/null || true

# 复制数据文件 (这可能需要较长时间)
echo "⚠️  正在复制数据文件，这可能需要几分钟..."
cp -r data /home/user/webapp/

# 复制交易系统
cp -r trading_subsystems /home/user/webapp/ 2>/dev/null || true
cp -r trading_signals_system /home/user/webapp/ 2>/dev/null || true

echo "✅ 文件复制完成!"
```

---

## 依赖安装

### 1. 安装系统依赖

```bash
# 更新包列表
sudo apt update

# 安装Python和pip
sudo apt install -y python3 python3-pip python3-venv

# 安装Node.js和npm (如果尚未安装)
curl -fsSL https://deb.nodesource.com/setup_14.x | sudo -E bash -
sudo apt install -y nodejs

# 验证安装
python3 --version
node --version
npm --version
```

### 2. 安装Python依赖

```bash
cd /home/user/webapp

# 使用备份的requirements.txt安装依赖
pip3 install -r requirements.txt

# 或者使用导出的完整依赖列表
# pip3 install -r /tmp/webapp_complete_backup_*/dependencies/python_requirements.txt
```

**主要Python包** (参考):
- Flask>=2.0.0
- requests>=2.26.0
- python-dotenv>=0.19.0
- APScheduler>=3.8.0
- ccxt>=2.0.0
- pandas>=1.3.0
- numpy>=1.21.0
- 其他约70个依赖包

### 3. 安装PM2

```bash
# 全局安装PM2
sudo npm install -g pm2

# 验证安装
pm2 --version

# 设置PM2开机自启动
pm2 startup
# 按照输出的命令执行 (通常是 sudo env PATH=... pm2 startup ...)
```

---

## 数据库和数据文件

### 数据文件结构

本系统使用 **JSONL (JSON Lines)** 格式存储数据，不需要额外的数据库服务器。

所有数据位于 `/home/user/webapp/data/` 目录:

```
data/
├── coin_change_tracker/          # 币种变化追踪数据
│   ├── coin_change_20260301.jsonl
│   ├── coin_change_20260302.jsonl
│   ├── ...
│   └── aggregated/               # 聚合数据
│       ├── 10min_up_ratio_20260301.json
│       ├── positive_ratio_stats_20260301.json
│       └── velocity_stats_20260301.json
├── btc_daily_range/              # BTC日内振幅数据
│   └── btc_range_20260301.jsonl
├── crypto_index/                 # 加密指数数据
├── panic_index/                  # 恐慌指数数据
├── signals/                      # 信号数据
├── liquidation/                  # 爆仓数据
└── okx_trading_logs/             # OKX交易日志
```

### 数据验证

```bash
cd /home/user/webapp/data

# 检查数据目录大小
du -sh .

# 检查最新的数据文件
ls -lht coin_change_tracker/coin_change_*.jsonl | head -5

# 验证数据文件格式 (检查第一行)
head -1 coin_change_tracker/coin_change_20260311.jsonl | jq .
```

---

## 服务配置

### PM2 Ecosystem配置

主要配置文件: `ecosystem.config.js`

```javascript
module.exports = {
  apps: [
    {
      name: "flask-app",
      script: "app.py",
      interpreter: "python3",
      cwd: "/home/user/webapp",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "500M",
      env: {
        FLASK_ENV: "production",
        PORT: "9002"
      }
    },
    {
      name: "coin-change-tracker",
      script: "source_code/coin_change_tracker.py",
      interpreter: "python3",
      cwd: "/home/user/webapp",
      instances: 1,
      autorestart: true,
      watch: false
    },
    {
      name: "coin-change-aggregator",
      script: "source_code/coin_change_aggregator.py",
      interpreter: "python3",
      cwd: "/home/user/webapp",
      instances: 1,
      autorestart: true,
      watch: false
    },
    {
      name: "btc-daily-range",
      script: "source_code/btc_daily_range_collector.py",
      interpreter: "python3",
      cwd: "/home/user/webapp",
      instances: 1,
      autorestart: true,
      watch: false
    },
    {
      name: "crypto-index-collector",
      script: "source_code/crypto_index_collector.py",
      interpreter: "python3",
      cwd: "/home/user/webapp",
      instances: 1,
      autorestart: true,
      watch: false
    },
    {
      name: "signal-collector",
      script: "source_code/signal_collector.py",
      interpreter: "python3",
      cwd: "/home/user/webapp",
      instances: 1,
      autorestart: true,
      watch: false
    },
    {
      name: "intraday-pattern-monitor",
      script: "source_code/intraday_pattern_monitor.py",
      interpreter: "python3",
      cwd: "/home/user/webapp",
      instances: 1,
      autorestart: true,
      watch: false
    }
  ]
};
```

### 端口配置

- **Flask应用**: 端口 `9002` (可在 ecosystem.config.js 中修改)
- **PM2守护进程**: 无需开放外部端口

### 防火墙配置 (可选)

```bash
# 如果使用UFW防火墙
sudo ufw allow 9002/tcp
sudo ufw reload
```

---

## 启动服务

### 方法1: 使用PM2 Dump恢复 (推荐)

如果备份中包含 `pm2_dump.pm2` 文件:

```bash
# 复制PM2 dump文件
cp /tmp/webapp_complete_backup_*/dependencies/pm2_dump.pm2 ~/.pm2/dump.pm2

# 恢复PM2进程
cd /home/user/webapp
pm2 resurrect

# 查看进程状态
pm2 list
```

### 方法2: 手动启动所有服务

```bash
cd /home/user/webapp

# 启动所有服务
pm2 start ecosystem.config.js

# 查看进程列表
pm2 list

# 查看日志
pm2 logs --lines 50
```

### 方法3: 逐个启动服务

```bash
cd /home/user/webapp

# 1. 启动Flask应用
pm2 start app.py --name flask-app --interpreter python3

# 2. 启动数据采集器
pm2 start source_code/coin_change_tracker.py --name coin-change-tracker --interpreter python3
pm2 start source_code/btc_daily_range_collector.py --name btc-daily-range --interpreter python3
pm2 start source_code/crypto_index_collector.py --name crypto-index-collector --interpreter python3

# 3. 启动聚合器
pm2 start source_code/coin_change_aggregator.py --name coin-change-aggregator --interpreter python3

# 4. 启动监控器
pm2 start source_code/intraday_pattern_monitor.py --name intraday-pattern-monitor --interpreter python3
pm2 start source_code/signal_collector.py --name signal-collector --interpreter python3

# 5. 保存PM2配置
pm2 save
```

### 设置开机自启动

```bash
# 保存当前PM2进程列表
pm2 save

# 生成开机启动脚本
pm2 startup

# 按照输出的命令执行 (例如):
# sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u user --hp /home/user
```

---

## 验证部署

### 1. 检查PM2服务状态

```bash
pm2 list

# 期望输出: 所有服务状态为 "online"
# ┌────┬─────────────────────────────┬─────────┬─────────┬─────────┬──────────┐
# │ id │ name                        │ mode    │ status  │ restart │ uptime   │
# ├────┼─────────────────────────────┼─────────┼─────────┼─────────┼──────────┤
# │ 0  │ flask-app                   │ fork    │ online  │ 0       │ 2m       │
# │ 1  │ coin-change-tracker         │ fork    │ online  │ 0       │ 2m       │
# │ 2  │ coin-change-aggregator      │ fork    │ online  │ 0       │ 2m       │
# │ ...│ ...                         │ ...     │ ...     │ ...     │ ...      │
# └────┴─────────────────────────────┴─────────┴─────────┴─────────┴──────────┘
```

### 2. 检查Flask应用

```bash
# 测试Flask是否响应
curl http://localhost:9002/

# 测试API端点
curl http://localhost:9002/api/coin-change-tracker/history?limit=1

# 期望输出: JSON格式的响应
```

### 3. 检查数据采集

```bash
# 查看最新数据文件的修改时间
ls -lt /home/user/webapp/data/coin_change_tracker/coin_change_*.jsonl | head -1

# 查看实时日志
pm2 logs coin-change-tracker --lines 20

# 期望: 看到定期的数据采集日志
```

### 4. 访问Web界面

打开浏览器访问:
- 主页: `http://<服务器IP>:9002/`
- 币种追踪页面: `http://<服务器IP>:9002/coin-change-tracker`
- BTC振幅页面: `http://<服务器IP>:9002/btc-daily-range`

### 5. 检查系统资源使用

```bash
# 查看PM2进程内存使用
pm2 monit

# 查看系统资源
htop
# 或
top
```

---

## 故障排除

### 问题1: PM2服务无法启动

**症状**: `pm2 list` 显示服务状态为 "errored" 或 "stopped"

**解决方案**:
```bash
# 查看错误日志
pm2 logs flask-app --err --lines 50

# 常见问题:
# 1. Python依赖缺失 -> 重新运行 pip install -r requirements.txt
# 2. 端口被占用 -> 修改 ecosystem.config.js 中的端口号
# 3. 文件权限问题 -> 运行 chmod +x 对应的脚本文件
```

### 问题2: Flask应用无法访问

**症状**: 浏览器无法打开 `http://localhost:9002/`

**解决方案**:
```bash
# 1. 检查Flask是否在运行
pm2 list | grep flask-app

# 2. 检查端口是否监听
netstat -tulpn | grep 9002
# 或
ss -tulpn | grep 9002

# 3. 检查防火墙
sudo ufw status
# 如果9002端口被阻止，运行:
sudo ufw allow 9002/tcp

# 4. 查看Flask日志
pm2 logs flask-app --lines 100
```

### 问题3: 数据采集器不工作

**症状**: 数据文件没有更新

**解决方案**:
```bash
# 1. 检查采集器状态
pm2 list | grep tracker

# 2. 查看采集器日志
pm2 logs coin-change-tracker --lines 50

# 3. 手动测试采集器
cd /home/user/webapp
python3 source_code/coin_change_tracker.py

# 4. 检查网络连接 (采集器需要访问外部API)
curl -I https://api.coingecko.com/api/v3/ping
```

### 问题4: Python依赖缺失

**症状**: 日志中出现 `ModuleNotFoundError: No module named 'xxx'`

**解决方案**:
```bash
# 安装缺失的包
pip3 install 包名

# 或重新安装所有依赖
cd /home/user/webapp
pip3 install -r requirements.txt --upgrade

# 如果某些包安装失败，尝试:
pip3 install 包名 --no-cache-dir
```

### 问题5: 磁盘空间不足

**症状**: 服务崩溃或数据无法写入

**解决方案**:
```bash
# 检查磁盘使用情况
df -h

# 清理旧日志 (谨慎操作!)
cd /home/user/webapp
rm -rf logs/*.log.old
pm2 flush  # 清空PM2日志

# 清理旧数据 (如果需要)
# 只保留最近30天的数据
find data/coin_change_tracker -name "coin_change_*.jsonl" -mtime +30 -delete
```

### 问题6: PM2进程频繁重启

**症状**: `pm2 list` 显示 restart 次数持续增加

**解决方案**:
```bash
# 查看崩溃原因
pm2 logs <进程名> --err --lines 100

# 常见原因:
# 1. 内存泄漏 -> 增加 max_memory_restart 限制
# 2. 未捕获的异常 -> 修复代码错误
# 3. API限流 -> 增加请求间隔时间

# 临时解决: 停止自动重启
pm2 stop <进程名>
pm2 restart <进程名> --no-autorestart
```

---

## 系统维护

### 定期备份

建议每周创建一次完整备份:
```bash
cd /home/user/webapp
bash create_complete_backup.sh
```

### 日志轮转

PM2会自动管理日志，但建议定期清理:
```bash
# 查看日志大小
du -sh ~/.pm2/logs

# 清空所有日志
pm2 flush

# 或设置日志轮转 (安装pm2-logrotate模块)
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
```

### 更新依赖

定期更新Python包:
```bash
cd /home/user/webapp
pip3 list --outdated
pip3 install --upgrade 包名
```

---

## 联系和支持

如有问题，请查阅:
- 系统文档: `/home/user/webapp/docs/`
- 备份清单: `BACKUP_MANIFEST.md`
- Git提交历史: `git log`

---

**部署完成后，建议立即创建一个新的备份作为基线！**

EOF

# ==========================================
# 11. 计算备份大小和文件数
# ==========================================
echo -e "${YELLOW}📊 计算备份统计信息...${NC}"

TOTAL_FILES=$(find "${BACKUP_DIR}" -type f | wc -l)
TOTAL_DIRS=$(find "${BACKUP_DIR}" -type d | wc -l)
BACKUP_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)

echo "   - 文件数: ${TOTAL_FILES}"
echo "   - 目录数: ${TOTAL_DIRS}"
echo "   - 总大小: ${BACKUP_SIZE}"

# ==========================================
# 12. 压缩备份
# ==========================================
echo ""
echo -e "${YELLOW}🗜️  压缩备份文件...${NC}"
echo "   这可能需要几分钟，请耐心等待..."

tar -czf "${BACKUP_FILE}" -C /tmp "${BACKUP_NAME}"

# 检查压缩是否成功
if [ -f "${BACKUP_FILE}" ]; then
    COMPRESSED_SIZE=$(du -sh "${BACKUP_FILE}" | cut -f1)
    echo -e "${GREEN}✅ 压缩完成!${NC}"
    echo "   - 压缩后大小: ${COMPRESSED_SIZE}"
    
    # 删除临时目录
    echo -e "${YELLOW}🧹 清理临时文件...${NC}"
    rm -rf "${BACKUP_DIR}"
else
    echo -e "${RED}❌ 压缩失败!${NC}"
    exit 1
fi

# ==========================================
# 13. 生成最终报告
# ==========================================
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "=========================================="
echo -e "${GREEN}   ✅ 备份完成!${NC}"
echo "=========================================="
echo ""
echo -e "${BLUE}📦 备份文件: ${BACKUP_FILE}${NC}"
echo -e "${BLUE}📊 压缩后大小: ${COMPRESSED_SIZE}${NC}"
echo -e "${BLUE}⏱️  总耗时: ${MINUTES}分${SECONDS}秒${NC}"
echo ""
echo "下一步操作:"
echo "  1. 解压备份:"
echo "     cd /tmp && tar -xzf ${BACKUP_NAME}.tar.gz"
echo ""
echo "  2. 查看备份清单:"
echo "     cat /tmp/${BACKUP_NAME}/BACKUP_MANIFEST.md"
echo ""
echo "  3. 查看部署指南:"
echo "     cat /tmp/${BACKUP_NAME}/DEPLOYMENT_GUIDE.md"
echo ""
echo "  4. 恢复系统:"
echo "     按照 DEPLOYMENT_GUIDE.md 中的步骤操作"
echo ""
echo "=========================================="
