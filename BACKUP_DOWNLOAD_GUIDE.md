# 备份文件外网下载指南

## 📋 功能概述

已为您创建了备份文件的外网下载接口，您可以通过浏览器直接下载备份文件。

---

## 🔗 API 接口

### 1. 获取备份文件列表

**接口地址**:
```
GET https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/list
```

**返回示例**:
```json
{
  "success": true,
  "count": 9,
  "backups": [
    {
      "filename": "webapp_backup_20260326_3.tar.gz",
      "size": 341071025,
      "size_mb": 325.27,
      "mtime": "2026-03-25T17:08:46.116738",
      "location": "/home/user/aidrive",
      "downloadable": true
    }
  ]
}
```

### 2. 下载备份文件

**接口地址**:
```
GET https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/<filename>
```

**示例**:
```
https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/webapp_backup_20260326_3.tar.gz
```

---

## 📥 下载链接（最新3个备份）

### 备份 1（最新）
- **文件名**: `webapp_backup_20260326_3.tar.gz`
- **大小**: 325.27 MB
- **时间**: 2026-03-25 17:08:46
- **下载地址**: 
  ```
  https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/webapp_backup_20260326_3.tar.gz
  ```

### 备份 2
- **文件名**: `webapp_backup_20260326_2.tar.gz`
- **大小**: 325.27 MB
- **时间**: 2026-03-25 17:07:15
- **下载地址**:
  ```
  https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/webapp_backup_20260326_2.tar.gz
  ```

### 备份 3
- **文件名**: `webapp_backup_20260326_1.tar.gz`
- **大小**: 325.15 MB
- **时间**: 2026-03-25 16:20:49
- **下载地址**:
  ```
  https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/webapp_backup_20260326_1.tar.gz
  ```

---

## 🖱️ 使用方法

### 方法 1：浏览器直接下载
1. 复制上面的下载地址
2. 粘贴到浏览器地址栏
3. 按回车键开始下载

### 方法 2：命令行下载（curl）
```bash
# 下载最新备份
curl -O "https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/webapp_backup_20260326_3.tar.gz"

# 或使用 wget
wget "https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/webapp_backup_20260326_3.tar.gz"
```

### 方法 3：Python 脚本下载
```python
import requests

url = "https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/webapp_backup_20260326_3.tar.gz"
filename = "webapp_backup_20260326_3.tar.gz"

print(f"正在下载 {filename}...")
response = requests.get(url, stream=True)

with open(filename, 'wb') as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)

print(f"✅ 下载完成: {filename}")
```

---

## 📊 备份文件说明

### 文件命名规则
```
webapp_backup_YYYYMMDD_N.tar.gz
```
- `YYYYMMDD`: 备份日期（年月日）
- `N`: 当天第几次备份（1, 2, 3...）

### 文件内容
每个备份包含完整的项目数据：
- Python 脚本：417 个文件（5.66 MB）
- Markdown 文档：129 个文件（1.07 MB）
- HTML 模板：295 个文件（14.22 MB）
- 配置文件：324 个文件（3.28 MB）
- 数据文件：1,506 个文件（3.30 GB）
- 日志文件：58 个文件（597 MB）
- 其他文件：1,372 个文件（169 MB）

**压缩比**: 约 95%（3.6 GB → 325 MB）

---

## 🔍 获取最新备份列表

如果您想查看所有可用的备份文件，可以访问列表 API：

```bash
curl "https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/list"
```

或在浏览器中打开：
```
https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/list
```

---

## 🛡️ 安全特性

### 访问控制
- ✅ 只允许下载 `webapp_backup_` 开头的 `.tar.gz` 文件
- ✅ 自动验证文件名格式，防止路径遍历攻击
- ✅ 文件不存在时返回 404 错误

### 下载来源
- ✅ 优先从 `/home/user/aidrive`（GenSpark AI 云盘）下载
- ✅ 备用从 `/tmp`（本地备份）下载
- ❌ `/mnt/aidrive` 标记为不可下载（仅用于备用存储）

