# GPU-Enabled Development Environment with VS Code Server and Jupyter

This Docker setup provides a complete development environment with:
- NVIDIA GPU support
- VS Code Server (accessible via web browser)
- Jupyter Lab Server
- Python data science libraries

## Prerequisites

1. Docker Engine with NVIDIA Container Toolkit installed
2. docker-compose

## Setup Instructions

### Option 1: Using the build and run scripts (Recommended)

1. Make the scripts executable (if not already):
   ```bash
   chmod +x build.sh run.sh
   ```

2. Build the Docker image:
   ```bash
   ./build.sh
   ```

3. Run the container:
   ```bash
   ./run.sh
   ```

### Option 2: Using docker-compose

1. Build and start the container:
   ```bash
   docker-compose up --build
   ```

### Option 3: Manual Docker commands

1. Build the image:
   ```bash
   docker build -t gpu-dev-environment .
   ```

2. Run the container:
   ```bash
   docker run -it --gpus all -p 8080:8080 -p 8888:8888 -v $(pwd)/workspace:/home/developer/workspace gpu-dev-environment
   ```

## Accessing the Services

After starting the container, access the services at:
- VS Code Server: http://localhost:8080
- Jupyter Lab: http://localhost:8888

Your workspace files will be persisted in the `workspace` directory.

## Features

- Full NVIDIA GPU acceleration support
- No authentication required for local development
- Pre-installed Python libraries: numpy, pandas, matplotlib, seaborn
- VS Code extensions can be installed through the web interface

## Notes

- The container runs as a non-root user named `developer`
- All data in the `/home/developer/workspace` directory is mounted to the local `workspace` folder
- GPU access is enabled through the NVIDIA Container Runtime
- The build script includes checks for Docker and NVIDIA support
- The run script handles container lifecycle management