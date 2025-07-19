// Configuration settings for the application

const config = {
    // API endpoints
    api: {
        auth: {
            host: process.env.AUTH_API_HOST || 'localhost',
            port: process.env.AUTH_API_PORT || '8501'
        }
    },

    // Window settings
    window: {
        width: 640,
        height: 480,
        resizable: false,
        maximizable: false,
        fullscreenable: false,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: true,
            preload: require('path').join(__dirname, '../../preload.js')
        }
    },

    // Polling intervals (in milliseconds)
    intervals: {
        stats: 5000,
        state: 50000
    },

    // Asset paths
    assets: {
        icon: 'assets/icon.png',
        icons: {
            create: 'assets/create.png',
            start: 'assets/start.png',
            stop: 'assets/stop.png',
            restart: 'assets/restart.png',
            remove: 'assets/remove.png',
            vscode: 'assets/vscode.png',
            ssh: 'assets/ssh.png',
            rdp: 'assets/rdp.png',
            fm: 'assets/fm.png'
        }
    }
};

module.exports = config;
