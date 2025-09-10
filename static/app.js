class ChatApp {
    constructor() {
        this.baseUrl = 'http://localhost:5001';
        this.userId = 'web_user';
        this.panels = new Map();
        this.compatibilityResults = null;
        this.init();
        
        window.addEventListener('beforeunload', () => {
            this.closeAllWindows();
        });
    }

    init() {
        this.initPanels();
        this.initAskAll();
        this.initScrapingControls();
        this.checkHealth();
        this.testIframeCompatibility();
    }

    initPanels() {
        const panelElements = document.querySelectorAll('.ai-panel');
        panelElements.forEach(panelEl => {
            const model = panelEl.dataset.model;
            const panel = new AIPanel(panelEl, model, this);
            this.panels.set(model, panel);
        });
    }

    initAskAll() {
        const input = document.getElementById('ask-all-input');
        const button = document.getElementById('ask-all-button');
        const loading = document.querySelector('.ask-all-loading');

        const sendToAll = async () => {
            const message = input.value.trim();
            if (!message) return;

            const enabledPanels = Array.from(this.panels.values()).filter(panel => panel.isEnabled);
            if (enabledPanels.length === 0) {
                alert('No panels are enabled. Please enable at least one AI panel.');
                return;
            }

            input.disabled = true;
            button.disabled = true;
            loading.style.display = 'flex';
            input.value = '';

            enabledPanels.forEach(panel => {
                panel.injectMessage(message);
            });

            setTimeout(() => {
                input.disabled = false;
                button.disabled = false;
                loading.style.display = 'none';
            }, 3000);
        };

        button.addEventListener('click', sendToAll);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendToAll();
        });
    }

    initScrapingControls() {
        const scrapeAllButton = document.getElementById('scrape-all-button');
        const testCompatibilityButton = document.getElementById('test-compatibility-button');

        scrapeAllButton.addEventListener('click', () => {
            this.scrapeAllActivePanels();
        });

        testCompatibilityButton.addEventListener('click', () => {
            this.testIframeCompatibility();
        });
    }

    async checkHealth() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            const isHealthy = response.ok;
            this.updateConnectionStatus(isHealthy);
        } catch (error) {
            this.updateConnectionStatus(false);
        }
    }

    updateConnectionStatus(isConnected) {
        this.panels.forEach(panel => {
            panel.updateConnectionStatus(isConnected);
        });
    }

    async testIframeCompatibility() {
        try {
            const response = await fetch(`${this.baseUrl}/get_browser_sessions`);
            const sessions = await response.json();
            console.log('Browser sessions status:', sessions);
            
            this.panels.forEach(panel => {
                const sessionInfo = sessions[panel.model];
                if (sessionInfo && sessionInfo.is_active) {
                    panel.sessionActive = true;
                    panel.updateUI();
                }
            });
        } catch (error) {
            console.error('Failed to check browser sessions:', error);
        }
    }

    async scrapeAllActivePanels() {
        const enabledPanels = Array.from(this.panels.values()).filter(panel => panel.isEnabled);
        if (enabledPanels.length === 0) {
            alert('No panels are enabled. Please enable at least one AI panel.');
            return;
        }

        for (const panel of enabledPanels) {
            await panel.scrapeData();
        }
    }
    
    closeAllWindows() {
        this.panels.forEach(panel => {
            if (panel.aiWindow && !panel.aiWindow.closed) {
                panel.aiWindow.close();
            }
        });
    }
}

class AIPanel {
    constructor(element, model, app) {
        this.element = element;
        this.model = model;
        this.app = app;
        this.url = element.dataset.url;
        this.isEnabled = false;
        this.isConnected = false;
        this.sessionActive = false;
        this.messages = [];
        this.aiWindow = null;
        
        this.initElements();
        this.initEventListeners();
        this.updateUI();
    }

    initElements() {
        this.checkbox = this.element.querySelector('input[type="checkbox"]');
        this.statusIndicator = this.element.querySelector('.status-indicator');
        this.statusText = this.element.querySelector('.status-text');
        this.startSessionBtn = this.element.querySelector('.start-session-btn');
        this.previewMessages = this.element.querySelector('.preview-messages');
        this.previewInput = this.element.querySelector('.preview-input input');
        this.sendIndividualBtn = this.element.querySelector('.send-individual-btn');
        this.scrapeButton = this.element.querySelector('.scrape-button');
        this.refreshButton = this.element.querySelector('.refresh-button');
        this.connectionStatus = this.element.querySelector('.connection-status');
        
        this.isEnabled = this.checkbox.checked;
    }

