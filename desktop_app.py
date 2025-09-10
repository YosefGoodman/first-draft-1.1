import webview
import threading
import json
import os
import platform
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import time

class AIBrowserApp:
    def __init__(self):
        DEFAULT_WINDOWS_PATH = r"C:\Users\yosef\OneDrive\Desktop\Attachments"
        DEFAULT_LINUX_PATH = "/home/ubuntu/scraped_data"
        self.storage_path = os.environ.get('AI_STORAGE_PATH', DEFAULT_WINDOWS_PATH if platform.system() == 'Windows' else DEFAULT_LINUX_PATH)
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.ai_services = {
            'chatgpt': {
                'name': 'ChatGPT',
                'url': 'https://chatgpt.com/',
                'enabled': True,
                'connected': False
            },
            'claude': {
                'name': 'Claude',
                'url': 'https://claude.ai/new',
                'enabled': False,
                'connected': False
            },
            'mistral': {
                'name': 'Mistral',
                'url': 'https://chat.mistral.ai/chat',
                'enabled': False,
                'connected': False
            },
            'gemini': {
                'name': 'Gemini',
                'url': 'https://gemini.google.com/app',
                'enabled': False,
                'connected': False
            }
        }
        
        self.browser_windows = {}
        self.embedding_model = None
        
    def get_embedding_model(self):
        if self.embedding_model is None:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        return self.embedding_model
    
    def toggle_ai_service(self, service_id):
        if service_id in self.ai_services:
            self.ai_services[service_id]['enabled'] = not self.ai_services[service_id]['enabled']
            return self.ai_services[service_id]['enabled']
        return False
    
    def start_ai_browser(self, service_id):
        if service_id not in self.ai_services:
            return False
            
        service = self.ai_services[service_id]
        
        window = webview.create_window(
            title=f"{service['name']} - AI Browser",
            url=service['url'],
            width=800,
            height=600,
            resizable=True,
            shadow=True
        )
        
        self.browser_windows[service_id] = window
        self.ai_services[service_id]['connected'] = True
        
        return True
    
    def send_message_to_ai(self, service_id, message):
        if service_id not in self.ai_services or not self.ai_services[service_id]['enabled']:
            return False
            
        timestamp = datetime.now().isoformat()
        
        interaction_data = {
            'timestamp': timestamp,
            'service': service_id,
            'message': message,
            'response': f"Simulated response from {self.ai_services[service_id]['name']}"
        }
        
        filename = f"{service_id}_{timestamp.replace(':', '-')}.json"
        filepath = os.path.join(self.storage_path, filename)
        
        with open(filepath, 'w') as f:
            json.dump(interaction_data, f, indent=2)
            
        return True
    
    def send_message_to_all_active(self, message):
        results = {}
        for service_id, service in self.ai_services.items():
            if service['enabled'] and service['connected']:
                results[service_id] = self.send_message_to_ai(service_id, message)
        return results
    
    def scrape_ai_data(self, service_id):
        timestamp = datetime.now().isoformat()
        
        scraped_data = {
            'timestamp': timestamp,
            'service': service_id,
            'scraped_content': f"Scraped content from {self.ai_services[service_id]['name']}",
            'embeddings': []
        }
        
        model = self.get_embedding_model()
        content_embedding = model.encode(scraped_data['scraped_content']).tolist()
        scraped_data['embeddings'] = content_embedding
        
        filename = f"scraped_{service_id}_{timestamp.replace(':', '-')}.json"
        filepath = os.path.join(self.storage_path, filename)
        
        with open(filepath, 'w') as f:
            json.dump(scraped_data, f, indent=2)
            
        return scraped_data
    
    def get_api_data(self):
        return {
            'services': self.ai_services,
            'storage_path': self.storage_path
        }

app = AIBrowserApp()

