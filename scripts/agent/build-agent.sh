#!/bin/bash

# Docker build script for Dock Dash Agent Service Only
# This script builds the Docker image for the agent service without database dependencies

set -e

echo "🐳 Building Dock Dash Agent Service Docker Image..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="dock-dash-agent"
IMAGE_TAG="latest"
DOCKERFILE_PATH="./backend/agent/Dockerfile"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if Dockerfile exists
if [ ! -f "$DOCKERFILE_PATH" ]; then
    echo -e "${RED}❌ Dockerfile not found at $DOCKERFILE_PATH${NC}"
    exit 1
fi

# Build the Docker image
echo -e "${YELLOW}📦 Building Docker image: $IMAGE_NAME:$IMAGE_TAG${NC}"
echo "Using Dockerfile: $DOCKERFILE_PATH"

# Build with BuildKit for better caching and smaller images
export DOCKER_BUILDKIT=1

docker build \
    --tag "$IMAGE_NAME:$IMAGE_TAG" \
    --file "$DOCKERFILE_PATH" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    ./backend/agent

# Check if build was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully!${NC}"
    
    # Show image size
    IMAGE_SIZE=$(docker images "$IMAGE_NAME:$IMAGE_TAG" --format "table {{.Size}}" | tail -n 1)
    echo -e "${GREEN}📊 Image size: $IMAGE_SIZE${NC}"
    
    # Show image details
    echo -e "${YELLOW}📋 Image details:${NC}"
    docker images "$IMAGE_NAME:$IMAGE_TAG"
    
else
    echo -e "${RED}❌ Docker build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Build completed successfully!${NC}"
echo -e "${YELLOW}💡 To run the agent container, use: ./scripts/run-agent.sh${NC}"
