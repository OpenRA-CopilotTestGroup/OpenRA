@echo off

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python δ��װ��δ��ӵ��������������Ȱ�װ Python ��Python��ӵ���������.
    exit /b 1
)

python -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple --upgrade pip
pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
if %errorlevel% neq 0 (
    echo ���廪Դʧ��
    exit /b 1
)

python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo ���� pip ʧ��
    exit /b 1
)

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ��װ requirements.txt ʧ��
    exit /b 1
)

pip install -e .
if %errorlevel% neq 0 (
    echo ��װ�ɱ༭ģʽ�İ�ʧ��
    exit /b 1
)

echo ����������װ�ɹ�
exit /b 0
