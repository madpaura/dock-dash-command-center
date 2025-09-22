#!/bin/bash

# Build script for GPU Development Environment Container
# This builds the container with VSCode and Jupyter password integration

set -e

# Configuration
IMAGE_NAME="gpu-dev-environment"
TAG="latest"
DOCKERFILE="Dockerfile.gpu-dev"

echo "Building GPU Development Environment Container..."
echo "Image: $IMAGE_NAME:$TAG"
echo "Dockerfile: $DOCKERFILE"

# Build the container
docker build \
    -f $DOCKERFILE \
    -t $IMAGE_NAME:$TAG \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    .

echo "Build completed successfully!"
echo "Container image: $IMAGE_NAME:$TAG"
echo ""
echo "To run the container with password authentication:"
echo "docker run -d \\"
echo "  --name gpu-dev-user1 \\"
echo "  --gpus all \\"
echo "  -p 8080:8080 \\"
echo "  -p 8888:8888 \\"
echo "  -e PASSWORD=your_password \\"
echo "  -e JUPYTER_PASSWORD=your_password \\"
echo "  -v /path/to/workspace:/workspace \\"
echo "  -v /path/to/config:/config \\"
echo "  $IMAGE_NAME:$TAG"
