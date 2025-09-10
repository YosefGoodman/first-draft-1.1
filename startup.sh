#!/bin/bash

echo "Starting 4-Panel AI Chat Application..."
echo

echo "Installing Python dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo
echo "Checking if port 5001 is available..."
if command -v ss > /dev/null; then
    if ss -tuln | grep -q ":5001 "; then
        echo "Port 5001 is in use. Attempting to free it..."
        if command -v fuser > /dev/null; then
            fuser -k 5001/tcp 2>/dev/null || echo "No process found to kill on port 5001"
        else
            echo "Warning: Cannot automatically free port 5001. Please manually stop any process using this port."
            echo "You can check with: ss -tuln | grep :5001"
            exit 1
        fi
        sleep 2
    fi
fi

echo "Starting the application server..."
echo "Opening browser to http://localhost:5001..."
echo "Press Ctrl+C to stop the server"
echo

if command -v xdg-open > /dev/null; then
    xdg-open "http://localhost:5001" &
elif command -v open > /dev/null; then
    open "http://localhost:5001" &
elif command -v start > /dev/null; then
    start "http://localhost:5001" &
else
    echo "Could not detect browser opener. Please manually open http://localhost:5001"
fi

python app.py
