# 备份文件命名规则说明

## 📋 新命名格式

```
webapp_backup_YYYYMMDD_N.tar.gz
```

- **YYYYMMDD**: 日期（年月日）
- **N**: 序号（1, 2, 3...）

## 🌟 示例

```
webapp_backup_20260315_1.tar.gz  ← 2026-03-15 第1次备份
webapp_backup_20260315_2.tar.gz  ← 2026-03-15 第2次备份 (当天最新)
webapp_backup_20260316_1.tar.gz  ← 2026-03-16 第1次备份 (新日期从1开始)
webapp_backup_20260316_2.tar.gz  ← 2026-03-16 第2次备份 (当天最新，全局最新) ⭐
```

## ✨ 优点

| 特性 | 说明 | 示例 |
|------|------|------|
| 📅 日期清晰 | YYYYMMDD格式，一目了然 | 20260316 = 2026年3月16日 |
| 🔢 序号简单 | 1, 2, 3... 数字越大越新 | _2 比 _1 更新 |
| 🆕 新日期重置 | 每天从1开始，容易区分日期边界 | 16日的_1是当天第一个 |
| ⚡ 文件名短 | 不含时分秒，更简洁 | vs 旧格式: 20260316_025632 |
| 👀 易识别 | 快速找到最新备份 | 同日期序号最大即最新 |

## 📊 如何识别最新备份

### 方法1: 同一日期中的最新
**规则**: 同一日期中，序号最大的就是最新备份

```
2026-03-16:
  webapp_backup_20260316_1.tar.gz  ← 早期备份
  webapp_backup_20260316_2.tar.gz  ← 最新备份 ⭐
```

### 方法2: 全局最新
**规则**: 所有备份中，日期最新且序号最大的

```bash
# 命令行查找全局最新
ls -t /tmp/webapp_backup_*.tar.gz | head -1

# 输出: webapp_backup_20260316_2.tar.gz
```

### 方法3: 使用脚本
```python
from pathlib import Path
import re

backups = Path('/tmp').glob('webapp_backup_*.tar.gz')
latest = max(backups, key=lambda p: p.stat().st_mtime)
print(f"最新备份: {latest.name}")
```

## 🔄 命名规则逻辑

### 1. 创建新备份时
```python
# 伪代码
date = beijing_time.strftime('%Y%m%d')  # 例: 20260316
existing_count = count_backups_today(date)  # 统计今天已有备份数
sequence = existing_count + 1  # 序号 = 已有数量 + 1
filename = f'webapp_backup_{date}_{sequence}.tar.gz'
```

### 2. 跨天重置
```
2026-03-15:
  webapp_backup_20260315_1.tar.gz  (12:00创建)
  webapp_backup_20260315_2.tar.gz  (18:00创建)

2026-03-16 (新的一天):
  webapp_backup_20260316_1.tar.gz  (06:00创建) ← 序号重置为1
  webapp_backup_20260316_2.tar.gz  (18:00创建)
```

## 📖 实际案例

### 案例1: 自动备份（12小时间隔）
```
时间线:
  2026-03-15 02:00 → webapp_backup_20260315_1.tar.gz
  2026-03-15 14:00 → webapp_backup_20260315_2.tar.gz
  2026-03-16 02:00 → webapp_backup_20260316_1.tar.gz (新日期)
  2026-03-16 14:00 → webapp_backup_20260316_2.tar.gz (最新)
```

### 案例2: 手动备份
```
同一天手动创建多个备份:
  python3 auto_backup_system.py  → webapp_backup_20260316_1.tar.gz
  python3 auto_backup_system.py  → webapp_backup_20260316_2.tar.gz
  python3 auto_backup_system.py  → webapp_backup_20260316_3.tar.gz
```

## 🛠️ 使用命令

### 查看所有备份
```bash
ls -lh /tmp/webapp_backup_*.tar.gz
```

### 按日期分组查看
```bash
ls /tmp/webapp_backup_*.tar.gz | sed 's/_[0-9]*\.tar\.gz//' | uniq
```

### 查找特定日期的备份
```bash
ls /tmp/webapp_backup_20260316_*.tar.gz
```

### 删除旧日期的备份
```bash
# 删除2026-03-15的所有备份
rm /tmp/webapp_backup_20260315_*.tar.gz
```

## 🔍 备份分析示例

### 当前备份状态
```
📅 日期: 2026-03-15
  序号2: webapp_backup_20260315_2.tar.gz
        时间: 2026-03-15 14:51:59
        大小: 265.42 MB ⭐ 当天最新

📅 日期: 2026-03-16
  序号1: webapp_backup_20260316_1.tar.gz
        时间: 2026-03-16 02:48:48
        大小: 265.42 MB
  序号2: webapp_backup_20260316_2.tar.gz
        时间: 2026-03-16 02:56:32
        大小: 265.45 MB ⭐ 当天最新

🌟 全局最新备份: webapp_backup_20260316_2.tar.gz
   时间: 2026-03-16 02:56:32 (北京时间)
   大小: 265.45 MB
```

## ⚙️ 配置说明

### 自动备份设置
- **间隔**: 12小时
- **保留**: 最近3次
- **位置**: `/tmp/`
- **调度器**: `backup_scheduler.py` (PM2管理)

### 修改保留策略
```python
# auto_backup_system.py
MAX_BACKUPS = 3  # 修改此值可改变保留数量
```

## 📝 相关文件

- `auto_backup_system.py` - 备份脚本（包含命名逻辑）
- `backup_scheduler.py` - 自动备份调度器
- `BACKUP_SYSTEM.md` - 备份系统文档
- `BACKUP_TIME_FIX.md` - 时间修复报告

## 🎯 常见问题

### Q: 为什么不使用时分秒？
**A**: 简化文件名，序号已足够区分同一天的多个备份。时分秒信息可通过文件系统的mtime获取。

### Q: 如果一天创建超过10个备份会怎样？
**A**: 序号会继续增加：1, 2, 3... 10, 11, 12...，没有限制。

### Q: 删除中间的备份会影响序号吗？
**A**: 不会。序号只在创建时生成，删除不会重新编号。例如删除_2后，下次创建仍是_3。

### Q: 如何恢复特定日期的备份？
**A**: 
```bash
# 解压指定备份
tar -xzf /tmp/webapp_backup_20260316_1.tar.gz -C /tmp/restore/

# 或直接恢复到项目目录
cd /home/user
tar -xzf /tmp/webapp_backup_20260316_1.tar.gz
```

## 💡 最佳实践

1. **定期检查**: 每周查看一次备份列表，确认自动备份正常工作
2. **重要操作前**: 手动创建备份，避免意外
3. **异地备份**: 定期将 /tmp 中的备份复制到其他位置
4. **验证完整性**: 定期测试备份恢复流程

## 🔗 相关链接

- Web管理界面: https://9002-izdl7i89gq7ib3tbi6fq1-82b888ba.sandbox.novita.ai/backup-manager
- Git仓库: /home/user/webapp
- 备份位置: /tmp/webapp_backup_*.tar.gz

---

**文档版本**: 1.0  
**创建时间**: 2026-03-16 03:00 (北京时间)  
**最后更新**: 2026-03-16 03:00 (北京时间)  
**Git Commit**: 698c237
