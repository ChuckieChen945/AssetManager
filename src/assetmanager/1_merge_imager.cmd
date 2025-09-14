@REM 用于整理 thumbnail时快速合并图片
@REM 需要安装 ImageMagick: scoop install main/ImageMagick

@echo off
setlocal enabledelayedexpansion

REM 检查是否传入参数
if "%~1"=="" (
    echo 请把图片拖到本脚本上使用！
    pause
    exit /b
)

REM 统计传入的图片数量
set count=0
for %%i in (%*) do (
    set /a count+=1
)

REM 计算列数 = floor(sqrt(count))
for /f "tokens=1" %%i in ('powershell -command "[math]::Floor([math]::Sqrt(%count%))"') do set cols=%%i
if %cols% lss 1 set cols=1

REM 输出文件名（带时间戳）
set output=montage_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.jpg
set output=%output: =0%

@REM 调用 ImageMagick montage
montage %* -geometry +0+0 -tile %cols%x -background none "%output%"

echo 拼图完成！输出文件：%output%
@REM pause
