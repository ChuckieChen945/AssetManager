@echo off
setlocal

set "VENV_EXE=%~dp0..\..\.venv\Scripts\assetmanager.exe"

echo ���ڲ��� assetmanager ��ִ���ļ�...
if exist "%VENV_EXE%" (
  echo �ҵ���ִ���ļ�����ʼִ������...
  "%VENV_EXE%" categorize %*
  echo ����ִ����ϡ�
) else (
  echo δ�ҵ� assetmanager ��ִ���ļ������Ȱ�װ�򴴽����⻷����
)

echo.
@REM pause
