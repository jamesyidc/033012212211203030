# 完整重部署指南

<details>
<summary>📘 点击展开/收起：完整系统恢复和重部署流程</summary>

## 🎯 指南概述

本指南提供从完整备份恢复整个 webapp 系统的详细步骤，适用于：
- 灾难恢复
- 系统迁移到新服务器
- 开发环境重建
- 生产环境部署

---

## 📦 备份文件说明

### 当前完整备份

**文件位置**：`/tmp/webapp_backup_YYYYMMDD_N.tar.gz`
- **压缩后大小**：~285 MB
- **原始大小**：~3.6 GB
- **文件数量**：3,949+ 文件
- **压缩比**：约 13:1

### 备份内容清单

#### ✅ 核心代码 (约 5 MB)
- `core_code/` - 核心 Flask 应用代码
- `source_code/` - 数据收集器和管理器
- `panic_paged_v2/` - Panic V2 系统
- `panic_v3/` - Panic V3 系统
- `major-events-system/` - 重大事件系统
- 根目录 Python 文件

#### ✅ 数据目录 (约 3.5 GB)
**大型数据目录**：
- `support_resistance_daily/` - 977 MB (支撑阻力每日数据)
- `support_resistance_jsonl/` - 740 MB (支撑阻力 JSONL)
- `data/` - 259 MB (主数据目录，445+ JSONL 文件)
- `coin_change_tracker/` - 182 MB (币种变化追踪)
- `price_speed_jsonl/` - 173 MB (价格速度数据)
- `anchor_profit_stats/` - 163 MB (锚点收益统计)
- `anchor_unified/` - 117 MB (统一锚点数据)
- `sar_slope_jsonl/` - 116 MB (SAR 斜率数据)
- `v1v2_jsonl/` - 108 MB (V1V2 版本数据)

**中型数据目录**：
- `anchor_daily/` - 81 MB
- `sar_jsonl/` - 65 MB
- `gdrive_jsonl/` - 24 MB
- `okx_trading_jsonl/` - 18 MB
- `panic_daily/` - 13 MB
- `escape_signal_jsonl/` - 12 MB
- `extreme_jsonl/` - 8.8 MB

**其他 60+ 数据目录** (每个 < 10 MB)

#### ✅ 配置和依赖
- `.env` - 环境变量配置
- `requirements.txt` - Python 依赖
- `package.json` - Node.js 依赖
- `ecosystem.config.js` - PM2 进程配置
- 各种 JSON/YAML 配置文件

#### ✅ 日志文件
- `logs/` - 系统运行日志 (~10 MB)
- `okx_trading_logs/` - 交易日志
- `okx_strategy_logs/` - 策略日志

#### ✅ 前端资源
- HTML 模板 (290+ 文件)
- JavaScript 文件
- CSS 样式表
- 静态资源

#### ❌ 排除内容
- `.git/` - Git 版本控制 (375 MB，需单独备份)
- `__pycache__/` - Python 缓存
- `.pytest_cache/` - 测试缓存

---

## 🚀 重部署步骤

### 第一步：系统准备

#### 1.1 系统要求
```bash
# 操作系统
Ubuntu 20.04+ / Debian 10+ / CentOS 7+

# 磁盘空间
至少 10 GB 可用空间（推荐 20 GB）

# 内存
至少 2 GB RAM（推荐 4 GB）

# 软件要求
- Python 3.8+
- Node.js 14+
- npm 或 yarn
- PM2 进程管理器
```

#### 1.2 安装基础软件

**Ubuntu/Debian**:
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 3 和 pip
sudo apt install -y python3 python3-pip python3-venv

# 安装 Node.js 和 npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 安装 PM2
sudo npm install -g pm2

# 安装其他工具
sudo apt install -y git curl wget htop
```

**CentOS/RHEL**:
```bash
# 更新系统
sudo yum update -y

# 安装 Python 3
sudo yum install -y python3 python3-pip

# 安装 Node.js
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs

# 安装 PM2
sudo npm install -g pm2

# 安装其他工具
sudo yum install -y git curl wget htop
```

### 第二步：恢复备份文件

#### 2.1 上传备份文件
```bash
# 将备份文件上传到服务器（使用 scp 或其他方式）
# 假设备份文件位于 /tmp/webapp_backup_YYYYMMDD_N.tar.gz

# 创建工作目录
mkdir -p /home/user
cd /home/user

# 解压备份
tar -xzf /tmp/webapp_backup_YYYYMMDD_N.tar.gz

# 验证解压
ls -lh webapp/
du -sh webapp/
```

#### 2.2 验证备份完整性
```bash
cd /home/user/webapp

