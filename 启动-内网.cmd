@echo off
chcp 65001 >nul
cd /d "%~dp0"
setlocal enabledelayedexpansion

echo ============================================
echo   青禾 · AI 校园社区  内网演示启动
echo   后端 :8000（0.0.0.0）  前端 :5173（0.0.0.0）
echo ============================================
echo.

if not exist "%~dp0backend\.venv\Scripts\python.exe" (
  echo [X] 未找到 Python 虚拟环境，请先双击「一键安装.cmd」
  pause
  exit /b 1
)
if not exist "%~dp0frontend\node_modules" (
  echo [X] 未找到前端依赖，请先双击「一键安装.cmd」
  pause
  exit /b 1
)

rem ---- 取第一个 IPv4 地址作为内网访问地址 ----
set "MYIP="
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  set "T=%%a"
  set "T=!T: =!"
  if not defined MYIP set "MYIP=!T!"
)
if not defined MYIP set "MYIP=127.0.0.1"

echo [1/3] 启动后端 FastAPI ...
start "青禾-后端" /D "%~dp0backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo [2/3] 启动前端 Vite ...
start "青禾-前端" /D "%~dp0frontend" cmd /k "npm run dev -- --host 0.0.0.0"

echo [3/3] 等待服务就绪 ...
timeout /t 10 /nobreak >nul

echo.
echo   本机访问：  http://127.0.0.1:5173
echo   内网访问：  http://%MYIP%:5173    ^<== 发给同一网段的同学
echo   接口文档：  http://%MYIP%:8000/docs
echo.
echo   同一网段的电脑打不开时，用【管理员】PowerShell 执行：
echo     New-NetFirewallRule -DisplayName "青禾-5173" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5173
echo     New-NetFirewallRule -DisplayName "青禾-8000" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000
echo.
echo   关闭「青禾-后端」「青禾-前端」两个窗口即可停止服务。
echo.

start "" http://127.0.0.1:5173
pause
