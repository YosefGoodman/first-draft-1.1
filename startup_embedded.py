#!/usr/bin/env python3
"""
Startup script for the embedded browser version of the Multi-AI Chatbot Manager
"""

import subprocess
import sys
import os
import time
import threading

def start_backend_server():
    """Start the backend HTTP server"""
    try:
        subprocess.run([sys.executable, "app.py"], cwd=os.path.dirname(os.path.abspath(__file__)))
    except KeyboardInterrupt:
        pass

def start_embedded_app():
    """Start the embedded desktop application"""
    try:
        from desktop_app_embedded import main
        main()
    except KeyboardInterrupt:
        pass

def main():
    print("Starting Multi-AI Chatbot Manager (Embedded Browser Version)")
    print("=" * 60)
    
    backend_thread = threading.Thread(target=start_backend_server, daemon=True)
    backend_thread.start()
    
    print("Starting backend server...")
    time.sleep(2)
    
    print("Starting embedded desktop application...")
    start_embedded_app()

if __name__ == "__main__":
    main()
