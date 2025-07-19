#!/bin/bash

# Create deployment directory
DEPLOY_DIR="cxl-manager-deploy"
mkdir -p $DEPLOY_DIR

# Copy necessary files excluding __pycache__
rsync -av --exclude='*/__pycache__' agent scripts admin_service.py manager_app.py database.py query_agents.py .env $DEPLOY_DIR/

# Create setup script
cat > $DEPLOY_DIR/setup.sh << 'EOF'
#!/bin/bash

# Install dependencies
pip3 install -r requirements.txt

# Setup manager service
chmod +x scripts/setup_manager_service.sh
./scripts/setup_manager_service.sh

# Setup agent service
chmod +x scripts/setup_agent_service.sh
./scripts/setup_agent_service.sh

echo "Installation complete. Services are running."
EOF

# Create requirements file
pip3 freeze > $DEPLOY_DIR/requirements.txt

# Create archive
tar -czvf cxl-manager-deploy.tar.gz $DEPLOY_DIR

# Cleanup
rm -rf $DEPLOY_DIR

echo "Deployment package created: cxl-manager-deploy.tar.gz"