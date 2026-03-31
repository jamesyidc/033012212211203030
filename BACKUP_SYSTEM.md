# 自动备份系统文档

## 📋 概述

自动备份系统实现了完整项目的定时备份，每12小时自动执行一次，保留最近3次备份，并提供Web界面进行管理和监控。

**重要**: 备份包含**完整的3.6GB项目数据**，压缩后约265MB（压缩率12:1）。

## 🎯 核心功能

### 1. 自动备份
- ⏰ **备份频率**: 每12小时自动执行
- 📦 **保留策略**: 保留最近3次备份
- 📁 **备份位置**: `/tmp` 目录
- 🗜️ **压缩格式**: `.tar.gz`
- 💾 **备份大小**: ~265MB 压缩 / ~3.16GB 未压缩
- 📊 **压缩率**: 约12:1（JSONL数据高度可压缩）

### 2. 备份内容

#### ✅ 包含的完整内容（3,325+ 文件）
| 类型 | 数量 | 大小（未压缩） | 路径/模式 | 说明 |
|------|------|----------------|----------|------|
| **Python文件** | 401 | 5.38 MB | `**/*.py`, `**/*.pyc` | 所有Python代码和编译缓存 |
| **HTML模板** | 289 | 14.02 MB | `templates/**/*.html` | Web界面模板 |
| **Markdown文档** | 17 | 174.74 KB | `*.md`, `docs/**/*.md` | 系统文档 |
| **配置文件** | 290 | 3.20 MB | `*.json`, `*.js`, `*.yaml`, `*.yml` | 所有配置 |
| **数据文件** | 931 | 2.97 GB | `**/*.jsonl`, `**/*.json`, `**/*.csv` | **完整数据集** |
| **日志文件** | 38 | 1.52 MB | `logs/**/*.log` | 运行日志 |
| **缓存文件** | - | 包含 | `__pycache__/**/*.pyc` | Python缓存 |
| **其他文件** | 1,359 | 167.30 MB | 静态资源、脚本等 | 其他辅助文件 |

**数据目录详情**（2.97 GB）：
- `support_resistance_daily/`: 977 MB (41文件)
- `support_resistance_jsonl/`: 740 MB (4文件，含697MB单文件)
- `anchor_daily/`: 191 MB
- `coin_change_tracker/`: 182 MB
- `price_speed_jsonl/`: 173 MB
- `anchor_profit_stats/`: 163 MB
- `v1v2_jsonl/`: 108 MB
- 其他数据目录: ~400 MB

#### ❌ 排除的内容
| 类型 | 说明 |
|------|------|
| `.git/` | Git仓库（使用Git管理版本） |
| `tmp/` | 临时文件 |

### 3. 文件类型统计

根据最新备份统计 (2026-03-16)：

| 文件类型 | 数量 | 大小（未压缩） | 占比 |
|---------|------|----------------|------|
| Python | 401 | 5.38 MB | 0.2% |
| HTML | 289 | 14.02 MB | 0.4% |
| Markdown | 17 | 174.74 KB | <0.1% |
| 配置文件 | 290 | 3.20 MB | 0.1% |
| **数据文件** | **931** | **2.97 GB** | **94.0%** |
| 日志文件 | 38 | 1.52 MB | <0.1% |
| 其他 | 1,359 | 167.30 MB | 5.3% |
| **总计** | **3,325** | **~3.16 GB** | **100%** |
| **压缩后** | - | **~265 MB** | **压缩率 12:1** |

## 🚀 使用方法

### 方式1：手动执行备份

```bash
cd /home/user/webapp
python3 auto_backup_system.py
```

