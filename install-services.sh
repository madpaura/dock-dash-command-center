#!/bin/bash

# Docker Dashboard Services Installation Script
# This script installs and enables the backend and agent services

set -e
PWD=$(pwd)
echo "Installing Docker Dashboard Services..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root (use sudo)"
    exit 1
fi

SYSTEMD_DIR="/etc/systemd/system"

FRONTEND_SERVICE_FILE="$PWD/gpu-coder-frontend.service"

# backend admin & agent
BACKEND_SERVICE_FILE="$PWD/backend/gpu-coder-admin.service"
AGENT_SERVICE_FILE="$PWD/backend/agent/gpu-coder-agent.service"

# Check if service files exist
if [ ! -f "$BACKEND_SERVICE_FILE" ]; then
    echo "Error: Backend service file not found at $BACKEND_SERVICE_FILE"
    exit 1
fi

if [ ! -f "$AGENT_SERVICE_FILE" ]; then
    echo "Error: Agent service file not found at $AGENT_SERVICE_FILE"
    exit 1
fi

# Install backend service
echo "Installing backend service..."
cp "$BACKEND_SERVICE_FILE" "$SYSTEMD_DIR/gpu-coder-admin.service"
chmod 644 "$SYSTEMD_DIR/gpu-coder-admin.service"

# Install agent service
echo "Installing agent service..."
cp "$AGENT_SERVICE_FILE" "$SYSTEMD_DIR/gpu-coder-agent.service"
chmod 644 "$SYSTEMD_DIR/gpu-coder-agent.service"

# Install frontend service
echo "Installing frontend service..."
cp "$FRONTEND_SERVICE_FILE" "$SYSTEMD_DIR/gpu-coder-frontend.service"
chmod 644 "$SYSTEMD_DIR/gpu-coder-frontend.service"

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable services
echo "Enabling services..."
systemctl enable gpu-coder-admin.service
systemctl enable gpu-coder-agent.service
systemctl enable gpu-coder-frontend.service

echo "Services installed successfully!"
echo ""
echo "To start the services:"
echo "  sudo systemctl start gpu-coder-admin"
echo "  sudo systemctl start gpu-coder-agent"
echo "  sudo systemctl start gpu-coder-frontend"
echo ""
echo "To check status:"
echo "  sudo systemctl status gpu-coder-admin"
echo "  sudo systemctl status gpu-coder-agent"
echo "  sudo systemctl status gpu-coder-frontend"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u gpu-coder-admin -f"
echo "  sudo journalctl -u gpu-coder-agent -f"
echo "  sudo journalctl -u gpu-coder-frontend -f"
