const { BrowserWindow, Menu } = require('electron');
const config = require('../utils/config');
const path = require('path');

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow(config.window);
    mainWindow.loadFile('index.html');

    // Remove menu bar while keeping title bar
    // Menu.setApplicationMenu(null);

    // Open the DevTools in development mode
    if (process.env.NODE_ENV === 'development') {
        mainWindow.webContents.openDevTools();
    }

    return mainWindow;
}

function getMainWindow() {
    return mainWindow;
}

module.exports = {
    createWindow,
    getMainWindow
};
