# ABC一键平仓按钮显示问题 - 修复报告

## 🐛 问题描述

用户反馈：在 ABC 持仓追踪页面看不到"一键平仓"按钮

## 🔍 问题原因

**文件路径错误**：
- ❌ 修改了根目录的 `abc_position.html` 
- ✅ Flask 实际使用的是 `templates/abc_position.html`

**Flask 路由配置**：
```python
@app.route('/abc-position')
def abc_position_page():
    return render_template('abc_position.html')  # 使用 templates/ 目录
```

## 🔧 修复方案

将修改后的文件复制到正确的位置：

```bash
cp abc_position.html templates/abc_position.html
pm2 restart flask-app
```

## ✅ 验证结果

```bash
curl -s 'http://localhost:9002/abc-position' | grep "一键平仓"
# 输出：一键平仓 (4次，对应4个账户)
```

## 📝 Git 提交

```
commit 056ac7f
Fix: Copy one-click close all button to templates directory
```

## 🌐 访问链接

https://9002-iwyspq7c2ufr5cnosf8lb-82b888ba.sandbox.novita.ai/abc-position

## 🎯 修复状态

✅ **已完成并部署**

现在每个账户卡片都应该显示：
1. ⚙️ ABC设置 按钮（紫色）
2. 🔴 一键平仓 按钮（红色，新增）

**建议**：请强制刷新浏览器（Ctrl+Shift+R）清除缓存后查看。

---

**修复时间**: 2026-03-19 15:50 UTC+8  
**Flask 状态**: Online (PID 33537)
