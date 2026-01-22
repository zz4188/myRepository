@echo off
chcp 65001 >nul
echo ====================================
echo TicketMaster 安装脚本
echo ====================================
echo.

echo 步骤 1: 检查 Python 环境...
python --version
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo.

echo 步骤 2: 升级 pip...
python -m pip install --upgrade pip
echo.

echo 步骤 3: 安装依赖包...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo.

echo 步骤 4: 安装应用程序...
python setup.py install
if %errorlevel% neq 0 (
    echo [警告] 应用安装失败，但不影响使用
)
echo.

echo ====================================
echo 安装完成！
echo ====================================
echo.
echo 运行方式:
echo   1. 双击运行 run.bat
echo   2. 或执行命令: python main.py
echo.
echo 打包说明:
echo   运行 build_exe.py 可将程序打包为 exe 文件
echo.

pause
