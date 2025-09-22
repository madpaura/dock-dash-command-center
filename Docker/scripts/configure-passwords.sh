#!/bin/bash

# Configure VSCode and Jupyter passwords for GPU development container
# This script is called during container startup with user-specific passwords

set -e

# Get password from environment variable
USER_PASSWORD="${PASSWORD:-changeme123}"
JUPYTER_PASS="${JUPYTER_PASSWORD:-$USER_PASSWORD}"
USERNAME="${USER:-developer}"

echo "Configuring VSCode and Jupyter authentication for user: $USERNAME"

# Configure VSCode Server password
echo "Setting up VSCode Server password authentication..."

# Create code-server config directory
mkdir -p /config/.config/code-server

# Generate code-server config with password
cat > /config/.config/code-server/config.yaml << EOF
bind-addr: 0.0.0.0:8080
auth: password
password: $USER_PASSWORD
cert: false
disable-telemetry: true
disable-update-check: true
user-data-dir: /config/.config/code-server
extensions-dir: /config/.config/code-server/extensions
EOF

echo "VSCode Server password configured: $USER_PASSWORD"

# Configure Jupyter password
echo "Setting up Jupyter password authentication..."

# Create jupyter config directory
mkdir -p /config/.jupyter

# Generate Jupyter password hash
JUPYTER_PASSWORD_HASH=$(python3 -c "
from jupyter_server.auth import passwd
print(passwd('$JUPYTER_PASS'))
")

# Create Jupyter config with password
cat > /config/.jupyter/jupyter_server_config.py << EOF
# Jupyter Server Configuration
c.ServerApp.ip = '0.0.0.0'
c.ServerApp.port = 8888
c.ServerApp.open_browser = False
c.ServerApp.allow_root = False
c.ServerApp.password = '$JUPYTER_PASSWORD_HASH'
c.ServerApp.token = ''
c.ServerApp.disable_check_xsrf = True
c.ServerApp.allow_origin = '*'
c.ServerApp.base_url = '${JUPYTER_BASE_URL:-/}'
c.ServerApp.notebook_dir = '/workspace'
c.ServerApp.root_dir = '/workspace'
EOF

# Also create legacy Jupyter Notebook config for compatibility
cat > /config/.jupyter/jupyter_notebook_config.py << EOF
# Jupyter Notebook Configuration (Legacy)
c.NotebookApp.ip = '0.0.0.0'
c.NotebookApp.port = 8888
c.NotebookApp.open_browser = False
c.NotebookApp.allow_root = False
c.NotebookApp.password = '$JUPYTER_PASSWORD_HASH'
c.NotebookApp.token = ''
c.NotebookApp.disable_check_xsrf = True
c.NotebookApp.allow_origin = '*'
c.NotebookApp.base_url = '${JUPYTER_BASE_URL:-/}'
c.NotebookApp.notebook_dir = '/workspace'
EOF

echo "Jupyter password configured: $JUPYTER_PASS"

# Set proper permissions for the developer user
sudo chown -R ${USERNAME}:${USERNAME} /config/.config /config/.jupyter 2>/dev/null || true
sudo chmod -R 755 /config/.config /config/.jupyter 2>/dev/null || true

# Also copy configs to user home directory as backup
cp -r /config/.jupyter ~/.jupyter 2>/dev/null || true
cp -r /config/.config ~/.config 2>/dev/null || true

echo "Password configuration completed for user: $USERNAME"
echo "VSCode will be available at: http://localhost:8080 (password: $USER_PASSWORD)"
echo "Jupyter will be available at: http://localhost:8888 (password: $JUPYTER_PASS)"
