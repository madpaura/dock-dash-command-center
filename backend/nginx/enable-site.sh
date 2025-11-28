#!/bin/bash
# This script ensures the dev-services site is enabled

CONFIG_SOURCE="/home/vishwa/workspace/gpu/dock-dash-command-center/backend/nginx/sites-available/dev-services"
CONFIG_TARGET="/etc/nginx/sites-enabled/dev-services"

# Check if the symlink already exists
if [ ! -L "$CONFIG_TARGET" ]; then
    # Create the symlink
    ln -s "$CONFIG_SOURCE" "$CONFIG_TARGET"
    echo "Created symlink for dev-services site"
    
    # Test nginx configuration
    if nginx -t; then
        # Reload nginx to apply changes
        systemctl reload nginx
        echo "Nginx reloaded successfully"
    else
        echo "Nginx configuration test failed"
        # Remove the symlink if config test fails
        rm -f "$CONFIG_TARGET"
        exit 1
    fi
else
    echo "Symlink for dev-services site already exists"
fi