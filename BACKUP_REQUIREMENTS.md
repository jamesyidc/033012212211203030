# 备份系统要求说明

<details>
<summary>📋 点击展开/收起：备份系统重要要求</summary>

## 🔴 核心要求（必须严格遵守）

### 1. 备份文件大小要求
- ✅ **备份文件必须 ≥ 260 MB**（压缩后）
- ⚠️ 如果备份小于 260 MB，说明数据不完整，备份会自动失败
- 📊 正常情况下，完整备份约 285 MB（包含 3.6 GB 数据）

### 2. 备份保留策略
- 📦 **保留最近 3 个备份**
- 🗑️ 自动删除超过 3 个的旧备份
- 💾 备份位置：`/tmp/webapp_backup_*.tar.gz`

### 3. 数据保护（绝对禁止）
- ❌ **绝对不允许删除任何历史数据**
- ❌ 禁止运行数据清理脚本
- ❌ 禁止手动删除 JSONL 文件
- ⚠️ 所有历史数据都是宝贵资产，必须永久保留

### 4. 自动备份
- ⏰ 每 12 小时自动执行一次
- 📝 记录详细信息到 `data/backup_history.jsonl`
- 🔍 自动验证备份完整性

## 📦 备份内容

### 必须包含的内容
- ✅ 所有源代码（Python, HTML, JS, CSS）
- ✅ 所有配置文件（JSON, YAML, ENV）
- ✅ **所有数据目录**（最重要！）
  - `support_resistance_daily/` (977 MB)
  - `support_resistance_jsonl/` (740 MB)
  - `data/` (259 MB)
  - `coin_change_tracker/` (182 MB)
  - `price_speed_jsonl/` (173 MB)
  - `anchor_profit_stats/` (163 MB)
  - `anchor_unified/` (117 MB)
  - `sar_slope_jsonl/` (116 MB)
  - `v1v2_jsonl/` (108 MB)
  - 以及其他 60+ 数据目录
- ✅ 所有日志文件
- ✅ 所有辅助脚本

### 排除的内容
- ❌ `.git/` 目录（版本控制历史）
- ❌ `__pycache__/` 目录（Python 缓存）
- ❌ `.pytest_cache/` 目录（测试缓存）

## 🚨 故障排查

### 备份失败：文件小于 260 MB
**原因**：数据不完整，可能的情况：
1. 某些数据目录被清理或删除
2. 数据收集器停止运行
3. 磁盘空间不足

**解决方案**：
1. 检查所有大型数据目录是否存在
2. 检查 PM2 进程是否正常运行：`pm2 list`
3. 检查磁盘空间：`df -h`
4. 从旧备份恢复丢失的数据

### 备份文件找不到
**位置**：所有备份文件在 `/tmp/` 目录
**命令**：`ls -lh /tmp/webapp_backup_*.tar.gz`

### 查看备份历史
**文件**：`/home/user/webapp/data/backup_history.jsonl`
**命令**：`tail -20 /home/user/webapp/data/backup_history.jsonl | jq .`

## 📖 使用说明

### 手动创建备份
```bash
cd /home/user/webapp
python3 auto_backup_system.py
```

### 查看备份列表
```bash
cd /home/user/webapp
python3 auto_backup_system.py list
```

### 查看备份统计
```bash
cd /home/user/webapp
python3 auto_backup_system.py stats
```

### 恢复备份
```bash
cd /home/user
tar -xzf /tmp/webapp_backup_YYYYMMDD_N.tar.gz
cd webapp
# 安装依赖
pip install -r requirements.txt
# 启动服务
pm2 start ecosystem.config.js
```

## ⚙️ 配置文件

**文件位置**：`/home/user/webapp/auto_backup_system.py`

**关键配置**：
```python
MAX_BACKUPS = 3              # 保留备份数量
MIN_BACKUP_SIZE_MB = 260     # 最小备份大小（MB）
BACKUP_DIR = Path('/tmp')    # 备份目录
```

## 🔒 数据安全承诺

1. ✅ 所有历史数据永久保留
2. ✅ 备份大小自动验证
3. ✅ 失败时不删除原有数据
4. ✅ 详细记录每次备份
5. ✅ 自动清理只删除旧备份文件，不删除数据

## 📊 项目统计

- **项目总大小**：3.6 GB
- **备份压缩后**：285 MB
- **压缩比**：约 13:1
- **JSONL 文件**：1,350+ 个
- **数据目录**：80+ 个

## 📞 联系信息

如有问题，请查看：
- 备份系统脚本：`auto_backup_system.py`
- 备份历史记录：`data/backup_history.jsonl`
- 系统日志：`logs/`

---
**最后更新**：2026-03-17  
**维护者**：系统管理员  
**状态**：✅ 正常运行

</details>
