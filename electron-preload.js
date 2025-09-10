const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    createAIView: (serviceName) => ipcRenderer.invoke('create-ai-view', serviceName),
    destroyAIView: (serviceName) => ipcRenderer.invoke('destroy-ai-view', serviceName),
    sendMessage: (serviceName, message) => ipcRenderer.invoke('send-message', serviceName, message),
    scrapeData: (serviceName) => ipcRenderer.invoke('scrape-data', serviceName),
    getPythonStatus: () => ipcRenderer.invoke('get-python-status'),
    
    onPythonLog: (callback) => ipcRenderer.on('python-log', callback),
    onAIResponse: (callback) => ipcRenderer.on('ai-response', callback)
});
