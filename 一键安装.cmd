@echo off
chcp 65001 >nul
cd /d "%~dp0"
setlocal

echo ============================================
echo   青禾 · AI 校园社区  一键安装
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [X] 未检测到 python，请先安装 Python 3.10+ 并勾选 Add to PATH
  pause
  exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
  echo [X] 未检测到 npm，请先安装 Node.js 18+ 并加入 PATH
  pause
  exit /b 1
)

echo [1/3] 创建 Python 虚拟环境并安装后端依赖...
cd /d "%~dp0backend"
if not exist ".venv\Scripts\python.exe" python -m venv .venv
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [X] 后端依赖安装失败，请检查网络或 Python 版本（建议 3.11）
  pause
  exit /b 1
)

echo.
echo [2/3] 安装前端依赖...
cd /d "%~dp0frontend"
call npm install
if errorlevel 1 (
  echo [X] 前端依赖安装失败，请检查 Node.js（建议 18+）
  pause
  exit /b 1
)

echo.
echo [3/3] 初始化数据库（建库 + 建表 + 演示数据）...
cd /d "%~dp0backend"
".venv\Scripts\python.exe" scripts\init_db.py
if errorlevel 1 (
  echo [X] 数据库初始化失败，请检查 backend\.env 中的 MySQL 配置
  pause
  exit /b 1
)

cd /d "%~dp0"
echo.
echo 安装完成。双击「启动.cmd」即可运行。
pause