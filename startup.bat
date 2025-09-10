@echo off
echo Starting 4-Panel AI Chat Application...
echo.

echo Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Checking if port 5001 is available...
netstat -an | findstr ":5001" >nul
if %errorlevel% equ 0 (
    echo Port 5001 is in use. Attempting to free it...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5001"') do taskkill /f /pid %%a >nul 2>&1
    timeout /t 2 >nul
)

echo.
echo Starting the application server...
echo Opening browser to http://localhost:5001...
echo Press Ctrl+C to stop the server
echo.

start "" "http://localhost:5001"
python app.py
pause
