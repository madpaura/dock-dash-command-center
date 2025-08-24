# Agent-Only Docker Setup for Dock Dash Command Center

This guide provides instructions for running **only the backend/agent service** in a Docker environment without database dependencies.

## 🐳 Overview

The agent-only setup includes:
- **Minimal Agent Image**: Optimized Python 3.11-slim container (~120MB)
- **Docker Management**: Full Docker CLI access for container management
- **No Database**: Standalone service without MySQL dependency
- **Health Monitoring**: Built-in health checks
- **Persistent Storage**: Port manager database and logs

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+ (optional)
- At least 1GB RAM available
- Port 8510 available on host
- Docker socket access (`/var/run/docker.sock`)

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Start agent service only
./scripts/agent-compose-up.sh

# Stop agent service
docker-compose -f docker-compose-agent.yml down
```

### Option 2: Individual Container

```bash
# Build the agent image
./scripts/build-agent.sh

# Run the agent container
./scripts/run-agent.sh

# Stop the agent container
docker stop dock-dash-agent
```

## 📁 File Structure

```
dock-dash-command-center/
├── backend/agent/
│   ├── Dockerfile                 # Agent container definition
│   ├── requirements-agent.txt     # Minimal Python dependencies
│   ├── .dockerignore             # Exclude unnecessary files
│   ├── agent_server.py           # Main agent application
│   ├── monitoring_service.py     # Resource monitoring
│   ├── container_manager.py      # Docker container management
│   └── port_manager.db          # Persistent port allocations
├── docker-compose-agent.yml      # Agent-only orchestration
└── scripts/
    ├── build-agent.sh            # Build agent image
    ├── run-agent.sh              # Run agent container
    └── agent-compose-up.sh       # Start with compose
```

## 🔧 Configuration

### Environment Variables

```bash
# Agent Configuration
AGENT_PORT=8510                    # Agent service port

# Docker Configuration
DOCKER_IMAGE=gpu-dev-environment   # Default container image
DOCKER_TAG=latest                  # Default container tag
DOCKER_CPU=4                       # Default CPU allocation
DOCKER_MEM_LMT=4g                 # Default memory limit

# Code Server Configuration
CODE_DEFAULT_WORKSPACE=/workspace  # Default workspace path
CODE_PORT=8080                     # Code server port
SUDO_PASSWORD=abc                  # Container sudo password

# Jupyter Configuration
JUPYTER_PORT=8888                  # Jupyter notebook port

# Paths
QVP_BINARY_MOUNT=/opt/qvp         # QVP binaries mount
TOOLS_MOUNT=/opt/tools            # Tools mount path
WORKDIR_TEMPLATE=/home/vishwa/template/
WORKDIR_DEPLOY=/home/vishwa/vms/
```

### Volume Mounts

```yaml
volumes:
  # Docker socket for container management (REQUIRED)
  - /var/run/docker.sock:/var/run/docker.sock
  
  # Agent logs
  - ./backend/agent/logs:/app/logs
  
  # Persistent port manager database
  - ./backend/agent/port_manager.db:/app/port_manager.db
  
  # Configuration
  - ./backend/config.toml:/app/config.toml
```

## 🏗️ Agent Image Details

### Base Image
- **Python 3.11-slim**: Minimal Debian-based runtime
- **Size**: ~120MB (smaller than full backend)

### Installed Components
- **Docker CLI**: For container management
- **System Tools**: procps for monitoring
- **Python Dependencies**: Flask, Docker SDK, psutil

### Security Features
- **Non-root User**: Runs as `appuser` (UID 1000)
- **Minimal Dependencies**: Only agent-required packages
- **Health Checks**: Docker health monitoring

## 📊 Monitoring & Health Checks

### Health Check Endpoint

```bash
curl http://localhost:8510/health
```

Response format:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-24T12:30:00",
  "version": "1.0.0",
  "service": "agent",
  "docker": "healthy",
  "port": 8510
}
```

### Available Endpoints

- **Health Check**: `GET /health`
- **System Stats**: `GET /get_system_stats`
- **Docker Images**: `GET /get_docker_images`
- **Container Management**: `POST /api/containers`
- **Resource Monitoring**: Various monitoring endpoints

## 🔍 Troubleshooting

### Common Issues

#### 1. Agent Won't Start
```bash
# Check logs
docker logs dock-dash-agent

# Common causes:
# - Port 8510 already in use
# - Docker socket permission denied
# - Missing configuration files
```

#### 2. Docker Socket Permission Denied
```bash
# Check Docker socket permissions
ls -la /var/run/docker.sock

# Ensure Docker group access
sudo usermod -aG docker $USER
newgrp docker
```

#### 3. Container Management Fails
```bash
# Test Docker access from container
docker exec dock-dash-agent docker ps

# Check if Docker daemon is running
systemctl status docker
```

### Debug Commands

```bash
# Enter agent container
docker exec -it dock-dash-agent /bin/bash

# Check agent processes
docker exec dock-dash-agent ps aux

# Test Docker CLI access
docker exec dock-dash-agent docker version

# Check port allocations
docker exec dock-dash-agent ls -la port_manager.db
```

## 🚀 Production Deployment

### Resource Requirements

**Minimum:**
- CPU: 0.5 cores
- RAM: 512MB
- Disk: 2GB

**Recommended:**
- CPU: 1 core
- RAM: 1GB
- Disk: 10GB

### Security Considerations

1. **Docker Socket Security**: Mounting Docker socket gives container full Docker access
2. **Network Isolation**: Use Docker networks for service isolation
3. **File Permissions**: Ensure proper permissions on mounted volumes
4. **Container Limits**: Set resource limits in production

### Scaling

```bash
# Run multiple agent instances on different ports
docker run -d --name agent-8511 -p 8511:8510 dock-dash-agent
docker run -d --name agent-8512 -p 8512:8510 dock-dash-agent
```

## 📝 Maintenance

### Update Agent Image
```bash
# Rebuild and restart
./scripts/build-agent.sh
docker stop dock-dash-agent
./scripts/run-agent.sh
```

### Backup Port Manager Database
```bash
# Backup port allocations
cp ./backend/agent/port_manager.db ./backup/port_manager_$(date +%Y%m%d).db
```

### Log Management
```bash
# View agent logs
docker logs -f dock-dash-agent

# Rotate logs
docker logs dock-dash-agent > agent-$(date +%Y%m%d).log
```

## 🔗 Integration with Backend Manager

If you have a separate backend manager service, the agent can register with it:

```bash
# Set manager connection in environment
-e MGMT_SERVER_IP=your-manager-host
-e MGMT_SERVER_PORT=8500
```

The agent will automatically register itself with the manager on startup.

## 📞 Support

For agent-specific issues:
1. Check health endpoint: `curl http://localhost:8510/health`
2. Review agent logs: `docker logs dock-dash-agent`
3. Verify Docker socket access
4. Test container management capabilities

---

**Note**: This agent-only setup provides full Docker container management capabilities without database dependencies, making it ideal for distributed deployments where each server runs its own agent service.
