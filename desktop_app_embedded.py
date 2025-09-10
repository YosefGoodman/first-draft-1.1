import sys
import os
import json
import threading
import time
import requests
import ctypes
import ctypes.util
import sysconfig
import signal
from cef_capi import cef_string_ctor, size_ctor, struct, header, __version__
from cef_capi.app_client import client_ctor, app_ctor, settings_main_args_ctor

gtk_lib = ctypes.util.find_library('gtk-3')
if not gtk_lib:
    raise Exception("GTK-3 library not found")
gtk = ctypes.CDLL(gtk_lib)

GTK_WINDOW_TOPLEVEL = 0
GTK_ORIENTATION_VERTICAL = 1
GTK_ORIENTATION_HORIZONTAL = 0

gtk.gtk_init.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p))]
gtk.gtk_window_new.argtypes = [ctypes.c_int]
gtk.gtk_window_new.restype = ctypes.c_void_p
gtk.gtk_window_set_title.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
gtk.gtk_window_set_default_size.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
gtk.gtk_widget_show_all.argtypes = [ctypes.c_void_p]
gtk.gtk_main.argtypes = []
gtk.gtk_main_quit.argtypes = []
gtk.gtk_box_new.argtypes = [ctypes.c_int, ctypes.c_int]
gtk.gtk_box_new.restype = ctypes.c_void_p
gtk.gtk_container_add.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
gtk.gtk_box_pack_start.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool, ctypes.c_bool, ctypes.c_uint]
gtk.gtk_label_new.argtypes = [ctypes.c_char_p]
gtk.gtk_label_new.restype = ctypes.c_void_p
gtk.gtk_button_new_with_label.argtypes = [ctypes.c_char_p]
gtk.gtk_button_new_with_label.restype = ctypes.c_void_p
gtk.gtk_check_button_new_with_label.argtypes = [ctypes.c_char_p]
gtk.gtk_check_button_new_with_label.restype = ctypes.c_void_p
gtk.gtk_toggle_button_set_active.argtypes = [ctypes.c_void_p, ctypes.c_bool]
gtk.gtk_toggle_button_get_active.argtypes = [ctypes.c_void_p]
gtk.gtk_toggle_button_get_active.restype = ctypes.c_bool
gtk.gtk_widget_set_sensitive.argtypes = [ctypes.c_void_p, ctypes.c_bool]
gtk.gtk_widget_get_sensitive.argtypes = [ctypes.c_void_p]
gtk.gtk_widget_get_sensitive.restype = ctypes.c_bool
gtk.gtk_grid_new.argtypes = []
gtk.gtk_grid_new.restype = ctypes.c_void_p
gtk.gtk_grid_attach.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
gtk.gtk_grid_set_row_spacing.argtypes = [ctypes.c_void_p, ctypes.c_uint]
gtk.gtk_grid_set_column_spacing.argtypes = [ctypes.c_void_p, ctypes.c_uint]
gtk.gtk_entry_new.argtypes = []
gtk.gtk_entry_new.restype = ctypes.c_void_p
gtk.gtk_entry_set_placeholder_text.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
gtk.gtk_entry_get_text.argtypes = [ctypes.c_void_p]
gtk.gtk_entry_get_text.restype = ctypes.c_char_p
gtk.gtk_entry_set_text.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

gobject_lib = ctypes.util.find_library('gobject-2.0')
if gobject_lib:
    gobject = ctypes.CDLL(gobject_lib)
    gobject.g_signal_connect_data.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
    gobject.g_signal_connect_data.restype = ctypes.c_ulong

class CefBrowserWidget:
    def __init__(self, service_name, url):
        self.service_name = service_name
        self.url = url
        self.browser = None
        self.window_info = None
        
    def create_browser(self):
        """Create a CEF browser instance for this service"""
        self.window_info = struct.cef_window_info_t()
        self.window_info.windowless_rendering_enabled = 1
        
        cef_url = cef_string_ctor(self.url)
        browser_settings = size_ctor(struct.cef_browser_settings_t)
        client = client_ctor()
        
        self.browser = header.cef_browser_host_create_browser(
            self.window_info, client, cef_url, browser_settings, None, None)
        
        return self.browser is not None
        
    def load_url(self, url):
        self.url = url
        if self.browser:
            cef_url = cef_string_ctor(url)
            if hasattr(self.browser, 'get_main_frame'):
                frame = self.browser.get_main_frame()
                if frame:
                    frame.load_url(cef_url)

