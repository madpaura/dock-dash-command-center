# GPU Dashboard Command Center

A comprehensive web-based platform for managing Docker containers, GPU resources, and user access across multiple servers.

## Overview

GPU Dashboard Command Center provides:
- **Multi-tenant container management** with user isolation
- **GPU-enabled development environments** with VS Code Server and Jupyter
- **Real-time monitoring** of server resources and container statistics
- **Role-based access control** (Admin, QVP, Regular users)
- **Automated nginx routing** for user-specific service access

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ or compatible Linux distribution
- **RAM**: Minimum 4GB (8GB+ recommended)
- **Disk**: 20GB+ available space
- **Docker**: Docker Engine 20.10+
- **Docker Compose**: 2.0+

### For GPU Support
- NVIDIA GPU with CUDA support
- NVIDIA Container Toolkit installed
- NVIDIA drivers 470+

### Software Dependencies
- **Node.js**: 18+ (for frontend)
- **Python**: 3.9+ (for backend)
- **MySQL**: 8.0+ (or use Docker container)
- **Nginx**: For reverse proxy routing

## Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd dock-dash-command-center
```

### 2. Setup Database
```bash
# Using Docker (recommended)
docker run -d --name mysql \
  -e MYSQL_ROOT_PASSWORD=12qwaszx \
  -e MYSQL_DATABASE=user_auth_db \
  -p 3306:3306 \
  mysql:8.0

# Or use existing MySQL and create database
mysql -u root -p -e "CREATE DATABASE user_auth_db;"
```

### 3. Setup Backend
```bash
cd backend

# Create virtual environment
python -m venv admin-env
source admin-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run backend
python app.py
```

### 4. Setup Frontend
```bash
# From project root
npm install
npm run dev
```

### 5. Setup Agent (on each Docker host)
```bash
cd backend/agent

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run agent
python agent_server.py
```

## Configuration

### Backend Environment Variables (`.env`)

```bash
# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=12qwaszx
DB_NAME=user_auth_db

# Server
MGMT_SERVER_IP=127.0.0.1
MGMT_SERVER_PORT=8500

# Agent
AGENT_PORT=8510
AGENTS_LIST=192.168.1.100,192.168.1.101

# Docker
DOCKER_IMAGE=gpu-dev-env-test
DOCKER_TAG=latest

# Workspace
WORKDIR_TEMPLATE=/home/user/template/
WORKDIR_DEPLOY=/home/user/vms/

# Nginx
NGINX_CONFIG_FILE=/etc/nginx/sites-available/dev-services
```

### Agent Environment Variables

```bash
# Docker
DOCKER_IMAGE=gpu-dev-env-test
DOCKER_TAG=latest
DOCKER_CPU=4
DOCKER_MEM_LMT=4g

# Workspace
WORKDIR_TEMPLATE=/home/user/template/
WORKDIR_DEPLOY=/home/user/vms/

# Ports
CODE_PORT=8080
JUPYTER_PORT=8888
```

## Project Structure

```
dock-dash-command-center/
├── src/                    # Frontend (React + TypeScript)
│   ├── components/         # Reusable UI components
│   ├── pages/              # Route pages
│   ├── hooks/              # Custom React hooks
│   └── lib/                # API clients and utilities
├── backend/                # Backend (Flask + Python)
│   ├── services/           # Business logic services
│   ├── database/           # Database repositories
│   ├── utils/              # Helpers and validators
│   ├── nginx/              # Nginx configuration management
│   └── agent/              # Docker agent service
├── Docker/                 # Docker image build files
├── scripts/                # Deployment scripts
└── docs/                   # Documentation
```

## Access Points

After setup, access the services at:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | Web dashboard |
| Backend API | http://localhost:8500 | REST API |
| Agent API | http://localhost:8510 | Agent service |
| User VSCode | http://server/user/{username}/vscode/ | Per-user VS Code |
| User Jupyter | http://server/user/{username}/jupyter/ | Per-user Jupyter |

## User Roles

| Role | Capabilities |
|------|-------------|
| **Admin** | Full system access, user management, server management |
| **QVP** | Build/deploy access, no user management |
| **Regular** | Own container access only |

## Development

### Frontend Development
```bash
npm run dev          # Start dev server with hot reload
npm run build        # Build for production
npm run lint         # Run ESLint
```

### Backend Development
```bash
cd backend
source admin-env/bin/activate
python app.py        # Auto-reload enabled in debug mode
```

### Running Tests
```bash
# Backend nginx routing tests
cd backend/nginx/test
python test_nginx_routing.py
```

## Docker Deployment

### Full Stack
```bash
./scripts/admin/docker-compose-up.sh
```

### Agent Only
```bash
./scripts/agent/agent-compose-up.sh
```

## Troubleshooting

### Configuration Validation
The application validates all configuration on startup. If validation fails, check:
- All required environment variables are set
- Directory paths exist and are writable
- Database is accessible
- Docker daemon is running

### Common Issues

1. **Database connection failed**
   - Verify MySQL is running: `docker ps | grep mysql`
   - Check credentials in `.env`

2. **Agent not responding**
   - Verify agent is running: `curl http://agent-ip:8510/health`
   - Check Docker socket permissions

3. **Container creation fails**
   - Verify Docker image exists: `docker images`
   - Check workspace directories exist

4. **Nginx routing not working**
   - Verify nginx config: `sudo nginx -t`
   - Check nginx is reloaded: `sudo systemctl reload nginx`

## Documentation

- [Architecture Overview](./ARCHITECTURE.md) - System design and components
- [Backend README](../backend/README.md) - Backend setup and API details
- [Agent README](../backend/agent/README.md) - Agent deployment guide
- [Frontend README](../src/README.md) - Frontend development guide

## License

Proprietary - All rights reserved

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review application logs
3. Verify health endpoints
4. Check configuration validation output
