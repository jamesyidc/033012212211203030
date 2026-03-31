# 完整重新部署指南

## 📦 备份内容概览

### 备份包含的完整内容 (~3.16 GB 未压缩，~265 MB 压缩)

#### 1. Python 代码文件 (401 文件, ~5.38 MB)
- **核心应用代码** (`core_code/`): Flask 应用、API、数据处理
- **数据收集器** (`source_code/`): 各种数据采集脚本
- **特殊系统** (`panic_paged_v2/`, `panic_v3/`, `special_systems/`): 独立系统模块
- **根目录工具**: 数据管理器、监控器、备份系统等

#### 2. HTML 模板文件 (289 文件, ~14.02 MB)
- `templates/`: 所有Web UI模板
- 包括各个系统的前端界面

#### 3. Markdown 文档 (17 文件, ~174.74 KB)
- 系统文档
- 修复报告
- 部署指南

#### 4. 配置文件 (290 文件, ~3.20 MB)
- **PM2 配置**: `ecosystem.*.json` 文件
- **Python 依赖**: `requirements.txt`
- **Node.js 配置**: `package.json`, `package-lock.json`
- **JSON 配置**: 各种系统配置文件
- **JavaScript 配置**: `*.js` 配置文件
- **YAML 配置**: `*.yaml`, `*.yml` 文件

#### 5. 数据文件 (931 文件, ~2.97 GB) ⭐ 主要内容
**大型数据目录**:
- `support_resistance_daily/`: 977 MB (41 文件)
- `support_resistance_jsonl/`: 740 MB (4 文件，含 697MB 单文件)
- `anchor_daily/`: 191 MB
- `coin_change_tracker/`: 182 MB
- `price_speed_jsonl/`: 173 MB
- `anchor_profit_stats/`: 163 MB
- `v1v2_jsonl/`: 108 MB
- `gdrive_jsonl/`: 88 MB
- `price_position/`: 69 MB
- `sar_jsonl/`: 66 MB

**其他数据目录**:
- `anchor_jsonl/`, `anchor_unified/`, `coin_price_tracker/`
- `crypto_index_jsonl/`, `extreme_jsonl/`, `okx_trading_jsonl/`
- `panic_jsonl/`, `positive_ratio_stats/`, `query_jsonl/`
- `sar_jsonl_backup_old_params/`, `sar_slope_jsonl/`

**数据格式**: 主要是 `.jsonl` (JSON Lines) 格式，压缩率约 10-13:1

#### 6. 日志文件 (38 文件, ~1.52 MB)
- `logs/`: PM2 服务日志
- 应用运行日志
- 错误日志

#### 7. 缓存文件 (包含在 Other 中)
- `__pycache__/`: Python 编译缓存
- 各模块的 `.pyc` 文件

#### 8. 其他文件 (1359 文件, ~167.30 MB)
- 静态资源
- 图片、字体等
- Shell 脚本
- 其他辅助文件

---

## 🔄 完整重新部署步骤

### 前置要求
```bash
# 1. 系统环境
- Ubuntu/Debian Linux
- Python 3.12+
- Node.js 16+
- Git

# 2. 必需软件包
sudo apt update
sudo apt install -y python3-pip nodejs npm git curl
```

### Step 1: 恢复备份文件

```bash
# 从 /tmp 目录复制最新备份
LATEST_BACKUP=$(ls -t /tmp/webapp_backup_*.tar.gz | head -1)
echo "最新备份: $LATEST_BACKUP"

# 解压到临时目录
mkdir -p /tmp/webapp_restore
cd /tmp/webapp_restore
tar -xzf $LATEST_BACKUP

# 查看解压内容
ls -la webapp/
du -sh webapp/
```

### Step 2: 复制到目标目录

```bash
# 停止现有服务（如果有）
pm2 stop all 2>/dev/null || true

# 备份现有目录（如果需要）
if [ -d /home/user/webapp ]; then
    mv /home/user/webapp /home/user/webapp_backup_$(date +%Y%m%d_%H%M%S)
fi

# 复制解压的文件
cp -r /tmp/webapp_restore/webapp /home/user/

# 设置权限
cd /home/user/webapp
chmod +x *.py *.sh 2>/dev/null || true
chmod -R u+w .
```

### Step 3: 安装 Python 依赖

```bash
cd /home/user/webapp

# 创建虚拟环境（可选）
# python3 -m venv venv
# source venv/bin/activate

# 安装依赖
pip3 install -r requirements.txt

# 验证关键依赖
python3 -c "import flask; print(f'Flask: {flask.__version__}')"
python3 -c "import requests; print(f'Requests installed')"
```

### Step 4: 安装 PM2 全局工具

```bash
# 安装 PM2
npm install -g pm2

# 验证安装
pm2 --version
```

### Step 5: 启动所有服务