# 检查关键目录
ls -lh support_resistance_daily/ | wc -l  # 应该有 40+ 文件
ls -lh data/ | wc -l                      # 应该有 400+ 文件
ls -lh source_code/ | wc -l               # 应该有 100+ 文件

# 检查总大小
du -sh .  # 应该约 3.6 GB

# 检查 JSONL 文件数量
find . -name "*.jsonl" -type f | wc -l  # 应该有 1,300+ 文件
```

### 第三步：配置环境

#### 3.1 创建 Python 虚拟环境
```bash
cd /home/user/webapp

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip setuptools wheel
```

#### 3.2 安装 Python 依赖
```bash
# 确保在虚拟环境中
source venv/bin/activate

# 安装所有依赖
pip install -r requirements.txt

# 验证安装
pip list | grep -E "flask|requests|pandas|numpy"
```

#### 3.3 安装 Node.js 依赖
```bash
cd /home/user/webapp

# 安装 npm 包（如果有 node_modules 目录，可跳过）
npm install

# 或使用 yarn
# yarn install

# 验证安装
npm list --depth=0
```

#### 3.4 配置环境变量
```bash
cd /home/user/webapp

# 编辑 .env 文件
nano .env

# 必须配置的环境变量示例：
# OKX_API_KEY=your_api_key
# OKX_SECRET_KEY=your_secret_key
# OKX_PASSPHRASE=your_passphrase
# TELEGRAM_BOT_TOKEN=your_token
# TELEGRAM_CHAT_ID=your_chat_id
# DATABASE_URL=your_database_url
# FLASK_SECRET_KEY=your_secret_key

# 保存并退出（Ctrl+O, Enter, Ctrl+X）

# 设置文件权限
chmod 600 .env
```

### 第四步：启动服务

#### 4.1 启动 Flask 应用

**选项 A：使用 PM2（推荐）**
```bash
cd /home/user/webapp

# 检查 ecosystem.config.js 配置
cat ecosystem.config.js

# 启动所有服务
pm2 start ecosystem.config.js

# 查看状态
pm2 status

# 查看日志
pm2 logs

# 保存 PM2 配置
pm2 save

# 设置开机自启
pm2 startup
```

**选项 B：手动启动**
```bash
cd /home/user/webapp

# 激活虚拟环境
source venv/bin/activate

# 启动 Flask 应用
python app.py

# 或使用 gunicorn（推荐生产环境）
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### 4.2 启动数据收集器

所有数据收集器已在 `ecosystem.config.js` 中配置，通过 PM2 启动：

```bash
# PM2 会自动启动所有配置的收集器
pm2 status

# 应该看到以下进程（示例）：
# - flask-app (Flask 主应用)
# - anchor-daily-reader (锚点每日读取器)
# - gdrive-jsonl-manager (Google Drive JSONL 管理)
# - panic-daily-manager (Panic 每日管理)
# - sar-jsonl-collector (SAR 数据收集器)
# - price-speed-collector (价格速度收集器)
# - coin-change-tracker (币种变化追踪)
# - 以及其他 20+ 个数据收集器...
```

**手动启动单个收集器**（如果需要）：
```bash
cd /home/user/webapp/source_code

# 激活虚拟环境
source ../venv/bin/activate

# 启动特定收集器
python anchor_daily_reader.py
python sar_jsonl_collector.py
python coin_change_tracker.py
# 等等...
```

#### 4.3 验证服务运行

**检查 Flask 应用**：
```bash
# 检查端口监听
netstat -tlnp | grep 5000

# 或使用 ss
ss -tlnp | grep 5000

# 测试 API
curl http://localhost:5000/api/health
curl http://localhost:5000/api/status
```

**检查 PM2 进程**：
```bash
# 查看所有进程状态
pm2 status

# 查看特定进程日志
pm2 logs flask-app
pm2 logs anchor-daily-reader

# 查看进程详细信息
pm2 info flask-app

# 监控资源使用
pm2 monit
```

### 第五步：数据验证

#### 5.1 验证数据完整性
```bash
cd /home/user/webapp

# 检查各个数据目录的文件数量
echo "=== 数据完整性检查 ==="
echo "support_resistance_daily: $(ls support_resistance_daily/ | wc -l) 文件"
echo "support_resistance_jsonl: $(ls support_resistance_jsonl/ | wc -l) 文件"
echo "data: $(ls data/ | wc -l) 文件"
echo "anchor_daily: $(ls anchor_daily/ | wc -l) 文件"
echo "sar_jsonl: $(ls sar_jsonl/ | wc -l) 文件"

# 检查最新数据文件
echo -e "\n=== 最新数据文件 ==="
ls -lht support_resistance_daily/*.jsonl | head -5
ls -lht data/*.jsonl | head -5

# 检查 JSONL 文件行数（抽样）
echo -e "\n=== 数据文件行数抽样 ==="
wc -l support_resistance_daily/support_resistance_*.jsonl | tail -5
wc -l data/*.jsonl | tail -5
```

