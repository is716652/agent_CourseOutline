@echo off
chcp 65001 >nul
title 教学大纲生成系统 - 虚拟环境检查与修复工具
echo ========================================
echo   教学大纲生成系统 - 虚拟环境检查与修复
echo ========================================
echo.

:: 设置项目根目录为当前脚本所在目录
set "PROJECT_ROOT=%~dp0"
set "VENV_PATH=%PROJECT_ROOT%.venv"
set "REQUIREMENTS_FILE=%PROJECT_ROOT%requirements.txt"
set "PYTHON_SCRIPT=%PROJECT_ROOT%run.py"
set "PYVENV_CFG=%VENV_PATH%\pyvenv.cfg"

echo 🔍 检查项目环境...
echo 项目路径: %PROJECT_ROOT%
echo 虚拟环境路径: %VENV_PATH%
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未检测到Python环境！
    echo 请先安装Python 3.10或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 显示Python版本信息
echo ✅ Python版本信息:
python --version
for /f "delims=" %%i in ('python -c "import sys; print(sys.executable)"') do set "CURRENT_PYTHON=%%i"
echo Python可执行文件路径: %CURRENT_PYTHON%
echo.

:: 检查requirements.txt是否存在
if not exist "%REQUIREMENTS_FILE%" (
    echo ❌ 错误: 未找到requirements.txt文件！
    echo 请确保在项目根目录执行此脚本
    pause
    exit /b 1
)

:: 检查虚拟环境是否存在并验证路径一致性
if exist "%VENV_PATH%" (
    echo 🔍 检测到现有虚拟环境，正在验证...
    
    :: 检查路径一致性
    if exist "%PYVENV_CFG%" (
        echo 🔍 检查虚拟环境路径配置...
        findstr /C:"executable" "%PYVENV_CFG%" | findstr /C:"%CURRENT_PYTHON%" >nul
        if errorlevel 1 (
            echo ⚠️  检测到Python路径不一致，准备重新创建虚拟环境...
            goto :recreate_venv
        )
    )
    
    :: 尝试激活虚拟环境并检查是否正常工作
    call "%VENV_PATH%\Scripts\activate.bat" >nul 2>&1
    if errorlevel 1 (
        echo ⚠️  虚拟环境损坏或路径无效，准备重新创建...
        goto :recreate_venv
    )
    
    :: 检查关键依赖是否存在
    echo 🔍 检查依赖包...
    python -c "import flask, requests" >nul 2>&1
    if errorlevel 1 (
        echo ⚠️  依赖包缺失或损坏，准备重新安装...
        goto :install_deps
    )
    
    :: 检查依赖版本是否匹配
    echo 🔍 验证依赖版本...
    pip check >nul 2>&1
    if errorlevel 1 (
        echo ⚠️  依赖版本冲突，准备重新安装...
        goto :install_deps
    )
    
    echo ✅ 虚拟环境验证通过！
    goto :test_app
) else (
    echo 📦 未检测到虚拟环境，准备创建...
    goto :create_venv
)

:recreate_venv
echo.
echo 🗑️  删除损坏的虚拟环境...
if exist "%VENV_PATH%" (
    rmdir /s /q "%VENV_PATH%" 2>nul
    if exist "%VENV_PATH%" (
        echo ❌ 无法删除虚拟环境目录，请手动删除后重试
        pause
        exit /b 1
    )
)

:create_venv
echo.
echo 🚀 使用当前Python创建新虚拟环境...
echo 执行命令: "%CURRENT_PYTHON%" -m venv "%VENV_PATH%"
"%CURRENT_PYTHON%" -m venv "%VENV_PATH%"
if errorlevel 1 (
    echo ❌ 虚拟环境创建失败！
    echo 可能原因：
    echo 1. Python版本过低（需要3.10+）
    echo 2. 磁盘空间不足
    echo 3. 权限问题
    pause
    exit /b 1
)

echo ✅ 虚拟环境创建成功！

:: 显示新的配置
if exist "%PYVENV_CFG%" (
    echo 📋 新虚拟环境配置:
    echo ----------------------------------------
    type "%PYVENV_CFG%"
    echo ----------------------------------------
    echo.
)

:install_deps
echo.
echo 📦 激活虚拟环境...
call "%VENV_PATH%\Scripts\activate.bat"
if errorlevel 1 (
    echo ❌ 虚拟环境激活失败！
    pause
    exit /b 1
)

echo.
echo 📥 升级pip到最新版本...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ⚠️  pip升级失败，继续安装依赖...
)

echo.
echo 📥 安装项目依赖...
echo 这可能需要几分钟时间，请耐心等待...
pip install -r "%REQUIREMENTS_FILE%"
if errorlevel 1 (
    echo ❌ 依赖安装失败！
    echo 可能原因：
    echo 1. 网络连接问题
    echo 2. 某些包在当前系统不可用
    echo 3. 权限问题
    echo.
    echo 🔧 尝试修复方案：
    echo 1. 检查网络连接
    echo 2. 使用国内镜像源：
    echo    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
    pause
    exit /b 1
)

echo ✅ 依赖安装完成！

:test_app
echo.
echo 🧪 测试应用启动...
:: 设置测试环境变量
set FLASK_ENV=development
set FLASK_DEBUG=0

:: 检查run.py是否存在
if not exist "%PYTHON_SCRIPT%" (
    echo ❌ 未找到run.py文件！
    pause
    exit /b 1
)

:: 尝试导入主要模块
echo 🔍 检查主要模块...
python -c "from app import create_app; print('✅ 应用模块导入成功')" 2>nul
if errorlevel 1 (
    echo ❌ 应用模块导入失败！
    echo 请检查代码是否有语法错误
    pause
    exit /b 1
)

echo.
echo ========================================
echo           🎉 环境设置完成！
echo ========================================
echo.
echo ✅ Python版本: 
python --version
echo.
echo ✅ 虚拟环境路径: %VENV_PATH%
echo.
echo ✅ 已安装的关键依赖包:
pip list | findstr "Flask\|requests\|python-docx\|Jinja2"
echo.
echo 🚀 启动应用命令:
echo    1. 激活虚拟环境: %VENV_PATH%\Scripts\activate.bat
echo    2. 启动应用: python run.py
echo.
echo 💡 或者直接运行: start_app.bat
echo.

:: 询问是否立即启动应用
echo 是否现在启动应用？ (Y/N)
set /p choice="请选择: "
if /i "%choice%"=="Y" (
    echo.
    echo 🚀 正在启动应用...
    echo 应用将在 http://127.0.0.1:5000 启动
    echo 按 Ctrl+C 停止应用
    echo.
    python "%PYTHON_SCRIPT%"
) else (
    echo.
    echo 👋 设置完成！您可以随时运行 python run.py 启动应用
)

echo.
pause