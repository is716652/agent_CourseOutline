@echo off
chcp 65001 >nul
title 教学大纲生成系统 - 自动化打包工具

set "PROJECT_ROOT=%~dp0"
set "VENV_PATH=%PROJECT_ROOT%.venv"
set "RELEASE_DIR=%PROJECT_ROOT%release"
set "DIST_DIR=%PROJECT_ROOT%dist"
set "BUILD_DIR=%PROJECT_ROOT%build"
set "SPEC_FILE=%PROJECT_ROOT%app.spec"

echo ========================================
echo    教学大纲生成系统 - 自动化打包工具
echo ========================================
echo.

:: 检查虚拟环境
if not exist "%VENV_PATH%\Scripts\activate.bat" (
    echo ❌ 虚拟环境未找到！
    echo 请先运行 setup_venv.bat 初始化环境
    pause
    exit /b 1
)

:: 激活虚拟环境
echo 🔄 激活虚拟环境...
call "%VENV_PATH%\Scripts\activate.bat"

:: 检查PyInstaller是否安装
echo 🔍 检查PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 📦 安装PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ PyInstaller安装失败！
        pause
        exit /b 1
    )
    echo ✅ PyInstaller安装完成
) else (
    echo ✅ PyInstaller已安装
)

:: 清理旧的构建文件
echo.
echo 🧹 清理构建文件...
if exist "%DIST_DIR%" (
    echo    删除 dist 目录...
    rmdir /s /q "%DIST_DIR%" 2>nul
)
if exist "%BUILD_DIR%" (
    echo    删除 build 目录...
    rmdir /s /q "%BUILD_DIR%" 2>nul
)
if exist "%RELEASE_DIR%" (
    echo    删除旧的 release 目录...
    rmdir /s /q "%RELEASE_DIR%" 2>nul
)

:: 创建release目录
echo 📁 创建release目录...
mkdir "%RELEASE_DIR%" 2>nul

:: 显示打包选项
echo.
echo 🎯 选择打包模式：
echo    1. 单文件模式 (推荐) - 生成单个exe文件，便于分发
echo    2. 目录模式 - 生成包含exe和依赖的目录，启动更快
echo    3. 两种模式都生成
echo.
set /p choice="请选择打包模式 (1/2/3): "

if "%choice%"=="1" goto :build_onefile
if "%choice%"=="2" goto :build_onedir
if "%choice%"=="3" goto :build_both
echo ❌ 无效选择，默认使用单文件模式
goto :build_onefile

:build_onefile
echo.
echo 🚀 开始单文件模式打包...
echo 这可能需要几分钟时间，请耐心等待...
echo.

pyinstaller "%SPEC_FILE%" ^
    --onefile ^
    --clean ^
    --noconfirm ^
    --distpath "%DIST_DIR%" ^
    --workpath "%BUILD_DIR%" ^
    --specpath "%PROJECT_ROOT%"

if errorlevel 1 (
    echo ❌ 单文件模式打包失败！
    goto :error_exit
)

echo ✅ 单文件模式打包完成
goto :copy_to_release

:build_onedir
echo.
echo 🚀 开始目录模式打包...
echo 这可能需要几分钟时间，请耐心等待...
echo.

pyinstaller "%SPEC_FILE%" ^
    --onedir ^
    --clean ^
    --noconfirm ^
    --distpath "%DIST_DIR%" ^
    --workpath "%BUILD_DIR%" ^
    --specpath "%PROJECT_ROOT%"

if errorlevel 1 (
    echo ❌ 目录模式打包失败！
    goto :error_exit
)

echo ✅ 目录模式打包完成
goto :copy_to_release

:build_both
echo.
echo 🚀 开始两种模式打包...
echo.

:: 先打包目录模式
echo 📂 1/2 目录模式打包中...
pyinstaller "%SPEC_FILE%" ^
    --onedir ^
    --clean ^
    --noconfirm ^
    --distpath "%DIST_DIR%" ^
    --workpath "%BUILD_DIR%" ^
    --specpath "%PROJECT_ROOT%"

if errorlevel 1 (
    echo ❌ 目录模式打包失败！
    goto :error_exit
)

