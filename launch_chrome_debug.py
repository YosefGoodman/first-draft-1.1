#!/usr/bin/env python3
"""
Chrome Remote Debugging Launcher
Launches Chrome with remote debugging enabled for Playwright automation
"""

import subprocess
import sys
import time
import requests
import os
import signal
from pathlib import Path

def is_chrome_debug_running():
    """Check if Chrome is already running with remote debugging on port 9222"""
    try:
        response = requests.get("http://localhost:9222/json", timeout=2)
        return response.status_code == 200
    except:
        return False

def find_chrome_executable():
    """Find Chrome executable on different platforms"""
    possible_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable", 
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/snap/bin/chromium",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
        "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    try:
        result = subprocess.run(["which", "google-chrome"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
        
    try:
        result = subprocess.run(["which", "chromium"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    return None

def launch_chrome_debug():
    """Launch Chrome with remote debugging enabled"""
    if is_chrome_debug_running():
        print("Chrome remote debugging is already running on port 9222")
        return True
    
    chrome_path = find_chrome_executable()
    if not chrome_path:
        print("Error: Could not find Chrome executable")
        print("Please install Google Chrome or Chromium")
        return False
    
    print(f"Found Chrome at: {chrome_path}")
    
    user_data_dir = Path.home() / ".chrome-debug-data"
    user_data_dir.mkdir(exist_ok=True)
    
    chrome_args = [
        chrome_path,
        f"--user-data-dir={user_data_dir}",
        "--remote-debugging-port=9222",
        "--remote-debugging-address=0.0.0.0",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-features=TranslateUI",
        "--disable-ipc-flooding-protection",
        "--enable-automation",
        "--password-store=basic",
        "--use-mock-keychain",
    ]
    
    try:
        print("Launching Chrome with remote debugging...")
        process = subprocess.Popen(
            chrome_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )
        
        for i in range(10):
            time.sleep(1)
            if is_chrome_debug_running():
                print("Chrome remote debugging started successfully on port 9222")
                return True
            print(f"Waiting for Chrome to start... ({i+1}/10)")
        
        print("Error: Chrome failed to start with remote debugging")
        return False
        
    except Exception as e:
        print(f"Error launching Chrome: {e}")
        return False

def stop_chrome_debug():
    """Stop Chrome debugging session"""
    try:
        requests.post("http://localhost:9222/json/runtime/evaluate", 
                     json={"expression": "window.close()"}, timeout=2)
    except:
        pass
    
    try:
        subprocess.run(["pkill", "-f", "remote-debugging-port=9222"], 
                      capture_output=True)
    except:
        pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        stop_chrome_debug()
        print("Chrome debugging session stopped")
    else:
        success = launch_chrome_debug()
        if success:
            print("Chrome is ready for Playwright automation")
            print("Press Ctrl+C to stop Chrome debugging")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                stop_chrome_debug()
                print("\nChrome debugging session stopped")
        else:
            sys.exit(1)
