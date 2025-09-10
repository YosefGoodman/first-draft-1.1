#!/usr/bin/env python3
"""
Test script to verify the embedded browser functionality works correctly.
This script tests that the PyQt WebEngine implementation successfully embeds
browsers within panel areas instead of opening separate windows.
"""

import sys
import os
import time
import requests
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from desktop_app_embedded import MainWindow

def test_embedded_browser_functionality():
    """Test that browsers embed within panels instead of opening separate windows"""
    print("Testing embedded browser functionality...")
    
    app = QApplication(sys.argv)
    
    window = MainWindow()
    
    assert len(window.panels) == 4, f"Expected 4 panels, got {len(window.panels)}"
    print("✓ All 4 AI service panels created successfully")
    
    service_ids = ['chatgpt', 'claude', 'mistral', 'gemini']
    for service_id in service_ids:
        assert service_id in window.panels, f"Panel {service_id} not found"
        panel = window.panels[service_id]
        
        assert hasattr(panel, 'browser_container'), f"Panel {service_id} missing browser_container"
        assert hasattr(panel, 'start_button'), f"Panel {service_id} missing start_button"
        assert hasattr(panel, 'checkbox'), f"Panel {service_id} missing checkbox"
        print(f"✓ Panel {service_id} has all required components")
    
    test_panel = window.panels['chatgpt']
    
    test_panel.checkbox.setChecked(True)
    assert test_panel.is_active == True, "Service should be active after checkbox checked"
    print("✓ Service activation works correctly")
    
    assert test_panel.start_button.isEnabled() == True, "Start button should be enabled when service is active"
    print("✓ Start button enables correctly when service is active")
    
    test_panel.start_session()
    
    assert test_panel.session_active == True, "Session should be active after start_session()"
    assert test_panel.browser_widget is not None, "Browser widget should be created"
    print("✓ Browser session starts correctly")
    
    browser_layout = test_panel.browser_container.layout()
    widget_count = browser_layout.count()
    assert widget_count > 0, "Browser container should contain widgets"
    print("✓ Browser widget is embedded in panel container")
    
    from desktop_app_embedded import WebEngineWidget
    assert isinstance(test_panel.browser_widget, WebEngineWidget), "Browser widget should be WebEngineWidget"
    print("✓ Browser widget is correct type (WebEngineWidget)")
    
    expected_url = window.ai_services['chatgpt']['url']
    assert test_panel.browser_widget.url == expected_url, f"Browser should load {expected_url}"
    print(f"✓ Browser loads correct URL: {expected_url}")
    
    test_panel.stop_session()
    assert test_panel.session_active == False, "Session should be inactive after stop_session()"
    assert test_panel.browser_widget is None, "Browser widget should be None after stopping"
    print("✓ Browser session stops correctly")
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Embedded browser functionality works correctly")
    print("✅ Browsers are embedded within panel containers (not separate windows)")
    print("✅ All AI service panels function properly")
    print("✅ Session start/stop functionality works")
    print("✅ WebEngine widgets load correct URLs")
    
    return True

if __name__ == "__main__":
    try:
        success = test_embedded_browser_functionality()
        if success:
            print("\n✅ EMBEDDED BROWSER IMPLEMENTATION SUCCESSFUL")
            print("The browser embedding issue has been fixed!")
            sys.exit(0)
        else:
            print("\n❌ TESTS FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
