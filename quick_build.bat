@echo off
chcp 65001 >nul
title 快速打包工具

echo 🚀 教学大纲生成系统 - 快速打包
echo.

:: 激活虚拟环境
call .venv\Scripts\activate.bat

:: 检查PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 📦 安装PyInstaller...
    pip install pyinstaller
)

:: 清理和打包
echo 🧹 清理旧文件...
rmdir /s /q dist 2>nul
rmdir /s /q build 2>nul

echo 📦 开始打包...
pyinstaller app.spec --onefile --clean --noconfirm

if errorlevel 1 (
    echo ❌ 打包失败！
    pause
    exit /b 1
)

:: 创建release目录
if not exist release mkdir release
if not exist release\单文件版本 mkdir release\单文件版本

:: 复制文件
copy dist\教学大纲生成系统.exe release\单文件版本\ >nul
copy config.ini release\单文件版本\ >nul

echo ✅ 打包完成！
echo 📂 文件位置: release\单文件版本\教学大纲生成系统.exe
echo.

set /p choice="是否测试运行？ (Y/N): "
if /i "%choice%"=="Y" (
    start "" "release\单文件版本\教学大纲生成系统.exe"
)

pause