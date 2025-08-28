# -*- mode: python ; coding: utf-8 -*-
# 教学大纲生成系统 PyInstaller 配置文件

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 项目根目录
block_cipher = None
project_root = os.path.abspath('.')

# 收集所有数据文件
datas = [
    # 配置文件
    ('config.ini', '.'),
    # Flask模板文件
    ('app/web_templates', 'app/web_templates'),
    # 静态文件
    ('app/static', 'app/static'),
    # Word模板文件
    ('app/templates', 'app/templates'),
    # 其他数据文件目录
    ('output', 'output'),
    ('uploads', 'uploads'),
]

# 收集所有隐藏导入
hiddenimports = [
    'app',
    'app.routes',
    'app.models',
    'app.services',
    'app.services.teaching_outline_generator',
    'app.services.word_generator',
    'app.utils',
    'app.utils.exceptions',
    'flask',
    'flask.templating',
    'flask.json',
    'requests',
    'docx',
    'docx.shared',
    'docx.enum.text',
    'docx.enum.table',
    'jinja2',
    'jinja2.ext',
    'configparser',
    'webbrowser',
    'threading',
    'socket',
    'json',
    'logging',
    'datetime',
    'os',
    'sys',
    'time',
    're',
    'urllib',
    'urllib.parse',
    'uuid',
    'base64',
    'hashlib',
]

# 收集python-docx的数据文件
try:
    docx_datas = collect_data_files('docx')
    datas.extend(docx_datas)
except:
    pass

# 收集jinja2的数据文件
try:
    jinja2_datas = collect_data_files('jinja2')
    datas.extend(jinja2_datas)
except:
    pass

# 分析配置
a = Analysis(
    ['run.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'tensorflow',
        'torch',
        'pygame',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 处理重复文件
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 单文件模式配置
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='教学大纲生成系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保留控制台窗口以显示启动信息
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',  # 可选：版本信息文件
    icon='app_icon.ico',  # 可选：应用图标
)

# 收集模式配置（生成dist目录）
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='教学大纲生成系统_收集模式',
)

# 目录模式配置
exe_dir = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='教学大纲生成系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 配置文件说明
"""
PyInstaller 打包配置说明：

1. 单文件模式 (onefile): 
   - 所有文件打包成一个exe文件
   - 启动较慢，但分发简单
   - 使用: pyinstaller app.spec --onefile

2. 目录模式 (onedir):
   - 生成包含exe和依赖文件的目录
   - 启动较快，但需要分发整个目录
   - 使用: pyinstaller app.spec --onedir

3. 数据文件包含：
   - 模板文件：Flask HTML模板和Word模板
   - 静态文件：CSS、JS、图片等
   - 配置文件：config.ini
   - 输出目录：output、uploads

4. 隐藏导入：
   - 包含所有必要的Python模块
   - Flask相关模块
   - docx文档处理模块
   - 其他依赖模块

5. 排除模块：
   - 排除不需要的大型模块以减小文件大小
   - GUI框架、科学计算库等

6. 注意事项：
   - 确保所有模板文件和静态文件都被包含
   - 测试打包后的程序功能是否正常
   - 检查配置文件是否正确加载
"""