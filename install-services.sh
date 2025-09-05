#!/bin/bash

# Docker Dashboard Services Installation Script
# This script installs and enables the backend and agent services

set -e

echo "Installing Docker Dashboard Services..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root (use sudo)"
    exit 1
fi

# Define paths
BACKEND_SERVICE_FILE="/home/vishwa/gpu/dock-dash-command-center/backend/dock-dash-backend.service"
AGENT_SERVICE_FILE="/home/vishwa/gpu/dock-dash-command-center/backend/agent/dock-dash-agent.service"
SYSTEMD_DIR="/etc/systemd/system"

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
cp "$BACKEND_SERVICE_FILE" "$SYSTEMD_DIR/dock-dash-backend.service"
chmod 644 "$SYSTEMD_DIR/dock-dash-backend.service"

# Install agent service
echo "Installing agent service..."
cp "$AGENT_SERVICE_FILE" "$SYSTEMD_DIR/dock-dash-agent.service"
chmod 644 "$SYSTEMD_DIR/dock-dash-agent.service"

# Ensure www-data user exists and is in docker group
echo "Setting up user permissions..."
if ! id "www-data" &>/dev/null; then
    echo "Creating www-data user..."
    useradd -r -s /bin/false www-data
fi

# Add www-data to docker group
usermod -a -G docker www-data

# Set proper ownership
echo "Setting file permissions..."
chown -R www-data:www-data /home/vishwa/gpu/dock-dash-command-center/backend

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable services
echo "Enabling services..."
systemctl enable dock-dash-backend.service
systemctl enable dock-dash-agent.service

echo "Services installed successfully!"
echo ""
echo "To start the services:"
echo "  sudo systemctl start dock-dash-backend"
echo "  sudo systemctl start dock-dash-agent"
echo ""
echo "To check status:"
echo "  sudo systemctl status dock-dash-backend"
echo "  sudo systemctl status dock-dash-agent"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u dock-dash-backend -f"
echo "  sudo journalctl -u dock-dash-agent -f"
