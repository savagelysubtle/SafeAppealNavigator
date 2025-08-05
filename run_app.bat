@echo off
:: AI Research Agent - Windows Application Launcher
:: This batch file starts both the backend and frontend servers

echo ============================================================
echo          AI Research Agent - Application Launcher
echo ============================================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python and try again.
    pause
    exit /b 1
)

:: Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH.
    echo Please install Node.js and try again.
    pause
    exit /b 1
)

:: Run the Python launcher script
echo Starting AI Research Agent...
python run_app.py

:: If Python script exits, pause to show any error messages
pause