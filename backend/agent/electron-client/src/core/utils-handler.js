const { ipcMain, app } = require('electron');
const { generateUserHash } = require('../utils/helpers');

function setupUtilHandlers() {
    // Handler for user hash generation
    ipcMain.handle('generate-user-hash', async (event, username) => {
        return generateUserHash(username);
    });

    // Handler for closing the app
    ipcMain.handle('close-app', () => {
        app.quit();
    });
}

module.exports = {
    setupUtilHandlers
};
