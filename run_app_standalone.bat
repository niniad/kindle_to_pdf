@echo off
cd /d "%~dp0"

echo Checking for Virtual Environment...
if not exist ".venv\Scripts\python.exe" (
    echo Error: Virtual environment not found at .venv
    echo Please run build_standalone.bat first (even if you only want to run locally).
    pause
    exit /b
)

echo Starting App...
".venv\Scripts\python.exe" app.py

if errorlevel 1 (
    echo.
    echo The application crashed or closed unexpectedly.
    pause
)
