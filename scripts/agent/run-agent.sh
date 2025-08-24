#!/bin/bash

# Docker run script for Dock Dash Agent Service Only
# This script runs the Docker container for agent service without database

set -e

echo "🚀 Starting Dock Dash Agent Service..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="dock-dash-agent"
IMAGE_TAG="latest"
CONTAINER_NAME="dock-dash-agent"
HOST_PORT="8510"
CONTAINER_PORT="8510"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if image exists
if ! docker image inspect "$IMAGE_NAME:$IMAGE_TAG" > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker image $IMAGE_NAME:$IMAGE_TAG not found.${NC}"
    echo -e "${YELLOW}💡 Please build the image first: ./scripts/build-agent.sh${NC}"
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
mkdir -p ./backend/agent/logs

echo -e "${BLUE}🐳 Starting new agent container: $CONTAINER_NAME${NC}"

# Run the container
docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    -p "$HOST_PORT:$CONTAINER_PORT" \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$(pwd)/backend/agent/logs:/app/logs" \
    -v "$(pwd)/backend/agent/port_manager.db:/app/port_manager.db" \
    -v "$(pwd)/backend/config.toml:/app/config.toml" \
    -e AGENT_PORT=8510 \
    -e DOCKER_IMAGE=gpu-dev-environment \
    -e DOCKER_TAG=latest \
    -e DOCKER_CPU=4 \
    -e DOCKER_MEM_LMT=4g \
    -e CODE_DEFAULT_WORKSPACE=/workspace \
    -e CODE_PORT=8080 \
    -e JUPYTER_PORT=8888 \
    "$IMAGE_NAME:$IMAGE_TAG"

# Check if container started successfully
sleep 2
if docker ps --format 'table {{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
    echo -e "${GREEN}✅ Agent container started successfully!${NC}"
    echo -e "${GREEN}🌐 Agent API available at: http://localhost:$HOST_PORT${NC}"
    echo -e "${BLUE}📊 Container status:${NC}"
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo -e "\n${YELLOW}📋 Useful commands:${NC}"
    echo -e "  View logs: ${BLUE}docker logs -f $CONTAINER_NAME${NC}"
    echo -e "  Stop container: ${BLUE}docker stop $CONTAINER_NAME${NC}"
    echo -e "  Restart container: ${BLUE}docker restart $CONTAINER_NAME${NC}"
    echo -e "  Enter container: ${BLUE}docker exec -it $CONTAINER_NAME /bin/bash${NC}"
    echo -e "  Test agent: ${BLUE}curl http://localhost:$HOST_PORT/health${NC}"
    
else
    echo -e "${RED}❌ Failed to start agent container!${NC}"
    echo -e "${YELLOW}📋 Checking logs...${NC}"
    docker logs "$CONTAINER_NAME"
    exit 1
fi
