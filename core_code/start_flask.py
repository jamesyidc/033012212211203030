#!/usr/bin/env python3
"""
Flask App Launcher - 启动包装器
修正路径并启动Flask应用
"""
import sys
import os

# 设置正确的路径
webapp_root = '/home/user/webapp'
os.chdir(webapp_root)
sys.path.insert(0, webapp_root)
sys.path.insert(0, os.path.join(webapp_root, 'source_code'))
sys.path.insert(0, os.path.join(webapp_root, 'sr_v2'))
sys.path.insert(0, os.path.join(webapp_root, 'escape_v2'))
sys.path.insert(0, os.path.join(webapp_root, 'code', 'python'))

# 创建一个临时的app.py副本，修正BASE_DIR
app_content = open('/home/user/webapp/code/python/app.py', 'r', encoding='utf-8').read()

# 替换BASE_DIR的计算
app_content = app_content.replace(
    "BASE_DIR = Path(__file__).parent.parent",
    "BASE_DIR = Path('/home/user/webapp')"
)

# 创建临时文件并执行
import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=webapp_root) as f:
    f.write(app_content)
    temp_file = f.name

try:
    # 执行修正后的应用
    exec(compile(open(temp_file, 'r', encoding='utf-8').read(), temp_file, 'exec'), {'__name__': '__main__'})
finally:
    # 清理临时文件
    if os.path.exists(temp_file):
        os.unlink(temp_file)
