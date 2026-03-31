# 备份对比报告

## 旧备份 (2026-03-16 02:55) - 265.45 MB

**统计信息**（来自 backup_history.jsonl）：
- Python: 401 files (5.40 MB)
- Markdown: 20 files (199.12 KB)
- HTML: 289 files (14.02 MB)  
- Config: 291 files (3.21 MB)
- **Data: 931 files (2.97 GB)** ⚠️
- Logs: 38 files (1.71 MB)
- Other: 1359 files (167.30 MB)

**压缩后**: 265.45 MB  
**未压缩**: ~3.2 GB

## 当前备份 (2026-03-17 17:11) - 526 MB

**实际统计**：
- Python: 402+ files (~5.42 MB)
- Markdown: 55+ files (~550 KB)
- HTML: 290+ files (~14 MB)
- Config: 295+ files (~3.23 MB)
- **Data: 1,329 files (1.85 GB)** ⚠️
- Logs: 39 files (~9.6 MB)
- JSONL total: 1,337 files
- .git: 375 MB

**压缩后**: 526 MB (含 .git)  
**未压缩**: 2.2 GB

## 🔴 数据丢失分析

### 丢失的数据
- **Data 目录**: 2.97 GB → 1.85 GB = **1.12 GB 丢失**
- **文件数**: 估计 500+ 个 JSONL 文件被删除

### 被删除数据的时间范围
- SAR 数据: 2026-02-11 至 2026-03-16 (删除原因: `clean_recent_sar_data.py`)
- Support Resistance: 2026-02-08 之后
- 其他数据收集器: 可能也有类似清理

### 清理脚本
1. `core_code/clean_recent_sar_data.py`
   - 删除 2026-02-11 及之后的所有 SAR 数据
   - 硬编码截止日期: 2026-02-10
   
2. `core_code/panic_routes_clean.py`
   - 可能也执行了数据清理

## 🔍 当前系统数据盘点

### 大型数据目录
| 目录 | 大小 | 文件数 | 时间范围 |
|------|------|--------|----------|
| support_resistance_daily | 977 MB | 41 | 2025-12-25 ~ 2026-02-07 ⚠️ |
| data/ | 260 MB | 445 JSONL | 2026-01-28 ~ 2026-03-17 |
| coin_change_tracker | 182 MB | 116 JSONL | 部分历史 |
| anchor_daily | 81 MB | | 2025-12 ~ 2026-02 |
| sar_jsonl | 65 MB | 29 JSONL | 仅 2月10日前 ⚠️ |
| price_position | 69 MB | | |
| gdrive_jsonl | 24 MB | | |
| okx_trading_jsonl | 18 MB | | |
| 其他 60+ 目录 | ~500 MB | | |

### 数据完整性状态
- ✅ 2026年1月: 完整 (01-28 开始)
- ✅ 2026年2月: **部分** (02-01 ~ 02-10，之后被清理)
- ❌ 2026年2月11日-3月16日: **SAR 数据全部删除**
- ✅ 2026年3月: 部分（非 SAR 数据存在）

## ⚠️ 关键问题

1. **数据被自动清理脚本永久删除**
   - `clean_recent_sar_data.py` 在某个时间点被执行
   - 删除了约 1.12 GB 的数据
   - 这些数据**无法从当前系统恢复**

2. **旧备份已被自动清理删除**
   - 备份系统的 `cleanup_old_backups()` 只保留最近3个
   - 包含完整数据的 265MB 备份已被删除

3. **当前备份虽然体积大（526MB），但数据不完整**
   - 包含了 .git (375MB) 导致体积增大
   - 实际数据只有 1.8 GB，缺少 1.12 GB

## 💡 解决方案

### 方案 1: 接受当前数据状态
- 使用当前 526MB 备份（包含 .git）
- 或使用 169MB 备份（不含 .git）
- 接受 2月11日-3月16日的 SAR 数据已丢失

### 方案 2: 从数据收集器重新生成（如果仍在运行）
- 检查 PM2 中的 collector 进程
- 如果 collectors 仍在内存中持有数据，导出它们
- 但这可能性很小（collectors 通常实时写入文件）

### 方案 3: 从 OKX API 或其他源重新获取
- 如果数据来自外部 API（如 OKX），可以重新拉取历史数据
- 需要 API 支持历史数据查询

## 📋 建议行动

1. **立即禁用所有清理脚本**
   - ✅ 已禁用备份自动清理
   - ⚠️ 需要禁用或修改 `clean_recent_sar_data.py`
   - ⚠️ 检查其他可能的清理脚本

2. **使用当前完整备份**
   - 文件: `/tmp/webapp_WITH_GIT_COMPLETE_20260317.tar.gz` (526 MB)
   - 包含所有当前存在的数据
   - 包含完整 Git 历史

3. **创建数据恢复计划**（如果需要丢失的数据）
   - 确认是否有其他备份源
   - 联系 API 提供商获取历史数据
   - 接受数据丢失，从当前时间点重新开始收集

---
**报告生成时间**: 2026-03-17 17:15 (Beijing Time)
**当前最完整备份**: /tmp/webapp_WITH_GIT_COMPLETE_20260317.tar.gz (526 MB)
