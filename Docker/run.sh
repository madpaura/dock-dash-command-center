#!/bin/bash

# Run script for GPU-enabled development environment

IMAGE_NAME="gpu-dev-environment"
CONTAINER_NAME="gpu-dev-environment-container"

echo "Starting GPU-enabled development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null
then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if the image exists
if ! docker images | grep -q $IMAGE_NAME
then
    echo "Error: Docker image $IMAGE_NAME not found."
    echo "Please build the image first using ./build.sh"
    exit 1
fi

# Stop and remove existing container if running
if docker ps -a --format '{{.Names}}' | grep -q $CONTAINER_NAME
then
    echo "Stopping existing container..."
    docker stop $CONTAINER_NAME > /dev/null 2>&1
    docker rm $CONTAINER_NAME > /dev/null 2>&1
fi

# Run the container
echo "Starting container with GPU support..."
docker run -d \
    --name $CONTAINER_NAME \
    --gpus all \
    -p 8080:8080 \
    -p 8888:8888 \
    -v $(pwd)/workspace:/home/developer/workspace \
    $IMAGE_NAME

if [ $? -eq 0 ]; then
    echo ""
    echo "Container started successfully!"
    echo ""
    echo "Access the services at:"
    echo "  VS Code Server: http://localhost:8080"
    echo "  Jupyter Server: http://localhost:8888"
    echo ""
    echo "To stop the container:"
    echo "  docker stop $CONTAINER_NAME"
    echo ""
else
    echo "Failed to start container!"
    exit 1
fi