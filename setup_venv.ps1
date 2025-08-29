# 教学大纲生成系统 - 虚拟环境检查与修复工具 (PowerShell版本)
# 设置控制台编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "教学大纲生成系统 - 环境修复工具"

# 设置项目路径
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPath = Join-Path $ProjectRoot ".venv"
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"
$PythonScript = Join-Path $ProjectRoot "run.py"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  教学大纲生成系统 - 虚拟环境检查与修复" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "🔍 检查项目环境..." -ForegroundColor Yellow
Write-Host "项目路径: $ProjectRoot" -ForegroundColor Gray
Write-Host "虚拟环境路径: $VenvPath" -ForegroundColor Gray
Write-Host ""

# 检查Python是否安装
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python未安装"
    }
} catch {
    Write-Host "❌ 错误: 未检测到Python环境！" -ForegroundColor Red
    Write-Host "请先安装Python 3.10或更高版本" -ForegroundColor Yellow
    Write-Host "下载地址: https://www.python.org/downloads/" -ForegroundColor Blue
    Read-Host "按回车键退出"
    exit 1
}

# 检查Python版本
try {
    $versionOutput = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    $version = [decimal]$versionOutput
    if ($version -lt 3.10) {
        Write-Host "⚠️  警告: Python版本过低 ($versionOutput)，建议使用3.10或更高版本" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  无法检测Python版本" -ForegroundColor Yellow
}

Write-Host ""

# 检查requirements.txt
if (-not (Test-Path $RequirementsFile)) {
    Write-Host "❌ 错误: 未找到requirements.txt文件！" -ForegroundColor Red
    Write-Host "请确保在项目根目录执行此脚本" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

# 检查虚拟环境路径一致性
$needRecreate = $false
$needReinstall = $false
$PyvenvCfg = Join-Path $VenvPath "pyvenv.cfg"

if (Test-Path $VenvPath) {
    Write-Host "🔍 检测到现有虚拟环境，正在验证..." -ForegroundColor Yellow
    
    # 检查路径一致性
    if (Test-Path $PyvenvCfg) {
        Write-Host "🔍 检查虚拟环境路径配置..." -ForegroundColor Yellow
        $cfgContent = Get-Content $PyvenvCfg
        $executableLine = $cfgContent | Where-Object { $_ -match "^executable\s*=" }
        
        if ($executableLine) {
            $cfgPythonPath = ($executableLine -split "=", 2)[1].Trim()
            if ($cfgPythonPath -ne $currentPython) {
                Write-Host "⚠️  检测到Python路径不一致，准备重新创建虚拟环境..." -ForegroundColor Yellow
                Write-Host "配置文件中的Python路径: $cfgPythonPath" -ForegroundColor Red
                Write-Host "当前系统Python路径: $currentPython" -ForegroundColor Green
                $needRecreate = $true
            }
        }
    }
    
    # 如果路径一致，继续检查其他问题
    if (-not $needRecreate) {
        # 检查激活脚本是否存在
        $activateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
        if (-not (Test-Path $activateScript)) {
            Write-Host "⚠️  虚拟环境激活脚本缺失" -ForegroundColor Yellow
            $needRecreate = $true
        } else {
            # 尝试激活虚拟环境
            try {
                & $activateScript -ErrorAction Stop
                Write-Host "✅ 虚拟环境激活成功" -ForegroundColor Green
                
                # 检查关键依赖
                Write-Host "🔍 检查依赖包..." -ForegroundColor Yellow
                $checkResult = python -c "import flask, requests; print('OK')" 2>&1
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "⚠️  关键依赖缺失，准备重新安装..." -ForegroundColor Yellow
                    $needReinstall = $true
                } else {
                    Write-Host "✅ 关键依赖检查通过" -ForegroundColor Green
                }
                
                # 检查依赖完整性
                if (-not $needReinstall) {
                    Write-Host "🔍 验证依赖完整性..." -ForegroundColor Yellow
                    $pipCheck = pip check 2>&1
                    if ($LASTEXITCODE -ne 0) {
                        Write-Host "⚠️  依赖版本冲突，准备重新安装..." -ForegroundColor Yellow
                        $needReinstall = $true
                    } else {
                        Write-Host "✅ 依赖完整性验证通过" -ForegroundColor Green
                    }
                }
                
            } catch {
                Write-Host "⚠️  虚拟环境损坏，准备重新创建..." -ForegroundColor Yellow
                $needRecreate = $true
            }
        }
    }
} else {
    Write-Host "📦 未检测到虚拟环境，准备创建..." -ForegroundColor Yellow
    $needRecreate = $true
}

# 重新创建虚拟环境
if ($needRecreate) {
    Write-Host ""
    if (Test-Path $VenvPath) {
        Write-Host "🗑️  删除损坏的虚拟环境..." -ForegroundColor Yellow
        try {
            Remove-Item -Path $VenvPath -Recurse -Force -ErrorAction Stop
            Write-Host "✅ 旧虚拟环境已删除" -ForegroundColor Green
        } catch {
            Write-Host "❌ 无法删除虚拟环境目录，请手动删除后重试" -ForegroundColor Red
            Write-Host "路径: $VenvPath" -ForegroundColor Gray
            Read-Host "按回车键退出"
            exit 1
        }
    }
    
    Write-Host "🚀 创建新的虚拟环境..." -ForegroundColor Yellow
    $createResult = python -m venv $VenvPath 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 虚拟环境创建失败！" -ForegroundColor Red
        Write-Host "错误信息: $createResult" -ForegroundColor Gray
        Write-Host "可能原因：" -ForegroundColor Yellow
        Write-Host "1. Python版本过低（需要3.10+）" -ForegroundColor Gray
        Write-Host "2. 磁盘空间不足" -ForegroundColor Gray
        Write-Host "3. 权限问题" -ForegroundColor Gray
        Read-Host "按回车键退出"
        exit 1
    }
    
    Write-Host "✅ 虚拟环境创建成功！" -ForegroundColor Green
    $needReinstall = $true
}

