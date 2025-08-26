#!/bin/bash

# Docker run script for Dock Dash Command Center Backend
# This script runs the Docker container with proper configuration

set -e

echo "🚀 Starting Dock Dash Command Center Backend..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="gpu-farm-admin"
IMAGE_TAG="latest"
CONTAINER_NAME="gpu-farm-admin-instance"
HOST_PORT="8500"
CONTAINER_PORT="8500"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if image exists
if ! docker image inspect "$IMAGE_NAME:$IMAGE_TAG" > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker image $IMAGE_NAME:$IMAGE_TAG not found.${NC}"
    echo -e "${YELLOW}💡 Please build the image first: ./scripts/build-docker.sh${NC}"
    exit 1
fi

# Stop and remove existing container if it exists
if docker ps -a --format 'table {{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
    echo -e "${YELLOW}🛑 Stopping existing container: $CONTAINER_NAME${NC}"
    docker stop "$CONTAINER_NAME" > /dev/null 2>&1 || true
    echo -e "${YELLOW}🗑️  Removing existing container: $CONTAINER_NAME${NC}"
    docker rm "$CONTAINER_NAME" > /dev/null 2>&1 || true
fi

# Create logs directory if it doesn't exist
mkdir -p ../../backend/logs

# Check if required config files exist
if [ ! -f "../../backend/agents.txt" ]; then
    echo -e "${YELLOW}⚠️  Creating empty agents.txt file${NC}"
    touch ../../backend/agents.txt
fi

if [ ! -f "../../backend/config.toml" ]; then
    echo -e "${YELLOW}⚠️  Creating default config.toml file${NC}"
    cat > ../../backend/config.toml << 'EOF'
[server]
host = "0.0.0.0"
port = 8500

[database]
host = "localhost"
port = 3306
user = "root"
password = "12qwaszx"
name = "user_auth_db"
EOF
fi

echo -e "${BLUE}🐳 Starting new container: $CONTAINER_NAME${NC}"

# Run the container
docker run -d \
    --name "$CONTAINER_NAME" \
    --network host \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$(pwd)/../../backend/logs:/app/logs" \
    -v "$(pwd)/../../backend/agents.txt:/app/agents.txt" \
    -v "$(pwd)/../../backend/config.toml:/app/config.toml" \
    -e DB_HOST=localhost \
    -e DB_PORT=3306 \
    -e DB_USER=root \
    -e DB_PASSWORD=12qwaszx \
    -e DB_NAME=user_auth_db \
    -e MGMT_SERVER_PORT=8500 \
    -e MGMT_SERVER_IP=0.0.0.0 \
    "$IMAGE_NAME:$IMAGE_TAG"

# Check if container started successfully
sleep 2
if docker ps --format 'table {{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
    echo -e "${GREEN}✅ Container started successfully!${NC}"
    echo -e "${GREEN}🌐 Backend API available at: http://localhost:$HOST_PORT${NC}"
    echo -e "${BLUE}📊 Container status:${NC}"
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo -e "\n${YELLOW}📋 Useful commands:${NC}"
    echo -e "  View logs: ${BLUE}docker logs -f $CONTAINER_NAME${NC}"
    echo -e "  Stop container: ${BLUE}docker stop $CONTAINER_NAME${NC}"
    echo -e "  Restart container: ${BLUE}docker restart $CONTAINER_NAME${NC}"
    echo -e "  Enter container: ${BLUE}docker exec -it $CONTAINER_NAME /bin/bash${NC}"
    
else
    echo -e "${RED}❌ Failed to start container!${NC}"
    echo -e "${YELLOW}📋 Checking logs...${NC}"
    docker logs "$CONTAINER_NAME"
    exit 1
fi
