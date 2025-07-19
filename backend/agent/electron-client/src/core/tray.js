const { Tray, Menu } = require('electron');
const path = require('path');
const config = require('../utils/config');
const { getMainWindow } = require('./window');

let tray = null;

function createTray() {
    const iconPath = path.join(__dirname, '../../', config.assets.icon);
    tray = new Tray(iconPath);
    updateTrayMenu();
    return tray;
}

function updateTrayMenu() {
    const mainWindow = getMainWindow();
    
    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Container Actions',
            submenu: [
                {
                    label: 'Create',
                    icon: path.join(__dirname, '../../', config.assets.icons.create),
                    click: () => mainWindow.webContents.send('container-action', 'create')
                },
                {
                    label: 'Start',
                    icon: path.join(__dirname, '../../', config.assets.icons.start),
                    click: () => mainWindow.webContents.send('container-action', 'start')
                },
                {
                    label: 'Stop',
                    icon: path.join(__dirname, '../../', config.assets.icons.stop),
                    click: () => mainWindow.webContents.send('container-action', 'stop')
                },
                {
                    label: 'Restart',
                    icon: path.join(__dirname, '../../', config.assets.icons.restart),
                    click: () => mainWindow.webContents.send('container-action', 'restart')
                },
                {
                    label: 'Remove',
                    icon: path.join(__dirname, '../../', config.assets.icons.remove),
                    click: () => mainWindow.webContents.send('container-action', 'remove')
                }
            ]
        },
        {
            label: 'Services',
            submenu: [
                {
                    label: 'VS Code',
                    icon: path.join(__dirname, '../../', config.assets.icons.vscode),
                    click: () => mainWindow.webContents.send('service-action', 'vscode')
                },
                {
                    label: 'SSH',
                    icon: path.join(__dirname, '../../', config.assets.icons.ssh),
                    click: () => mainWindow.webContents.send('service-action', 'ssh')
                },
                {
                    label: 'RDP',
                    icon: path.join(__dirname, '../../', config.assets.icons.rdp),
                    click: () => mainWindow.webContents.send('service-action', 'rdp')
                },
                {
                    label: 'FM UI',
                    icon: path.join(__dirname, '../../', config.assets.icons.fm),
                    click: () => mainWindow.webContents.send('service-action', 'fm')
                }
            ]
        }
    ]);

    tray.setContextMenu(contextMenu);
}

module.exports = {
    createTray,
    updateTrayMenu
};