---

## 📈 自动化下载脚本

### Bash 脚本示例
```bash
#!/bin/bash
# download_latest_backup.sh

# 获取备份列表
echo "🔍 获取备份文件列表..."
backup_list=$(curl -s "https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/list")

# 提取最新备份文件名
latest_backup=$(echo "$backup_list" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['success'] and data['backups']:
    for backup in data['backups']:
        if backup['downloadable']:
            print(backup['filename'])
            break
")

if [ -z "$latest_backup" ]; then
    echo "❌ 没有找到可下载的备份文件"
    exit 1
fi

echo "📦 最新备份: $latest_backup"
echo "⬇️  开始下载..."

# 下载文件
curl -O "https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/$latest_backup"

echo "✅ 下载完成: $latest_backup"
```

使用方法：
```bash
chmod +x download_latest_backup.sh
./download_latest_backup.sh
```

---

## 🔧 故障排查

### 问题 1：下载链接无法访问
**解决方案**：
- 检查沙箱服务是否运行：`pm2 status flask-app`
- 重启 Flask 服务：`pm2 restart flask-app`

### 问题 2：文件不存在（404 错误）
**解决方案**：
- 访问列表 API 确认文件名：`/api/backup/list`
- 检查文件是否在可下载目录中

### 问题 3：下载速度慢
**解决方案**：
- 使用断点续传：`curl -C - -O <URL>`
- 或使用下载工具（如 IDM、迅雷等）

---

## 📝 技术实现

### Flask 路由代码
```python
@app.route('/api/backup/list', methods=['GET'])
def backup_list():
    """获取备份文件列表"""
    # 扫描备份目录，返回文件列表
    pass

@app.route('/api/backup/download/<filename>', methods=['GET'])
def backup_download(filename):
    """下载备份文件"""
    # 验证文件名，发送文件
    return send_file(file_path, as_attachment=True)
```

### 安全检查
```python
# 只允许下载符合规则的文件
if not filename.startswith('webapp_backup_') or not filename.endswith('.tar.gz'):
    return jsonify({'error': '无效的文件名'}), 400
```

---

## 🎯 快速开始

### 一键下载最新备份
```bash
# 方法 1：直接用浏览器打开
https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/webapp_backup_20260326_3.tar.gz

# 方法 2：命令行（Linux/Mac）
curl -O "https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/webapp_backup_20260326_3.tar.gz"

# 方法 3：命令行（Windows PowerShell）
Invoke-WebRequest -Uri "https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/webapp_backup_20260326_3.tar.gz" -OutFile "webapp_backup_20260326_3.tar.gz"
```

---

## 📚 相关文档

- **备份管理器页面**: https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/backup-manager
- **AI 云盘指南**: AIDRIVE_BACKUP_GUIDE.md
- **快速参考**: BACKUP_QUICK_REFERENCE.md
- **详细文档**: AUTO_BACKUP_TO_AIDRIVE.md
- **GitHub**: https://github.com/jamesyidc/33650000319

---

## ✅ 功能清单

- [x] 备份文件列表 API
- [x] 备份文件下载 API
- [x] 文件名安全验证
- [x] 自动查找文件位置
- [x] 支持多个备份目录
- [x] 文件大小和时间信息
- [x] HTTP 直接下载
- [x] 外网可访问

---

## 🎉 总结

✅ **外网下载功能已完成！**

您现在可以通过以下方式下载备份：
1. 🌐 **浏览器直接下载**（最简单）
2. 📝 **命令行工具下载**（curl/wget）
3. 🐍 **Python 脚本下载**（自动化）

**最新备份下载链接**：
```
https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/webapp_backup_20260326_3.tar.gz
```

复制链接到浏览器即可开始下载！ 🎊

---

*最后更新: 2026-03-25 17:35*  
*维护者: GenSpark AI Developer*