输出示例：
```
================================================================================
🔄 自动备份系统
================================================================================

🚀 开始备份...
📅 备份时间: 2026-03-16 02:40:06 (北京时间)
📁 备份文件: /tmp/webapp_backup_20260316_024006.tar.gz

📊 统计备份内容...
📦 使用tar命令直接创建备份...
🔧 执行命令: tar ... -czf webapp_backup_20260316_024006.tar.gz webapp/
✅ tar压缩完成

✅ 备份完成!
📦 备份大小: 265.41 MB

📊 备份内容统计:
  - PYTHON: 401 文件, 5.38 MB
  - MARKDOWN: 17 文件, 174.74 KB
  - HTML: 289 文件, 14.02 MB
  - CONFIG: 290 文件, 3.20 MB
  - DATA: 931 文件, 2.97 GB
  - LOGS: 38 文件, 1.52 MB
  - OTHER: 1359 文件, 167.30 MB
  - PYTHON: 148 文件, 4.85 MB
  - MARKDOWN: 15 文件, 523.45 KB
  - HTML: 88 文件, 1.92 MB
  - CONFIG: 22 文件, 1.15 MB
  - DATA: 3245 文件, 150.23 MB
  - OTHER: 95 文件, 8.44 MB
```

### 方式2：查看备份列表

```bash
python3 auto_backup_system.py list
```

### 方式3：获取备份统计

```bash
python3 auto_backup_system.py stats
```

### 方式4：通过Web界面管理

访问：`https://9002-<sandbox-id>.sandbox.novita.ai/backup-manager`

功能：
- ✅ 查看备份列表和状态
- ✅ 手动触发备份
- ✅ 查看备份历史记录
- ✅ 文件类型分布图表
- ✅ 备份大小趋势图表

## ⚙️ 系统配置

### 自动备份调度器

**服务名**: `backup-scheduler`（计划添加到PM2）

**配置文件**: `/home/user/webapp/backup_scheduler.py`

**启动方式**:
```bash
# 方式1：直接运行
python3 /home/user/webapp/backup_scheduler.py

# 方式2：通过PM2管理（推荐）
pm2 start /home/user/webapp/backup_scheduler.py --name backup-scheduler --interpreter python3
pm2 save
```

### 备份参数配置

编辑 `/home/user/webapp/auto_backup_system.py`：

```python
# 备份目录
BACKUP_DIR = Path('/tmp')

# 最大保留备份数
MAX_BACKUPS = 3

# 备份间隔（秒）
BACKUP_INTERVAL = 12 * 60 * 60  # 12小时
```

## 📊 API接口

### 1. 获取备份状态

**请求**:
```http
GET /api/backup/status
```

**响应**:
```json
{
  "success": true,
  "backups": [
    {
      "filename": "webapp_backup_20260316_022057.tar.gz",
      "filepath": "/tmp/webapp_backup_20260316_022057.tar.gz",
      "size": 175234560,
      "size_formatted": "167.12 MB",
      "timestamp": "2026-03-16T02:20:57+08:00",
      "mtime": 1773597657.123
    }
  ],
  "total_backups": 1,
  "total_size": 175234560,
  "total_size_formatted": "167.12 MB",
  "backup_history": [
    {
      "timestamp": "2026-03-16T02:20:57+08:00",
      "filename": "webapp_backup_20260316_022057.tar.gz",
      "size_bytes": 175234560,
      "size_formatted": "167.12 MB",
      "file_stats": {
        "python": {"count": 148, "size": "4.85 MB"},
        "html": {"count": 88, "size": "1.92 MB"},
        "markdown": {"count": 15, "size": "523.45 KB"},
        "config": {"count": 22, "size": "1.15 MB"},
        "data": {"count": 3245, "size": "150.23 MB"}
      },
      "status": "success"
    }
  ],
  "backup_dir": "/tmp",
  "max_backups": 3
}
```

### 2. 手动触发备份

**请求**:
```http
POST /api/backup/trigger
```

**响应**:
```json
{
  "success": true,
  "message": "备份任务已启动",
  "pid": 12345
}
```

## 🔄 恢复流程

### 场景1：恢复整个项目

```bash
# 1. 查找最新备份
ls -lh /tmp/webapp_backup_*.tar.gz | tail -1

# 2. 解压到临时目录
mkdir -p /tmp/restore_temp
cd /tmp/restore_temp
tar -xzf /tmp/webapp_backup_20260316_022057.tar.gz

# 3. 复制到目标位置
cp -r /tmp/restore_temp/webapp/* /home/user/webapp/

# 4. 重启服务
cd /home/user/webapp
pm2 restart all
```

