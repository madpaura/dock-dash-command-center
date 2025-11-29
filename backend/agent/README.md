# GPU Dashboard - Agent Service

Distributed Docker agent service for container management and resource monitoring.

## Overview

The agent runs on each Docker host and provides:
- Container lifecycle management (create, start, stop, delete)
- System resource monitoring (CPU, memory, disk)
- Port allocation and management
- Workspace setup and configuration

## Quick Start

### 1. Setup Environment
```bash
cd backend/agent

# Create virtual environment (or use existing)
python -m venv agent-env
source agent-env/bin/activate

# Install dependencies
pip install -r requirements-agent.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Run Agent
```bash
python agent_server.py
```

Agent starts at `http://0.0.0.0:8510`

## Configuration

### Environment Variables (`.env`)

```bash
# Agent
AGENT_PORT=8510

# Docker
DOCKER_IMAGE=gpu-dev-env-test
DOCKER_TAG=latest
DOCKER_HOSTNAME=cxl-dev
DOCKER_CPU=4
DOCKER_CPU_PERCENT=100
DOCKER_MEM_LMT=4g
DOCKER_MEM_SWAP=5g

# Code Server
CODE_DEFAULT_WORKSPACE=/workspace
CODE_PORT=8080
SUDO_PASSWORD=abc

# Jupyter
JUPYTER_PORT=8888

# Workspace Paths
WORKDIR_TEMPLATE=/home/user/template/
WORKDIR_DEPLOY=/home/user/vms/
WORKSPACE_MOUNT=/home/developer/workspace

# Optional Mounts
QVP_BINARY_MOUNT=/opt/qvp
TOOLS_MOUNT=/opt/tools
GUEST_OS_MOUNT=/opt/os/guestos
```

## Project Structure

```
agent/
├── agent_server.py        # Main Flask application
├── container_manager.py   # Docker container operations
├── monitoring_service.py  # System monitoring
├── resource_allocator.py  # Port allocation
├── config_validator.py    # Startup validation
├── .env                   # Configuration
└── port_manager.db        # Port allocation database
```

## API Endpoints

### Health & Monitoring
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/get_system_stats` | System resources |
| GET | `/get_docker_images` | List Docker images |

### Container Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/containers` | Create container |
| POST | `/api/containers/<id>/start` | Start container |
| POST | `/api/containers/<id>/stop` | Stop container |
| POST | `/api/containers/<id>/delete` | Delete container |
| GET | `/api/containers/<id>/status` | Container status |
| GET | `/api/containers/<id>/ports` | Port allocations |

### Image Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/get_docker_images` | List images |
| DELETE | `/delete_docker_image/<id>` | Delete image |

## Components

### ContainerManager
Handles Docker container operations using the Docker SDK.

```python
class DockerContainerManager:
    def create_container(image, name, ports, volumes, ...) -> Container
    def start_container(container_id, recreate_if_missing) -> dict
    def stop_container(container_id) -> dict
    def delete_container(container_id) -> dict
```

Features:
- Automatic image pull if not found
- NVIDIA runtime support with fallback
- Workspace setup and permissions
- Port mapping configuration

### MonitoringService
Collects system resource statistics.

```python
# Returns:
{
    'cpu_percent': 45.2,
    'memory_percent': 62.1,
    'memory_total': 16000000000,
    'memory_available': 6000000000,
    'disk_percent': 55.0,
    'disk_total': 500000000000,
    'disk_free': 225000000000
}
```

### PortManager
Manages dynamic port allocation for user containers.

```python
class PortManager:
    def allocate_ports(username) -> dict  # Returns port range
    def deallocate_ports(username) -> bool
    def get_allocated_ports(username) -> dict
```

Port allocation scheme (per user):
- `start_port + 0`: Code Server (8080)
- `start_port + 1`: SSH (2222)
- `start_port + 2`: Spice
- `start_port + 3`: FM UI
- `start_port + 4`: FM
- `start_port + 8`: Jupyter (8888)

## Container Creation Flow

1. **Port Allocation**: Allocate unique port range for user
2. **Workspace Setup**: Copy template to user directory
3. **Volume Configuration**: Setup mounts for workspace, tools, etc.
4. **Container Creation**: Create Docker container with configuration
5. **Start Container**: Start and verify container is running

```python
# Example container creation
POST /api/containers
{
    "username": "user1",
    "image": "gpu-dev-env-test:latest",
    "cpu": 4,
    "memory": "4g"
}
```

## Configuration Validation

On startup, the agent validates:
- Required environment variables
- Workspace directories exist and are writable
- Docker daemon is accessible
- Docker image is available (or can be pulled)

```python
from config_validator import validate_agent_config
validate_agent_config(strict=True)
```

## Docker Deployment

### Using Docker Compose
```bash
# From project root
./scripts/agent/agent-compose-up.sh
```

### Manual Docker Run
```bash
docker build -t dock-dash-agent -f backend/agent/Dockerfile .
docker run -d \
  --name dock-dash-agent \
  -p 8510:8510 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /home/user/vms:/home/user/vms \
  dock-dash-agent
```

### Volume Mounts (Required)
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock  # Docker access
  - /home/user/vms:/home/user/vms              # User workspaces
  - /home/user/template:/home/user/template    # Workspace template
```

## Troubleshooting

### Agent Won't Start
```bash
# Check configuration
python config_validator.py

# Check Docker access
docker ps

# Check logs
tail -f agent_service.log
```

### Container Creation Fails
```bash
# Check Docker image exists
docker images | grep gpu-dev-env

# Check workspace directories
ls -la /home/user/vms/
ls -la /home/user/template/

# Check port availability
netstat -tlnp | grep 9000
```

### NVIDIA Runtime Error
If NVIDIA runtime is not available, the agent will automatically fall back to creating containers without GPU support.

### Port Conflicts
```bash
# Check allocated ports
sqlite3 port_manager.db "SELECT * FROM port_allocations;"

# Deallocate ports for user
curl -X POST http://localhost:8510/api/ports/deallocate -d '{"username": "user1"}'
```

## Logging

Logs are written to `agent_service.log`:
```bash
tail -f agent_service.log
```

Log levels:
- INFO: Normal operations
- WARNING: Non-critical issues
- ERROR: Failures requiring attention
- SUCCESS: Successful operations

## Security Considerations

1. **Docker Socket**: Mounting Docker socket gives full Docker access
2. **Port Range**: Ensure allocated port range is available
3. **Workspace Permissions**: Set proper ownership (1000:1000 for container user)
4. **Network**: Consider firewall rules for agent port
