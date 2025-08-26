#!/bin/bash

# Docker stop script for Dock Dash Command Center
# This script stops and cleans up Docker containers

set -e

echo "🛑 Stopping Dock Dash Command Center..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="gpu-farm-admin-instance"

# Function to stop individual container
stop_individual_container() {
    if docker ps --format 'table {{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
        echo -e "${YELLOW}🛑 Stopping container: $CONTAINER_NAME${NC}"
        docker stop "$CONTAINER_NAME"
        echo -e "${GREEN}✅ Container stopped: $CONTAINER_NAME${NC}"
    else
        echo -e "${BLUE}ℹ️  Container not running: $CONTAINER_NAME${NC}"
    fi
}

# Function to stop docker-compose stack
stop_compose_stack() {
    if [ -f "docker-compose.yml" ]; then
        echo -e "${YELLOW}🛑 Stopping Docker Compose stack...${NC}"
        
        # Use docker compose (newer) or docker-compose (legacy)
        if docker compose version &> /dev/null; then
            COMPOSE_CMD="docker compose"
        else
            COMPOSE_CMD="docker-compose"
        fi
        
        $COMPOSE_CMD down
        echo -e "${GREEN}✅ Docker Compose stack stopped${NC}"
    else
        echo -e "${BLUE}ℹ️  No docker-compose.yml found${NC}"
    fi
}

# Check command line arguments
if [ "$1" = "--compose" ] || [ "$1" = "-c" ]; then
    stop_compose_stack
elif [ "$1" = "--individual" ] || [ "$1" = "-i" ]; then
    stop_individual_container
else
    # Default: try both methods
    echo -e "${BLUE}🔍 Checking for running services...${NC}"
    
    # First try to stop compose stack
    stop_compose_stack
    
    # Then stop individual container if it's still running
    stop_individual_container
fi

echo -e "${GREEN}🎉 Cleanup completed!${NC}"
