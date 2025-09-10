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
