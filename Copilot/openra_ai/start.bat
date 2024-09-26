@echo off

cd /d %~dp0

set "marker_file=install_done.txt"

if exist "%marker_file%" (
    echo ��鰲װ״̬...

    for /f "tokens=1 delims=" %%i in (%marker_file%) do (
        set install_status=%%i
    )

    setlocal enabledelayedexpansion
    echo ��װ״̬: !install_status!

    if "!install_status!"=="installed=true" (
        echo �����Ѿ���װ��������װ����...
    ) else (
        echo ��װ������...
        call install.bat
        if errorlevel 1 (
            echo ��װʧ�ܣ�ִֹͣ�С�
            pause
            exit /b 1
        )
        echo ��װ��ɣ����±���ļ�...
        echo installed=true> "%marker_file%"
    )
) else (
    echo ��װ������...
    call install.bat
    if errorlevel 1 (
        echo ��װʧ�ܣ�ִֹͣ�С�
        pause
        exit /b 1
    )
    echo ��װ��ɣ���������ļ�...
    echo installed=true> "%marker_file%"
)

start "Copilot_Whisper_Mic" python ./whisper_mic/cli.py --config config.json
