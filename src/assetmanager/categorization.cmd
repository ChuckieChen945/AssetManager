@echo off
setlocal

REM 优先使用项目根下 .venv 中的 assetmanager.exe
set "VENV_EXE=%~dp0..\..\.venv\Scripts\assetmanager.exe"

if exist "%VENV_EXE%" (
  "%VENV_EXE%" categorize %*
  goto :eof
)

REM 回退到全局安装的 assetmanager（例如经 uv/hatch 安装后）
where assetmanager >nul 2>nul
if %errorlevel%==0 (
  assetmanager categorize %*
  goto :eof
)

echo 未找到 assetmanager 可执行文件。请先安装或创建虚拟环境。
exit /b 1
