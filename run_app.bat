@echo off
setlocal

cd /d "%~dp0"
chcp 65001

echo [1/3] Checking Environment...
set PYTHON_EXE=python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Pythonが見つかりません。インストールしてください。
    pause
    exit /b 1
)

REM Check if venv exists. If not, create it.
if not exist ".venv" (
    echo [2/3] 初回セットアップ: 仮想環境を作成中...
    python -m venv .venv
    echo ライブラリをインストール中...
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    python -m pip install -r src\requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

echo [3/3] アプリを起動します...
REM Use PYTHONPATH just in case
set PYTHONPATH=%~dp0src
python src\app.py

if errorlevel 1 (
    echo アプリケーションがエラーで終了しました。
    pause
)
