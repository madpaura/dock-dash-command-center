# Backend Architecture

## Overview

The backend follows a **Service-Repository** pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                      Flask Application                       │
│                         (app.py)                            │
├─────────────────────────────────────────────────────────────┤
│                      API Routes Layer                        │
│   /api/auth/* │ /api/admin/* │ /api/users/* │ /api/...     │
├─────────────────────────────────────────────────────────────┤
│                      Services Layer                          │
│  AuthService │ UserService │ ServerService │ AgentService   │
├─────────────────────────────────────────────────────────────┤
│                    Repository Layer                          │
│  UserRepository │ SessionRepository │ AuditRepository       │
├─────────────────────────────────────────────────────────────┤
│                      Database (MySQL)                        │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
backend/
├── app.py                    # Main application entry point
├── services/                 # Business logic
│   ├── auth_service.py       # Authentication & sessions
│   ├── user_service.py       # User management & containers
│   ├── server_service.py     # Server monitoring
│   ├── docker_service.py     # Docker image management
│   ├── agent_service.py      # Agent communication
│   ├── nginx_service.py      # Nginx routing
│   ├── ssh_service.py        # SSH connections
│   ├── audit_service.py      # Audit logging
│   ├── cleanup_service.py    # Resource cleanup
│   ├── container_service.py  # Container operations
│   ├── traffic_service.py    # Traffic monitoring
│   ├── build_service.py      # Docker image builds
│   ├── registry_service.py   # Registry management
│   └── upload_service.py     # Guest OS uploads
├── database/                 # Data access
│   ├── __init__.py           # Database manager
│   ├── base.py               # Base repository class
│   ├── user_repository.py    # User CRUD
│   ├── session_repository.py # Session management
│   ├── audit_repository.py   # Audit logs
│   ├── registry_repository.py
│   ├── project_repository.py
│   └── upload_repository.py
├── utils/                    # Utilities
│   ├── config_validator.py   # Startup validation
│   ├── permissions.py        # RBAC system
│   ├── validators.py         # Input validation
│   └── helpers.py            # Helper functions
├── api/                      # Additional route modules
│   ├── container_routes.py
│   ├── traffic_routes.py
│   ├── registry_routes.py
│   ├── build_routes.py
│   └── upload_routes.py
├── middleware/               # Request middleware
│   └── traffic_tracker.py
├── nginx/                    # Nginx management
│   ├── add_user.py           # User route manager
│   ├── sites-available/      # Config files
│   └── test/                 # Tests
└── agent/                    # Agent service (separate deployment)
```

## Services

### AuthService
Handles authentication and session management.

```python
class AuthService:
    def login(email, password) -> dict
    def logout(token) -> bool
    def validate_session(token) -> dict
    def register_user(email, password, username) -> dict
```

### UserService
Manages users, containers, and workspaces.

```python
class UserService:
    def get_user_by_id(user_id) -> dict
    def delete_user(user_id, admin_username, delete_workspace) -> dict
    def approve_user(user_id, server, resources, admin_username) -> dict
    def get_admin_users() -> list
    def admin_reset_password(user_id, new_password, admin_username) -> dict
```

Key responsibilities:
- User CRUD operations
- Container creation and assignment
- Workspace setup and deletion
- Nginx route configuration

### AgentService
Communicates with Docker agents on remote hosts.

```python
class AgentService:
    def query_agent_stats(agent_ip) -> dict
    def create_container(agent_ip, config) -> dict
    def delete_container(agent_ip, container_name) -> dict
    def query_agent_port_info(agent_ip, container_name) -> dict
```

### NginxService
Manages nginx routing for user services.

```python
class NginxService:
    def add_user_route(username, vscode_server, jupyter_server) -> dict
    def remove_user_route(username) -> dict
    def check_user_exists(username) -> bool
```

## Database Schema

### users
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(255) UNIQUE,
    email VARCHAR(255) UNIQUE,
    password VARCHAR(255),
    is_admin BOOLEAN,
    is_approved BOOLEAN,
    user_type ENUM('admin', 'qvp', 'regular'),
    status VARCHAR(50),
    metadata JSON,
    redirect_url VARCHAR(255),
    created_at TIMESTAMP,
    last_login TIMESTAMP
);
```

### user_sessions
```sql
CREATE TABLE user_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    session_token VARCHAR(255),
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN
);
```

### audit_logs
```sql
CREATE TABLE audit_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(255),
    action_type VARCHAR(100),
    details JSON,
    ip_address VARCHAR(50),
    server_id VARCHAR(100),
    log_level VARCHAR(20),
    source VARCHAR(100),
    created_at TIMESTAMP
);
```

## Permission System

### User Types
- **admin**: Full system access
- **qvp**: Restricted admin (build/deploy only)
- **regular**: Own container access only

### Permission Checks
```python
from utils.permissions import has_permission, require_permission

# Check permission
if has_permission(user_type, 'manage_users'):
    # Allow action

# Decorator for routes
@require_permission('delete_user')
def delete_user_endpoint():
    pass
```

### Permission Matrix
| Permission | admin | qvp | regular |
|------------|-------|-----|---------|
| view_dashboard | ✓ | ✓ | ✗ |
| manage_users | ✓ | ✗ | ✗ |
| view_servers | ✓ | ✓ | ✗ |
| delete_server | ✓ | ✗ | ✗ |
| view_images | ✓ | ✓ | ✗ |
| delete_image | ✓ | ✗ | ✗ |
| build_images | ✓ | ✓ | ✗ |
| push_images | ✓ | ✓ | ✗ |

## Configuration Validation

On startup, the backend validates:

1. **Required Environment Variables**
   - MGMT_SERVER_IP
   - AGENT_PORT
   - WORKDIR_DEPLOY
   - WORKDIR_TEMPLATE
   - NGINX_CONFIG_FILE

2. **Directory Paths**
   - Workspace directories exist
   - Directories are readable/writable

3. **File Paths**
   - Nginx config file accessible

4. **Network Settings**
   - Valid port numbers
   - Valid IP addresses

5. **Database Configuration**
   - Connection parameters set

```python
from utils.config_validator import validate_config

# Raises ConfigValidationError if validation fails
validate_config(strict=True)
```

## Request Flow

### User Login
```
1. POST /api/login
2. AuthService.login()
3. UserRepository.get_user_by_email()
4. Verify password (bcrypt)
5. SessionRepository.create_session()
6. Return session token
```

### Container Creation (User Approval)
```
1. POST /api/admin/users/{id}/approve
2. UserService.approve_user()
3. AgentService.create_container()
4. NginxService.add_user_route()
5. UserRepository.update_user_metadata()
6. AuditRepository.log_event()
```

### User Deletion
```
1. DELETE /api/users/{id}
2. UserService.delete_user()
3. AgentService.delete_container()
4. NginxService.remove_user_route()
5. (Optional) Delete workspace folder
6. UserRepository.delete_user()
7. AuditRepository.log_event()
```

## Error Handling

All services return consistent response format:

```python
{
    'success': True/False,
    'message': 'Description',
    'data': {...}  # Optional
}
```

Errors are logged with Loguru:
```python
from loguru import logger

logger.error(f"Failed to create container: {e}")
logger.info(f"User {username} logged in")
logger.warning(f"Agent {ip} not responding")
```

## Middleware

### Traffic Tracker
Tracks API request statistics:
```python
from middleware.traffic_tracker import setup_traffic_tracking
setup_traffic_tracking(app)
```

## Agent Communication

Backend communicates with agents via HTTP:

```python
# Agent endpoints
GET  /health                    # Health check
GET  /get_system_stats          # System resources
POST /api/containers            # Create container
POST /api/containers/{id}/start # Start container
POST /api/containers/{id}/stop  # Stop container
POST /api/containers/{id}/delete # Delete container
GET  /api/containers/{id}/ports # Get port info
```

## Scalability

- **Multiple Agents**: Backend can manage multiple Docker hosts
- **Connection Pooling**: Database connections are pooled
- **Caching**: Server stats cached with TTL
- **Concurrent Queries**: ThreadPoolExecutor for parallel agent queries
