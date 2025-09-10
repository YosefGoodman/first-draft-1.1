#!/usr/bin/env python3
import json
import os
import time
import threading
import http.server
import socketserver
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from urllib.parse import urlparse, parse_qs
import signal
import sys
import platform
from database import init_db, save_interaction, get_similar_context
#change this path to desired location to keep scraped data.
DEFAULT_WINDOWS_PATH = r"C:\Users\yosef\OneDrive\Desktop\Attachments"
DEFAULT_LINUX_PATH = "/home/ubuntu/scraped_data"
STORAGE_PATH = os.environ.get('AI_STORAGE_PATH', DEFAULT_WINDOWS_PATH if platform.system() == 'Windows' else DEFAULT_LINUX_PATH)
if not os.path.exists(STORAGE_PATH):
    os.makedirs(STORAGE_PATH)

embedding_model = None
browser_sessions = {}
server = None

def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return embedding_model

class BrowserSession:
    def __init__(self, service_name, url):
        self.service_name = service_name
        self.url = url
        self.driver = None
        self.is_active = False
        self.last_scraped_data = None
        self.window_handle = None
        
    def start_session(self):
        try:
            print(f"Starting browser session for {self.service_name} at {self.url}")
            print(f"Note: Using window.open() approach - user will interact manually with opened tab")
            
            self.driver = None
            self.is_active = True
            self.window_handle = None
            
            return True
        except Exception as e:
            print(f"Failed to start browser session for {self.service_name}: {e}")
            return False
    
    def inject_message(self, message):
        if not self.is_active:
            return False
            
        try:
            print(f"Preparing enhanced message for {self.service_name}: {message}")
            
            similar_context = get_similar_context("web_user", message, limit=3)
            enhanced_message = message
            if similar_context:
                context_text = "\n".join(similar_context)
                enhanced_message = f"Context from previous conversations:\n{context_text}\n\nCurrent question: {message}"
            
            timestamp = datetime.now().isoformat()
            interaction_data = {
                'timestamp': timestamp,
                'service': self.service_name,
                'message': message,
                'enhanced_message': enhanced_message,
                'status': 'ready_for_manual_input',
                'instructions': f'Please copy this enhanced message to the {self.service_name} tab and send it manually'
            }
            
            filename = f"message_{self.service_name}_{timestamp.replace(':', '-')}.json"
            filepath = os.path.join(STORAGE_PATH, filename)
            
            with open(filepath, 'w') as f:
                json.dump(interaction_data, f, indent=2)
            
            print(f"Enhanced message saved to: {filepath}")
            print(f"Enhanced message: {enhanced_message}")
            
            return True
            
        except Exception as e:
            print(f"Failed to inject message into {self.service_name}: {e}")
            return False
    
    def _inject_message_by_site(self, message):
        print(f"Manual message injection for {self.service_name}: User should copy the enhanced message to the browser tab")
        return True
    
    def scrape_current_data(self):
        if not self.is_active:
            return None
            
        try:
            print(f"Scraping simulation for {self.service_name} - user should manually copy conversation data")
            
            timestamp = datetime.now().isoformat()
            scraped_data = {
                'service': self.service_name,
                'url': self.url,
                'timestamp': timestamp,
                'title': f'{self.service_name} - Manual Chat Session',
                'chat_elements': [
                    {
                        'role': 'system',
                        'text': f'Manual scraping placeholder for {self.service_name}. User should copy actual conversation data.',
                        'html': '<div>Manual scraping placeholder</div>'
                    }
                ],
                'full_text': f'Manual scraping session for {self.service_name}. Please copy actual conversation data from the browser tab.',
                'status': 'manual_scraping_required',
                'instructions': f'Please manually copy conversation data from the {self.service_name} browser tab'
            }
            
            model = get_embedding_model()
            embedding = model.encode(scraped_data['full_text'])
            scraped_data['embedding'] = embedding.tolist()
            
            self.last_scraped_data = scraped_data
            return scraped_data
            
        except Exception as e:
            print(f"Failed to create scraping placeholder for {self.service_name}: {e}")
            return None
    
    def _scrape_by_site(self):
        print(f"Manual scraping placeholder for {self.service_name}")
        return None
    
    def close_session(self):
        if self.driver:
            print(f"Closing browser session for {self.service_name}")
            self.driver.quit()
            self.driver = None
        self.is_active = False
        self.window_handle = None

class AIBrowserHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/home/ubuntu/repos/first-draft-1.1", **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/templates/index.html'
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {"status": "healthy", "timestamp": datetime.now().isoformat()}
            self.wfile.write(json.dumps(response).encode())
            return
        elif self.path == '/get_browser_sessions':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            sessions_info = {}
            for service, session in browser_sessions.items():
                sessions_info[service] = {
                    'service': service,
                    'url': session.url,
                    'is_active': session.is_active,
                    'has_data': session.last_scraped_data is not None
                }
            self.wfile.write(json.dumps(sessions_info).encode())
            return
        super().do_GET()
    
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            if self.path == '/start_browser_session':
                result = start_browser_session(data)
            elif self.path == '/close_browser_session':
                result = close_browser_session(data)
            elif self.path == '/inject_message':
                result = inject_message(data)
            elif self.path == '/scrape_chat_data':
                result = scrape_chat_data(data)
            elif self.path == '/send_message_to_ai':
                result = send_message_to_ai(data)
            else:
                self.send_response(404)
                self.end_headers()
                return
            
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def start_browser_session(data):
    service = data.get('service')
    url = data.get('url')
    
    if not service or not url:
        return {'error': 'Missing service or URL'}
    
    if service in browser_sessions:
        browser_sessions[service].close_session()
    
    session = BrowserSession(service, url)
    success = session.start_session()
    
    if success:
        browser_sessions[service] = session
        return {
            'success': True,
            'service': service,
            'url': url,
            'status': 'Browser session started'
        }
    else:
        return {'error': 'Failed to start browser session'}

def close_browser_session(data):
    service = data.get('service')
    
    if service in browser_sessions:
        browser_sessions[service].close_session()
        del browser_sessions[service]
        return {'success': True, 'message': f'Closed session for {service}'}
    
    return {'error': 'Session not found'}

def inject_message(data):
    service = data.get('service')
    message = data.get('message')
    
    if not service or not message:
        return {'error': 'Missing service or message'}
    
    if service not in browser_sessions:
        return {'error': 'Browser session not found'}
    
    session = browser_sessions[service]
    success = session.inject_message(message)
    
    if success:
        return {
            'success': True,
            'service': service,
            'message': 'Message injected successfully'
        }
    else:
        return {'error': 'Failed to inject message'}


