@echo off
echo Starting Multi-AI Chatbot Manager (Embedded Browser Version)
echo ============================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is required but not installed.
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import cef_capi, gi" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
)

REM Start the embedded application
python startup_embedded.py
pause
