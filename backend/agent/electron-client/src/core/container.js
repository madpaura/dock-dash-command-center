const { ipcMain } = require('electron');
const axios = require('axios');

let containerAxios = null;
const statsPolling = new Map();

function handleContainerError(error, operation) {
    if (axios.isCancel(error)) {
        return { success: false, error: 'Request cancelled' };
    }

    const errorMessage = error.response?.data?.error || `Failed to ${operation}`;
    const statusCode = error.response?.status;

    console.error(`Container operation failed:`, {
        operation,
        message: errorMessage,
        statusCode,
        timestamp: new Date().toISOString()
    });

    return {
        success: false,
        error: errorMessage,
        statusCode
    };
}

function setupContainerHandlers() {
    ipcMain.handle('set-container-api', async (event, { ip, port }) => {
        containerAxios = axios.create({
            baseURL: `http://${ip}:${port}`,
            timeout: 15000,
            headers: { 'Content-Type': 'application/json' },
            retry: 2,
            retryDelay: 1000
        });

        containerAxios.interceptors.response.use(
            response => {
                if (response.config.url.includes('/stats') && !response.data.running) {
                    const containerId = response.config.url.split('/')[3];
                    const polling = statsPolling.get(containerId);
                    if (polling) {
                        clearInterval(polling);
                        statsPolling.delete(containerId);
                    }
                }
                return response;
            },
            error => { throw error; }
        );

        return { success: true };
    });

    ipcMain.handle('get-container-info', async (event, containerId) => {
        if (!containerAxios) {
            return { success: false, error: 'Container API not set' };
        }

        try {
            const response = await containerAxios.get(`/api/containers/${containerId}`);
            return response.data;
        } catch (error) {
            return handleContainerError(error, 'fetch container info');
        }
    });

    ipcMain.handle('get-container-stats', async (event, containerId) => {
        if (!containerAxios) {
            return { success: false, error: 'Container API not set' };
        }

        try {
            if (statsPolling.has(containerId)) {
                clearInterval(statsPolling.get(containerId));
            }

            const fetchStats = async () => {
                try {
                    const response = await containerAxios.get(`/api/containers/${containerId}/stats`);
                    event.sender.send('container-stats-update', { containerId, stats: response.data });
                    return response.data;
                } catch (error) {
                    const errorResult = handleContainerError(error, 'fetch container stats');
                    event.sender.send('container-stats-error', { containerId, error: errorResult });
                    return errorResult;
                }
            };

            const initialStats = await fetchStats();
            
            if (initialStats.running) {
                const pollInterval = setInterval(fetchStats, 5000);
                statsPolling.set(containerId, pollInterval);
            }

            return initialStats;
        } catch (error) {
            return handleContainerError(error, 'fetch container stats');
        }
    });

    ipcMain.handle('container-action', async (event, { action, containerId }) => {
        if (!containerAxios) {
            return { success: false, error: 'Container API not set' };
        }

        try {
            const response = await containerAxios.post(`/api/containers/${containerId}/${action}`);
            
            if (action === 'stop' && statsPolling.has(containerId)) {
                clearInterval(statsPolling.get(containerId));
                statsPolling.delete(containerId);
            }
            
            return response.data;
        } catch (error) {
            return handleContainerError(error, `perform ${action}`);
        }
    });

    ipcMain.handle('container-create', async (event, username, sessionToken) => {
        if (!containerAxios) {
            return { success: false, error: 'Container API not set' };
        }

        try {
            const response = await containerAxios.post('/api/containers', {
                user: username,
                session_token: sessionToken
            });
            return response.data;
        } catch (error) {
            return handleContainerError(error, 'create container');
        }
    });

    ipcMain.handle('get-container-ports', async (event, containerId) => {
        if (!containerAxios) {
            return { success: false, error: 'Container API not set' };
        }
        try {
            const response = await containerAxios.get(`/api/containers/${containerId}/ports`);
            return response.data;
        } catch (error) {
            return handleContainerError(error, 'fetching ports');
        }
    });
}

module.exports = {
    setupContainerHandlers
};
