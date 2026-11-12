@echo off
chcp 65001 >nul
cd /d "%~dp0"
setlocal

echo ============================================
echo   青禾 · AI 校园社区  一键启动
echo   后端 FastAPI :8000   前端 Vite :5173
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

echo [1/3] 启动后端 FastAPI ...
start "青禾-后端" /D "%~dp0backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo [2/3] 启动前端 Vite ...
start "青禾-前端" /D "%~dp0frontend" cmd /k "npm run dev"

echo [3/3] 等待服务就绪 ...
timeout /t 8 /nobreak >nul
start "" http://127.0.0.1:5173

echo.
echo 后端文档：http://127.0.0.1:8000/docs
echo 前端页面：http://127.0.0.1:5173
echo 关闭「青禾-后端」和「青禾-前端」两个窗口即可停止服务。
echo.
pause