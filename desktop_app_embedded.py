import sys
import os
import json
import threading
import time
import requests
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import cef_capi as cef

class CEFBrowserWidget:
    def __init__(self, service_name, url, parent_widget):
        self.service_name = service_name
        self.url = url
        self.parent_widget = parent_widget
        self.browser = None
        self.window_info = None
        self.setup_browser()
        
    def setup_browser(self):
        window_info = cef.WindowInfo()
        window_info.parent_window = self.parent_widget.get_window().get_xid()
        
        browser_settings = cef.BrowserSettings()
        
        self.browser = cef.CreateBrowserSync(
            window_info=window_info,
            url=self.url,
            browser_settings=browser_settings
        )
        
    def load_url(self, url):
        if self.browser:
            self.browser.GetMainFrame().LoadUrl(url)
            
    def get_browser(self):
        return self.browser

class AIPanel:
    def __init__(self, service_id, service_name, service_url):
        self.service_id = service_id
        self.service_name = service_name
        self.service_url = service_url
        self.browser_widget = None
        self.is_active = False
        self.session_active = False
        
        self.setup_ui()
        
    def setup_ui(self):
        self.panel_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.panel_box.set_margin_left(5)
        self.panel_box.set_margin_right(5)
        self.panel_box.set_margin_top(5)
        self.panel_box.set_margin_bottom(5)
        
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.checkbox = Gtk.CheckButton()
        self.checkbox.connect("toggled", self.toggle_active)
        
        title_label = Gtk.Label(label=self.service_name)
        title_label.set_markup(f"<b>{self.service_name}</b>")
        
        header_box.pack_start(self.checkbox, False, False, 0)
        header_box.pack_start(title_label, False, False, 0)
        
        self.status_label = Gtk.Label(label="Inactive")
        self.status_label.set_markup('<span color="gray">Inactive</span>')
        
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.start_button = Gtk.Button(label="Start Session")
        self.start_button.connect("clicked", self.start_session)
        self.start_button.set_sensitive(False)
        
        self.scrape_button = Gtk.Button(label="Scrape Data")
        self.scrape_button.connect("clicked", self.scrape_data)
        self.scrape_button.set_sensitive(False)
        
        button_box.pack_start(self.start_button, True, True, 0)
        button_box.pack_start(self.scrape_button, True, True, 0)
        
        self.browser_container = Gtk.Frame()
        self.browser_container.set_size_request(400, 300)
        
        self.browser_placeholder = Gtk.Label(label="Browser will appear here when session starts")
        self.browser_placeholder.set_markup('<span color="#666">Browser will appear here when session starts</span>')
        self.browser_container.add(self.browser_placeholder)
        
        self.panel_box.pack_start(header_box, False, False, 0)
        self.panel_box.pack_start(self.status_label, False, False, 0)
        self.panel_box.pack_start(button_box, False, False, 0)
        self.panel_box.pack_start(self.browser_container, True, True, 0)
        
        self.checkbox.set_active(True)
        
    def toggle_active(self, checkbox):
        self.is_active = checkbox.get_active()
        self.start_button.set_sensitive(self.is_active)
        if self.is_active:
            self.status_label.set_markup('<span color="green">Active</span>')
            if not self.session_active:
                GLib.idle_add(self.start_session, None)
        else:
            self.status_label.set_markup('<span color="gray">Inactive</span>')
            if self.session_active:
                self.stop_session(None)
                
    def start_session(self, button):
        if not self.session_active:
            if self.browser_placeholder.get_parent():
                self.browser_container.remove(self.browser_placeholder)
            
            drawing_area = Gtk.DrawingArea()
            drawing_area.set_size_request(400, 300)
            drawing_area.realize()
            self.browser_container.add(drawing_area)
            drawing_area.show()
            
            self.browser_widget = CEFBrowserWidget(self.service_name, self.service_url, drawing_area)
            
            self.session_active = True
            self.start_button.set_label("Stop Session")
            self.start_button.disconnect_by_func(self.start_session)
            self.start_button.connect("clicked", self.stop_session)
            self.scrape_button.set_sensitive(True)
            self.status_label.set_markup('<span color="blue">Session Active</span>')
            
            try:
                response = requests.post('http://localhost:8000/start_session', 
                                       json={'service_id': self.service_id})
                if response.status_code == 200:
                    print(f"Backend session started for {self.service_name}")
            except Exception as e:
                print(f"Failed to start backend session for {self.service_name}: {e}")
                
    def stop_session(self, button):
        if self.session_active:
            if self.browser_widget:
                for child in self.browser_container.get_children():
                    if child != self.browser_placeholder:
                        self.browser_container.remove(child)
                self.browser_widget = None
                
                self.browser_container.add(self.browser_placeholder)
                self.browser_placeholder.show()
                
            self.session_active = False
            self.start_button.set_label("Start Session")
            self.start_button.disconnect_by_func(self.stop_session)
            self.start_button.connect("clicked", self.start_session)
            self.scrape_button.set_sensitive(False)
            self.status_label.set_markup('<span color="green">Active</span>')
            
    def scrape_data(self, button):
        if self.session_active:
            try:
                response = requests.post('http://localhost:8000/scrape_data', 
                                       json={'service_id': self.service_id})
                if response.status_code == 200:
                    print(f"Data scraped for {self.service_name}")
            except Exception as e:
                print(f"Failed to scrape data for {self.service_name}: {e}")
                
    def send_message(self, message):
        if self.session_active:
            try:
                response = requests.post('http://localhost:8000/inject_message', 
                                       json={'service_id': self.service_id, 'message': message})
                if response.status_code == 200:
                    print(f"Message sent to {self.service_name}")
            except Exception as e:
                print(f"Failed to send message to {self.service_name}: {e}")

