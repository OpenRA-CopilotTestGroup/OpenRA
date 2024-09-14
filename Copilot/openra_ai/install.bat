@echo off

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 未安装或未添加到环境变量，请先安装 Python 或将Python添加到环境变量.
    exit /b 1
)

python -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple --upgrade pip
pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
if %errorlevel% neq 0 (
    echo 换清华源失败
    exit /b 1
)

python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo 升级 pip 失败
    exit /b 1
)

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 安装 requirements.txt 失败
    exit /b 1
)

pip install -e .
if %errorlevel% neq 0 (
    echo 安装可编辑模式的包失败
    exit /b 1
)

echo 所有依赖安装成功
exit /b 0
