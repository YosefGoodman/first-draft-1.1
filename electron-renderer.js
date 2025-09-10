class ElectronAIControlPanel {
    constructor() {
        this.services = ['chatgpt', 'claude', 'mistral', 'gemini'];
        this.activeServices = new Set();
        this.logPanel = document.getElementById('log-panel');
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkPythonStatus();
        this.log('Electron AI Control Panel ready', 'info');
    }

    setupEventListeners() {
        this.services.forEach(service => {
            const serviceElement = document.querySelector(`[data-service="${service}"]`);
            const startBtn = serviceElement.querySelector('.start-session');
            const stopBtn = serviceElement.querySelector('.stop-session');
            const scrapeBtn = serviceElement.querySelector('.scrape-data');

            startBtn.addEventListener('click', () => this.startSession(service));
            stopBtn.addEventListener('click', () => this.stopSession(service));
            scrapeBtn.addEventListener('click', () => this.scrapeData(service));
        });

        document.getElementById('send-all').addEventListener('click', () => this.sendToAll());
        document.getElementById('scrape-all').addEventListener('click', () => this.scrapeAll());
        document.getElementById('toggle-logs').addEventListener('click', () => this.toggleLogs());

        document.querySelector('.global-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendToAll();
            }
        });
    }

    async startSession(service) {
        this.log(`Starting session for ${service}...`, 'info');
        this.updateServiceStatus(service, 'connecting');

        try {
            const result = await window.electronAPI.createAIView(service);
            
            if (result.success) {
                this.activeServices.add(service);
                this.updateServiceStatus(service, 'connected');
                this.log(`${service} session started successfully`, 'success');
            } else {
                this.updateServiceStatus(service, 'disconnected');
                this.log(`Failed to start ${service}: ${result.message}`, 'error');
            }
        } catch (error) {
            this.updateServiceStatus(service, 'disconnected');
            this.log(`Error starting ${service}: ${error.message}`, 'error');
        }
    }

    async stopSession(service) {
        this.log(`Stopping session for ${service}...`, 'info');

        try {
            const result = await window.electronAPI.destroyAIView(service);
            
            if (result.success) {
                this.activeServices.delete(service);
                this.updateServiceStatus(service, 'disconnected');
                this.log(`${service} session stopped`, 'info');
            } else {
                this.log(`Failed to stop ${service}: ${result.message}`, 'error');
            }
        } catch (error) {
            this.log(`Error stopping ${service}: ${error.message}`, 'error');
        }
    }

    async sendMessage(service, message) {
        this.log(`Sending message to ${service}: ${message.substring(0, 50)}...`, 'info');

        try {
            const result = await window.electronAPI.sendMessage(service, message);
            
            if (result.success) {
                this.log(`Message sent to ${service} successfully`, 'success');
                return true;
            } else {
                this.log(`Failed to send message to ${service}: ${result.message}`, 'error');
                return false;
            }
        } catch (error) {
            this.log(`Error sending message to ${service}: ${error.message}`, 'error');
            return false;
        }
    }

    async scrapeData(service) {
        this.log(`Scraping data from ${service}...`, 'info');

        try {
            const result = await window.electronAPI.scrapeData(service);
            
            if (result.success) {
                this.log(`Scraped ${result.chatElements.length} messages from ${service}`, 'success');
                return result;
            } else {
                this.log(`Failed to scrape ${service}: ${result.message}`, 'error');
                return null;
            }
        } catch (error) {
            this.log(`Error scraping ${service}: ${error.message}`, 'error');
            return null;
        }
    }

    async sendToAll() {
        const input = document.querySelector('.global-input');
        const message = input.value.trim();
        
        if (!message) {
            this.log('No message to send', 'error');
            return;
        }

        const enabledServices = this.getEnabledServices();
        if (enabledServices.length === 0) {
            this.log('No services enabled for broadcast', 'error');
            return;
        }

        this.log(`Broadcasting message to ${enabledServices.length} services`, 'info');

        const results = await Promise.all(
            enabledServices.map(service => this.sendMessage(service, message))
        );

        const successCount = results.filter(r => r).length;
        this.log(`Broadcast complete: ${successCount}/${enabledServices.length} successful`, 'info');

        input.value = '';
    }

    async scrapeAll() {
        const enabledServices = this.getEnabledServices();
        if (enabledServices.length === 0) {
            this.log('No services enabled for scraping', 'error');
            return;
        }

        this.log(`Scraping data from ${enabledServices.length} services`, 'info');

        const results = await Promise.all(
            enabledServices.map(service => this.scrapeData(service))
        );

        const successCount = results.filter(r => r !== null).length;
        this.log(`Scraping complete: ${successCount}/${enabledServices.length} successful`, 'info');
    }

    getEnabledServices() {
        return this.services.filter(service => {
            const checkbox = document.querySelector(`[data-service="${service}"] .service-checkbox`);
            return checkbox.checked && this.activeServices.has(service);
        });
    }

    updateServiceStatus(service, status) {
        const serviceElement = document.querySelector(`[data-service="${service}"]`);
        const statusIndicator = serviceElement.querySelector('.status-indicator');
        const statusText = serviceElement.querySelector('.service-status');
        const startBtn = serviceElement.querySelector('.start-session');
        const stopBtn = serviceElement.querySelector('.stop-session');
        const scrapeBtn = serviceElement.querySelector('.scrape-data');

        statusIndicator.className = 'status-indicator';
        statusIndicator.classList.add(`status-${status}`);

        const statusTexts = {
            'connected': 'Connected',
            'disconnected': 'Not Connected',
            'connecting': 'Connecting...'
        };
        statusText.textContent = statusTexts[status] || status;

        if (status === 'connected') {
            startBtn.disabled = true;
            stopBtn.disabled = false;
            scrapeBtn.disabled = false;
        } else if (status === 'connecting') {
            startBtn.disabled = true;
            stopBtn.disabled = true;
            scrapeBtn.disabled = true;
        } else {
            startBtn.disabled = false;
            stopBtn.disabled = true;
            scrapeBtn.disabled = true;
        }
    }

    async checkPythonStatus() {
        try {
            const isRunning = await window.electronAPI.getPythonStatus();
            this.log(`Python backend status: ${isRunning ? 'Running' : 'Not running'}`, 'info');
        } catch (error) {
            this.log(`Error checking Python status: ${error.message}`, 'error');
        }
    }

    log(message, type = 'info') {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        
        this.logPanel.appendChild(logEntry);
        this.logPanel.scrollTop = this.logPanel.scrollHeight;

        const entries = this.logPanel.querySelectorAll('.log-entry');
        if (entries.length > 50) {
            entries[0].remove();
        }

        console.log(`[${type.toUpperCase()}] ${message}`);
    }

    toggleLogs() {
        this.logPanel.classList.toggle('visible');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ElectronAIControlPanel();
});
