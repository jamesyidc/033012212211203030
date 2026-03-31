# 备份管理器认证功能说明

## 🔐 功能概述

备份管理器现已添加 HTTP Basic Authentication 认证，确保只有授权用户才能访问备份文件和相关功能。

## 🔑 登录凭据

```
用户名：jamesyi
密码：rr123456
```

## 🌐 受保护的端点

以下端点需要认证才能访问：

### 1. 备份管理器页面
- **URL**: https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/backup-manager
- **方法**: GET
- **认证**: 需要
- **描述**: 备份管理器 Web 界面

### 2. 备份列表 API
- **URL**: https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/list
- **方法**: GET
- **认证**: 需要
- **描述**: 获取所有可用备份文件的列表

### 3. 备份下载 API
- **URL**: https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/<filename>
- **方法**: GET
- **认证**: 需要
- **描述**: 下载指定的备份文件

## 📱 使用方法

### 浏览器访问

1. 在浏览器中打开备份管理器 URL
2. 浏览器会自动弹出登录对话框
3. 输入用户名和密码
4. 点击确定后即可访问

**浏览器会记住凭据**，在会话期间无需重复输入。

### cURL 命令行访问

```bash
# 方法 1: 使用 -u 参数
curl -u jamesyi:rr123456 https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/backup-manager

# 方法 2: 使用 Authorization 头
curl -H "Authorization: Basic amFtZXN5aTpycjEyMzQ1Ng==" https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/backup-manager

# 下载备份文件
curl -u jamesyi:rr123456 -O https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/webapp_backup_20260326_3.tar.gz
```

### wget 下载

```bash
# 方法 1: 在 URL 中包含凭据
wget https://jamesyi:rr123456@9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/webapp_backup_20260326_3.tar.gz

# 方法 2: 使用 --user 和 --password 参数
wget --user=jamesyi --password=rr123456 https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/webapp_backup_20260326_3.tar.gz
```

### Python 脚本

```python
import requests
from requests.auth import HTTPBasicAuth

# 设置认证
auth = HTTPBasicAuth('jamesyi', 'rr123456')

# 获取备份列表
response = requests.get(
    'https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/list',
    auth=auth
)

if response.status_code == 200:
    backups = response.json()['backups']
    print(f"找到 {len(backups)} 个备份文件")
else:
    print(f"认证失败: {response.status_code}")

# 下载备份文件
filename = 'webapp_backup_20260326_3.tar.gz'
response = requests.get(
    f'https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/api/backup/download/{filename}',
    auth=auth,
    stream=True
)

if response.status_code == 200:
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"下载完成: {filename}")
```

## 🛡️ 安全特性

### 1. 未授权访问保护
- 未提供凭据的请求返回 **401 Unauthorized**
- 浏览器自动提示输入用户名和密码
- API 调用必须包含认证信息

### 2. HTTP Basic Authentication
- 使用标准的 HTTP Basic Auth 协议
- 凭据通过 Base64 编码传输（建议使用 HTTPS）
- 兼容所有现代浏览器和 HTTP 客户端

### 3. 会话管理
- 浏览器会话期间自动保持认证状态
- 无需每次请求都重新输入密码
- 关闭浏览器后需要重新认证

## 🔍 故障排查

### 问题：浏览器一直提示输入密码

**原因**：输入的用户名或密码不正确

**解决**：
1. 确认用户名是 `jamesyi`（全小写）
2. 确认密码是 `rr123456`（区分大小写）
3. 清除浏览器缓存后重试

### 问题：cURL 返回 401 错误

**原因**：认证凭据未正确传递

**解决**：
```bash
# 确保使用 -u 参数或 Authorization 头
curl -u jamesyi:rr123456 <URL>

# 检查是否有拼写错误
```

### 问题：Python 脚本认证失败

**原因**：requests 库认证配置错误

**解决**：
```python
from requests.auth import HTTPBasicAuth

# 确保使用 HTTPBasicAuth
auth = HTTPBasicAuth('jamesyi', 'rr123456')
response = requests.get(url, auth=auth)
```

## 📝 技术实现

### 使用的库
- **Flask-HTTPAuth** 4.8.0
- 提供简单易用的 HTTP Basic Auth 装饰器

### 代码示例

```python
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

# 用户验证
@auth.verify_password
def verify_password(username, password):
    if username == 'jamesyi' and password == 'rr123456':
        return username
    return None

# 受保护的路由
@app.route('/backup-manager')
@auth.login_required
def backup_manager():
    return render_template('backup_manager.html')
```

## 🔄 修改密码

如需修改密码，请编辑 `/home/user/webapp/core_code/app.py`：

```python
# 找到这部分代码
BACKUP_MANAGER_USERS = {
    'jamesyi': 'rr123456'  # 修改这里的密码
}
```

修改后重启 Flask 应用：

```bash
cd /home/user/webapp
pm2 restart flask-app
```

## 📊 测试验证

### 测试未授权访问
```bash
curl -I https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/backup-manager
# 应返回: HTTP/2 401
# 应包含: www-authenticate: Basic realm="Authentication Required"
```

### 测试授权访问
```bash
curl -I -u jamesyi:rr123456 https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/backup-manager
# 应返回: HTTP/2 200
```

## 🎯 最佳实践

1. **使用 HTTPS**：始终通过 HTTPS 访问（当前已配置）
2. **定期更改密码**：建议定期更新认证密码
3. **不要分享凭据**：保持登录信息的机密性
4. **使用环境变量**：生产环境建议使用环境变量存储凭据
5. **启用日志监控**：监控认证失败尝试

## 📞 支持

如有问题或需要帮助，请：
1. 检查本文档的故障排查部分
2. 查看 Flask 应用日志：`pm2 logs flask-app`
3. 验证认证凭据是否正确

---

**最后更新**：2026-03-25  
**版本**：1.0.0
