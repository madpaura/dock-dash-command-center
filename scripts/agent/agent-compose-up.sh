#!/bin/bash

# Docker Compose script for agent-only deployment
# This script starts only the agent service without database

set -e

echo "🚀 Starting Dock Dash Agent Service Only..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker and Docker Compose are available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed or not in PATH${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed or not in PATH${NC}"
    exit 1
fi

# Check if docker-compose-agent.yml exists
if [ ! -f "docker-compose-agent.yml" ]; then
    echo -e "${RED}❌ docker-compose-agent.yml not found in current directory${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}📁 Creating necessary directories...${NC}"
mkdir -p ./backend/agent/logs

# Start the agent service
echo -e "${BLUE}🐳 Starting agent service with Docker Compose...${NC}"

# Use docker compose (newer) or docker-compose (legacy)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Start agent service only
$COMPOSE_CMD -f docker-compose-agent.yml up -d agent

echo -e "${YELLOW}⏳ Waiting for agent service to be ready...${NC}"

# Wait for agent to be ready
echo -e "${BLUE}🔧 Waiting for agent API...${NC}"
timeout=60
counter=0
while ! curl -f http://localhost:8510/health > /dev/null 2>&1; do
    if [ $counter -eq $timeout ]; then
        echo -e "${RED}❌ Agent failed to start within $timeout seconds${NC}"
        $COMPOSE_CMD -f docker-compose-agent.yml logs agent
        exit 1
    fi
    echo -n "."
    sleep 1
    ((counter++))
done
echo -e "\n${GREEN}✅ Agent API is ready!${NC}"

echo -e "${GREEN}🎉 Agent service is running successfully!${NC}"
echo -e "${GREEN}🌐 Agent API: http://localhost:8510${NC}"

echo -e "\n${YELLOW}📋 Useful commands:${NC}"
echo -e "  View agent logs: ${BLUE}$COMPOSE_CMD -f docker-compose-agent.yml logs -f agent${NC}"
echo -e "  Stop agent service: ${BLUE}$COMPOSE_CMD -f docker-compose-agent.yml down${NC}"
echo -e "  Restart agent: ${BLUE}$COMPOSE_CMD -f docker-compose-agent.yml restart agent${NC}"
echo -e "  Check status: ${BLUE}$COMPOSE_CMD -f docker-compose-agent.yml ps${NC}"
echo -e "  Test agent: ${BLUE}curl http://localhost:8510/health${NC}"