#### 5.2 测试 API 端点
```bash
# 测试主要 API 端点
curl http://localhost:5000/api/health
curl http://localhost:5000/api/status
curl http://localhost:5000/api/data/latest
curl http://localhost:5000/api/sar/current
curl http://localhost:5000/api/support-resistance/latest

# 测试前端页面
curl http://localhost:5000/ > /tmp/index.html
curl http://localhost:5000/support_resistance.html > /tmp/sr.html

# 检查响应大小
ls -lh /tmp/index.html /tmp/sr.html
```

#### 5.3 验证数据收集
```bash
# 等待几分钟，检查新数据是否生成
sleep 300  # 等待 5 分钟

# 检查最新文件修改时间
find . -name "*.jsonl" -type f -mmin -10 | head -20

# 检查日志文件
tail -50 logs/flask.log
tail -50 logs/data-collector.log
```

### 第六步：配置和优化

#### 6.1 配置防火墙
```bash
# Ubuntu/Debian (使用 ufw)
sudo ufw allow 5000/tcp
sudo ufw reload

# CentOS/RHEL (使用 firewalld)
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

#### 6.2 配置 Nginx 反向代理（可选）
```bash
# 安装 Nginx
sudo apt install nginx  # Ubuntu/Debian
# sudo yum install nginx  # CentOS/RHEL

# 创建配置文件
sudo nano /etc/nginx/sites-available/webapp

# 添加以下内容：
# server {
#     listen 80;
#     server_name your-domain.com;
#
#     location / {
#         proxy_pass http://localhost:5000;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#         proxy_set_header X-Forwarded-Proto $scheme;
#     }
# }

# 启用配置
sudo ln -s /etc/nginx/sites-available/webapp /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

#### 6.3 配置系统监控
```bash
# 设置 PM2 监控
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 100M
pm2 set pm2-logrotate:retain 10

# 设置系统资源监控
pm2 install pm2-server-monit
```

#### 6.4 配置备份系统
```bash
cd /home/user/webapp

# 检查备份系统配置
cat auto_backup_system.py | grep -E "MAX_BACKUPS|MIN_BACKUP_SIZE_MB"

# 测试备份功能
python3 auto_backup_system.py

# 设置定时备份（cron）
crontab -e

# 添加以下行（每12小时备份一次）
# 0 */12 * * * cd /home/user/webapp && python3 auto_backup_system.py

# 或使用 PM2 定时任务
pm2 start ecosystem.config.js  # 确保 backup-scheduler 已配置
```

---

## 🔧 组件映射和功能说明

### Flask 主应用 (`app.py`)
**位置**：`/home/user/webapp/core_code/app.py` 或 `/home/user/webapp/app.py`
**功能**：
- Web 服务器主入口
- API 路由管理
- 数据聚合和展示
- 实时数据接口

**启动命令**：
```bash
cd /home/user/webapp
source venv/bin/activate
python app.py
# 或
pm2 start ecosystem.config.js
```

### 数据收集器系统

#### 1. 锚点数据收集 (`anchor_daily_reader.py`)
**位置**：`/home/user/webapp/source_code/anchor_daily_reader.py`
**功能**：收集每日锚点交易数据
**数据目录**：`anchor_daily/`
**启动**：`pm2 start anchor-daily-reader`

#### 2. SAR 指标收集 (`sar_jsonl_collector.py`)
**位置**：`/home/user/webapp/source_code/sar_jsonl_collector.py`
**功能**：收集 SAR（抛物线转向）指标数据
**数据目录**：`sar_jsonl/`
**启动**：`pm2 start sar-jsonl-collector`

#### 3. 支撑阻力数据收集
**位置**：多个收集器
**功能**：计算和存储支撑/阻力位
**数据目录**：`support_resistance_daily/`, `support_resistance_jsonl/`

#### 4. 币种变化追踪 (`coin_change_tracker.py`)
**位置**：`/home/user/webapp/source_code/coin_change_tracker.py`
**功能**：追踪币种价格变化和波动
**数据目录**：`coin_change_tracker/`
**启动**：`pm2 start coin-change-tracker`

#### 5. 价格速度监控
**位置**：`price_speed_collector.py`, `price_speed_10m_collector.py`
**功能**：监控价格变化速度
**数据目录**：`price_speed_jsonl/`, `price_speed_10m/`

