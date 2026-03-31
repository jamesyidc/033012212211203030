# Webapp 完整部署指南

## 📦 备份信息

**备份文件**: `webapp_full_backup_20260317.tar.gz`  
**文件大小**: 522 MB (压缩后)  
**原始大小**: 2.2 GB (未压缩)  
**文件数量**: 7926 个文件/目录  
**备份时间**: 2026-03-17 15:02 (UTC+8)  
**备份位置**: `/tmp/webapp_full_backup_20260317.tar.gz`

---

## 📋 备份内容清单

### 1. 源代码文件
```
✅ Python 文件 (402+)
   - 主应用: app.py, flask应用
   - 采集器: source_code/ 下所有collector
   - API路由: core_code/ 下所有routes
   - 工具脚本: 各种管理和监控脚本
   
✅ HTML 模板 (290+)
   - templates/ 目录下所有HTML文件
   - 前端页面和组件
   
✅ JavaScript 文件
   - static/js/ 下所有JS文件
   - 前端逻辑和交互代码
   
✅ CSS 样式文件
   - static/css/ 下所有样式文件
```

### 2. 配置文件
```
✅ .env - 环境变量配置（OKX API密钥等）
✅ requirements.txt - Python依赖列表
✅ package.json - Node.js依赖配置
✅ ecosystem.config.js - PM2进程配置
✅ 各模块的配置JSON文件
```

### 3. 数据文件 (完整历史数据)
```
✅ data/ 目录 (259 MB, 445个JSONL文件)
   ├── abc_position/ - ABC开仓系统数据
   ├── coin_change_tracker/ - 币种变动追踪数据 (122个文件)
   ├── positive_ratio_stats/ - 正比率统计数据 (49个文件)
   ├── price_position/ - 价格位置数据 (27个文件)
   ├── sar_bias_stats/ - SAR偏差统计 (42个文件)
   ├── market_sentiment/ - 市场情绪数据 (24个文件)
   ├── new_high_low/ - 新高新低事件 (22个文件)
   ├── daily_predictions/ - 每日预测 (41个文件)
   ├── okx_trading_logs/ - OKX交易日志 (50个文件)
   └── okx_trading_history/ - OKX交易历史 (38个文件)

✅ 历史数据时间范围: 2026-01-28 至 2026-03-17 (接近2个月)

✅ 根目录数据文件夹
   ├── coin_change_tracker/ - 币种变动原始数据 (182MB)
   ├── positive_ratio_stats/ - 正比率原始数据 (18MB)
   ├── price_position/ - 价格位置原始数据 (69MB)
   ├── sar_bias_stats/ - SAR统计原始数据 (8MB)
   ├── market_sentiment/ - 市场情绪原始数据 (1.1MB)
   ├── new_high_low/ - 新高新低原始数据 (452KB)
   ├── okx_trading_history/ - 交易历史原始数据 (1.9MB)
   ├── okx_trading_logs/ - 交易日志原始数据 (1.7MB)
   ├── daily_predictions/ - 每日预测原始数据 (308KB)
   ├── sar_1min/ - SAR 1分钟数据 (5.7MB)
   ├── panic_jsonl/ - 恐慌指数数据
   ├── btc_daily_range/ - BTC日内波动范围
   └── 其他模块数据文件夹
```

### 4. 日志文件
```
✅ logs/ 目录 (9.6 MB)
   - PM2进程日志
   - Flask应用日志
   - 各采集器运行日志
   - 错误日志和调试日志
```

### 5. 模块依赖
```
✅ node_modules/ 目录
   - Node.js依赖包
   - 前端库和工具
   
✅ Python 虚拟环境依赖
   - 通过requirements.txt安装
```

### 6. 系统目录和模块
```
✅ source_code/ - 核心源代码目录
   - 所有采集器和处理器
   - API接口和路由
   
✅ core_code/ - 核心代码目录
   - Flask路由文件
   - 业务逻辑处理
   
✅ panic_paged_v2/ - 恐慌指数分页系统V2
✅ panic_v3/ - 恐慌指数系统V3
✅ major-events-system/ - 重大事件系统

✅ templates/ - HTML模板目录
✅ static/ - 静态资源目录
✅ abc_position/ - ABC持仓系统
```

### 7. 缓存和临时文件
```
✅ __pycache__/ - Python字节码缓存
✅ .pytest_cache/ - Pytest测试缓存
✅ *.pyc 文件
```

---

## 🚀 完整部署步骤

### 阶段1: 系统准备

#### 1.1 服务器要求
```bash
操作系统: Ubuntu 20.04+ / Debian 10+
内存: 至少 4GB RAM
磁盘: 至少 10GB 可用空间
Python: 3.8+
Node.js: 14+
```

