@echo off
setlocal

cd /d "%~dp0"

REM Define Python path (found in scoop)
set PYTHON_EXE=C:\Users\ninni\scoop\apps\python\current\python.exe

echo [0/5] Cleaning up old environment...
if exist ".venv" (
    rmdir /s /q ".venv"
    if exist ".venv" (
        echo Error: Could not delete .venv folder. Please close any programs using it and try again.
        pause
        exit /b 1
    )
)
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "KindlePDFCapture.spec" del "KindlePDFCapture.spec"

echo [1/5] Checking Python...
if not exist "%PYTHON_EXE%" (
    echo Error: Python executable not found at "%PYTHON_EXE%"
    echo Please check your Python installation.
    pause
    exit /b 1
)

echo [2/5] Creating Virtual Environment (.venv)...
"%PYTHON_EXE%" -m venv .venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment.
    pause
    exit /b 1
)

echo [3/5] Installing Dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
if errorlevel 1 (
    echo Error: Failed to install dependencies.
    pause
    exit /b 1
)

echo [4/5] Building Executable with PyInstaller...
pyinstaller --noconsole --onefile --clean --name "KindlePDFCapture" --collect-all customtkinter app.py
if errorlevel 1 (
    echo Error: PyInstaller failed.
    pause
    exit /b 1
)

echo [5/5] Build Complete!
echo.
echo The standalone application is located in the "dist" folder:
echo %~dp0dist\KindlePDFCapture.exe
echo.
echo You can move "KindlePDFCapture.exe" anywhere on your computer and run it.

pause
