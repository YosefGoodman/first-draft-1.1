#!/bin/bash

echo "Starting Multi-AI Chatbot Manager (Embedded Browser Version)"
echo "============================================================"

if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed."
    exit 1
fi

python3 -c "import cef_capi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    pip install -r requirements.txt
fi

python3 startup_embedded.py