def scrape_chat_data(data):
    service = data.get('service')
    
    if not service:
        return {'error': 'Missing service'}
    
    if service not in browser_sessions:
        return {'error': 'Browser session not found. Please start a session first.'}
    
    session = browser_sessions[service]
    scraped_data = session.scrape_current_data()
    
    if not scraped_data:
        return {'error': 'Failed to scrape data'}
    
    try:
        filename = f"{service}_{int(time.time())}.json"
        filepath = os.path.join(STORAGE_PATH, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(scraped_data, f, indent=2, ensure_ascii=False)
        
        return {
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'data_preview': {
                'title': scraped_data['title'],
                'chat_elements_count': len(scraped_data['chat_elements']),
                'text_length': len(scraped_data['full_text'])
            }
        }
        
    except Exception as e:
        return {'error': str(e)}

def get_scraped_files():
    try:
        files = []
        for filename in os.listdir(STORAGE_PATH):
            if filename.endswith('.json'):
                filepath = os.path.join(STORAGE_PATH, filename)
                stat = os.stat(filepath)
                files.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        return {'files': files, 'storage_path': STORAGE_PATH}
    except Exception as e:
        return {'error': str(e)}

def send_message_to_ai(data):
    service = data.get('service')
    message = data.get('message')
    
    if not service or not message:
        return {'error': 'Missing service or message'}
    
    if service not in browser_sessions:
        return {'error': 'Browser session not found'}
    
    session = browser_sessions[service]
    
    success = session.inject_message(message)
    if not success:
        return {'error': 'Failed to send message'}
    
    time.sleep(5)
    
    scraped_data = session.scrape_current_data()
    if scraped_data:
        filename = f"{service}_response_{int(time.time())}.json"
        filepath = os.path.join(STORAGE_PATH, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(scraped_data, f, indent=2, ensure_ascii=False)
        
        if scraped_data['chat_elements']:
            latest_response = scraped_data['chat_elements'][-1]['text']
            save_interaction("web_user", message, latest_response)
    
    latest_response = ""
    if scraped_data and scraped_data['chat_elements']:
        latest_response = scraped_data['chat_elements'][-1]['text'] if scraped_data['chat_elements'] else ""
    
    return {
        'success': True,
        'service': service,
        'message_sent': message,
        'response_preview': latest_response[:500],
        'scraped_file': filename if scraped_data else None
    }

def consolidate_storage_files():
    """
    Consolidate all JSON files in storage directory into a single file and delete originals
    """
    try:
        print(f"Checking for files to consolidate in: {STORAGE_PATH}")
        
        if not os.path.exists(STORAGE_PATH):
            print("Storage directory doesn't exist, skipping consolidation")
            return
        
        json_files = [f for f in os.listdir(STORAGE_PATH) if f.endswith('.json')]
        
        if len(json_files) <= 1:
            print(f"Found {len(json_files)} JSON files, no consolidation needed")
            return
        
        print(f"Found {len(json_files)} JSON files to consolidate")
        
        consolidated_data = {
            'consolidation_timestamp': datetime.now().isoformat(),
            'original_files_count': len(json_files),
            'consolidated_files': [],
            'all_interactions': [],
            'all_embeddings': []
        }
        
        files_to_delete = []
        
        for filename in json_files:
            filepath = os.path.join(STORAGE_PATH, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                
                consolidated_data['consolidated_files'].append({
                    'original_filename': filename,
                    'file_data': file_data
                })
                
                if 'chat_elements' in file_data:
                    consolidated_data['all_interactions'].extend(file_data['chat_elements'])
                
                if 'embedding' in file_data:
                    consolidated_data['all_embeddings'].append({
                        'source_file': filename,
                        'embedding': file_data['embedding']
                    })
                
                files_to_delete.append(filepath)
                print(f"Processed: {filename}")
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue
        
        if not consolidated_data['consolidated_files']:
            print("No valid files to consolidate")
            return
        
        consolidated_filename = f"consolidated_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        consolidated_filepath = os.path.join(STORAGE_PATH, consolidated_filename)
        
        with open(consolidated_filepath, 'w', encoding='utf-8') as f:
            json.dump(consolidated_data, f, indent=2, ensure_ascii=False)
        
        for filepath in files_to_delete:
            try:
                os.remove(filepath)
                print(f"Deleted: {os.path.basename(filepath)}")
            except Exception as e:
                print(f"Error deleting {filepath}: {e}")
        
        print(f"Consolidation complete! Created: {consolidated_filename}")
        print(f"Consolidated {len(files_to_delete)} files into 1 file")
        
    except Exception as e:
        print(f"Error during file consolidation: {e}")

def signal_handler(sig, frame):
    print('\nShutting down browser sessions...')
    for session in browser_sessions.values():
        session.close_session()
    if server:
        server.shutdown()
    sys.exit(0)

def main():
    global server
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Initializing database...")
    init_db()
    
    print("Consolidating storage files...")
    consolidate_storage_files()
    
    PORT = 5001
    print(f"Starting AI Browser Server on port {PORT}")
    print(f"Storage path: {STORAGE_PATH}")
    print("Open http://localhost:5001 in your browser")
    
    with socketserver.TCPServer(("", PORT), AIBrowserHandler) as httpd:
        server = httpd
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            signal_handler(None, None)

if __name__ == '__main__':
    main()