#### 1.2 安装系统依赖
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 和基础工具
sudo apt install -y python3 python3-pip python3-venv

# 安装 Node.js 和 npm
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs

# 安装 PM2 (全局)
sudo npm install -g pm2

# 安装其他必要工具
sudo apt install -y git curl wget htop
```

---

### 阶段2: 恢复备份

#### 2.1 解压备份文件
```bash
# 进入用户目录
cd /home/user

# 解压完整备份
tar -xzf /tmp/webapp_full_backup_20260317.tar.gz

# 验证解压结果
ls -la webapp/
du -sh webapp/
```

#### 2.2 设置目录权限
```bash
# 设置所有者
sudo chown -R $USER:$USER /home/user/webapp

# 设置目录权限
chmod -R 755 /home/user/webapp

# 设置数据目录权限
chmod -R 755 /home/user/webapp/data
chmod -R 755 /home/user/webapp/logs
```

---

### 阶段3: Python环境配置

#### 3.1 创建虚拟环境
```bash
cd /home/user/webapp

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

#### 3.2 安装Python依赖
```bash
# 升级pip
pip install --upgrade pip

# 安装所有依赖
pip install -r requirements.txt

# 验证安装
pip list
```

#### 3.3 主要Python依赖列表
```
Flask==2.3.0 - Web框架
requests==2.31.0 - HTTP请求
python-dotenv==1.0.0 - 环境变量
pytz==2023.3 - 时区处理
pandas==2.0.0 - 数据处理
numpy==1.24.0 - 数值计算
ccxt==4.0.0 - 加密货币交易所API
websocket-client==1.6.0 - WebSocket客户端
supervisor==4.2.5 - 进程管理（可选）
```

---

### 阶段4: Node.js环境配置

#### 4.1 安装Node.js依赖
```bash
cd /home/user/webapp

# 如果有package.json，安装依赖
if [ -f package.json ]; then
    npm install
fi

# 验证PM2安装
pm2 --version
```

#### 4.2 PM2配置说明
```bash
# PM2配置文件: ecosystem.config.js (如果存在)
# 或者通过命令手动管理进程
```

---

### 阶段5: 环境变量配置

#### 5.1 配置.env文件
```bash
cd /home/user/webapp

# 查看.env文件
cat .env

# 需要配置的主要环境变量：
# OKX API配置
API_KEY_MAIN=b0c18f2d-e014-4ae8-9c3c-cb02161de4db
API_SECRET_MAIN=92F864C599B2CE2EC5186AD14C8B4110
API_PASSPHRASE_MAIN=Tencent@123

API_KEY_POIT=8650e46c-059b-431d-93cf-55f8c79babdb
API_SECRET_POIT=4C2BD2AC6A08615EA7F36A6251857FCE
API_PASSPHRASE_POIT=Wu666666.

API_KEY_FANGFANG12=e5867a9a-93b7-476f-81ce-093c3aacae0d
API_SECRET_FANGFANG12=4624EE63A9BF3F84250AC71C9A37F47D
API_PASSPHRASE_FANGFANG12=Tencent@123

API_KEY_DADANINI=1463198a-fad0-46ac-9ad8-2a386461782c
API_SECRET_DADANINI=1D112283B7456290056C253C56E9F3A6
API_PASSPHRASE_DADANINI=Tencent@123

# Flask配置
FLASK_APP=app.py
FLASK_ENV=production
FLASK_PORT=9002
FLASK_DEBUG=False

# 数据目录
DATA_DIR=data
LOGS_DIR=logs
```

---

### 阶段6: 启动服务

#### 6.1 启动Flask应用
```bash
cd /home/user/webapp

# 方法1: 使用PM2启动（推荐）
pm2 start app.py --name flask-app --interpreter python3

# 方法2: 直接启动（用于测试）
python3 app.py
```

#### 6.2 启动所有采集器
```bash
cd /home/user/webapp

# ABC持仓追踪器
pm2 start source_code/abc_position_tracker.py --name abc-position-tracker --interpreter python3

# 币种变动追踪器
pm2 start source_code/coin_change_tracker.py --name coin-change-tracker --interpreter python3

# SAR采集器
pm2 start source_code/sar_jsonl_collector.py --name sar-jsonl-collector --interpreter python3

# SAR偏差统计采集器
pm2 start source_code/sar_bias_stats_collector.py --name sar-bias-stats-collector --interpreter python3

# 正比率统计采集器
pm2 start positive_ratio_stats/positive_ratio_collector.py --name positive-ratio-collector --interpreter python3

# 价格位置采集器
pm2 start price_position/price_position_collector.py --name price-position-collector --interpreter python3

# 市场情绪采集器
pm2 start market_sentiment/market_sentiment_collector.py --name market-sentiment-collector --interpreter python3

# 新高新低采集器
pm2 start new_high_low/new_high_low_collector.py --name new-high-low-collector --interpreter python3

# 恐慌指数采集器
pm2 start panic_jsonl/panic_wash_collector.py --name panic-wash-collector --interpreter python3

# 备份调度器
pm2 start auto_backup_system.py --name backup-scheduler --interpreter python3
```