```bash
cd /home/user/webapp

# 使用 PM2 ecosystem 配置启动所有服务
pm2 start ecosystem.core.config.json

# 或逐个启动关键服务
pm2 start core_code/app.py --name flask-app --interpreter python3
pm2 start data_health_monitor.py --name data-health-monitor --interpreter python3
pm2 start coin_change_tracker.py --name coin-change-tracker --interpreter python3
# ... 根据需要启动其他服务

# 查看服务状态
pm2 list
pm2 logs --lines 50
```

### Step 6: 启动备份调度器

```bash
cd /home/user/webapp

# 启动 12 小时自动备份
pm2 start backup_scheduler.py --name backup-scheduler --interpreter python3

# 保存 PM2 配置
pm2 save

# 设置 PM2 开机自启动
pm2 startup
```

### Step 7: 验证部署

```bash
# 1. 检查所有服务状态
pm2 status

# 2. 测试 Flask API
curl http://localhost:9002/api/health
curl http://localhost:9002/

# 3. 查看日志
pm2 logs flask-app --lines 20 --nostream

# 4. 检查数据目录
ls -lh /home/user/webapp/support_resistance_jsonl/
ls -lh /home/user/webapp/anchor_daily/

# 5. 测试备份系统
python3 auto_backup_system.py list
```

---

## 📊 服务架构映射

### 核心服务

| 服务名 | 文件路径 | 端口 | 用途 | 内存 |
|--------|----------|------|------|------|
| `flask-app` | `core_code/app.py` | 9002 | 主 Web 应用 | ~50MB |
| `data-health-monitor` | `data_health_monitor.py` | - | 数据健康监控 | ~10MB |
| `coin-change-tracker` | `coin_change_tracker.py` | - | 币价涨跌追踪 | ~45MB |
| `coin-price-tracker` | `coin_price_tracker.py` | - | 币价数据收集 | ~30MB |
| `backup-scheduler` | `backup_scheduler.py` | - | 自动备份调度 | ~10MB |

### 数据收集器

| 服务名 | 文件路径 | 数据目录 | 更新频率 |
|--------|----------|----------|----------|
| `crypto-index-collector` | `crypto_index_jsonl_manager.py` | `crypto_index_jsonl/` | 实时 |
| `extreme-collector` | `extreme_jsonl_manager.py` | `extreme_jsonl/` | 5分钟 |
| `gdrive-collector` | `gdrive_jsonl_manager.py` | `gdrive_jsonl/` | 1小时 |
| `panic-daily-collector` | `panic_daily_manager.py` | `panic_daily/` | 1天 |
| `price-speed-collector` | `price_speed_jsonl_manager.py` | `price_speed_jsonl/` | 实时 |
| `sar-api-collector` | `sar_api_jsonl.py` | `sar_jsonl/` | 5分钟 |
| `v1v2-collector` | `v1v2_jsonl_manager.py` | `v1v2_jsonl/` | 实时 |

### 特殊系统

| 系统名 | 目录 | 用途 |
|--------|------|------|
| Panic Paged V2 | `panic_paged_v2/` | 恐慌指数系统 V2 |
| Panic V3 | `panic_v3/` | 恐慌指数系统 V3 |
| Major Events | `special_systems/major-events-system/` | 重大事件系统 |

---

## 🔧 常用维护命令

### PM2 服务管理
```bash
# 查看所有服务
pm2 list

# 查看详细信息
pm2 show flask-app

# 重启服务
pm2 restart flask-app
pm2 restart all

# 停止服务
pm2 stop flask-app
pm2 stop all

# 查看日志
pm2 logs flask-app
pm2 logs --lines 100 --nostream

# 清空日志
pm2 flush

# 监控
pm2 monit
```

### 备份系统
```bash
# 手动创建备份
cd /home/user/webapp
python3 auto_backup_system.py

# 列出所有备份
python3 auto_backup_system.py list
ls -lh /tmp/webapp_backup_*.tar.gz

# 查看备份历史
cat data/backup_history.jsonl | jq .

# Web 界面查看备份
# 访问: http://localhost:9002/backup-manager
```

### 数据管理
```bash
# 查看数据目录大小
du -sh /home/user/webapp/*/

# 查看最大的数据文件
find /home/user/webapp -name "*.jsonl" -type f -exec ls -lh {} \; | sort -k5 -h | tail -10

# 清理旧日志
find /home/user/webapp/logs -name "*.log" -mtime +30 -delete

# 验证数据完整性
python3 -c "
import json
import sys
file = 'support_resistance_jsonl/support_resistance_levels.jsonl'
count = 0
try:
    with open(file) as f:
        for line in f:
            json.loads(line)
            count += 1
    print(f'✅ {file}: {count} 条记录')
except Exception as e:
    print(f'❌ 错误: {e}', file=sys.stderr)
    sys.exit(1)
"
```

