# 自动备份到 AI 云盘功能说明

## 📋 功能概述

自动备份系统现已集成 **AI 云盘自动转存功能**，每次备份完成后会自动将备份文件复制到 AI 云盘（`/mnt/aidrive`），实现数据的双重保护。

---

## 🎯 核心特性

### 1. **自动转存流程**
```
创建备份 (/tmp) → 验证大小 → 复制到 AI 云盘 → 清理旧备份 → 记录日志
```

### 2. **备份策略**
- **备份周期**: 每 12 小时自动执行一次
- **本地备份**: 保留最近 3 个备份文件（`/tmp`）
- **AI 云盘**: 同步保留最近 3 个备份文件（`/mnt/aidrive`）
- **最小大小**: 备份文件必须 ≥ 260 MB（压缩后）

### 3. **双重清理机制**
- **本地清理**: 自动删除超过 3 个的旧备份（`/tmp`）
- **云盘清理**: 自动删除 AI 云盘中超过 3 个的旧备份

---

## 📊 当前状态

### AI 云盘备份文件
```bash
# 查看 AI 云盘备份
sudo ls -lh /mnt/aidrive/*.tar.gz

# 输出示例
-rw-r--r-- 1 root root 324M Mar 25 16:16 webapp_backup_20260325_2.tar.gz
-rw-r--r-- 1 root root 326M Mar 25 16:20 webapp_backup_20260326_1.tar.gz
```

### 本地备份文件（/tmp）
```bash
# 查看本地备份
ls -lh /tmp/webapp_backup_*.tar.gz

# 输出示例
-rw-r--r-- 1 user user 321M Mar 24 20:51 webapp_backup_20260325_1.tar.gz
-rw-r--r-- 1 user user 324M Mar 25 08:54 webapp_backup_20260325_2.tar.gz
-rw-r--r-- 1 user user 326M Mar 25 16:20 webapp_backup_20260326_1.tar.gz
```

### 存储空间
- **AI 云盘总容量**: 649 MB（2 个备份文件）
- **本地 /tmp**: 971 MB（3 个备份文件）

---

## 🔄 工作流程详解

### 步骤 1: 创建备份
```python
backup_path = create_backup()  # 在 /tmp 创建压缩包
```

### 步骤 2: 验证备份大小
```python
if backup_size < MIN_BACKUP_SIZE_MB:  # 260 MB
    print("❌ 备份失败：文件过小")
    return None
```

### 步骤 3: 转存到 AI 云盘
```python
copy_to_aidrive(backup_path)
# 使用 sudo cp 复制文件
# 验证文件大小一致性
# 超时时间：5 分钟
```

### 步骤 4: 清理旧备份
```python
# 本地清理（/tmp）
cleanup_old_backups()  # 保留最近 3 个

# AI 云盘清理
cleanup_old_aidrive_backups()  # 保留最近 3 个
```

---

## 📝 日志记录

### 成功转存日志示例
```
☁️  转存备份到 AI 云盘...
✅ 备份已成功转存到 AI 云盘
   位置: /mnt/aidrive/webapp_backup_20260326_1.tar.gz
   大小: 325.15 MB

🧹 清理 AI 云盘旧备份（保留最近3个）...
✅ AI 云盘当前备份数量 2 <= 3，无需清理
```

### 查看完整日志
```bash
# PM2 日志（最近 50 行）
pm2 logs backup-manager --lines 50 --nostream

# 备份历史记录
cat /home/user/webapp/data/backup_history.jsonl
```

---

## 🚀 管理命令

### 查看备份列表
```bash
cd /home/user/webapp
python auto_backup_system.py list
```

### 查看备份统计
```bash
cd /home/user/webapp
python auto_backup_system.py stats
```

### 手动执行备份（会自动转存）
```bash
cd /home/user/webapp
python auto_backup_system.py
```

### 重启备份管理器
```bash
pm2 restart backup-manager
```

### 查看 PM2 状态
```bash
pm2 status backup-manager
```

---

## 🔍 验证与测试

### 1. 验证 AI 云盘挂载
```bash
ls -lh /mnt/aidrive/
# 应该能看到备份文件列表
```

### 2. 验证文件完整性
```bash
# 比对本地和云盘文件大小
ls -lh /tmp/webapp_backup_20260326_1.tar.gz
sudo ls -lh /mnt/aidrive/webapp_backup_20260326_1.tar.gz
# 两者大小应该完全一致
```

### 3. 测试恢复（从 AI 云盘）
```bash
# 复制到临时目录
sudo cp /mnt/aidrive/webapp_backup_20260326_1.tar.gz /tmp/test_restore.tar.gz

# 解压测试
cd /tmp
tar -tzf test_restore.tar.gz | head -20
```

---

## 📈 备份内容统计

每次备份包含完整的项目数据：

