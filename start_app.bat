@echo off
chcp 65001 >nul
title 教学大纲生成系统

:: 设置项目根目录
set "PROJECT_ROOT=%~dp0"
set "VENV_PATH=%PROJECT_ROOT%.venv"

echo ========================================
echo      教学大纲生成系统 - 快速启动
echo ========================================
echo.

:: 检查虚拟环境是否存在
if not exist "%VENV_PATH%\Scripts\activate.bat" (
    echo ❌ 虚拟环境未找到！
    echo 请先运行 setup_venv.bat 初始化环境
    pause
    exit /b 1
)

:: 激活虚拟环境
echo 🔄 激活虚拟环境...
call "%VENV_PATH%\Scripts\activate.bat"

:: 启动应用
echo 🚀 启动教学大纲生成系统...
echo.
echo 📱 应用地址: http://127.0.0.1:5000/teaching-outline
echo 🛑 按 Ctrl+C 停止应用
echo.

python run.py