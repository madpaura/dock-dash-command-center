# GPU Dashboard - Backend

Flask-based backend API for the GPU Dashboard Command Center.

## Technology Stack

- **Flask** - Web framework
- **Python 3.9+** - Runtime
- **MySQL** - Database
- **Docker SDK** - Container management
- **Paramiko** - SSH connections
- **Loguru** - Logging

## Quick Start

### 1. Setup Virtual Environment
```bash
python -m venv admin-env
source admin-env/bin/activate  # Linux/Mac
# or
admin-env\Scripts\activate     # Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Setup Database
```bash
# MySQL must be running
# Database will be auto-initialized on first run
```

### 5. Run Server
```bash
python app.py
```

Server starts at `http://localhost:8500`

## Configuration

### Environment Variables (`.env`)

```bash
# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=user_auth_db

# Server
MGMT_SERVER_IP=127.0.0.1
MGMT_SERVER_PORT=8500

# Agent Communication
AGENT_PORT=8510
AGENTS_LIST=192.168.1.100,192.168.1.101

# Docker Defaults
DOCKER_IMAGE=gpu-dev-env-test
DOCKER_TAG=latest
DOCKER_CPU=4
DOCKER_MEM_LMT=4g

# Workspace Paths
WORKDIR_TEMPLATE=/path/to/template/
WORKDIR_DEPLOY=/path/to/vms/

# Nginx
NGINX_CONFIG_FILE=/etc/nginx/sites-available/dev-services
```

## Project Structure

```
backend/
├── app.py                 # Main Flask application
├── services/              # Business logic layer
│   ├── auth_service.py    # Authentication
│   ├── user_service.py    # User management
│   ├── server_service.py  # Server operations
│   ├── docker_service.py  # Docker management
│   ├── agent_service.py   # Agent communication
│   ├── nginx_service.py   # Nginx routing
│   ├── ssh_service.py     # SSH connections
│   ├── audit_service.py   # Audit logging
│   └── cleanup_service.py # Resource cleanup
├── database/              # Data access layer
│   ├── __init__.py        # Database manager
│   ├── base.py            # Base repository
│   ├── user_repository.py # User CRUD
│   ├── session_repository.py
│   └── audit_repository.py
├── utils/                 # Utilities
│   ├── config_validator.py # Startup validation
│   ├── permissions.py     # RBAC permissions
│   ├── validators.py      # Input validation
│   └── helpers.py         # Helper functions
├── nginx/                 # Nginx management
│   ├── add_user.py        # User route management
│   └── sites-available/   # Config files
├── api/                   # Additional API routes
│   ├── container_routes.py
│   └── traffic_routes.py
├── middleware/            # Request middleware
│   └── traffic_tracker.py
└── agent/                 # Agent service (separate)
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | User login |
| POST | `/api/logout` | User logout |
| POST | `/api/register` | User registration |
| GET | `/api/validate-session` | Validate session |

### Admin - Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/users` | List all users |
| POST | `/api/admin/users` | Create user |
| PUT | `/api/admin/users/<id>` | Update user |
| DELETE | `/api/users/<id>` | Delete user |
| POST | `/api/admin/users/<id>/approve` | Approve user |
| POST | `/api/admin/users/<id>/reset-password` | Reset password |

### Admin - Servers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/servers` | List servers |
| POST | `/api/admin/servers` | Add server |
| DELETE | `/api/admin/servers/<id>` | Remove server |
| GET | `/api/admin/servers/<id>/stats` | Server statistics |

### Admin - Docker
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/docker-images` | List images |
| DELETE | `/api/admin/docker-images/<id>` | Delete image |
| POST | `/api/admin/servers/<id>/cleanup` | Cleanup server |

### User Services
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/user/services` | Get user services |
| GET | `/api/user/container/status` | Container status |
| POST | `/api/containers/<id>/start` | Start container |
| POST | `/api/containers/<id>/stop` | Stop container |

### Health & Monitoring
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/admin/logs` | Audit logs |
| GET | `/api/admin/stats` | System statistics |

## Services Architecture

### AuthService
- User authentication
- Session management
- Password hashing (bcrypt)

### UserService
- User CRUD operations
- Container assignment
- Workspace management
- Nginx route configuration

### AgentService
- Communication with Docker agents
- Container lifecycle operations
- Resource queries

### NginxService
- User route management
- Configuration updates
- Nginx reload

## Configuration Validation

The backend validates all configuration on startup:

```python
from utils.config_validator import validate_config

# Checks:
# - Required environment variables
# - Directory paths exist
# - File paths accessible
# - Network settings valid
# - Database connectivity
```

If validation fails, the server will not start and will display specific errors.

## Permissions System

Role-based access control with three user types:

| Permission | Admin | QVP | Regular |
|------------|-------|-----|---------|
| manage_users | ✓ | ✗ | ✗ |
| view_servers | ✓ | ✓ | ✗ |
| delete_image | ✓ | ✗ | ✗ |
| build_images | ✓ | ✓ | ✗ |
| view_dashboard | ✓ | ✓ | ✗ |

## Development

### Debug Mode
Auto-reload is enabled by default:
```python
app.run(debug=True, use_reloader=True)
```

### Logging
Uses Loguru for structured logging:
```python
from loguru import logger
logger.info("Message")
logger.error("Error occurred")
```

Logs are written to `manager_backend.log`.

### Adding New Endpoints
1. Add route in `app.py` or create new file in `api/`
2. Create service method if needed
3. Add permission check if required
4. Update API documentation

## Testing

```bash
# Run nginx routing tests
cd nginx/test
python test_nginx_routing.py
```

## Docker Deployment

See `DOCKER_README.md` in project root for Docker deployment instructions.
