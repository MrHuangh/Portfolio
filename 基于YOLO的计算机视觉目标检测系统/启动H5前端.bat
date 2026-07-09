@echo off
chcp 65001 >nul
title AI智能检测 - H5前端

echo ========================================
echo     AI 智能检测系统 - H5前端
echo ========================================
echo.
echo [*] 启动 HTTP 服务 (端口 3000)...
echo [*] 请在浏览器访问: http://localhost:3000
echo [*] 按 Ctrl+C 停止服务
echo.

cd /d "%~dp0frontend"
python -m http.server 3000

pause
