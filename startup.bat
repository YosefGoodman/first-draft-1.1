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
echo Starting the application server...
echo Opening browser to http://localhost:5001...
echo Press Ctrl+C to stop the server
echo.

start "" "http://localhost:5001"
python app.py
pause
