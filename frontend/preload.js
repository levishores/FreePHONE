const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    getAppVersion: () => ipcRenderer.invoke('get-app-version'),
    showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
    
    // Add more IPC methods as needed
    onMenuAction: (callback) => ipcRenderer.on('menu-action', callback),
    removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel)
});
