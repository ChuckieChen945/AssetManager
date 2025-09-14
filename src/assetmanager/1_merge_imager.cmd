@REM �������� thumbnailʱ���ٺϲ�ͼƬ
@REM ��Ҫ��װ ImageMagick: scoop install main/ImageMagick

@echo off
setlocal enabledelayedexpansion

REM ����Ƿ������
if "%~1"=="" (
    echo ���ͼƬ�ϵ����ű���ʹ�ã�
    pause
    exit /b
)

REM ͳ�ƴ����ͼƬ����
set count=0
for %%i in (%*) do (
    set /a count+=1
)

REM �������� = floor(sqrt(count))
for /f "tokens=1" %%i in ('powershell -command "[math]::Floor([math]::Sqrt(%count%))"') do set cols=%%i
if %cols% lss 1 set cols=1

REM ����ļ�������ʱ�����
set output=montage_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.jpg
set output=%output: =0%

@REM ���� ImageMagick montage
montage %* -geometry +0+0 -tile %cols%x -background none "%output%"

echo ƴͼ��ɣ�����ļ���%output%
@REM pause
