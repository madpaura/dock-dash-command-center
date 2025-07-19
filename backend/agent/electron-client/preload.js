const { contextBridge, ipcRenderer, shell } = require('electron')
const { showLoading, hideLoading, resetUI } = require('./src/utils/ui')

contextBridge.exposeInMainWorld('electronAPI', {
    // UI Utilities
    showLoading: showLoading,
    hideLoading: hideLoading,
    resetUI: resetUI,
    
  // Auth related
  login: (username, password) => ipcRenderer.invoke('login', { username, password }),
  validateSession: (userId, sessionToken) => ipcRenderer.invoke('validate-session', { userId, sessionToken }),
  logout: (userId) => ipcRenderer.invoke('logout', { userId }),
  getUserInfo: (userId) => ipcRenderer.invoke('get-user-info', { userId }),

  // Container related
  setContainerApi: (ip, port) => ipcRenderer.invoke('set-container-api', { ip, port }),
  getContainerStats: (containerId) => ipcRenderer.invoke('get-container-stats', containerId),
  getContainerInfo: (containerId) => ipcRenderer.invoke('get-container-info', containerId),
  containerAction: (action, containerId) => ipcRenderer.invoke('container-action', { action, containerId }),
  containerCreate: (username, sessionToken) => ipcRenderer.invoke('container-create', username, sessionToken),
  getContainerPorts: (containerId) => ipcRenderer.invoke('get-container-ports', containerId),

  // Other
  generateUserHash: (username) => ipcRenderer.invoke('generate-user-hash', username),
  closeApp: () => ipcRenderer.invoke('close-app'),
  
  // Service connections
  sshConnect: (username, host, port) => ipcRenderer.invoke('ssh-connect', { username, host, port }),
  vscodeConnect: (host, port) => ipcRenderer.invoke('vscode-connect', { host, port }),
  rdpConnect: (host, port, spice_port) => ipcRenderer.invoke('rdp-connect', { host, port, spice_port}),
  fmConnect: (host, port) => ipcRenderer.invoke('fm-connect', { host, port }),
  
  // Utilities
  openExternal: (url) => shell.openExternal(url),
  
  // Event listeners
  on: (channel, callback) => {
    ipcRenderer.on(channel, (event, ...args) => callback(...args))
  }
})