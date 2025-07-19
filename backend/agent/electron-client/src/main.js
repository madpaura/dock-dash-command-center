const { app, BrowserWindow } = require('electron');
require('dotenv').config();

// Import core modules
const { createWindow } = require('./core/window');
const { createTray } = require('./core/tray');
const { setupAuthHandlers } = require('./core/auth');
const { setupContainerHandlers } = require('./core/container');
const { setupServiceHandlers } = require('./services/services');
const { setupUtilHandlers } = require('./core/utils-handler');

// Initialize the application
function initializeApp() {
    // Create main window
    const mainWindow = createWindow();

    // Create system tray
    createTray();

    // Setup IPC handlers
    setupAuthHandlers();
    setupContainerHandlers();
    setupServiceHandlers();
    setupUtilHandlers();

    // Handle window activation
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
}

// When app is ready
app.whenReady().then(initializeApp);

// Quit when all windows are closed
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