class AIPanel:
    def __init__(self, service_id, service_name, service_url):
        self.service_id = service_id
        self.service_name = service_name
        self.service_url = service_url
        self.browser_widget = None
        self.is_active = True  # Auto-activate all panels
        self.session_active = False
        
    def start_session(self):
        """Start a CEF browser session for this AI service"""
        if not self.session_active:
            print(f"Starting CEF browser session for {self.service_name}")
            self.browser_widget = CefBrowserWidget(self.service_name, self.service_url)
            
            if self.browser_widget.create_browser():
                print(f"✓ CEF browser created successfully for {self.service_name}")
                self.session_active = True
                
                try:
                    response = requests.post('http://localhost:8000/start_session', 
                                           json={'service_id': self.service_id})
                    if response.status_code == 200:
                        print(f"✓ Backend session started for {self.service_name}")
                except Exception as e:
                    print(f"⚠ Failed to start backend session for {self.service_name}: {e}")
            else:
                print(f"✗ Failed to create CEF browser for {self.service_name}")
                
    def stop_session(self):
        """Stop the CEF browser session"""
        if self.session_active:
            print(f"Stopping CEF browser session for {self.service_name}")
            self.browser_widget = None
            self.session_active = False
            
    def scrape_data(self):
        """Scrape data from the AI service"""
        if self.session_active:
            try:
                response = requests.post('http://localhost:8000/scrape_data', 
                                       json={'service_id': self.service_id})
                if response.status_code == 200:
                    print(f"✓ Data scraped for {self.service_name}")
                    return response.json()
            except Exception as e:
                print(f"⚠ Failed to scrape data for {self.service_name}: {e}")
                
    def send_message(self, message):
        """Send a message to the AI service"""
        if self.session_active:
            try:
                response = requests.post('http://localhost:8000/inject_message', 
                                       json={'service_id': self.service_id, 'message': message})
                if response.status_code == 200:
                    print(f"✓ Message sent to {self.service_name}: {message}")
                    return True
            except Exception as e:
                print(f"⚠ Failed to send message to {self.service_name}: {e}")
        return False

class MainWindow:
    def __init__(self):
        self.ai_services = {
            'chatgpt': {
                'name': 'ChatGPT',
                'url': 'https://chat.openai.com'
            },
            'claude': {
                'name': 'Claude',
                'url': 'https://claude.ai'
            },
            'mistral': {
                'name': 'Mistral',
                'url': 'https://chat.mistral.ai'
            },
            'gemini': {
                'name': 'Gemini',
                'url': 'https://gemini.google.com'
            }
        }
        
        self.panels = {}
        self.running = True
        self.setup_panels()
        self.auto_start_all_sessions()
        
    def setup_panels(self):
        """Initialize all AI service panels"""
        print("Setting up AI service panels...")
        for service_id, service_info in self.ai_services.items():
            panel = AIPanel(service_id, service_info['name'], service_info['url'])
            self.panels[service_id] = panel
            print(f"✓ Panel created for {service_info['name']}")
            
    def auto_start_all_sessions(self):
        """Automatically start all browser sessions immediately"""
        print("\n🚀 Auto-starting all AI browser sessions...")
        
        def delayed_start():
            time.sleep(1)  # Brief delay for CEF initialization
            for panel in self.panels.values():
                if panel.is_active and not panel.session_active:
                    panel.start_session()
            print("✅ All browser sessions auto-started!")
        
        timer_thread = threading.Thread(target=delayed_start)
        timer_thread.daemon = True
        timer_thread.start()
        
    def send_to_all(self, message):
        """Send a message to all active AI services"""
        print(f"\n📤 Sending message to all active AIs: {message}")
        results = {}
        for service_id, panel in self.panels.items():
            if panel.is_active and panel.session_active:
                success = panel.send_message(message)
                results[service_id] = success
        return results
        
    def scrape_all(self):
        """Scrape data from all active AI services"""
        print("\n🔍 Scraping data from all active AIs...")
        results = {}
        for service_id, panel in self.panels.items():
            if panel.is_active and panel.session_active:
                data = panel.scrape_data()
                results[service_id] = data
        return results
        
    def start_all_sessions(self):
        """Start all inactive sessions"""
        print("\n▶️ Starting all inactive sessions...")
        for panel in self.panels.values():
            if panel.is_active and not panel.session_active:
                panel.start_session()
                
    def stop_all_sessions(self):
        """Stop all active sessions"""
        print("\n⏹️ Stopping all active sessions...")
        for panel in self.panels.values():
            if panel.session_active:
                panel.stop_session()
                
    def shutdown(self):
        """Clean shutdown of the application"""
        print("\n🔄 Shutting down Multi-AI Chatbot Manager...")
        self.running = False
        self.stop_all_sessions()

def main():
    """Main entry point for the CEF-based Multi-AI Chatbot Manager"""
    print(f"🚀 Starting Multi-AI Chatbot Manager with CEF {__version__}")
    print("=" * 60)
    
    app = app_ctor()
    settings, main_args = settings_main_args_ctor()
    settings.log_severity = struct.LOGSEVERITY_WARNING
    settings.no_sandbox = 1
    settings.windowless_rendering_enabled = 1
    
    if not header.cef_initialize(main_args, settings, app, None):
        print("❌ Failed to initialize CEF")
        return 1
    
    print("✅ CEF initialized successfully")
    
    window = MainWindow()
    
    def quit_handler(signum, frame):
        print("\n🛑 Received shutdown signal...")
        window.shutdown()
        header.cef_shutdown()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, quit_handler)
    signal.signal(signal.SIGTERM, quit_handler)
    
    print("\n🎯 Multi-AI Chatbot Manager is running!")
    print("📋 Available commands:")
    print("  - All browsers auto-start immediately")
    print("  - Use Ctrl+C to shutdown")
    print("  - Backend API available at http://localhost:8000")
    print("=" * 60)
    
    try:
        header.cef_run_message_loop()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    finally:
        window.shutdown()
        header.cef_shutdown()
        print("✅ Shutdown complete")
        
    return 0

if __name__ == '__main__':
    sys.exit(main())
