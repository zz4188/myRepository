@echo off
chcp 65001 >nul
echo ====================================
echo TicketMaster
echo Windows 抢票软件
echo ====================================
echo.

cd /d "%~dp0"

python main.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 程序运行失败
    echo 请确保已安装 Python 和所有依赖包
    echo.
    echo 运行 install.bat 安装依赖
    echo.
    pause
)
