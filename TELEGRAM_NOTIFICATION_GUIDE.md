# Telegram通知配置说明

## 📋 功能说明

预判数据生成脚本 (`manual_generate_prediction.py`) 会在生成预判数据后自动发送3次Telegram通知。

## 🔧 配置步骤

### 1. 获取Telegram Bot Token

1. 在Telegram中找到 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 创建新机器人
3. 按提示设置机器人名称和用户名
4. BotFather 会返回你的 Bot Token，格式类似：`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

### 2. 获取Chat ID

**方法1：使用 @userinfobot**
1. 在Telegram中找到 [@userinfobot](https://t.me/userinfobot)
2. 点击 Start 或发送任意消息
3. 机器人会返回你的 Chat ID

**方法2：使用 @getidsbot**
1. 在Telegram中找到 [@getidsbot](https://t.me/getidsbot)
2. 点击 Start 或发送任意消息
3. 机器人会返回你的 Chat ID

**方法3：手动获取**
1. 先让你的机器人发送一条消息给你（你需要先 /start 你的机器人）
2. 访问：`https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. 在返回的JSON中找到 `"chat":{"id":...}` 字段

### 3. 配置文件

编辑 `config/configs/telegram_config.json`：

```json
{
  "bot_token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
  "chat_id": "987654321"
}
```

**注意**：
- `bot_token`: 从 BotFather 获取的完整token
- `chat_id`: 你的Telegram用户ID（纯数字）

### 4. 测试配置

运行脚本测试：

```bash
cd /home/user/webapp/core_code
python3 manual_generate_prediction.py
```

如果配置正确，你会收到3条预判通知消息。

## 📱 消息格式

通知消息包含以下信息：

```
🔮 币圈行情预判 (2026-03-17)

📊 柱状图统计 (0-2点)
🟢 绿色: 12根
🔴 红色: 0根
🟡 黄色: 0根
⚪ 空白: 0根

🎯 预判信号: 诱多不参与

💬 操作建议:
🟢 全部绿色柱子，单边诱多行情，不参与操作。操作提示：不参与

⏰ 分析时间: 2026-03-16 18:03:52
```

## 🔄 自动化配置

如需每天自动生成预判并发送通知，设置crontab：

```bash
# 编辑crontab
crontab -e

# 添加定时任务（每天凌晨2:05分执行）
5 2 * * * cd /home/user/webapp/core_code && python3 manual_generate_prediction.py >> /tmp/prediction.log 2>&1
```

## ⚠️ 常见问题

### 1. 消息发送失败：404 Not Found
- **原因**: Bot Token 无效或格式错误
- **解决**: 检查 `bot_token` 配置，确保从 BotFather 复制完整

### 2. 消息发送失败：400 Bad Request: chat not found
- **原因**: Chat ID 错误或机器人未启动
- **解决**: 
  1. 在Telegram中找到你的机器人
  2. 点击 Start 或发送 `/start`
  3. 重新获取正确的 Chat ID

### 3. 消息发送失败：403 Forbidden
- **原因**: 机器人被用户阻止
- **解决**: 在Telegram中解除对机器人的阻止

### 4. 没有收到消息
- **原因**: 可能配置文件路径错误
- **解决**: 确认 `/home/user/webapp/config/configs/telegram_config.json` 文件存在且有正确权限

## 🔒 安全提示

1. **不要泄露Bot Token**：Token相当于密码，任何人拿到都可以控制你的机器人
2. **配置文件权限**：
   ```bash
   chmod 600 /home/user/webapp/config/configs/telegram_config.json
   ```
3. **不要提交到Git**：配置文件应该在 `.gitignore` 中

## 📝 相关文件

| 文件 | 说明 |
|------|------|
| `core_code/manual_generate_prediction.py` | 预判生成和TG通知脚本 |
| `config/configs/telegram_config.json` | TG配置文件 |
| `data/daily_predictions/prediction_YYYYMMDD.jsonl` | 生成的预判数据 |

## 💡 高级用法

### 自定义消息内容

编辑 `manual_generate_prediction.py` 中的消息模板（第214-227行）：

```python
message = f"""<b>🔮 自定义标题</b>

你的自定义内容...
"""
```

### 发送到多个群组

修改 `send_telegram_message()` 函数，循环发送到多个 `chat_id`：

```python
chat_ids = ["123456789", "987654321"]  # 多个chat_id
for chat_id in chat_ids:
    # 发送逻辑...
```

### 只发送1次消息

修改 `manual_generate_prediction.py` 中的循环次数（第230行）：

```python
for i in range(1):  # 改为1次
    ...
```

---

**最后更新**: 2026-03-17  
**维护人员**: AI Assistant
