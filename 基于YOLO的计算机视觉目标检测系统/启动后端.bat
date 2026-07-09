@echo off
chcp 65001 >nul
title AI智能检测 - 后端服务

echo ========================================
echo     AI 智能检测系统 - 后端服务
echo ========================================
echo.

:: 进入后端目录
cd /d "%~dp0backend"

:: 激活conda环境
call conda activate yolov11 2>nul
if %errorlevel% neq 0 (
    echo [×] 未找到 conda 环境 "yolov11"
    echo.
    echo 请先运行 "一键部署环境.bat" 创建环境
    echo 或手动执行:
    echo   conda activate yolov11
    echo   python server.py
    pause
    exit /b
)

echo [✓] 已激活虚拟环境: yolov11
echo [*] 加载模型中，请稍候...
echo.

python server.py

pause
