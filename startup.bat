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
echo Open your browser to http://localhost:5001 when ready
echo Press Ctrl+C to stop the server
echo.

python app.py
pause