echo ✅ 目录模式打包完成

:: 再打包单文件模式
echo.
echo 📄 2/2 单文件模式打包中...
pyinstaller "%SPEC_FILE%" ^
    --onefile ^
    --clean ^
    --noconfirm ^
    --distpath "%DIST_DIR%" ^
    --workpath "%BUILD_DIR%" ^
    --specpath "%PROJECT_ROOT%"

if errorlevel 1 (
    echo ❌ 单文件模式打包失败！
    goto :error_exit
)

echo ✅ 两种模式打包都完成
goto :copy_to_release

:copy_to_release
echo.
echo 📦 复制文件到release目录...

:: 创建发布目录结构
mkdir "%RELEASE_DIR%\单文件版本" 2>nul
mkdir "%RELEASE_DIR%\目录版本" 2>nul
mkdir "%RELEASE_DIR%\配置文件" 2>nul
mkdir "%RELEASE_DIR%\使用说明" 2>nul

:: 复制单文件版本
if exist "%DIST_DIR%\教学大纲生成系统.exe" (
    echo    复制单文件版本...
    copy "%DIST_DIR%\教学大纲生成系统.exe" "%RELEASE_DIR%\单文件版本\" >nul
)

:: 复制目录版本
if exist "%DIST_DIR%\教学大纲生成系统" (
    echo    复制目录版本...
    xcopy "%DIST_DIR%\教学大纲生成系统" "%RELEASE_DIR%\目录版本\教学大纲生成系统\" /e /i /h /y >nul
)

:: 复制配置文件
echo    复制配置文件...
copy "%PROJECT_ROOT%config.ini" "%RELEASE_DIR%\配置文件\" >nul 2>&1

