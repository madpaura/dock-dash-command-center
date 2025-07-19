#!/bin/bash

# Build directory
BUILD_DIR="../../static/downloads"
mkdir -p "$BUILD_DIR"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
if ! command_exists npm; then
    echo "Error: npm is required but not installed."
    exit 1
fi

# Install dependencies
npm install

# Build for each platform
echo "Building Electron apps..."

# Windows Docker build
if command_exists docker; then
    echo "Building Windows executable using Docker..."
    docker run --rm -ti \
     --env-file <(env | grep -iE 'DEBUG|NODE_|ELECTRON_|YARN_|NPM_|CI|CIRCLE|TRAVIS_|APPVEYOR_|CSC_|GH_|GITHUB_|BT_|AWS_|STRIP|BUILD_') \
     --env ELECTRON_CACHE="/root/.cache/electron" \
     --env ELECTRON_BUILDER_CACHE="/root/.cache/electron-builder" \
     -v ${PWD}:/project \
     -v ${PWD##*/}-node-modules:/project/node_modules \
     -v ~/.cache/electron:/root/.cache/electron \
     -v ~/.cache/electron-builder:/root/.cache/electron-builder \
     electronuserland/builder:wine \
     yarn install && yarn build --win
    mv "dist/cxl-qvp Setup 1.0.0.exe" "$BUILD_DIR/cxl-qvp_1.0.0.exe"
else
    echo "Warning: docker not found, skipping Windows Docker build"
fi

# Linux builds
echo "Building Linux packages..."
npm run build:linux
mv "dist/cxl-qvp_1.0.0_amd64.deb" "$BUILD_DIR/cxl-qvp_1.0.0.deb"

echo "Build process completed!"
