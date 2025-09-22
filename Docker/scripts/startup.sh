#!/bin/bash

# GPU Development Container Startup Script
# Configures VSCode and Jupyter with user passwords and starts services

set -e

echo "Starting GPU Development Environment..."

# Get environment variables
USER_PASSWORD="${PASSWORD:-changeme123}"
JUPYTER_PASS="${JUPYTER_PASSWORD:-$USER_PASSWORD}"
SUDO_PASS="${SUDO_PASSWORD:-$USER_PASSWORD}"
USERNAME="${USER:-developer}"

echo "Configuring services for user: $USERNAME"

# Configure password authentication
/opt/scripts/configure-passwords.sh

# Update sudo password for the user
echo "$USERNAME:$SUDO_PASS" | sudo chpasswd

# Start SSH service
sudo service ssh start

# Function to start code-server
start_code_server() {
    echo "Starting VSCode Server on port 8080..."
    code-server \
        --bind-addr 0.0.0.0:8080 \
        --config /config/.config/code-server/config.yaml \
        --user-data-dir /config/.config/code-server \
        --extensions-dir /config/.config/code-server/extensions \
        /workspace &
    CODE_SERVER_PID=$!
    echo "VSCode Server started with PID: $CODE_SERVER_PID"
}

# Function to start Jupyter
start_jupyter() {
    echo "Starting Jupyter Lab on port 8888..."
    cd /workspace
    jupyter lab \
        --ip=0.0.0.0 \
        --port=8888 \
        --no-browser \
        --allow-root \
        --config=/config/.jupyter/jupyter_server_config.py &
    JUPYTER_PID=$!
    echo "Jupyter Lab started with PID: $JUPYTER_PID"
}

# Start services
start_code_server
start_jupyter

# Function to handle shutdown
cleanup() {
    echo "Shutting down services..."
    if [ ! -z "$CODE_SERVER_PID" ]; then
        kill $CODE_SERVER_PID 2>/dev/null || true
    fi
    if [ ! -z "$JUPYTER_PID" ]; then
        kill $JUPYTER_PID 2>/dev/null || true
    fi
    sudo service ssh stop
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

echo "GPU Development Environment is ready!"
echo "VSCode Server: http://localhost:8080 (password: $USER_PASSWORD)"
echo "Jupyter Lab: http://localhost:8888 (password: $JUPYTER_PASS)"
echo "SSH Access: ssh $USERNAME@localhost -p 22 (password: $SUDO_PASS)"

# Keep the container running
while true; do
    # Check if services are still running
    if ! kill -0 $CODE_SERVER_PID 2>/dev/null; then
        echo "VSCode Server died, restarting..."
        start_code_server
    fi
    
    if ! kill -0 $JUPYTER_PID 2>/dev/null; then
        echo "Jupyter Lab died, restarting..."
        start_jupyter
    fi
    
    sleep 30
done
