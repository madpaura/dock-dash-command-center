const { spawn, execSync } = require('child_process');
const os = require('os');
const { shell, dialog } = require('electron');
const path = require('path');
const fs = require('fs');

class RDPHelper {
    static isWindows() {
        return os.platform() === 'win32';
    }

    static findRemoteViewerPath() {
        try {
            // First try to find remote-viewer in PATH
            try {
                if (this.isWindows()) {
                    execSync('where remote-viewer.exe');
                    return 'remote-viewer.exe';
                } else {
                    execSync('which remote-viewer');
                    return 'remote-viewer';
                }
            } catch (e) {
                // Not in PATH, continue with other checks
            }

            if (this.isWindows()) {
                // Check Program Files directories for various possible installations
                const programDirs = [process.env['ProgramFiles'], process.env['ProgramFiles(x86)']];
                const versionedDirs = Array.from({ length: 5 }, (_, i) => `v${21 + i}`); // v21 to v25
                
                for (const programDir of programDirs) {
                    if (!programDir) continue;

                    // Check standard path
                    const standardPath = path.join(programDir, 'VirtViewer', 'remote-viewer.exe');
                    if (fs.existsSync(standardPath)) {
                        return standardPath;
                    }

                    // Check versioned paths
                    for (const version of versionedDirs) {
                        const versionedPath = path.join(programDir, `VirtViewer ${version}`, 'remote-viewer.exe');
                        if (fs.existsSync(versionedPath)) {
                            return versionedPath;
                        }
                    }
                }
                throw new Error('remote-viewer not found');
            } else {
                // On Linux, we've already checked PATH which is the standard installation location
                throw new Error('remote-viewer not found');
            }
        } catch (error) {
            return null;
        }
    }

    static isRemoteViewerInstalled() {
        return this.findRemoteViewerPath() !== null;
    }

    static getInstallationInstructions( { host, port, spice_port } ) {
        if (this.isWindows()) {
            return {
                title: 'Remote Viewer Installation Required',
                message: 'Remote Viewer (virt-viewer) is required for RDP connections.',
                downloadUrl: `http://${host}:${port}/downloads/virt-viewer-x64-11.0-1.0.msi`,
                instructions: 'Please download and install Virt Viewer for Windows.'
            };
        } else {
            return {
                title: 'Remote Viewer Installation Required',
                message: 'Remote Viewer (virt-viewer) is required for RDP connections.',
                command: 'sudo apt-get install virt-viewer',
                instructions: 'Please install virt-viewer using your package manager:'
            };
        }
    }

    static async promptInstallation(window, host, port, spice_port) {
        const info = this.getInstallationInstructions({ host, port, spice_port });
        
        const buttons = this.isWindows() ? ['Download', 'Cancel'] : ['Copy Command', 'Cancel'];
        
        const result = await dialog.showMessageBox(window, {
            type: 'info',
            title: info.title,
            message: info.message,
            detail: info.instructions,
            buttons: buttons,
            defaultId: 0,
            cancelId: 1
        });

        if (result.response === 0) {
            if (this.isWindows()) {
                shell.openExternal(info.downloadUrl);
                return { success: false, needsInstallation: true };
            } else {
                // Copy command to clipboard
                const { clipboard } = require('electron');
                clipboard.writeText(info.command);
                return { success: false, needsInstallation: true, message: 'Installation command copied to clipboard' };
            }
        }

        return { success: false, needsInstallation: true, message: 'Installation required' };
    }

    static async launchRDP(window, { host, port, spice_port }) {
        try {
            
            if (this.isRemoteViewerInstalled()) {
                return await this.promptInstallation(window, host, port, spice_port);
            }

            const command = this.findRemoteViewerPath();
            if (!command) {
                throw new Error('remote-viewer not found');
            }

            // Construct spice URL with password if provided
            const spiceUrl = `spice://${host}:${spice_port}`;
            const viewer = spawn(command, [spiceUrl], {
                detached: true,
                stdio: 'ignore'
            });

            viewer.unref();
            return { success: true };
        } catch (error) {
            console.error('RDP launch failed:', error);
            return {
                success: false,
                error: `Failed to launch RDP: ${error.message}`
            };
        }
    }
}

module.exports = RDPHelper;
