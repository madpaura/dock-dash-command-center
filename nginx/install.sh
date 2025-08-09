#!/bin/bash

# Installation script for Dev Services Nginx setup

echo "=== Dev Services Nginx Setup ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "Nginx is not installed. Installing..."
    apt update
    apt install -y nginx
fi

# Copy configuration files
echo "Copying configuration files..."
cp /home/vishwa/gpu/dock-dash-command-center/nginx/nginx.conf /etc/nginx/nginx.conf

# Create sites-available directory if it doesn't exist
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/sites-enabled

# Copy site configuration
cp /home/vishwa/gpu/dock-dash-command-center/nginx/sites-available/dev-services /etc/nginx/sites-available/

# Remove default site to prevent conflicts
rm -f /etc/nginx/sites-enabled/default

# Create symlink to enable site
ln -sf /home/vishwa/gpu/dock-dash-command-center/nginx/sites-available/dev-services /etc/nginx/sites-enabled/dev-services

# Copy systemd service files
echo "Installing systemd services..."
cp /home/vishwa/gpu/dock-dash-command-center/nginx/dev-services-enable-site.service /etc/systemd/system/
cp /home/vishwa/gpu/dock-dash-command-center/nginx/dev-services-nginx.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable services
systemctl enable dev-services-enable-site

# Test nginx configuration
echo "Testing Nginx configuration..."
if nginx -t; then
    echo "Nginx configuration is valid"
    # Reload nginx
    systemctl reload nginx
    echo "Nginx reloaded successfully"
else
    echo "Nginx configuration test failed"
    exit 1
fi

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Add backend servers using the manage_servers.sh script:"
echo "   /home/vishwa/gpu/dock-dash-command-center/nginx/manage_servers.sh vscode add IP:PORT"
echo "   /home/vishwa/gpu/dock-dash-command-center/nginx/manage_servers.sh jupyter add IP:PORT"
echo ""
echo "2. Add users using the add_user.sh script:"
echo "   sudo ./add_user.sh username vscode_ip:port jupyter_ip:port"
echo ""
echo "3. Access your services:"
echo "   VSCode: http://your-server-ip/username/vscode/"
echo "   Jupyter: http://your-server-ip/username/jupyter/"
echo "   Health: http://your-server-ip/health"