# 安装依赖
if ($needReinstall) {
    Write-Host ""
    Write-Host "📦 激活虚拟环境..." -ForegroundColor Yellow
    
    $activateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
    try {
        & $activateScript -ErrorAction Stop
        Write-Host "✅ 虚拟环境激活成功" -ForegroundColor Green
    } catch {
        Write-Host "❌ 虚拟环境激活失败！" -ForegroundColor Red
        Read-Host "按回车键退出"
        exit 1
    }
    
    Write-Host ""
    Write-Host "📥 升级pip到最新版本..." -ForegroundColor Yellow
    $pipUpgrade = python -m pip install --upgrade pip 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ pip升级完成" -ForegroundColor Green
    } else {
        Write-Host "⚠️  pip升级失败，继续安装依赖..." -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "📥 安装项目依赖..." -ForegroundColor Yellow
    Write-Host "这可能需要几分钟时间，请耐心等待..." -ForegroundColor Gray
    
    $installResult = pip install -r $RequirementsFile 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 依赖安装失败！" -ForegroundColor Red
        Write-Host "错误信息: $installResult" -ForegroundColor Gray
        Write-Host ""
        Write-Host "🔧 尝试修复方案：" -ForegroundColor Yellow
        Write-Host "1. 检查网络连接" -ForegroundColor Gray
        Write-Host "2. 使用国内镜像源：" -ForegroundColor Gray
        Write-Host "   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/" -ForegroundColor Blue
        Write-Host "3. 单独安装失败的包" -ForegroundColor Gray
        Read-Host "按回车键退出"
        exit 1
    }
    
    Write-Host "✅ 依赖安装完成！" -ForegroundColor Green
}

# 测试应用
Write-Host ""
Write-Host "🧪 测试应用启动..." -ForegroundColor Yellow

if (-not (Test-Path $PythonScript)) {
    Write-Host "❌ 未找到run.py文件！" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 检查主要模块
Write-Host "🔍 检查主要模块..." -ForegroundColor Yellow
$moduleCheck = python -c "from app import create_app; print('OK')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 应用模块导入成功" -ForegroundColor Green
} else {
    Write-Host "❌ 应用模块导入失败！" -ForegroundColor Red
    Write-Host "错误信息: $moduleCheck" -ForegroundColor Gray
    Write-Host "请检查代码是否有语法错误" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

# 显示成功信息
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "           🎉 环境设置完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$pythonVersionFull = python --version
Write-Host "✅ Python版本: $pythonVersionFull" -ForegroundColor Green
Write-Host ""
Write-Host "✅ 虚拟环境路径: $VenvPath" -ForegroundColor Green
Write-Host ""
Write-Host "✅ 已安装的关键依赖包:" -ForegroundColor Green
$packages = pip list | Select-String "Flask|requests|python-docx|Jinja2"
$packages | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
Write-Host ""

Write-Host "🚀 启动应用命令:" -ForegroundColor Yellow
Write-Host "   1. 激活虚拟环境: $VenvPath\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "   2. 启动应用: python run.py" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 或者直接运行: start_app.bat" -ForegroundColor Blue
Write-Host ""

# 询问是否启动应用
$choice = Read-Host "是否现在启动应用？ (Y/N)"
if ($choice -match "^[Yy]") {
    Write-Host ""
    Write-Host "🚀 正在启动应用..." -ForegroundColor Yellow
    Write-Host "应用将在 http://127.0.0.1:5000 启动" -ForegroundColor Blue
    Write-Host "按 Ctrl+C 停止应用" -ForegroundColor Gray
    Write-Host ""
    
    & python $PythonScript
} else {
    Write-Host ""
    Write-Host "👋 设置完成！您可以随时运行 python run.py 启动应用" -ForegroundColor Green
}

Read-Host "按回车键退出"