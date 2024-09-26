@echo off

cd /d %~dp0

set "marker_file=install_done.txt"

if exist "%marker_file%" (
    echo 检查安装状态...

    for /f "tokens=1 delims=" %%i in (%marker_file%) do (
        set install_status=%%i
    )

    setlocal enabledelayedexpansion
    echo 安装状态: !install_status!

    if "!install_status!"=="installed=true" (
        echo 依赖已经安装，跳过安装步骤...
    ) else (
        echo 安装依赖中...
        call install.bat
        if errorlevel 1 (
            echo 安装失败，停止执行。
            pause
            exit /b 1
        )
        echo 安装完成，更新标记文件...
        echo installed=true> "%marker_file%"
    )
) else (
    echo 安装依赖中...
    call install.bat
    if errorlevel 1 (
        echo 安装失败，停止执行。
        pause
        exit /b 1
    )
    echo 安装完成，创建标记文件...
    echo installed=true> "%marker_file%"
)

start "Copilot_Whisper_Mic" python ./whisper_mic/cli.py --config config.json
