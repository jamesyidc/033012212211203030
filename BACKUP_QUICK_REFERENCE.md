# 备份系统快速参考指南

## 📋 一键命令

### 查看备份状态
```bash
# 查看 PM2 服务状态
pm2 status backup-manager

# 查看实时日志
pm2 logs backup-manager --lines 20

# 查看 AI 云盘备份
sudo ls -lh /mnt/aidrive/*.tar.gz

# 查看本地备份
ls -lh /tmp/webapp_backup_*.tar.gz
```

### 手动操作
```bash
# 立即执行备份（会自动转存到 AI 云盘）
cd /home/user/webapp && python auto_backup_system.py

# 查看备份列表
cd /home/user/webapp && python auto_backup_system.py list

# 查看备份统计
cd /home/user/webapp && python auto_backup_system.py stats
```

### 服务管理
```bash
# 重启备份服务
pm2 restart backup-manager

# 停止备份服务
pm2 stop backup-manager

# 启动备份服务
pm2 start backup-manager
```

---

## 📊 当前配置

| 配置项 | 值 |
|--------|-----|
| 备份周期 | 每 12 小时 |
| 本地保留 | 最近 3 个备份 |
| AI云盘保留 | 最近 3 个备份 |
| 最小大小 | 260 MB |
| 本地路径 | `/tmp/webapp_backup_*.tar.gz` |
| 云盘路径 | `/mnt/aidrive/webapp_backup_*.tar.gz` |

---

## 🔄 自动化流程

```
创建备份 → 验证大小 → 转存AI云盘 → 清理旧备份 → 完成
   ↓          ↓          ↓           ↓          ↓
  /tmp     ≥260MB   /mnt/aidrive   保留3个    记录日志
```

---

## 📈 最新状态

### ✅ 功能状态
- **服务状态**: 运行中（PM2）
- **本地备份**: 3 个文件（971 MB）
- **AI 云盘**: 2 个文件（649 MB）
- **最新备份**: webapp_backup_20260326_1.tar.gz
- **备份大小**: 325.15 MB
- **备份时间**: 2026-03-26 00:19:34

### ⏰ 调度信息
- **首次运行**: 立即执行
- **后续运行**: 每 12 小时
- **下次备份**: 2026-03-26 12:20:53（北京时间）

---

## 🆘 故障排查

### 问题：AI 云盘无法访问
```bash
# 检查挂载
ls -ld /mnt/aidrive/

# 检查权限
sudo ls -l /mnt/aidrive/
```

### 问题：备份文件过小
```bash
# 查看备份日志
tail -1 /home/user/webapp/data/backup_history.jsonl | python3 -m json.tool

# 检查磁盘空间
df -h /tmp/
```

### 问题：服务无响应
```bash
# 查看错误日志
pm2 logs backup-manager --err --lines 50

# 重启服务
pm2 restart backup-manager
```

---

## 📂 文件位置

| 文件类型 | 路径 |
|----------|------|
| 备份脚本 | `/home/user/webapp/auto_backup_system.py` |
| 调度器 | `/home/user/webapp/backup_scheduler.py` |
| 历史记录 | `/home/user/webapp/data/backup_history.jsonl` |
| 本地备份 | `/tmp/webapp_backup_*.tar.gz` |
| AI云盘备份 | `/mnt/aidrive/webapp_backup_*.tar.gz` |
| PM2日志 | `~/.pm2/logs/backup-manager-*.log` |

---

## 🔗 相关链接

- **详细文档**: [AUTO_BACKUP_TO_AIDRIVE.md](AUTO_BACKUP_TO_AIDRIVE.md)
- **备份管理器**: https://9002-iwyspq7c2ufr5cnosf8lb-2e77fc33.sandbox.novita.ai/backup-manager
- **GitHub仓库**: https://github.com/jamesyidc/33650000319

---

*最后更新: 2026-03-25 16:30*