#### 6. Panic 指标管理 (`panic_daily_manager.py`)
**位置**：`/home/user/webapp/source_code/panic_daily_manager.py`
**功能**：管理 Panic & Greed 指标数据
**数据目录**：`panic_daily/`
**启动**：`pm2 start panic-daily-manager`

#### 7. Google Drive 同步 (`gdrive_jsonl_manager.py`)
**位置**：`/home/user/webapp/source_code/gdrive_jsonl_manager.py`
**功能**：同步数据到 Google Drive
**数据目录**：`gdrive_jsonl/`

#### 8. OKX 交易数据
**位置**：多个交易相关脚本
**功能**：
- 交易历史记录
- 订单监控
- 止盈止损管理
**数据目录**：`okx_trading_jsonl/`, `okx_trading_logs/`

### 前端系统

#### 1. 主页面
**文件**：`index.html`, `control_center.html`
**功能**：系统控制中心和数据总览

#### 2. 支撑阻力可视化
**文件**：`support_resistance.html`
**功能**：展示支撑阻力位图表

#### 3. 交易监控
**文件**：`okx_trading.html`, `okx_trading_marks.html`
**功能**：实时交易监控和标记

#### 4. 数据管理
**文件**：各种 HTML 管理界面
**功能**：数据管理、配置、监控

---

## 📋 验证清单

### ✅ 系统级验证
- [ ] Python 3.8+ 已安装
- [ ] Node.js 14+ 已安装
- [ ] PM2 已安装
- [ ] 虚拟环境已创建
- [ ] 所有依赖已安装
- [ ] 环境变量已配置

### ✅ 数据验证
- [ ] 备份文件已完整解压
- [ ] 项目大小约 3.6 GB
- [ ] JSONL 文件数 1,300+
- [ ] 主要数据目录都存在
- [ ] 最新数据文件时间正确

### ✅ 服务验证
- [ ] Flask 应用启动成功
- [ ] API 端点响应正常
- [ ] 前端页面可访问
- [ ] PM2 进程全部在线
- [ ] 数据收集器正常运行

### ✅ 功能验证
- [ ] 数据实时更新
- [ ] 日志正常记录
- [ ] 备份系统运行
- [ ] 监控系统工作
- [ ] API 返回正确数据

---

## 🚨 故障排查

### 问题 1：Flask 应用启动失败

**症状**：
```
ModuleNotFoundError: No module named 'flask'
```

**解决方案**：
```bash
# 确保在虚拟环境中
source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt

# 检查 Flask 版本
pip show flask
```

### 问题 2：PM2 进程频繁重启

**症状**：
```
pm2 status 显示 restart 次数很高
```

**解决方案**：
```bash
# 查看错误日志
pm2 logs <process-name> --err

# 检查内存使用
pm2 monit

# 增加最大内存限制（在 ecosystem.config.js 中）
# max_memory_restart: '500M'
```

### 问题 3：数据文件权限错误

**症状**：
```
PermissionError: [Errno 13] Permission denied
```

**解决方案**：
```bash
# 修复所有文件权限
cd /home/user/webapp
chmod -R 755 .
chmod -R 777 data/
chmod -R 777 logs/

# 修复所有者
chown -R $USER:$USER .
```

### 问题 4：数据收集器不生成新数据

**症状**：
- JSONL 文件长时间未更新
- PM2 显示进程在线但无活动

**解决方案**：
```bash
# 检查进程日志
pm2 logs <collector-name> --lines 100

# 手动运行收集器测试
cd /home/user/webapp/source_code
source ../venv/bin/activate
python <collector-name>.py

# 检查 API 密钥配置
cat /home/user/webapp/.env | grep API

# 重启进程
pm2 restart <collector-name>
```

### 问题 5：磁盘空间不足

**症状**：
```
No space left on device
```

**解决方案**：
```bash
# 检查磁盘使用
df -h

# 检查大文件
du -sh /home/user/webapp/* | sort -hr | head -20

# 清理旧日志
pm2 flush

# 清理旧备份（只保留最近3个）
cd /tmp
ls -lt webapp_backup_*.tar.gz | tail -n +4 | xargs rm -f
```

### 问题 6：API 响应缓慢

**症状**：
- API 请求超时
- 响应时间 > 5 秒

**解决方案**：
```bash
# 检查系统负载
top
htop

# 检查数据库连接
# 根据具体数据库类型调整

# 增加 worker 数量（gunicorn）
# gunicorn -w 8 -b 0.0.0.0:5000 app:app

# 或在 ecosystem.config.js 中增加实例数
# instances: 4
```