| 类型 | 文件数 | 大小 |
|------|--------|------|
| Python 脚本 | 416 | 5.65 MB |
| Markdown 文档 | 126 | 1.05 MB |
| HTML 模板 | 295 | 14.22 MB |
| 配置文件 | 324 | 3.28 MB |
| 数据文件 | 1505 | 3.29 GB |
| 日志文件 | 58 | 595.86 MB |
| 其他文件 | 1372 | 169.40 MB |

**压缩后大小**: ~325 MB  
**压缩率**: ~95% （3.6 GB → 325 MB）

---

## ⚙️ 配置参数

### 关键配置（`auto_backup_system.py`）
```python
BACKUP_INTERVAL = 12 * 60 * 60  # 12 小时
MAX_BACKUPS = 3                  # 保留数量
MIN_BACKUP_SIZE_MB = 260         # 最小大小
BACKUP_DIR = Path('/tmp')        # 本地备份目录
AIDRIVE_DIR = Path('/mnt/aidrive')  # AI 云盘路径
```

### 超时设置
- **备份创建**: 无超时限制（自动处理大文件）
- **云盘复制**: 5 分钟（300 秒）
- **文件清理**: 30 秒

---

## 🛡️ 安全与可靠性

### 1. **权限管理**
- 使用 `sudo` 执行云盘操作
- 备份文件权限: `rw-r--r--` (644)
- 所有者: root（AI 云盘）

### 2. **错误处理**
- 自动捕获并记录所有异常
- 复制失败不影响本地备份
- 超时自动终止避免卡死

### 3. **数据完整性**
- 复制后验证文件大小
- 大小不匹配自动标记失败
- 备份前清理临时文件

### 4. **资源优化**
- 单线程顺序执行避免并发冲突
- 自动清理释放磁盘空间
- 压缩率高（95%）节省存储

---

## 📅 定时任务

### 当前调度
- **首次运行**: 脚本启动时立即执行
- **后续运行**: 每 12 小时自动触发
- **下次备份**: 2026-03-26 12:20:53（北京时间）

### 查看下次备份时间
```bash
pm2 logs backup-manager --lines 5 --nostream | grep "下次备份时间"
```

---

## 🔧 故障排查

### 问题 1: AI 云盘不可用
```bash
# 检查挂载点
ls -ld /mnt/aidrive/

# 检查权限
sudo ls -l /mnt/aidrive/
```

**解决方案**: 
- 确保 AI 云盘已正确挂载
- 检查当前用户是否有访问权限

### 问题 2: 复制超时
```
❌ 复制超时（超过5分钟）
```

**解决方案**:
- 检查网络连接
- 查看 AI 云盘响应速度
- 考虑增加超时时间（修改 `timeout=300`）

### 问题 3: 磁盘空间不足
```
❌ 复制失败: No space left on device
```

**解决方案**:
```bash
# 查看 AI 云盘容量
df -h /mnt/aidrive/

# 手动清理旧备份
sudo rm /mnt/aidrive/webapp_backup_XXXXXXXX_X.tar.gz
```

---

## 📚 相关文档

- **备份系统**: `/home/user/webapp/auto_backup_system.py`
- **调度器**: `/home/user/webapp/backup_scheduler.py`
- **历史记录**: `/home/user/webapp/data/backup_history.jsonl`
- **PM2 配置**: `pm2 show backup-manager`

---

## 📞 技术支持

### 查看系统状态
```bash
# PM2 进程
pm2 status

# 备份服务
pm2 info backup-manager

# 实时日志
pm2 logs backup-manager --lines 100
```

### 紧急操作
```bash
# 停止备份服务
pm2 stop backup-manager

# 重启备份服务
pm2 restart backup-manager

# 删除备份服务
pm2 delete backup-manager
```

---

## ✅ 功能验证清单

- [x] 自动创建备份（每 12 小时）
- [x] 备份大小验证（≥ 260 MB）
- [x] 自动转存到 AI 云盘
- [x] 文件完整性校验
- [x] 本地旧备份清理（保留 3 个）
- [x] AI 云盘旧备份清理（保留 3 个）
- [x] 详细日志记录
- [x] 错误处理与重试机制
- [x] PM2 进程管理
- [x] 备份历史 JSONL 记录

---

## 🎉 总结

**自动备份到 AI 云盘功能已全面实现并稳定运行！**

- ✅ 每 12 小时自动备份
- ✅ 双重存储（本地 + AI 云盘）
- ✅ 自动清理释放空间
- ✅ 完整的日志记录
- ✅ 可靠的错误处理

**当前状态**: 
- 本地备份: 3 个文件（971 MB）
- AI 云盘: 2 个文件（649 MB）
- 服务状态: **运行中** ✅
- 下次备份: 2026-03-26 12:20:53

---

*最后更新: 2026-03-25 16:25*  
*服务地址: https://9002-iwyspq7c2ufr5cnosf8lb-2e77fc33.sandbox.novita.ai/backup-manager*
