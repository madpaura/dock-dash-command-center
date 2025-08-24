# Docker Setup for Dock Dash Command Center Backend

This guide provides comprehensive instructions for running the Dock Dash Command Center backend in a Docker environment with minimal size and full Docker management capabilities.

## 🐳 Overview

The Docker setup includes:
- **Minimal Backend Image**: Optimized Python 3.11-slim based container
- **Docker Management**: Full Docker CLI access for container management
- **MySQL Database**: Containerized database with persistent storage
- **Health Monitoring**: Built-in health checks and monitoring
- **Security**: Non-root user execution and proper volume mounting

## 📋 Prerequisites

- Docker Engine 20.10+ 
- Docker Compose 2.0+ (or docker-compose 1.29+)
- At least 2GB RAM available
- Port 8500 and 3306 available on host

## 🚀 Quick Start

### Option 1: Full Stack with Docker Compose (Recommended)

```bash
# Start the complete stack (backend + database)
./scripts/docker-compose-up.sh

# With frontend (if available)
./scripts/docker-compose-up.sh --with-frontend

# Stop all services
./scripts/docker-stop.sh --compose
```

### Option 2: Backend Only

```bash
# Build the Docker image
./scripts/build-docker.sh

# Run the backend container
./scripts/run-docker.sh

# Stop the container
./scripts/docker-stop.sh --individual
```

## 📁 File Structure

```
dock-dash-command-center/
├── backend/
│   ├── Dockerfile                 # Optimized backend container
│   ├── requirements-docker.txt    # Minimal Python dependencies
│   ├── .dockerignore             # Exclude unnecessary files
│   └── ...
├── docker-compose.yml            # Full stack orchestration
└── scripts/
    ├── build-docker.sh          # Build backend image
    ├── run-docker.sh            # Run backend container
    ├── docker-compose-up.sh     # Start full stack
    └── docker-stop.sh           # Stop services
```

## 🔧 Configuration

### Environment Variables

The backend container uses these key environment variables:

```bash
# Database Configuration
DB_HOST=mysql                    # Database host (mysql service in compose)
DB_PORT=3306                     # Database port
DB_USER=root                     # Database user
DB_PASSWORD=12qwaszx            # Database password
DB_NAME=user_auth_db            # Database name

# Server Configuration
MGMT_SERVER_PORT=8500           # Backend API port
MGMT_SERVER_IP=0.0.0.0         # Bind to all interfaces

# Docker Configuration
DOCKER_IMAGE=gpu-dev-environment # Default container image
DOCKER_TAG=latest               # Default container tag
DOCKER_CPU=4                    # Default CPU allocation
DOCKER_MEM_LMT=4g              # Default memory limit
```

### Volume Mounts

Critical volumes for Docker management:

```yaml
volumes:
  # Docker socket for container management (REQUIRED)
  - /var/run/docker.sock:/var/run/docker.sock
  
  # Application logs
  - ./backend/logs:/app/logs
  
  # Configuration files
  - ./backend/agents.txt:/app/agents.txt
  - ./backend/config.toml:/app/config.toml
```

## 🏗️ Docker Image Details

### Base Image
- **Python 3.11-slim**: Minimal Debian-based Python runtime
- **Size**: ~150MB (optimized for production)

### Installed Components
- **Docker CLI**: For managing containers on host
- **SSH Client**: For remote server connections
- **System Tools**: procps for monitoring

### Security Features
- **Non-root User**: Runs as `appuser` (UID 1000)
- **Minimal Attack Surface**: Only essential packages installed
- **Health Checks**: Built-in health monitoring

### Optimization Features
- **Multi-stage Caching**: Efficient Docker layer caching
- **Minimal Dependencies**: Only production-required packages
- **BuildKit Support**: Advanced build features

## 📊 Monitoring & Health Checks

### Health Check Endpoint

The backend provides a comprehensive health check at `/health`:

