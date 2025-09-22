# VSCode & Jupyter Password Integration

This document explains how user login passwords are integrated with VSCode and Jupyter containers for authentication.

## Overview

The system now supports password-based authentication for VSCode and Jupyter services using the user's login password or a custom container password.

## Architecture

### 1. Password Flow
```
User Registration/Approval → Container Creation → Password Configuration → VSCode/Jupyter Authentication
```

### 2. Components

#### Backend Components:
- **Container Manager** (`container_manager.py`): Accepts password parameter during container creation
- **User Service** (`user_service.py`): Manages user approval and container password settings
- **Password Configuration Script** (`configure-passwords.sh`): Configures VSCode and Jupyter with passwords
- **API Endpoints**: Handle password setting and user approval with passwords

#### Container Components:
- **Environment Variables**: Pass passwords to VSCode and Jupyter services
- **Configuration Files**: Generate VSCode and Jupyter config files with password authentication

## Usage

### 1. User Approval with Password
When approving a user, admins can provide a password for VSCode/Jupyter access:

```bash
POST /api/admin/users/{user_id}/approve
{
  "server": "server-ip",
  "resources": {...},
  "password": "user_password_for_vscode_jupyter"
}
```

### 2. User Container Password Management
Users can set their own container passwords:

```bash
POST /api/users/{user_id}/set-container-password
{
  "container_password": "new_password_for_containers"
}
```

### 3. Container Creation
When containers are created, the password is passed as environment variables:

```bash
POST /api/containers/create
{
  "user": "username",
  "password": "user_password",
  "session_token": "token"
}
```

## Environment Variables

The following environment variables are set in containers:

- `PASSWORD`: User's password for VSCode authentication
- `SUDO_PASSWORD`: System sudo password (same as user password)
- `JUPYTER_TOKEN`: Jupyter authentication token
- `JUPYTER_PASSWORD`: Jupyter password authentication
- `USER`: Username for configuration

## Configuration Files Generated

### VSCode Configuration
Location: `/config/.config/code-server/config.yaml`
```yaml
bind-addr: 0.0.0.0:8080
auth: password
password: user_password
cert: false
disable-telemetry: true
disable-update-check: true
```

### Jupyter Configuration
Location: `/config/.jupyter/jupyter_server_config.py`
```python
c.ServerApp.ip = '0.0.0.0'
c.ServerApp.port = 8888
c.ServerApp.password = 'hashed_password'
c.ServerApp.token = ''
c.ServerApp.allow_origin = '*'
```

## Security Considerations

1. **Password Storage**: Passwords are hashed when stored in user metadata
2. **Environment Variables**: Passwords are passed securely through environment variables
3. **Container Isolation**: Each user gets their own isolated container with their password
4. **Access Control**: Users can only set their own passwords (unless admin)

## Default Behavior

- If no password is provided during approval, defaults to "changeme123"
- Users are encouraged to set their own container passwords after approval
- Passwords must be at least 6 characters long

## Troubleshooting

### Common Issues:
1. **VSCode not accepting password**: Check if config file was generated correctly
2. **Jupyter authentication failing**: Verify password hash generation
3. **Container startup issues**: Check environment variable passing

### Logs:
- Container creation logs: Check agent service logs
- Password configuration: Check container startup logs
- Authentication issues: Check VSCode/Jupyter service logs

## Future Enhancements

1. **Password Encryption**: Implement proper encryption for stored passwords
2. **Password Policies**: Add password complexity requirements
3. **Multi-factor Authentication**: Add 2FA support for enhanced security
4. **Password Rotation**: Automatic password rotation capabilities
