const { spawn, execSync } = require('child_process');
const os = require('os');
const path = require('path');

class SSHHelper {
    static isWindows() {
        return os.platform() === 'win32';
    }

    static async launchSSH(username, host, port) {
        try {
            if (this.isWindows()) {
                return this.launchPutty(username, host, port);
            } else {
                return this.launchTerminal(username, host, port);
            }
        } catch (error) {
            console.error('SSH launch failed:', error);
            throw error;
        }
    }

    static isPuttyInstalled() {
        const puttyPaths = [
            path.join(process.env['ProgramFiles'], 'PuTTY', 'putty.exe'),
            path.join(process.env['ProgramFiles(x86)'], 'PuTTY', 'putty.exe')
        ];

        try {
            // First check if putty is in PATH
            execSync('where putty.exe');
            return true;
        } catch {
            // Check in standard installation paths
            return puttyPaths.some(p => {
                try {
                    require('fs').accessSync(p);
                    return true;
                } catch {
                    return false;
                }
            });
        }
    }

    static findPuttyPath() {
        const puttyPaths = [
            path.join(process.env['ProgramFiles'], 'PuTTY', 'putty.exe'),
            path.join(process.env['ProgramFiles(x86)'], 'PuTTY', 'putty.exe')
        ];

        try {
            // First check if putty is in PATH
            execSync('where putty.exe');
            return 'putty.exe';
        } catch {
            // Check in standard installation paths
            return puttyPaths.find(p => {
                try {
                    require('fs').accessSync(p);
                    return true;
                } catch {
                    return false;
                }
            });
        }
    }

    static launchPutty(username, host, port) {
        try {
            if (this.isPuttyInstalled()) {
                const puttyExe = this.findPuttyPath();
                const args = [
                    '-ssh',
                    `${username}@${host}`,
                    '-P',
                    `${port}`
                ];

                const putty = spawn(puttyExe, args, {
                    detached: true,
                    stdio: 'ignore',
                    windowsHide: false
                });

                putty.unref();
                return { success: true };
            } else {
                // Fallback to cmd
                const sshCommand = `ssh ${username}@${host} -p ${port}`;
                const cmd = spawn('cmd.exe', ['/c', 'start', 'cmd.exe', '/K', sshCommand], {
                    detached: true,
                    stdio: 'ignore',
                    windowsHide: false
                });

                cmd.unref();
                return { 
                    success: true,
                    message: 'PuTTY not found, using Windows Command Prompt instead'
                };
            }
        } catch (error) {
            console.error('SSH launch failed:', error);
            return {
                success: false,
                error: `Failed to launch SSH: ${error.message}`
            };
        }
    }

    static launchTerminal(username, host, port) {
        try {
            const command = `ssh ${username}@${host} -p ${port};read`;
            const terminal = spawn('gnome-terminal', ['--', 'bash', '-c', command], {
                detached: true,
                stdio: 'ignore'
            });
            
            terminal.unref();
            return { success: true };
        } catch (error) {
            console.error('Terminal launch failed:', error);
            return {
                success: false,
                error: `Failed to launch terminal: ${error.message}`
            };
        }
    }
}

module.exports = SSHHelper;