---

## 🔍 故障排除

### 问题 1: 服务启动失败
```bash
# 检查端口占用
netstat -tlnp | grep 9002

# 检查 Python 依赖
pip3 list | grep -i flask

# 查看详细错误日志
pm2 logs flask-app --err --lines 50
```

### 问题 2: 数据文件损坏
```bash
# 检查 JSONL 文件格式
cd /home/user/webapp
find . -name "*.jsonl" -type f -exec sh -c 'echo "检查: $1"; head -1 "$1" | jq . >/dev/null 2>&1 && echo "✅ 格式正确" || echo "❌ 格式错误"' _ {} \;
```

### 问题 3: 磁盘空间不足
```bash
# 检查磁盘使用
df -h

# 清理旧备份（保留最近3个）
cd /tmp
ls -t webapp_backup_*.tar.gz | tail -n +4 | xargs rm -f

# 清理旧日志
pm2 flush
find /home/user/webapp/logs -name "*.log" -mtime +7 -delete
```

### 问题 4: PM2 未安装
```bash
# 安装 PM2
npm install -g pm2

# 如果 npm 不可用，先安装 Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g pm2
```

---

## 🚀 性能优化建议

### 1. 内存优化
```bash
# 限制 PM2 服务最大内存
pm2 start app.py --max-memory-restart 500M

# 监控内存使用
pm2 list
watch -n 5 'pm2 list'
```

### 2. 日志管理
```json
// ecosystem.config.json 中配置日志轮转
{
  "apps": [{
    "name": "flask-app",
    "max_memory_restart": "500M",
    "error_file": "logs/flask-app-error.log",
    "out_file": "logs/flask-app-out.log",
    "log_date_format": "YYYY-MM-DD HH:mm:ss",
    "merge_logs": true,
    "max_log_lines": 10000
  }]
}
```

### 3. 数据库索引（如使用）
```python
# 如果使用数据库，确保关键字段有索引
# 示例 (伪代码):
# CREATE INDEX idx_timestamp ON coin_data(timestamp);
# CREATE INDEX idx_symbol ON coin_data(symbol);
```

---

## 📝 备份策略说明

### 自动备份
- **频率**: 每 12 小时
- **保留**: 最近 3 次备份
- **位置**: `/tmp/webapp_backup_YYYYMMDD_HHMMSS.tar.gz`
- **大小**: 约 265 MB 压缩 / 3.16 GB 未压缩
- **调度器**: `backup_scheduler.py` (PM2 管理)

### 手动备份
```bash
cd /home/user/webapp
python3 auto_backup_system.py
```

### 备份内容
- ✅ 所有 Python 代码 (401 文件)
- ✅ 所有 HTML 模板 (289 文件)
- ✅ 所有数据文件 (931 文件, 2.97 GB)
- ✅ 所有配置文件 (290 文件)
- ✅ 日志文件 (38 文件)
- ✅ `__pycache__` 缓存
- ❌ `.git` 目录 (排除)

### 恢复测试
定期测试备份恢复流程，确保备份可用：
```bash
# 每月测试一次
mkdir -p /tmp/restore_test
cd /tmp/restore_test
tar -xzf /tmp/webapp_backup_20260316_024006.tar.gz
cd webapp
python3 -m py_compile core_code/app.py
echo "✅ 备份恢复测试通过"
```

---

## 📞 支持与联系

- **部署文档**: `/home/user/webapp/DEPLOYMENT_GUIDE.md`
- **备份文档**: `/home/user/webapp/BACKUP_SYSTEM.md`
- **修复报告**: `/home/user/webapp/*.md` (各种修复文档)
- **系统状态**: `bash check_system_status.sh`

---

## 🎯 快速恢复清单

### 15分钟快速恢复
```bash
# 1. 解压备份 (2分钟)
cd /tmp && tar -xzf webapp_backup_*.tar.gz && cp -r webapp /home/user/

# 2. 安装依赖 (5分钟)
cd /home/user/webapp && pip3 install -r requirements.txt

# 3. 安装 PM2 (2分钟)
npm install -g pm2

# 4. 启动服务 (1分钟)
pm2 start ecosystem.core.config.json

# 5. 启动备份 (1分钟)
pm2 start backup_scheduler.py --name backup-scheduler --interpreter python3
pm2 save

# 6. 验证 (4分钟)
pm2 list
curl http://localhost:9002/api/health
python3 auto_backup_system.py list

echo "✅ 系统恢复完成！"
```

---

**文档版本**: v1.0  
**创建时间**: 2026-03-16 02:40  
**最后更新**: 2026-03-16 02:40  
**备份大小**: 265 MB (压缩) / 3.16 GB (未压缩)  
**文件总数**: 3,325 文件  