#### 6.3 启动监控服务
```bash
# 数据健康监控
pm2 start data_health_monitor.py --name data-health-monitor --interpreter python3

# 系统健康监控
pm2 start system_health_monitor.py --name system-health-monitor --interpreter python3
```

#### 6.4 查看所有PM2进程
```bash
pm2 list
pm2 status
```

---

### 阶段7: 验证部署

#### 7.1 检查Flask应用
```bash
# 访问主页
curl http://localhost:9002/

# 检查API
curl http://localhost:9002/api/health

# 查看日志
pm2 logs flask-app --lines 50
```

#### 7.2 检查采集器运行状态
```bash
# 查看所有PM2进程
pm2 list

# 查看特定采集器日志
pm2 logs abc-position-tracker --lines 20
pm2 logs coin-change-tracker --lines 20
pm2 logs sar-jsonl-collector --lines 20
```

#### 7.3 检查数据文件
```bash
cd /home/user/webapp

# 查看data目录
ls -lh data/

# 查看最新数据文件
ls -lt data/abc_position/*.jsonl | head -5
ls -lt data/coin_change_tracker/*.jsonl | head -5

# 统计数据文件数量
find data/ -name "*.jsonl" | wc -l
```

#### 7.4 检查日志文件
```bash
# 查看logs目录
ls -lh logs/

# 查看最新日志
tail -50 logs/flask_app.log
tail -50 logs/abc_position_tracker.log
```

---

### 阶段8: PM2进程管理

#### 8.1 PM2常用命令
```bash
# 查看所有进程
pm2 list

# 查看进程详情
pm2 show flask-app

# 重启进程
pm2 restart flask-app
pm2 restart all

# 停止进程
pm2 stop flask-app
pm2 stop all

# 删除进程
pm2 delete flask-app

# 查看日志
pm2 logs
pm2 logs flask-app
pm2 logs --lines 100

# 清空日志
pm2 flush

# 保存PM2进程列表
pm2 save

# 开机自启动
pm2 startup
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp /home/$USER
pm2 save
```

#### 8.2 PM2监控
```bash
# 实时监控
pm2 monit

# 查看进程资源使用
pm2 list
```

---

## 🗂️ 关键文件和目录对应关系

### Flask应用结构
```
/home/user/webapp/
├── app.py                          # Flask主应用入口
├── core_code/
│   ├── app.py                      # Flask应用逻辑
│   ├── abc_position_routes.py      # ABC持仓路由
│   ├── panic_routes_clean.py       # 恐慌指数路由
│   └── source_code/                # 核心源代码
│       ├── abc_position_tracker.py # ABC持仓追踪器
│       ├── coin_change_tracker.py  # 币种变动追踪器
│       ├── sar_jsonl_collector.py  # SAR数据采集器
│       └── 其他采集器...
├── templates/                      # HTML模板
│   ├── abc_position.html           # ABC持仓页面
│   ├── okx_trading.html            # OKX交易页面
│   ├── coin_change_tracker.html    # 币种变动页面
│   └── 其他模板...
├── static/                         # 静态资源
│   ├── css/
│   ├── js/
│   └── images/
├── data/                           # 数据存储目录
│   ├── abc_position/
│   ├── coin_change_tracker/
│   ├── positive_ratio_stats/
│   └── 其他数据目录...
├── logs/                           # 日志目录
├── .env                            # 环境变量配置
└── requirements.txt                # Python依赖列表
```

### 路由对应关系
```
Flask应用端口: 9002

主要路由:
- http://localhost:9002/ - 主页
- http://localhost:9002/abc-position - ABC开仓系统
- http://localhost:9002/okx-trading - OKX交易系统
- http://localhost:9002/coin-change-tracker - 币种变动追踪
- http://localhost:9002/panic-index - 恐慌指数
- http://localhost:9002/api/* - 各种API接口

API路由:
- /abc-position/api/current-state - ABC持仓当前状态
- /abc-position/api/history - ABC持仓历史数据
- /abc-position/api/real-positions - 实时持仓数据
- /coin-change-tracker/api/history - 币种变动历史
- /api/okx-trading/* - OKX交易API
```