def create_main_window():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Chatbot - 4 Panel Desktop</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                height: 100vh;
                display: flex;
                flex-direction: column;
            }
            
            .header {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                padding: 12px 20px;
                text-align: center;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .header h1 {
                color: white;
                font-size: 18px;
                font-weight: 600;
            }
            
            .main-container {
                flex: 1;
                display: flex;
                flex-direction: column;
                padding: 16px;
                gap: 16px;
            }
            
            .panels-grid {
                flex: 1;
                display: grid;
                grid-template-columns: 1fr 1fr;
                grid-template-rows: 1fr 1fr;
                gap: 16px;
                min-height: 0;
            }
            
            .ai-panel {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .panel-header {
                background: #673ab7;
                color: white;
                padding: 12px 16px;
                display: flex;
                align-items: center;
                gap: 12px;
                font-weight: 600;
                font-size: 14px;
            }
            
            .panel-checkbox {
                width: 16px;
                height: 16px;
                cursor: pointer;
            }
            
            .panel-status {
                margin-left: auto;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 10px;
                font-weight: 500;
            }
            
            .status-connected {
                background: #4caf50;
                color: white;
            }
            
            .status-disconnected {
                background: #f44336;
                color: white;
            }
            
            .panel-content {
                flex: 1;
                padding: 16px;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .start-browser-btn {
                padding: 8px 16px;
                background: #673ab7;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
                font-weight: 500;
                transition: background-color 0.2s;
            }
            
            .start-browser-btn:hover {
                background: #5e35b1;
            }
            
            .start-browser-btn:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            
            .panel-controls {
                display: flex;
                gap: 8px;
                margin-top: auto;
            }
            
            .scrape-btn, .individual-msg-btn {
                flex: 1;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-size: 10px;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            
            .scrape-btn {
                background: #e1bee7;
                color: #673ab7;
            }
            
            .scrape-btn:hover {
                background: #d1c4e9;
            }
            
            .individual-msg-btn {
                background: #c8e6c9;
                color: #2e7d32;
            }
            
            .individual-msg-btn:hover {
                background: #a5d6a7;
            }
            
            .chat-section {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 20px;
            }
            
            .chat-header {
                color: #673ab7;
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 16px;
                text-align: center;
            }
            
            .chat-input-container {
                display: flex;
                gap: 12px;
                align-items: center;
            }
            
            .chat-input {
                flex: 1;
                padding: 12px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 24px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.2s;
            }
            
            .chat-input:focus {
                border-color: #673ab7;
            }
            
            .send-btn {
                width: 48px;
                height: 48px;
                background: #673ab7;
                color: white;
                border: none;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                transition: background-color 0.2s;
            }
            
            .send-btn:hover {
                background: #5e35b1;
            }
            
            .chat-controls {
                display: flex;
                gap: 12px;
                margin-top: 12px;
                justify-content: center;
            }
            
            .control-btn {
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
                font-weight: 500;
                transition: background-color 0.2s;
            }
            
            .scrape-all-btn {
                background: #e1bee7;
                color: #673ab7;
            }
            
            .scrape-all-btn:hover {
                background: #d1c4e9;
            }
            
            .test-compatibility-btn {
                background: #fff3e0;
                color: #f57c00;
            }
            
            .test-compatibility-btn:hover {
                background: #ffe0b2;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>AI Chatbot - 4 Panel Desktop</h1>
        </div>
        
        <div class="main-container">
            <div class="panels-grid">
                <div class="ai-panel" id="chatgpt-panel">
                    <div class="panel-header">
                        <input type="checkbox" class="panel-checkbox" id="chatgpt-checkbox" checked>
                        <span>🤖 ChatGPT</span>
                        <span class="panel-status status-disconnected" id="chatgpt-status">Not Connected</span>
                    </div>
                    <div class="panel-content">
                        <button class="start-browser-btn" id="chatgpt-start-btn">Start Browser Session</button>
                        <div class="panel-controls">
                            <button class="scrape-btn" id="chatgpt-scrape-btn">Scrape Data</button>
                            <button class="individual-msg-btn" id="chatgpt-msg-btn">Send Message</button>
                        </div>
                    </div>
                </div>
                
                <div class="ai-panel" id="mistral-panel">
                    <div class="panel-header">
                        <input type="checkbox" class="panel-checkbox" id="mistral-checkbox">
                        <span>🔥 Mistral</span>
                        <span class="panel-status status-disconnected" id="mistral-status">Not Connected</span>
                    </div>
                    <div class="panel-content">
                        <button class="start-browser-btn" id="mistral-start-btn">Start Browser Session</button>
                        <div class="panel-controls">
                            <button class="scrape-btn" id="mistral-scrape-btn">Scrape Data</button>
                            <button class="individual-msg-btn" id="mistral-msg-btn">Send Message</button>
                        </div>
                    </div>
                </div>
                
                <div class="ai-panel" id="claude-panel">
                    <div class="panel-header">
                        <input type="checkbox" class="panel-checkbox" id="claude-checkbox">
                        <span>🧠 Claude</span>
                        <span class="panel-status status-disconnected" id="claude-status">Not Connected</span>
                    </div>
                    <div class="panel-content">
                        <button class="start-browser-btn" id="claude-start-btn">Start Browser Session</button>
                        <div class="panel-controls">
                            <button class="scrape-btn" id="claude-scrape-btn">Scrape Data</button>
                            <button class="individual-msg-btn" id="claude-msg-btn">Send Message</button>
                        </div>
                    </div>
                </div>
                
                <div class="ai-panel" id="gemini-panel">
                    <div class="panel-header">
                        <input type="checkbox" class="panel-checkbox" id="gemini-checkbox">
                        <span>💎 Gemini</span>
                        <span class="panel-status status-disconnected" id="gemini-status">Not Connected</span>
                    </div>
                    <div class="panel-content">
                        <button class="start-browser-btn" id="gemini-start-btn">Start Browser Session</button>
                        <div class="panel-controls">
                            <button class="scrape-btn" id="gemini-scrape-btn">Scrape Data</button>
                            <button class="individual-msg-btn" id="gemini-msg-btn">Send Message</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="chat-section">
                <div class="chat-header">Message Active AI Panels</div>
                <div class="chat-input-container">
                    <input type="text" class="chat-input" id="main-chat-input" placeholder="Type a message to send to all enabled AI panels...">
                    <button class="send-btn" id="send-all-btn">➤</button>
                </div>
                <div class="chat-controls">
                    <button class="control-btn scrape-all-btn" id="scrape-all-btn">Scrape All Active Panels</button>
                    <button class="control-btn test-compatibility-btn" id="test-compatibility-btn">Test Browser Compatibility</button>
                </div>
            </div>
        </div>
        
        <script>
            // JavaScript for handling UI interactions
            const services = ['chatgpt', 'mistral', 'claude', 'gemini'];
            
            // Initialize event listeners
            services.forEach(service => {
                // Checkbox toggle
                document.getElementById(`${service}-checkbox`).addEventListener('change', function() {
                    pywebview.api.toggle_ai_service(service).then(result => {
                        console.log(`${service} toggled:`, result);
                    });
                });
                
                // Start browser session
                document.getElementById(`${service}-start-btn`).addEventListener('click', function() {
                    pywebview.api.start_ai_browser(service).then(result => {
                        if (result) {
                            document.getElementById(`${service}-status`).textContent = 'Connected';
                            document.getElementById(`${service}-status`).className = 'panel-status status-connected';
                        }
                    });
                });
                
                // Scrape data
                document.getElementById(`${service}-scrape-btn`).addEventListener('click', function() {
                    pywebview.api.scrape_ai_data(service).then(result => {
                        console.log(`Scraped data from ${service}:`, result);
                        alert(`Data scraped from ${service}!`);
                    });
                });
                
                // Send individual message
                document.getElementById(`${service}-msg-btn`).addEventListener('click', function() {
                    const message = prompt(`Enter message for ${service}:`);
                    if (message) {
                        pywebview.api.send_message_to_ai(service, message).then(result => {
                            console.log(`Message sent to ${service}:`, result);
                            alert(`Message sent to ${service}!`);
                        });
                    }
                });
            });
            
            // Send message to all active AIs
            document.getElementById('send-all-btn').addEventListener('click', function() {
                const message = document.getElementById('main-chat-input').value;
                if (message.trim()) {
                    pywebview.api.send_message_to_all_active(message).then(results => {
                        console.log('Messages sent to all active AIs:', results);
                        alert('Messages sent to all active AI panels!');
                        document.getElementById('main-chat-input').value = '';
                    });
                }
            });
            
            // Scrape all active panels
            document.getElementById('scrape-all-btn').addEventListener('click', function() {
                services.forEach(service => {
                    pywebview.api.scrape_ai_data(service).then(result => {
                        console.log(`Scraped data from ${service}:`, result);
                    });
                });
                alert('Scraping data from all active panels!');
            });
            
            // Test compatibility
            document.getElementById('test-compatibility-btn').addEventListener('click', function() {
                alert('Testing browser compatibility for all AI services...');
                services.forEach(service => {
                    pywebview.api.start_ai_browser(service);
                });
            });
            
            // Handle Enter key in chat input
            document.getElementById('main-chat-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    document.getElementById('send-all-btn').click();
                }
            });
        </script>
    </body>
    </html>
    """
    
    return webview.create_window(
        title='AI Chatbot - 4 Panel Desktop',
        html=html_content,
        width=1200,
        height=800,
        resizable=True,
        shadow=True,
        js_api=app
    )

def main():
    main_window = create_main_window()
    
    webview.start(debug=True)

def main_embedded():
    """Entry point for the embedded browser version"""
    from desktop_app_embedded import main as embedded_main
    embedded_main()

if __name__ == '__main__':
    main()