```bash
curl http://localhost:8500/health
```

Response format:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-24T12:30:00",
  "version": "1.0.0",
  "database": "healthy",
  "services": {
    "auth_service": "healthy",
    "user_service": "healthy",
    "server_service": "healthy",
    "agent_service": "healthy"
  },
  "uptime": "running"
}
```

### Container Monitoring

```bash
# View container status
docker ps --filter "name=dock-dash"

# View logs
docker logs -f dock-dash-backend

# Monitor resource usage
docker stats dock-dash-backend

# Execute commands in container
docker exec -it dock-dash-backend /bin/bash
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Container Won't Start
```bash
# Check logs
docker logs dock-dash-backend

# Common causes:
# - Port 8500 already in use
# - Database connection failed
# - Missing environment variables
```

#### 2. Docker Socket Permission Denied
```bash
# Ensure Docker socket is accessible
ls -la /var/run/docker.sock

# Add user to docker group (if running without compose)
sudo usermod -aG docker $USER
```

#### 3. Database Connection Failed
```bash
# Check MySQL container status
docker ps --filter "name=mysql"

# Check MySQL logs
docker logs dock-dash-mysql

# Test database connection
docker exec -it dock-dash-mysql mysql -u root -p
```

#### 4. Health Check Failing
```bash
# Check health status
curl -f http://localhost:8500/health

# View detailed health info
curl http://localhost:8500/health | jq
```

### Debug Commands

```bash
# Enter backend container
docker exec -it dock-dash-backend /bin/bash

# Check Python processes
docker exec dock-dash-backend ps aux

# Test database connectivity from container
docker exec dock-dash-backend python -c "from database import UserDatabase; db = UserDatabase(); print('DB OK')"

# Check Docker CLI access from container
docker exec dock-dash-backend docker ps
```

## 🚀 Production Deployment

### Resource Requirements

**Minimum:**
- CPU: 1 core
- RAM: 1GB
- Disk: 5GB

**Recommended:**
- CPU: 2 cores
- RAM: 2GB
- Disk: 20GB

### Security Considerations

1. **Change Default Passwords**: Update database passwords in production
2. **Network Security**: Use Docker networks for service isolation
3. **Volume Permissions**: Ensure proper file permissions on mounted volumes
4. **SSL/TLS**: Configure reverse proxy with SSL for production

### Scaling

```bash
# Scale backend instances (with load balancer)
docker-compose up --scale backend=3

# Use external database for high availability
# Update DB_HOST to external MySQL instance
```

## 📝 Maintenance

### Backup Database
```bash
# Backup MySQL data
docker exec dock-dash-mysql mysqldump -u root -p12qwaszx user_auth_db > backup.sql

# Restore from backup
docker exec -i dock-dash-mysql mysql -u root -p12qwaszx user_auth_db < backup.sql
```

### Update Images
```bash
# Rebuild backend image
./scripts/build-docker.sh

# Update and restart services
docker-compose pull
docker-compose up -d
```

### Log Management
```bash
# Rotate logs
docker logs dock-dash-backend > backend-$(date +%Y%m%d).log

# Clean old logs
docker system prune -f
```

## 🔗 API Endpoints

Once running, the backend provides these key endpoints:

- **Health Check**: `GET /health`
- **Authentication**: `POST /api/login`, `POST /api/logout`
- **User Management**: `GET /api/admin/users`, `POST /api/admin/users`
- **Server Management**: `GET /api/admin/servers`
- **Docker Management**: `GET /api/admin/docker-images`
- **SSH Management**: `POST /api/admin/servers/{id}/ssh/connect`

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review container logs: `docker logs dock-dash-backend`
3. Verify health status: `curl http://localhost:8500/health`
4. Check Docker socket permissions and connectivity

---

**Note**: This Docker setup provides full container management capabilities while maintaining security and minimal image size. The backend can manage Docker containers on the host system through the mounted Docker socket.