### 场景2：恢复特定文件

```bash
# 1. 查看备份内容
tar -tzf /tmp/webapp_backup_20260316_022057.tar.gz | grep "your_file"

# 2. 提取特定文件
tar -xzf /tmp/webapp_backup_20260316_022057.tar.gz webapp/path/to/your_file

# 3. 复制到目标位置
cp webapp/path/to/your_file /home/user/webapp/path/to/
```

### 场景3：恢复数据文件

```bash
# 提取所有数据文件
tar -xzf /tmp/webapp_backup_20260316_022057.tar.gz "webapp/data/**/*.jsonl"

# 复制到目标位置
cp -r webapp/data/* /home/user/webapp/data/
```

## 📝 备份记录

备份历史记录保存在：
```
/home/user/webapp/data/backup_history.jsonl
```

每次备份成功或失败都会追加一条记录，包含：
- 时间戳
- 文件名
- 文件大小
- 文件统计信息
- 状态（success/failed）
- 错误信息（如果失败）

## 🛠️ 维护操作

### 查看备份日志

```bash
# 查看调度器日志
pm2 logs backup-scheduler

# 查看最近的备份
ls -lth /tmp/webapp_backup_*.tar.gz | head -5

# 查看备份历史记录
tail -10 /home/user/webapp/data/backup_history.jsonl | jq .
```

### 手动清理旧备份

```bash
# 删除所有备份（保留最近3个）
ls -t /tmp/webapp_backup_*.tar.gz | tail -n +4 | xargs rm -f
```

### 修改备份间隔

编辑 `backup_scheduler.py`:
```python
BACKUP_INTERVAL = 6 * 60 * 60  # 改为6小时
```

然后重启调度器：
```bash
pm2 restart backup-scheduler
```

## ⚠️ 注意事项

1. **磁盘空间**: 
   - 每次备份约167MB
   - 保留3次备份约500MB
   - 确保 `/tmp` 目录有足够空间

2. **备份时间**:
   - 备份过程需要2-3分钟
   - 建议在低峰期执行

3. **数据一致性**:
   - 备份过程中系统继续运行
   - 数据文件可能在备份时被修改
   - 建议在备份时暂停数据采集（可选）

4. **网络传输**:
   - 备份文件较大（167MB）
   - 从沙盒下载可能需要较长时间
   - 建议使用稳定的网络连接

## 🔗 相关文件

| 文件 | 说明 |
|------|------|
| `auto_backup_system.py` | 备份脚本 |
| `backup_scheduler.py` | 定时调度器 |
| `templates/backup_manager.html` | Web管理界面 |
| `core_code/app.py` | Flask API（backup相关） |
| `data/backup_history.jsonl` | 备份历史记录 |
| `/tmp/webapp_backup_*.tar.gz` | 备份文件 |

## 📞 故障排查

### 问题1：备份失败

**症状**: 执行备份时出错

**解决**:
```bash
# 检查磁盘空间
df -h /tmp

# 检查权限
ls -la /home/user/webapp
ls -la /tmp

# 查看详细错误
python3 /home/user/webapp/auto_backup_system.py
```

### 问题2：调度器未运行

**症状**: 12小时后没有自动备份

**解决**:
```bash
# 检查PM2状态
pm2 list | grep backup

# 启动调度器
pm2 start /home/user/webapp/backup_scheduler.py --name backup-scheduler --interpreter python3

# 查看日志
pm2 logs backup-scheduler
```

### 问题3：Web界面无法访问

**症状**: `/backup-manager` 返回404

**解决**:
```bash
# 重启Flask应用
pm2 restart flask-app

# 检查路由
curl http://localhost:9002/backup-manager
```

## 📈 未来改进

- [ ] 支持远程备份（上传到云存储）
- [ ] 支持增量备份
- [ ] 添加备份前后的钩子脚本
- [ ] 支持加密备份文件
- [ ] 邮件通知备份结果
- [ ] 支持自定义备份策略

---

**创建时间**: 2026-03-16  
**版本**: v1.0  
**维护者**: System Admin
