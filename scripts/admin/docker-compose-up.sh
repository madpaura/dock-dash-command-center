#!/bin/bash

# Docker Compose script for full stack deployment
# This script starts the entire Dock Dash Command Center stack

set -e

echo "🚀 Starting Dock Dash Command Center Full Stack..."

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

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ docker-compose.yml not found in current directory${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}📁 Creating necessary directories...${NC}"
mkdir -p ./backend/logs

# Start the services
echo -e "${BLUE}🐳 Starting services with Docker Compose...${NC}"

# Use docker compose (newer) or docker-compose (legacy)
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Start backend and database (without frontend by default)
$COMPOSE_CMD up -d mysql backend

echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"

# Wait for MySQL to be ready
echo -e "${BLUE}🗄️  Waiting for MySQL database...${NC}"
timeout=60
counter=0
while ! $COMPOSE_CMD exec mysql mysqladmin ping -h localhost --silent; do
    if [ $counter -eq $timeout ]; then
        echo -e "${RED}❌ MySQL failed to start within $timeout seconds${NC}"
        $COMPOSE_CMD logs mysql
        exit 1
    fi
    echo -n "."
    sleep 1
    ((counter++))
done
echo -e "\n${GREEN}✅ MySQL is ready!${NC}"

# Wait for backend to be ready
echo -e "${BLUE}🔧 Waiting for backend API...${NC}"
timeout=60
counter=0
while ! curl -f http://localhost:8500/health > /dev/null 2>&1; do
    if [ $counter -eq $timeout ]; then
        echo -e "${RED}❌ Backend failed to start within $timeout seconds${NC}"
        $COMPOSE_CMD logs backend
        exit 1
    fi
    echo -n "."
    sleep 1
    ((counter++))
done
echo -e "\n${GREEN}✅ Backend API is ready!${NC}"

echo -e "${GREEN}🎉 Full stack is running successfully!${NC}"
echo -e "${GREEN}🌐 Backend API: http://localhost:8500${NC}"
echo -e "${GREEN}🗄️  MySQL Database: localhost:3306${NC}"

echo -e "\n${YELLOW}📋 Useful commands:${NC}"
echo -e "  View all logs: ${BLUE}$COMPOSE_CMD logs -f${NC}"
echo -e "  View backend logs: ${BLUE}$COMPOSE_CMD logs -f backend${NC}"
echo -e "  View database logs: ${BLUE}$COMPOSE_CMD logs -f mysql${NC}"
echo -e "  Stop all services: ${BLUE}$COMPOSE_CMD down${NC}"
echo -e "  Restart services: ${BLUE}$COMPOSE_CMD restart${NC}"
echo -e "  Check status: ${BLUE}$COMPOSE_CMD ps${NC}"

# Optional: Start frontend if requested
if [ "$1" = "--with-frontend" ]; then
    echo -e "${BLUE}🎨 Starting frontend service...${NC}"
    $COMPOSE_CMD --profile frontend up -d frontend
    echo -e "${GREEN}🌐 Frontend: http://localhost:3000${NC}"
fi