class MainWindow:
    def __init__(self):
        self.ai_services = {
            'chatgpt': {
                'name': 'ChatGPT',
                'url': 'https://chat.openai.com',
                'active': False
            },
            'claude': {
                'name': 'Claude',
                'url': 'https://claude.ai',
                'active': False
            },
            'mistral': {
                'name': 'Mistral',
                'url': 'https://chat.mistral.ai',
                'active': False
            },
            'gemini': {
                'name': 'Gemini',
                'url': 'https://gemini.google.com',
                'active': False
            }
        }
        
        self.panels = {}
        self.setup_ui()
        
    def setup_ui(self):
        self.window = Gtk.Window()
        self.window.set_title("Multi-AI Chatbot Manager")
        self.window.set_default_size(1200, 800)
        self.window.connect("destroy", self.on_destroy)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_left(10)
        main_box.set_margin_right(10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        
        title_label = Gtk.Label(label="Multi-AI Chatbot Management Platform")
        title_label.set_markup('<span size="large" weight="bold">Multi-AI Chatbot Management Platform</span>')
        title_label.set_halign(Gtk.Align.CENTER)
        
        panels_grid = Gtk.Grid()
        panels_grid.set_row_spacing(10)
        panels_grid.set_column_spacing(10)
        panels_grid.set_column_homogeneous(True)
        panels_grid.set_row_homogeneous(True)
        
        service_ids = list(self.ai_services.keys())
        for i, service_id in enumerate(service_ids):
            service = self.ai_services[service_id]
            panel = AIPanel(service_id, service['name'], service['url'])
            self.panels[service_id] = panel
            
            row = i // 2
            col = i % 2
            panels_grid.attach(panel.panel_box, col, row, 1, 1)
            
        controls_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        ask_all_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ask_all_label = Gtk.Label(label="Ask All Active AIs:")
        ask_all_label.set_markup('<span weight="bold">Ask All Active AIs:</span>')
        
        self.message_entry = Gtk.Entry()
        self.message_entry.set_placeholder_text("Enter your message here...")
        self.message_entry.connect("activate", self.send_to_all)
        
        send_button = Gtk.Button(label="Send to All")
        send_button.connect("clicked", self.send_to_all)
        
        ask_all_box.pack_start(ask_all_label, False, False, 0)
        ask_all_box.pack_start(self.message_entry, True, True, 0)
        ask_all_box.pack_start(send_button, False, False, 0)
        
        scrape_all_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        scrape_all_button = Gtk.Button(label="Scrape All Active")
        scrape_all_button.connect("clicked", self.scrape_all)
        scrape_all_box.pack_start(scrape_all_button, False, False, 0)
        
        controls_box.pack_start(ask_all_box, False, False, 0)
        controls_box.pack_start(scrape_all_box, False, False, 0)
        
        main_box.pack_start(title_label, False, False, 0)
        main_box.pack_start(panels_grid, True, True, 0)
        main_box.pack_start(controls_box, False, False, 0)
        
        self.window.add(main_box)
        
    def send_to_all(self, widget):
        message = self.message_entry.get_text().strip()
        if message:
            for panel in self.panels.values():
                if panel.is_active and panel.session_active:
                    panel.send_message(message)
            self.message_entry.set_text("")
            
    def scrape_all(self, button):
        for panel in self.panels.values():
            if panel.is_active and panel.session_active:
                panel.scrape_data(None)
                
    def on_destroy(self, widget):
        for panel in self.panels.values():
            if panel.session_active:
                panel.stop_session(None)
        cef.Shutdown()
        Gtk.main_quit()

def main():
    settings = cef.Settings()
    settings.multi_threaded_message_loop = False
    cef.Initialize(settings)
    
    window = MainWindow()
    window.window.show_all()
    
    def cef_work():
        cef.MessageLoopWork()
        return True
    
    GLib.timeout_add(10, cef_work)
    
    Gtk.main()

if __name__ == '__main__':
    main()