    initEventListeners() {
        this.checkbox.addEventListener('change', () => {
            this.isEnabled = this.checkbox.checked;
            this.updateUI();
        });

        this.startSessionBtn.addEventListener('click', () => {
            this.startBrowserSession();
        });

        this.sendIndividualBtn.addEventListener('click', () => {
            this.sendIndividualMessage();
        });

        this.previewInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendIndividualMessage();
            }
        });

        this.scrapeButton.addEventListener('click', () => {
            this.scrapeData();
        });

        this.refreshButton.addEventListener('click', () => {
            this.refreshSession();
        });
    }

    updateUI() {
        if (this.isEnabled) {
            this.element.classList.remove('disabled');
        } else {
            this.element.classList.add('disabled');
        }

        this.startSessionBtn.disabled = !this.isEnabled || this.sessionActive;
        this.previewInput.disabled = !this.isEnabled || !this.sessionActive;
        this.sendIndividualBtn.disabled = !this.isEnabled || !this.sessionActive;
        this.scrapeButton.disabled = !this.isEnabled || !this.sessionActive;
        this.refreshButton.disabled = !this.isEnabled;
        
        if (this.sessionActive) {
            this.statusIndicator.className = 'status-indicator connected';
            this.statusText.textContent = 'Connected';
            this.startSessionBtn.textContent = 'Active';
        } else {
            this.statusIndicator.className = 'status-indicator disconnected';
            this.statusText.textContent = 'Not Connected';
            this.startSessionBtn.textContent = 'Start Session';
        }
    }

    updateConnectionStatus(isConnected) {
        this.isConnected = isConnected;
        if (this.connectionStatus) {
            this.connectionStatus.textContent = isConnected ? 'Ready' : 'Disconnected';
            this.connectionStatus.className = `connection-status ${isConnected ? 'connected' : 'disconnected'}`;
        }
        this.updateUI();
    }

    async startBrowserSession() {
        if (!this.isEnabled) return;

        this.statusIndicator.className = 'status-indicator connecting';
        this.statusText.textContent = 'Connecting...';
        this.startSessionBtn.disabled = true;

        try {
            const aiWindow = window.open(this.url, `${this.model}_tab`, 'width=1200,height=800,scrollbars=yes,resizable=yes');
            
            const response = await fetch(`${this.app.baseUrl}/start_browser_session`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    service: this.model,
                    url: this.url
                }),
            });

            const result = await response.json();
            
            if (result.success) {
                this.sessionActive = true;
                this.aiWindow = aiWindow;
                this.addPreviewMessage('System', `Browser session started. AI site opened in new tab. Please login and start chatting.`);
            } else {
                if (aiWindow) aiWindow.close();
                throw new Error(result.error || 'Failed to start session');
            }
        } catch (error) {
            console.error(`Failed to start session for ${this.model}:`, error);
            this.addPreviewMessage('Error', `Failed to start session: ${error.message}`);
        }

        this.updateUI();
    }

    async sendIndividualMessage() {
        const message = this.previewInput.value.trim();
        if (!message || !this.sessionActive) return;

        this.addPreviewMessage('You', message);
        this.previewInput.value = '';
        this.previewInput.disabled = true;
        this.sendIndividualBtn.disabled = true;

        try {
            const response = await fetch(`${this.app.baseUrl}/send_message_to_ai`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    service: this.model,
                    message: message
                }),
            });

            const result = await response.json();
            
            if (result.success) {
                this.addPreviewMessage(this.model, result.response_preview || 'Message sent successfully');
            } else {
                throw new Error(result.error || 'Failed to send message');
            }
        } catch (error) {
            console.error(`Failed to send message to ${this.model}:`, error);
            this.addPreviewMessage('Error', `Failed to send message: ${error.message}`);
        }

        this.previewInput.disabled = false;
        this.sendIndividualBtn.disabled = false;
    }

    addPreviewMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `preview-message ${sender === 'You' ? 'user' : 'bot'}`;
        messageDiv.innerHTML = `<strong>${sender}:</strong> ${text}`;
        this.previewMessages.appendChild(messageDiv);
        this.previewMessages.scrollTop = this.previewMessages.scrollHeight;
    }

    refreshSession() {
        if (this.sessionActive) {
            if (this.aiWindow && !this.aiWindow.closed) {
                this.aiWindow.close();
            }
            this.sessionActive = false;
            this.aiWindow = null;
            this.updateUI();
            this.startBrowserSession();
        }
    }

    async injectMessage(message) {
        if (!this.sessionActive) return false;

        try {
            const response = await fetch(`${this.app.baseUrl}/inject_message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    service: this.model,
                    message: message
                }),
            });

            const result = await response.json();
            
            if (result.success) {
                this.addPreviewMessage('Broadcast', message);
                return true;
            }
            return false;
        } catch (error) {
            console.error(`Failed to inject message into ${this.model}:`, error);
            return false;
        }
    }

    async scrapeData() {
        if (!this.isEnabled || !this.sessionActive) return;

        this.scrapeButton.disabled = true;
        this.scrapeButton.innerHTML = '<span class="material-icons">hourglass_empty</span>Scraping...';

        try {
            const response = await fetch(`${this.app.baseUrl}/scrape_chat_data`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    service: this.model
                }),
            });

            const result = await response.json();
            
            if (result.success) {
                console.log(`Scraped data for ${this.model}:`, result.data_preview);
                this.scrapeButton.innerHTML = '<span class="material-icons">check</span>Scraped!';
                this.scrapeButton.style.backgroundColor = '#4caf50';
                this.addPreviewMessage('System', `Data scraped: ${result.data_preview.chat_elements_count} messages`);
                
                setTimeout(() => {
                    this.scrapeButton.innerHTML = '<span class="material-icons">download</span>Scrape Data';
                    this.scrapeButton.style.backgroundColor = '';
                    this.scrapeButton.disabled = false;
                }, 2000);
            } else {
                throw new Error(result.error || 'Scraping failed');
            }
        } catch (error) {
            console.error(`Failed to scrape ${this.model}:`, error);
            this.scrapeButton.innerHTML = '<span class="material-icons">error</span>Failed';
            this.scrapeButton.style.backgroundColor = '#f44336';
            this.addPreviewMessage('Error', `Scraping failed: ${error.message}`);
            
            setTimeout(() => {
                this.scrapeButton.innerHTML = '<span class="material-icons">download</span>Scrape Data';
                this.scrapeButton.style.backgroundColor = '';
                this.scrapeButton.disabled = false;
            }, 2000);
        }
    }

    getModelIcon() {
        const icons = {
            'chatgpt': 'chat',
            'mistral': 'psychology',
            'claude': 'assistant',
            'gemini': 'auto_awesome'
        };
        return icons[this.model] || 'chat';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
