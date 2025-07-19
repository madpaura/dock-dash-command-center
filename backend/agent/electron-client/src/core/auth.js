const { ipcMain } = require('electron');
const axios = require('axios');
const config = require('../utils/config');

const AUTH_API_URL = `http://${config.api.auth.host}:${config.api.auth.port}`;

const authAxios = axios.create({
    baseURL: AUTH_API_URL,
    timeout: 15000,
    headers: { 'Content-Type': 'application/json' }
});

function handleAuthError(error, operation) {
    const errorMessage = error.response?.data?.error || `Failed to ${operation}`;
    const statusCode = error.response?.status;

    console.error(`Auth operation failed:`, {
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

function setupAuthHandlers() {
    ipcMain.handle('login', async (event, { username, password }) => {
        try {
            const response = await authAxios.post('/api/login', { username, password });
            return response.data;
        } catch (error) {
            return handleAuthError(error, 'Login');
        }
    });

    ipcMain.handle('validate-session', async (event, { userId, sessionToken }) => {
        try {
            const response = await authAxios.post('/api/validate_session', {
                user_id: userId,
                session_token: sessionToken
            });
            return response.data;
        } catch (error) {
            return handleAuthError(error, 'Session validation');
        }
    });

    ipcMain.handle('logout', async (event, { userId }) => {
        try {
            const response = await authAxios.post('/api/logout', { user_id: userId });
            return response.data;
        } catch (error) {
            return handleAuthError(error, 'Logout');
        }
    });

    ipcMain.handle('get-user-info', async (event, { userId }) => {
        try {
            const response = await authAxios.get(`/api/users/${userId}`);
            return response.data;
        } catch (error) {
            return handleAuthError(error, 'Get user info');
        }
    });
}

module.exports = {
    setupAuthHandlers
};
