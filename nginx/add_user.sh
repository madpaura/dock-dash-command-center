#!/bin/bash

# Script to add a new user with their VSCode and Jupyter server configurations
# Usage: sudo ./add_user.sh [username] [vscode_ip:port] [jupyter_ip:port]

CONFIG_FILE="/home/vishwa/gpu/dock-dash-command-center/nginx/sites-available/dev-services"
TEMP_FILE="/tmp/dev-services.tmp"

USERNAME=$1
VSCODE_SERVER=$2
JUPYTER_SERVER=$3

show_usage() {
    echo "Usage: $0 [username] [vscode_ip:port] [jupyter_ip:port]"
    echo "Example: $0 user3 192.168.1.10:8082 192.168.1.30:8090"
    exit 1
}

validate_inputs() {
    if [ $# -ne 3 ]; then
        echo "Error: Incorrect number of arguments"
        show_usage
    fi

    # Validate username (should not contain special characters)
    if [[ ! "$USERNAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        echo "Error: Invalid username. Only alphanumeric characters, hyphens, and underscores are allowed."
        exit 1
    fi

    # Validate VSCode server format
    if [[ ! "$VSCODE_SERVER" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$ ]]; then
        echo "Error: VSCode server must be in format ip:port"
        exit 1
    fi

    # Validate Jupyter server format
    if [[ ! "$JUPYTER_SERVER" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$ ]]; then
        echo "Error: Jupyter server must be in format ip:port"
        exit 1
    fi
}

# Check if user already exists in the config
check_user_exists() {
    if grep -q "upstream vscode_$USERNAME" "$CONFIG_FILE" || grep -q "upstream jupyter_$USERNAME" "$CONFIG_FILE"; then
        echo "Error: User $USERNAME already exists in the configuration"
        exit 1
    fi
}

add_user_to_config() {
    echo "Adding user $USERNAME with VSCode server $VSCODE_SERVER and Jupyter server $JUPYTER_SERVER"

    # Create a backup of the original file
    cp "$CONFIG_FILE" "$TEMP_FILE"

    # Add VSCode upstream block for the new user
    cat >> "$TEMP_FILE" <<EOF

# $USERNAME
upstream vscode_$USERNAME {
    server $VSCODE_SERVER max_fails=3 fail_timeout=30s;
    # Use least_conn for better load distribution
    least_conn;
    
    # Enable health checks
    zone vscode_$USERNAME 64k;
    keepalive 32;
    
    # List your VSCode servers for $USERNAME here
    # server ip_address:port max_fails=3 fail_timeout=30s;
    # Example:
    # server $VSCODE_SERVER max_fails=3 fail_timeout=30s;
}
EOF

    # Add Jupyter upstream block for the new user
    cat >> "$TEMP_FILE" <<EOF

# $USERNAME
upstream jupyter_$USERNAME {
    server $JUPYTER_SERVER max_fails=3 fail_timeout=30s;
    # Use least_conn for better load distribution
    least_conn;
    
    # Enable health checks
    zone jupyter_$USERNAME 64k;
    keepalive 32;
    
    # List your Jupyter servers for $USERNAME here
    # server ip_address:port max_fails=3 fail_timeout=30s;
    # Example:
    # server $JUPYTER_SERVER max_fails=3 fail_timeout=30s;
}
EOF

    # Add routing rules for VSCode
    sed -i "/if (\$user = \"user2\") {/a\\        if (\$user = \"$USERNAME\") {\n            proxy_pass http://vscode_$USERNAME/\$path\$is_args\$args;\n        }" "$TEMP_FILE"
    
    # Add routing rules for Jupyter
    sed -i "/proxy_pass http:\/\/jupyter_user2\/\$path\$is_args\$args;/a\\        if (\$user = \"$USERNAME\") {\n            proxy_pass http://jupyter_$USERNAME/\$path\$is_args\$args;\n        }" "$TEMP_FILE"

    # Move the temporary file to the original file
    mv "$TEMP_FILE" "$CONFIG_FILE"

    echo "User $USERNAME added successfully"
}

reload_nginx() {
    echo "Reloading Nginx configuration..."
    if sudo /usr/sbin/nginx -t; then
        sudo systemctl reload nginx
        if [ $? -eq 0 ]; then
            echo "Nginx reloaded successfully"
        else
            echo "Error reloading Nginx"
        fi
    else
        echo "Nginx configuration test failed. Please check the configuration."
    fi
}

# Main execution
validate_inputs "$@"
check_user_exists
add_user_to_config
reload_nginx

echo "User $USERNAME can now access:"
echo "  VSCode: http://your-server-ip/$USERNAME/vscode/"
echo "  Jupyter: http://your-server-ip/$USERNAME/jupyter/"