:: 创建使用说明
echo 📝 生成使用说明...
(
echo # 教学大纲生成系统 - 使用说明
echo.
echo ## 🚀 快速开始
echo.
echo ### 单文件版本 ^(推荐^)
echo 1. 运行 `单文件版本\教学大纲生成系统.exe`
echo 2. 程序会自动检测可用端口并启动
echo 3. 浏览器会自动打开到系统页面
echo 4. 如果浏览器未自动打开，请手动访问显示的地址
echo.
echo ### 目录版本
echo 1. 进入 `目录版本\教学大纲生成系统\` 目录
echo 2. 运行 `教学大纲生成系统.exe`
echo 3. 其他步骤同单文件版本
echo.
echo ## ⚙️ 配置说明
echo.
echo ### 端口配置
echo - 编辑 `配置文件\config.ini` 可修改端口设置
echo - 默认端口：5000
echo - 备用端口：5001, 5002, 5003, 5004, 5005
echo - 如果所有预设端口被占用，系统会自动分配可用端口
echo.
echo ### 配置参数
echo ```ini
echo [server]
echo host = 127.0.0.1          # 服务器地址
echo port = 5000               # 主端口
echo backup_ports = 5001,5002,5003,5004,5005  # 备用端口
echo debug = false             # 调试模式
echo.
echo [app]
echo auto_open_browser = true  # 自动打开浏览器
echo default_page = /teaching-outline  # 默认页面
echo ```
echo.
echo ## 📁 文件说明
echo.
echo - `单文件版本\`: 包含独立的exe文件，双击即可运行
echo - `目录版本\`: 包含exe和依赖文件的完整目录
echo - `配置文件\`: 系统配置文件，可自定义端口等设置
echo - `使用说明\`: 本文档和其他说明文件
echo.
echo ## 🔧 故障排除
echo.
echo ### 端口被占用
echo - 系统会自动尝试备用端口
echo - 可在配置文件中修改端口设置
echo - 查看控制台输出获取实际使用的端口
echo.
echo ### 无法启动
echo - 检查是否有杀毒软件拦截
echo - 尝试以管理员权限运行
echo - 检查防火墙设置
echo.
echo ### 浏览器未自动打开
echo - 手动访问控制台显示的地址
echo - 通常为：http://127.0.0.1:5000/teaching-outline
echo.
echo ## 🛡️ 安全说明
echo.
echo - 系统仅在本地运行，不会向外部发送数据
echo - 生成的文档保存在程序目录的 `output` 文件夹中
echo - 配置信息存储在本地配置文件中
echo.
echo ## 📞 技术支持
echo.
echo 如遇问题，请：
echo 1. 查看控制台输出的错误信息
echo 2. 检查配置文件设置
echo 3. 确保网络连接正常
echo 4. 验证AI API密钥配置
echo.
echo ---
echo 版本：1.0.0
echo 构建时间：%date% %time%
) > "%RELEASE_DIR%\使用说明\README.md"

:: 创建快速启动说明
(
echo # 快速启动指南
echo.
echo ## 🎯 推荐使用方式
echo.
echo 1. **运行程序**
echo    - 单文件版本：双击 `单文件版本\教学大纲生成系统.exe`
echo    - 目录版本：进入 `目录版本\教学大纲生成系统\` 后双击 `教学大纲生成系统.exe`
echo.
echo 2. **程序启动**
echo    - 控制台窗口会显示启动信息
echo    - 程序会自动检测并使用可用端口
echo    - 浏览器会自动打开到系统页面
echo.
echo 3. **开始使用**
echo    - 在网页中配置AI API密钥
echo    - 输入课程信息
echo    - 点击生成即可获得Word文档
echo.
echo ## 🔧 自定义配置
echo.
echo 如需修改端口或其他设置：
echo 1. 复制 `配置文件\config.ini` 到程序目录
echo 2. 编辑配置文件
echo 3. 重新启动程序
echo.
echo ## ⚡ 注意事项
echo.
echo - 首次运行可能需要几秒钟启动时间
echo - 保持控制台窗口开启，关闭会停止服务
echo - 生成的文档默认保存在 `output` 目录
echo - 支持同时运行多个实例（使用不同端口）
) > "%RELEASE_DIR%\使用说明\快速启动指南.md"

:: 显示结果信息
echo.
echo ========================================
echo            🎉 打包完成！
echo ========================================
echo.
echo 📊 构建结果:
if exist "%RELEASE_DIR%\单文件版本\教学大纲生成系统.exe" (
    echo ✅ 单文件版本: %RELEASE_DIR%\单文件版本\
)
if exist "%RELEASE_DIR%\目录版本\教学大纲生成系统" (
    echo ✅ 目录版本: %RELEASE_DIR%\目录版本\
)
echo ✅ 配置文件: %RELEASE_DIR%\配置文件\
echo ✅ 使用说明: %RELEASE_DIR%\使用说明\
echo.
echo 📂 发布目录: %RELEASE_DIR%
echo.
echo 🚀 测试建议:
echo 1. 进入release目录
echo 2. 运行单文件版本测试基本功能
echo 3. 测试端口配置和自动打开浏览器功能
echo 4. 验证文档生成功能
echo.

:: 询问是否立即测试
set /p test_choice="是否现在测试打包结果？ (Y/N): "
if /i "%test_choice%"=="Y" (
    echo.
    echo 🧪 启动测试...
    if exist "%RELEASE_DIR%\单文件版本\教学大纲生成系统.exe" (
        start "" "%RELEASE_DIR%\单文件版本\教学大纲生成系统.exe"
    ) else if exist "%RELEASE_DIR%\目录版本\教学大纲生成系统\教学大纲生成系统.exe" (
        start "" "%RELEASE_DIR%\目录版本\教学大纲生成系统\教学大纲生成系统.exe"
    ) else (
        echo ❌ 未找到可执行文件
    )
)

:: 询问是否打开release目录
set /p open_choice="是否打开release目录？ (Y/N): "
if /i "%open_choice%"=="Y" (
    start "" "%RELEASE_DIR%"
)

goto :end

:error_exit
echo.
echo ❌ 打包过程中出现错误！
echo.
echo 🔧 可能的解决方案：
echo 1. 检查虚拟环境是否正确激活
echo 2. 确保所有依赖都已正确安装
echo 3. 检查磁盘空间是否充足
echo 4. 查看上方的详细错误信息
echo 5. 尝试先运行 setup_venv.bat 修复环境
echo.
pause
exit /b 1

:end
echo.
echo 👋 打包完成！
pause