### PM2进程对应关系
```
进程名称                     脚本文件                           端口/作用
---------------------------------------------------------------------------
flask-app                   app.py                            9002
abc-position-tracker        source_code/abc_position_tracker.py   后台追踪
coin-change-tracker         source_code/coin_change_tracker.py    后台追踪
sar-jsonl-collector         source_code/sar_jsonl_collector.py    数据采集
sar-bias-stats-collector    source_code/sar_bias_stats_collector.py 统计
positive-ratio-collector    positive_ratio_stats/collector.py     统计
price-position-collector    price_position/collector.py           数据采集
market-sentiment-collector  market_sentiment/collector.py         情绪分析
new-high-low-collector      new_high_low/collector.py             新高新低
panic-wash-collector        panic_jsonl/panic_wash_collector.py   恐慌指数
backup-scheduler            auto_backup_system.py                 备份任务
data-health-monitor         data_health_monitor.py                数据监控
system-health-monitor       system_health_monitor.py              系统监控
```

---

## 📊 数据流向说明

### 1. 数据采集流程
```
OKX API → 采集器(collector) → JSONL文件 → data/目录 → Flask API → Web界面

示例：ABC持仓数据流
OKX API positions端点
    ↓
abc_position_tracker.py (每60秒采集)
    ↓
data/abc_position/abc_position_YYYYMMDD.jsonl (追加写入)
    ↓
Flask /abc-position/api/history (读取数据)
    ↓
templates/abc_position.html (图表展示)
```

### 2. 数据存储格式
```
JSONL格式（每行一个JSON对象）：
{"timestamp": "2026-03-17T15:00:00+08:00", "data": {...}}
{"timestamp": "2026-03-17T15:01:00+08:00", "data": {...}}
```

### 3. 备份流程
```
auto_backup_system.py (每12小时执行)
    ↓
tar -czf webapp_backup_*.tar.gz
    ↓
/tmp/webapp_backup_*.tar.gz
    ↓
保留所有历史备份（不再自动删除）
```

---

## 🛠️ 故障排查

### 问题1: Flask无法启动
```bash
# 检查端口占用
sudo netstat -tulnp | grep 9002

# 查看Flask日志
pm2 logs flask-app

# 检查Python环境
which python3
python3 --version

# 检查依赖安装
pip list | grep Flask
```

### 问题2: 采集器不工作
```bash
# 查看进程状态
pm2 list

# 查看采集器日志
pm2 logs abc-position-tracker

# 重启采集器
pm2 restart abc-position-tracker

# 检查数据文件是否更新
ls -lt data/abc_position/*.jsonl | head -1
```

### 问题3: 数据文件丢失
```bash
# 检查data目录权限
ls -ld data/
ls -l data/abc_position/

# 检查磁盘空间
df -h

# 检查备份
ls -lh /tmp/webapp_backup_*.tar.gz
```

### 问题4: PM2进程崩溃
```bash
# 查看崩溃日志
pm2 logs --err

# 重启所有进程
pm2 restart all

# 重新加载PM2配置
pm2 reload all
```

---

## 📝 重要说明

### 数据保护
1. **所有历史数据已恢复**: 2026-01-28 至 2026-03-17 的完整数据
2. **备份自动清理已禁用**: 所有备份将被永久保留
3. **定期备份**: 每12小时自动创建新备份
4. **数据不再删除**: 所有新数据将持续累积保存

### 部署注意事项
1. **环境变量**: 必须正确配置.env文件中的OKX API密钥
2. **端口冲突**: 确保9002端口未被占用
3. **权限问题**: 确保webapp目录及子目录有正确的读写权限
4. **Python版本**: 需要Python 3.8或更高版本
5. **依赖安装**: 必须在虚拟环境中安装所有Python依赖

### 监控和维护
1. **每日检查**: 使用`pm2 list`查看所有进程状态
2. **日志查看**: 定期查看logs目录下的日志文件
3. **磁盘空间**: 监控磁盘使用，确保有足够空间存储数据
4. **备份验证**: 定期验证备份文件的完整性

---

## 📞 支持与联系

**部署问题**: 查看PM2日志和Flask日志
**数据问题**: 检查data目录和JSONL文件
**性能问题**: 使用`pm2 monit`监控资源使用

---

**文档版本**: v1.0  
**更新日期**: 2026-03-17  
**备份文件**: webapp_full_backup_20260317.tar.gz  
**验证状态**: ✅ 完整备份已创建，包含所有文件和历史数据
