import sys
import os
import json
import threading
import time
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QCheckBox, QTextEdit, QLineEdit, QFrame
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QUrl
from PyQt5.QtGui import QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView

class WebEngineWidget(QWidget):
    def __init__(self, service_name, url, parent=None):
        super(WebEngineWidget, self).__init__(parent)
        self.service_name = service_name
        self.url = url
        self.browser = None
        self.setMinimumSize(400, 300)
        self.setupUI()
        
    def setupUI(self):
        layout = QVBoxLayout()
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(self.url))
        layout.addWidget(self.browser)
        self.setLayout(layout)
        
    def load_url(self, url):
        if self.browser:
            self.browser.setUrl(QUrl(url))
            
    def get_browser(self):
        return self.browser

class AIPanel(QWidget):
    def __init__(self, service_id, service_name, service_url, parent=None):
        super(AIPanel, self).__init__(parent)
        self.service_id = service_id
        self.service_name = service_name
        self.service_url = service_url
        self.browser_widget = None
        self.is_active = False
        self.session_active = False
        
        self.setupUI()
        
    def setupUI(self):
        layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self.toggle_active)
        
        title_label = QLabel(self.service_name)
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        header_layout.addWidget(self.checkbox)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        self.status_label = QLabel("Inactive")
        self.status_label.setStyleSheet("color: gray;")
        
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Session")
        self.start_button.clicked.connect(self.start_session)
        self.start_button.setEnabled(False)
        
        self.scrape_button = QPushButton("Scrape Data")
        self.scrape_button.clicked.connect(self.scrape_data)
        self.scrape_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.scrape_button)
        
        self.browser_container = QFrame()
        self.browser_container.setFrameStyle(QFrame.Box)
        self.browser_container.setMinimumHeight(300)
        self.browser_container.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        
        browser_layout = QVBoxLayout()
        self.browser_placeholder = QLabel("Browser will appear here when session starts")
        self.browser_placeholder.setAlignment(Qt.AlignCenter)
        self.browser_placeholder.setStyleSheet("color: #666;")
        browser_layout.addWidget(self.browser_placeholder)
        self.browser_container.setLayout(browser_layout)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.status_label)
        layout.addLayout(button_layout)
        layout.addWidget(self.browser_container)
        
        self.setLayout(layout)
        
    def toggle_active(self, state):
        self.is_active = state == Qt.Checked
        self.start_button.setEnabled(self.is_active)
        if self.is_active:
            self.status_label.setText("Active")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("Inactive")
            self.status_label.setStyleSheet("color: gray;")
            if self.session_active:
                self.stop_session()
                
    def start_session(self):
        if not self.session_active:
            self.browser_widget = WebEngineWidget(self.service_name, self.service_url)
            
            browser_layout = self.browser_container.layout()
            browser_layout.removeWidget(self.browser_placeholder)
            self.browser_placeholder.hide()
            browser_layout.addWidget(self.browser_widget)
            
            self.session_active = True
            self.start_button.setText("Stop Session")
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.stop_session)
            self.scrape_button.setEnabled(True)
            self.status_label.setText("Session Active")
            self.status_label.setStyleSheet("color: blue;")
            
            try:
                response = requests.post('http://localhost:8000/start_session', 
                                       json={'service_id': self.service_id})
                if response.status_code == 200:
                    print(f"Backend session started for {self.service_name}")
            except Exception as e:
                print(f"Failed to start backend session for {self.service_name}: {e}")
                
    def stop_session(self):
        if self.session_active:
            if self.browser_widget:
                browser_layout = self.browser_container.layout()
                browser_layout.removeWidget(self.browser_widget)
                self.browser_widget.deleteLater()
                self.browser_widget = None
                
                self.browser_placeholder.show()
                browser_layout.addWidget(self.browser_placeholder)
                
            self.session_active = False
            self.start_button.setText("Start Session")
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.start_session)
            self.scrape_button.setEnabled(False)
            self.status_label.setText("Active")
            self.status_label.setStyleSheet("color: green;")
            
    def scrape_data(self):
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

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        
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
        self.setupUI()
        
    def setupUI(self):
        self.setWindowTitle("Multi-AI Chatbot Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        title_label = QLabel("Multi-AI Chatbot Management Platform")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("margin: 10px; padding: 10px; background-color: #f0f0f0;")
        
        panels_layout = QGridLayout()
        
        service_ids = list(self.ai_services.keys())
        for i, service_id in enumerate(service_ids):
            service = self.ai_services[service_id]
            panel = AIPanel(service_id, service['name'], service['url'])
            self.panels[service_id] = panel
            
            row = i // 2
            col = i % 2
            panels_layout.addWidget(panel, row, col)
            
        controls_layout = QVBoxLayout()
        
        ask_all_layout = QHBoxLayout()
        ask_all_label = QLabel("Ask All Active AIs:")
        ask_all_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter your message here...")
        self.message_input.returnPressed.connect(self.send_to_all)
        
        send_button = QPushButton("Send to All")
        send_button.clicked.connect(self.send_to_all)
        
        ask_all_layout.addWidget(ask_all_label)
        ask_all_layout.addWidget(self.message_input)
        ask_all_layout.addWidget(send_button)
        
        scrape_all_layout = QHBoxLayout()
        scrape_all_button = QPushButton("Scrape All Active")
        scrape_all_button.clicked.connect(self.scrape_all)
        scrape_all_layout.addWidget(scrape_all_button)
        scrape_all_layout.addStretch()
        
        controls_layout.addLayout(ask_all_layout)
        controls_layout.addLayout(scrape_all_layout)
        
        main_layout.addWidget(title_label)
        main_layout.addLayout(panels_layout)
        main_layout.addLayout(controls_layout)
        
        central_widget.setLayout(main_layout)
        
    def send_to_all(self):
        message = self.message_input.text().strip()
        if message:
            for panel in self.panels.values():
                if panel.is_active and panel.session_active:
                    panel.send_message(message)
            self.message_input.clear()
            
    def scrape_all(self):
        for panel in self.panels.values():
            if panel.is_active and panel.session_active:
                panel.scrape_data()
                
    def closeEvent(self, event):
        for panel in self.panels.values():
            if panel.session_active:
                panel.stop_session()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