---

## 🔒 安全建议

### 1. 环境变量安全
```bash
# .env 文件权限
chmod 600 .env

# 不要提交到 Git
echo ".env" >> .gitignore

# 使用环境变量管理工具
# 如 dotenv, docker secrets, kubernetes secrets
```

### 2. API 密钥轮换
- 定期更换 OKX API 密钥
- 使用只读 API 密钥（如果可能）
- 限制 API 密钥的 IP 白名单

### 3. 数据备份安全
```bash
# 加密备份文件
tar -czf - webapp/ | gpg --symmetric --cipher-algo AES256 -o webapp_backup.tar.gz.gpg

# 上传到安全位置
# AWS S3, Google Cloud Storage, 加密云盘等
```

### 4. 系统更新
```bash
# 定期更新系统
sudo apt update && sudo apt upgrade -y

# 更新 Python 包
pip list --outdated
pip install --upgrade <package-name>

# 更新 Node.js 包
npm outdated
npm update
```

---

## 📞 支持和维护

### 日常维护任务

**每日**：
- [ ] 检查 PM2 进程状态：`pm2 status`
- [ ] 查看系统日志：`pm2 logs --lines 50`
- [ ] 检查磁盘空间：`df -h`

**每周**：
- [ ] 验证备份完整性
- [ ] 检查数据收集器运行状态
- [ ] 清理旧日志文件
- [ ] 查看系统性能指标

**每月**：
- [ ] 更新系统包
- [ ] 更新 Python/Node 依赖
- [ ] 审查安全日志
- [ ] 测试灾难恢复流程

### 监控指标

**系统资源**：
```bash
# CPU 使用率
top -bn1 | grep "Cpu(s)"

# 内存使用
free -h

# 磁盘使用
df -h /home/user/webapp
```

**应用指标**：
```bash
# PM2 进程统计
pm2 status
pm2 monit

# API 响应时间
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5000/api/health

# 数据更新频率
find data/ -name "*.jsonl" -type f -mmin -60 | wc -l
```

### 联系信息

**文档位置**：
- 备份系统：`/home/user/webapp/BACKUP_REQUIREMENTS.md`
- 本部署指南：`/home/user/webapp/COMPLETE_REDEPLOYMENT_GUIDE.md`
- 备份历史：`/home/user/webapp/data/backup_history.jsonl`

**日志位置**：
- Flask 日志：`/home/user/webapp/logs/`
- PM2 日志：`~/.pm2/logs/`
- 系统日志：`/var/log/`

---

## 📚 附录

### A. 完整依赖清单

**Python 包**（参考 `requirements.txt`）：
- Flask
- Requests
- Pandas
- NumPy
- 以及其他业务相关包

**Node.js 包**（参考 `package.json`）：
- 根据实际项目配置

### B. 目录结构图
```
webapp/
├── core_code/              # 核心代码
│   ├── app.py             # Flask 主应用
│   ├── source_code/       # 数据收集器
│   └── data/              # 配置数据
├── source_code/            # 源代码（收集器）
├── data/                   # 主数据目录
├── support_resistance_*/   # 支撑阻力数据
├── anchor_daily/           # 锚点每日数据
├── sar_jsonl/             # SAR 数据
├── logs/                   # 日志文件
├── venv/                   # Python 虚拟环境
├── .env                    # 环境变量
├── requirements.txt        # Python 依赖
├── package.json            # Node.js 依赖
└── ecosystem.config.js     # PM2 配置
```

### C. 常用命令速查

**PM2 管理**：
```bash
pm2 start ecosystem.config.js    # 启动所有服务
pm2 stop all                      # 停止所有服务
pm2 restart all                   # 重启所有服务
pm2 delete all                    # 删除所有服务
pm2 logs                          # 查看日志
pm2 monit                         # 监控面板
pm2 save                          # 保存配置
pm2 resurrect                     # 恢复保存的配置
```

**数据管理**：
```bash
# 统计 JSONL 文件
find . -name "*.jsonl" | wc -l

# 查看最新文件
find . -name "*.jsonl" -type f -mtime -1

# 计算目录大小
du -sh */

# 检查文件行数
wc -l data/*.jsonl
```

**备份管理**：
```bash
# 手动备份
python3 auto_backup_system.py

# 列出备份
python3 auto_backup_system.py list

# 查看统计
python3 auto_backup_system.py stats

# 恢复备份
cd /home/user && tar -xzf /tmp/webapp_backup_*.tar.gz
```

---

**最后更新**：2026-03-17  
**版本**：1.0  
**维护者**：系统管理员  
**状态**：✅ 已验证可用

</details>
