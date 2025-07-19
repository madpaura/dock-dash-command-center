# Electron App Build Instructions

## Prerequisites
- Node.js (v16 or higher)
- npm
- Docker (optional, for Windows build)

## Building the Application

1. Clone the repository
2. Navigate to the electron-ui directory
3. Run the build script:
```bash
./build.sh
```

This will:
- Install dependencies
- Build the application for all supported platforms
- Place the built executables in the `../../static/downloads` directory

### Windows Build
If you don't have Wine installed, you can use Docker for the Windows build. Make sure Docker is installed and running before running the build script.

## Troubleshooting
- If you encounter permission issues, try running the script with `sudo`
- Make sure Docker is running if you want to use the Windows Docker build
