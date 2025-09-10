const { app, BrowserWindow, BrowserView, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

class AIControlPanelElectron {
    constructor() {
        this.mainWindow = null;
        this.pythonProcess = null;
        this.aiViews = new Map();
        this.isDevMode = process.argv.includes('--dev');
        
        this.aiServices = [
            { name: 'chatgpt', url: 'https://chatgpt.com/', title: 'ChatGPT' },
            { name: 'claude', url: 'https://claude.ai/new', title: 'Claude' },
            { name: 'mistral', url: 'https://chat.mistral.ai/chat', title: 'Mistral' },
            { name: 'gemini', url: 'https://gemini.google.com/', title: 'Gemini' }
        ];
    }

    async createMainWindow() {
        this.mainWindow = new BrowserWindow({
            width: 1400,
            height: 1000,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                enableRemoteModule: false,
                preload: path.join(__dirname, 'electron-preload.js'),
                webSecurity: false
            },
            show: false,
            title: 'AI Control Panel - Electron'
        });

        await this.mainWindow.loadFile('electron-index.html');
        
        if (this.isDevMode) {
            this.mainWindow.webContents.openDevTools();
        }

        this.mainWindow.once('ready-to-show', () => {
            this.mainWindow.show();
        });

        this.mainWindow.on('closed', () => {
            this.cleanup();
        });

        this.setupIpcHandlers();
        this.startPythonBackend();
    }

    setupIpcHandlers() {
        ipcMain.handle('create-ai-view', async (event, serviceName) => {
            return await this.createAIView(serviceName);
        });

        ipcMain.handle('destroy-ai-view', async (event, serviceName) => {
            return await this.destroyAIView(serviceName);
        });

        ipcMain.handle('send-message', async (event, serviceName, message) => {
            return await this.sendMessageToAI(serviceName, message);
        });

        ipcMain.handle('scrape-data', async (event, serviceName) => {
            return await this.scrapeAIData(serviceName);
        });

        ipcMain.handle('get-python-status', async () => {
            return this.pythonProcess !== null;
        });
    }

    async createAIView(serviceName) {
        try {
            const service = this.aiServices.find(s => s.name === serviceName);
            if (!service) {
                throw new Error(`Unknown service: ${serviceName}`);
            }

            if (this.aiViews.has(serviceName)) {
                console.log(`View for ${serviceName} already exists`);
                return { success: true, message: 'View already exists' };
            }

            const view = new BrowserView({
                webPreferences: {
                    nodeIntegration: false,
                    contextIsolation: true,
                    webSecurity: false,
                    allowRunningInsecureContent: true
                }
            });

            this.mainWindow.addBrowserView(view);
            
            const bounds = this.calculateViewBounds(serviceName);
            view.setBounds(bounds);
            view.setAutoResize({ width: true, height: true });

            await view.webContents.loadURL(service.url);

            view.webContents.on('did-finish-load', () => {
                console.log(`${service.title} loaded successfully`);
            });

            view.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
                console.error(`Failed to load ${service.title}:`, errorDescription);
            });

            this.aiViews.set(serviceName, view);

            return { 
                success: true, 
                message: `${service.title} view created successfully`,
                url: service.url
            };

        } catch (error) {
            console.error(`Error creating view for ${serviceName}:`, error);
            return { 
                success: false, 
                message: error.message 
            };
        }
    }

    calculateViewBounds(serviceName) {
        const windowBounds = this.mainWindow.getBounds();
        const controlPanelHeight = 200;
        const availableHeight = windowBounds.height - controlPanelHeight;
        const viewWidth = Math.floor(windowBounds.width / 2);
        const viewHeight = Math.floor(availableHeight / 2);

        const positions = {
            'chatgpt': { x: 0, y: controlPanelHeight },
            'claude': { x: viewWidth, y: controlPanelHeight },
            'mistral': { x: 0, y: controlPanelHeight + viewHeight },
            'gemini': { x: viewWidth, y: controlPanelHeight + viewHeight }
        };

        return {
            x: positions[serviceName].x,
            y: positions[serviceName].y,
            width: viewWidth,
            height: viewHeight
        };
    }

    async destroyAIView(serviceName) {
        try {
            const view = this.aiViews.get(serviceName);
            if (view) {
                this.mainWindow.removeBrowserView(view);
                view.webContents.destroy();
                this.aiViews.delete(serviceName);
                return { success: true, message: `${serviceName} view destroyed` };
            }
            return { success: false, message: `No view found for ${serviceName}` };
        } catch (error) {
            console.error(`Error destroying view for ${serviceName}:`, error);
            return { success: false, message: error.message };
        }
    }

    async sendMessageToAI(serviceName, message) {
        try {
            const view = this.aiViews.get(serviceName);
            if (!view) {
                return { success: false, message: `No view found for ${serviceName}` };
            }

            const result = await view.webContents.executeJavaScript(`
                (function() {
                    const selectors = {
                        'chatgpt': ['textarea[data-id]', '#prompt-textarea', 'textarea', 'div[contenteditable="true"]'],
                        'claude': ['div[contenteditable="true"]', 'textarea', 'input[type="text"]'],
                        'mistral': ['textarea', 'input[type="text"]', 'div[contenteditable="true"]'],
                        'gemini': ['textarea', 'div[contenteditable="true"]', 'input[type="text"]']
                    };

                    const serviceSelectors = selectors['${serviceName}'] || selectors['chatgpt'];
                    
                    for (const selector of serviceSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            element.focus();
                            element.value = '${message.replace(/'/g, "\\'")}';
                            
                            if (element.tagName.toLowerCase() === 'div') {
                                element.textContent = '${message.replace(/'/g, "\\'")}';
                            }
                            
                            const inputEvent = new Event('input', { bubbles: true });
                            element.dispatchEvent(inputEvent);
                            
                            const enterEvent = new KeyboardEvent('keydown', {
                                key: 'Enter',
                                code: 'Enter',
                                keyCode: 13,
                                bubbles: true
                            });
                            element.dispatchEvent(enterEvent);
                            
                            return { success: true, selector: selector };
                        }
                    }
                    
                    return { success: false, message: 'No suitable input element found' };
                })();
            `);

            if (result.success) {
                console.log(`Message sent to ${serviceName} using selector: ${result.selector}`);
                return { 
                    success: true, 
                    message: `Message sent to ${serviceName}`,
                    selector: result.selector
                };
            } else {
                return { 
                    success: false, 
                    message: `Failed to find input element for ${serviceName}`
                };
            }

        } catch (error) {
            console.error(`Error sending message to ${serviceName}:`, error);
            return { success: false, message: error.message };
        }
    }

    async scrapeAIData(serviceName) {
        try {
            const view = this.aiViews.get(serviceName);
            if (!view) {
                return { success: false, message: `No view found for ${serviceName}` };
            }

            const result = await view.webContents.executeJavaScript(`
                (function() {
                    const chatElements = [];
                    const messageSelectors = [
                        '[data-message-author-role]',
                        '.message',
                        '[role="presentation"]',
                        '.conversation-turn',
                        '.chat-message'
                    ];

                    for (const selector of messageSelectors) {
                        const elements = document.querySelectorAll(selector);
                        if (elements.length > 0) {
                            elements.forEach((el, index) => {
                                const text = el.textContent.trim();
                                if (text) {
                                    chatElements.push({
                                        role: el.getAttribute('data-message-author-role') || 'unknown',
                                        text: text,
                                        index: index
                                    });
                                }
                            });
                            break;
                        }
                    }

                    return {
                        success: true,
                        chatElements: chatElements,
                        url: window.location.href,
                        title: document.title,
                        timestamp: new Date().toISOString()
                    };
                })();
            `);

            console.log(`Scraped ${result.chatElements.length} messages from ${serviceName}`);
            return result;

        } catch (error) {
            console.error(`Error scraping data from ${serviceName}:`, error);
            return { success: false, message: error.message };
        }
    }

    startPythonBackend() {
        try {
            console.log('Starting Python backend...');
            this.pythonProcess = spawn('python3', ['app.py'], {
                cwd: __dirname,
                stdio: ['pipe', 'pipe', 'pipe']
            });

            this.pythonProcess.stdout.on('data', (data) => {
                console.log(`Python Backend: ${data}`);
            });

            this.pythonProcess.stderr.on('data', (data) => {
                console.error(`Python Backend Error: ${data}`);
            });

            this.pythonProcess.on('close', (code) => {
                console.log(`Python backend exited with code ${code}`);
                this.pythonProcess = null;
            });

            setTimeout(() => {
                if (this.pythonProcess) {
                    console.log('Python backend started successfully');
                }
            }, 3000);

        } catch (error) {
            console.error('Failed to start Python backend:', error);
        }
    }

    cleanup() {
        if (this.pythonProcess) {
            console.log('Stopping Python backend...');
            this.pythonProcess.kill();
            this.pythonProcess = null;
        }

        this.aiViews.forEach((view, serviceName) => {
            try {
                this.mainWindow.removeBrowserView(view);
                view.webContents.destroy();
            } catch (error) {
                console.error(`Error cleaning up view for ${serviceName}:`, error);
            }
        });
        this.aiViews.clear();
    }
}

const electronApp = new AIControlPanelElectron();

app.whenReady().then(() => {
    electronApp.createMainWindow();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        electronApp.createMainWindow();
    }
});

app.on('before-quit', () => {
    electronApp.cleanup();
});
