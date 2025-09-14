@echo off
setlocal

set "VENV_EXE=%~dp0..\..\.venv\Scripts\assetmanager.exe"

echo 正在查找 assetmanager 可执行文件...
if exist "%VENV_EXE%" (
  echo 找到可执行文件，开始执行命令...
  "%VENV_EXE%" categorize %*
  echo 命令执行完毕。
) else (
  echo 未找到 assetmanager 可执行文件。请先安装或创建虚拟环境。
)

echo.
@REM pause
