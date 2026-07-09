@echo off
chcp 65001 >nul
title AI智能检测 - 环境部署

echo ========================================
echo     AI 智能检测系统 - 环境一键部署
echo ========================================
echo.
echo 此脚本将:
echo   1. 创建 conda 虚拟环境 (Python 3.9)
echo   2. 安装 PyTorch (CPU版)
echo   3. 安装 YOLOv11 + Flask 依赖
echo.
echo 如需 GPU 加速，请手动安装 CUDA 版 PyTorch
echo 详见 使用说明.txt
echo.
pause

echo.
echo [Step 1/4] 创建 conda 环境...
call conda create --name yolov11 python=3.9 -y
if %errorlevel% neq 0 (
    echo [×] 创建环境失败
    pause
    exit /b
)

echo.
echo [Step 2/4] 安装 PyTorch (CPU版，约 200MB)...
call conda activate yolov11
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
if %errorlevel% neq 0 (
    echo [×] PyTorch 安装失败
    pause
    exit /b
)

echo.
echo [Step 3/4] 安装 ultralytics (YOLOv11)...
pip install ultralytics
if %errorlevel% neq 0 (
    echo [×] ultralytics 安装失败
    pause
    exit /b
)

echo.
echo [Step 4/4] 安装 Flask 服务...
pip install flask flask-cors
if %errorlevel% neq 0 (
    echo [×] Flask 安装失败
    pause
    exit /b
)

echo.
echo ========================================
echo     ✅ 环境部署完成！
echo ========================================
echo.
echo 现在可以运行 "启动后端.bat" 启动服务
echo.

pause
