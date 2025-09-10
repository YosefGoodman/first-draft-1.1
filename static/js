class ChatApp {
    constructor() {
        this.baseUrl = 'http://localhost:5001';
        this.userId = 'web_user';
        this.panels = new Map();
        this.init();
    }

    init() {
        this.initPanels();
        this.initAskAll();
        this.checkHealth();
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
            if (enabledPanels.length === 0) return;

            input.disabled = true;
            button.disabled = true;
            loading.style.display = 'flex';
            input.value = '';

            enabledPanels.forEach(panel => {
                panel.sendMessage(message);
            });

            setTimeout(() => {
                input.disabled = false;
                button.disabled = false;
                loading.style.display = 'none';
            }, 2000);
        };

        button.addEventListener('click', sendToAll);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendToAll();
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

    async sendMessage(userId, message, model) {
        const response = await fetch(`${this.baseUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                message: message,
                model: model,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }
}

class AIPanel {
    constructor(element, model, app) {
        this.element = element;
        this.model = model;
        this.app = app;
        this.isEnabled = false;
        this.isConnected = false;
        this.messages = [];
        
        this.initElements();
        this.initEventListeners();
        this.updateUI();
    }

    initElements() {
        this.checkbox = this.element.querySelector('input[type="checkbox"]');
        this.messagesContainer = this.element.querySelector('.messages-container');
        this.messageInput = this.element.querySelector('.message-input');
        this.sendButton = this.element.querySelector('.send-button');
        this.copyButton = this.element.querySelector('.copy-button');
        this.connectionStatus = this.element.querySelector('.connection-status');
        
        this.isEnabled = this.checkbox.checked;
    }

    initEventListeners() {
        this.checkbox.addEventListener('change', () => {
            this.isEnabled = this.checkbox.checked;
            this.updateUI();
        });

        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });

        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        this.copyButton.addEventListener('click', () => {
            this.copyLastResponse();
        });
    }

    updateUI() {
        if (this.isEnabled) {
            this.element.classList.remove('disabled');
            this.messageInput.placeholder = 'Type your message...';
            this.messageInput.disabled = !this.isConnected;
            this.sendButton.disabled = !this.isConnected;
        } else {
            this.element.classList.add('disabled');
            this.messageInput.placeholder = 'Panel disabled';
            this.messageInput.disabled = true;
            this.sendButton.disabled = true;
        }

        this.copyButton.disabled = !this.isEnabled || this.messages.length === 0;
    }

    updateConnectionStatus(isConnected) {
        this.isConnected = isConnected;
        this.connectionStatus.textContent = isConnected ? 'Connected' : 'Disconnected';
        this.connectionStatus.className = `connection-status ${isConnected ? 'connected' : 'disconnected'}`;
        this.updateUI();
    }

    async sendMessage(customMessage = null) {
        const message = customMessage || this.messageInput.value.trim();
        if (!message || !this.isEnabled || !this.isConnected) return;

        this.addMessage(message, true);
        if (!customMessage) {
            this.messageInput.value = '';
        }

        this.showLoading();

        try {
            const response = await this.app.sendMessage(this.app.userId, message, this.model);
            this.hideLoading();
            this.addMessage(response.response || 'No response received', false);
        } catch (error) {
            this.hideLoading();
            this.addMessage(`Error: ${error.message}`, false);
        }

        this.updateUI();
    }

    addMessage(text, isUser) {
        const message = {
            text,
            isUser,
            timestamp: new Date()
        };
        
        this.messages.push(message);
        this.renderMessages();
        this.scrollToBottom();
    }

    renderMessages() {
        if (this.messages.length === 0) {
            this.messagesContainer.innerHTML = `
                <div class="empty-state">
                    <span class="material-icons">chat_bubble_outline</span>
                    <span>No messages yet</span>
                </div>
            `;
            return;
        }

        this.messagesContainer.innerHTML = this.messages.map(message => {
            const time = message.timestamp.toLocaleTimeString('en-US', { 
                hour12: false, 
                hour: '2-digit', 
                minute: '2-digit' 
            });

            const iconName = this.getModelIcon();
            
            return `
                <div class="message ${message.isUser ? 'user' : 'bot'}">
                    <div class="message-avatar ${message.isUser ? 'user' : 'bot'}">
                        <span class="material-icons">${message.isUser ? 'person' : iconName}</span>
                    </div>
                    <div class="message-content">
                        <div>${message.text}</div>
                        <div class="message-time">${time}</div>
                    </div>
                </div>
            `;
        }).join('');
    }

    showLoading() {
        const iconName = this.getModelIcon();
        const loadingHtml = `
            <div class="loading-message">
                <div class="message-avatar bot">
                    <span class="material-icons">${iconName}</span>
                </div>
                <div class="loading-content">
                    <div class="loading-spinner"></div>
                    <span>Thinking...</span>
                </div>
            </div>
        `;
        
        this.messagesContainer.insertAdjacentHTML('beforeend', loadingHtml);
        this.scrollToBottom();
    }

    hideLoading() {
        const loadingMessage = this.messagesContainer.querySelector('.loading-message');
        if (loadingMessage) {
            loadingMessage.remove();
        }
    }

    scrollToBottom() {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }

    copyLastResponse() {
        const lastBotMessage = this.messages.slice().reverse().find(msg => !msg.isUser);
        if (lastBotMessage) {
            navigator.clipboard.writeText(lastBotMessage.text).then(() => {
                this.showCopyFeedback();
            });
        }
    }

    showCopyFeedback() {
        const originalText = this.copyButton.innerHTML;
        this.copyButton.innerHTML = '<span class="material-icons">check</span>Copied!';
        this.copyButton.style.backgroundColor = '#4caf50';
        
        setTimeout(() => {
            this.copyButton.innerHTML = originalText;
            this.copyButton.style.backgroundColor = '';
        }, 2000);
    }

    getModelIcon() {
        const icons = {
            'openai': 'chat',
            'mistral': 'psychology',
            'llama': 'smart_toy',
            'claude': 'assistant'
        };
        return icons[this.model] || 'chat';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
