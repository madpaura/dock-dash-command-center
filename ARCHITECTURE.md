# GPU Dashboard Command Center - Architecture Overview

## System Architecture

The GPU Dashboard Command Center is a comprehensive container management platform built with a modern microservices architecture. The system consists of three main layers:

### 1. Frontend Layer (React + TypeScript)
**Location**: `/src/`
- **Framework**: React 18 with TypeScript, Vite build system
- **UI Library**: Tailwind CSS with shadcn-ui components
- **State Management**: React Context API for authentication
- **Key Components**:
  - **Pages**: AdminDashboard, AdminServers, AdminImages, AdminUsers, AdminLogs, UserDashboard, UserContainers, UserFileBrowser
  - **Components**: SSH Terminal, Server Dialogs, Resource Monitor, Container Cards, Cleanup Dialog
  - **API Layer**: Structured API clients for backend communication

### 2. Backend Layer (Flask + Python)
**Location**: `/backend/`
- **Framework**: Flask with modular architecture
- **Authentication**: Session-based with Bearer tokens
- **Architecture Pattern**: Service-Repository pattern

#### Core Components:
- **API Routes** (`app.py`): RESTful endpoints for all operations
- **Services** (`/services/`): Business logic layer
  - AuthService, UserService, ServerService, DockerService
  - SSHService, CleanupService, AuditService, AgentService, NginxService
- **Database** (`/database/`): Repository pattern with MySQL
  - UserRepository, SessionRepository, AuditRepository
- **Utils** (`/utils/`): Helper functions, validators, config validation, permissions

### 3. Agent Layer (Flask + Docker SDK)
**Location**: `/backend/agent/`
- **Purpose**: Distributed agents running on each Docker host
- **Key Components**:
  - **MonitoringService**: Resource collection and system monitoring
  - **ContainerManager**: Docker container lifecycle management
  - **ResourceAllocator**: CPU, memory, and port allocation
  - **PortManager**: Dynamic port allocation and management

## Data Flow Architecture

```
Frontend (React) 
    ↓ HTTP/REST API
Backend (Flask)
    ↓ Service Layer
Database (MySQL) + Agent Communication
    ↓ HTTP API Calls
Agent Services (Multiple Hosts)
    ↓ Docker SDK
Docker Daemon (Container Management)
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           GPU DASHBOARD COMMAND CENTER                          │
│                                ARCHITECTURE DIAGRAM                             │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND LAYER (React + TypeScript)               │
├─────────────────┬─────────────────┬─────────────────┬─────────────────────────┤
│     PAGES       │   COMPONENTS    │   API LAYER     │      HOOKS & UTILS      │
├─────────────────┼─────────────────┼─────────────────┼─────────────────────────┤
│ • AdminDashboard│ • Header/Sidebar│ • authApi       │ • useAuth               │
│ • AdminServers  │ • SSH Terminal  │ • adminApi      │ • usePermissions        │
│ • AdminImages   │ • Server Dialogs│ • serverApi     │ • useToast              │
│ • AdminUsers    │ • User Mgmt     │ • dockerApi     │ • API utilities         │
│ • AdminLogs     │ • Resource Mon  │ • userApi       │ • Validators            │
│ • UserDashboard │ • Container Cards│ • auditApi      │ • Theme Toggle          │
│ • UserContainers│ • Cleanup Dialog│ • sshApi        │ • Toast System          │
│ • UserFileBrowser│ • File Browser │ • cleanupApi    │ • Loading States        │
│ • Login/Register│ • Status Comps  │                 │                         │
└─────────────────┴─────────────────┴─────────────────┴─────────────────────────┘
                                        │
                                        │ HTTP/REST API
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND LAYER (Flask + Python)                    │
├─────────────────┬─────────────────┬─────────────────┬─────────────────────────┤
│   API ROUTES    │    SERVICES     │    DATABASE     │        UTILS            │
├─────────────────┼─────────────────┼─────────────────┼─────────────────────────┤
│ • /api/auth/*   │ • AuthService   │ • UserRepository│ • ConfigValidator       │
│ • /api/admin/*  │ • UserService   │ • SessionRepo   │ • Permissions           │
│ • /api/users/*  │ • ServerService │ • AuditRepo     │ • Validators            │
│ • /api/servers/*│ • DockerService │ • DatabaseMgr   │ • Helpers               │
│ • /api/docker/* │ • SSHService    │ • Connection    │                         │
│ • /api/ssh/*    │ • CleanupService│   Pool          │                         │
│ • /api/cleanup/*│ • AuditService  │ • MySQL DB      │                         │
│ • /api/audit/*  │ • AgentService  │                 │                         │
│                 │ • NginxService  │                 │                         │
└─────────────────┴─────────────────┴─────────────────┴─────────────────────────┘
                                        │
                                        │ HTTP API Calls
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AGENT LAYER (Distributed Flask Services)             │
├─────────────────┬─────────────────┬─────────────────┬─────────────────────────┤
│  MONITORING     │  CONTAINER MGR  │ RESOURCE ALLOC  │    PORT MANAGEMENT      │
├─────────────────┼─────────────────┼─────────────────┼─────────────────────────┤
│ • System Stats  │ • Docker SDK    │ • CPU Allocation│ • Dynamic Ports         │
│ • Resource Mon  │ • Lifecycle Mgr │ • Memory Limits │ • Conflict Resolution   │
│ • Health Checks │ • Image Mgmt    │ • GPU Assignment│ • User Isolation        │
│ • Performance   │ • Volume Mgmt   │ • Resource Pool │ • Port Tracking         │
│   Metrics       │ • Network Mgmt  │ • Quota Mgmt    │ • Range Management      │
│ • Cache Layer   │ • Container     │ • Load Balancing│ • Allocation DB         │
│   (10s TTL)     │   Operations    │                 │                         │
└─────────────────┴─────────────────┴─────────────────┴─────────────────────────┘
                                        │
                                        │ Docker SDK
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DOCKER INFRASTRUCTURE                              │
├─────────────────┬─────────────────┬─────────────────┬─────────────────────────┤
│   HOST SERVER 1 │   HOST SERVER 2 │   HOST SERVER 3 │      SHARED STORAGE     │
├─────────────────┼─────────────────┼─────────────────┼─────────────────────────┤
│ • Docker Daemon │ • Docker Daemon │ • Docker Daemon │ • Image Registry        │
│ • Agent Service │ • Agent Service │ • Agent Service │ • Volume Storage        │
│ • User Containers│ • User Containers│ • User Containers│ • Backup Systems       │
│ • Resource Pools│ • Resource Pools│ • Resource Pools│ • Log Aggregation       │
│ • Network Stack │ • Network Stack │ • Network Stack │ • Monitoring Data       │
│ • Storage Vols  │ • Storage Vols  │ • Storage Vols  │                         │
└─────────────────┴─────────────────┴─────────────────┴─────────────────────────┘
```

## Key Features

### Multi-Tenant User Management
- **Admin Users**: Full system management capabilities
- **QVP Users**: Restricted admin access (build/deploy only, no user management)
- **Regular Users**: Container access with resource limits
- **Authentication**: Session-based with audit logging
- **Authorization**: Role-based access control with granular permissions

### Container Orchestration
- **Lifecycle Management**: Create, start, stop, delete containers
- **Resource Allocation**: CPU, memory, GPU assignment
- **Port Management**: Dynamic port allocation with conflict resolution
- **Multi-Host Support**: Distributed agent architecture
- **Workspace Management**: Persistent user workspaces with automatic setup

### Infrastructure Monitoring
- **Real-time Metrics**: CPU, memory, disk usage across hosts
- **Container Statistics**: Resource usage and performance monitoring
- **Server Health**: Online/offline status with automatic detection
- **Audit Logging**: Comprehensive action tracking

### Advanced Operations
- **SSH Terminal**: Web-based SSH access to containers and hosts
- **Server Cleanup**: Automated Docker cleanup with selective operations
- **Image Management**: Docker image browsing, building, and registry push
- **File Browser**: Container filesystem access
- **Nginx Routing**: Automatic user-specific routing configuration

## Security Architecture

### Authentication & Authorization
- **Session Management**: Secure session tokens with expiration
- **Role-Based Access**: Admin, QVP, and Regular user types
- **Permission System**: Granular permission checks for all operations
- **API Security**: Bearer token authentication for all endpoints
- **Audit Trail**: Complete logging of all user actions

### Network Security
- **Agent Communication**: Secure HTTP API between backend and agents
- **SSH Integration**: Secure shell access with credential management
- **Port Isolation**: User-specific port allocations
- **Nginx Proxy**: Reverse proxy for user service isolation

## Database Schema

### Core Tables
- **users**: User accounts, roles, metadata, and container assignments
- **user_sessions**: Active session management
- **audit_logs**: Comprehensive action logging
- **port_allocations**: Dynamic port assignment tracking
- **registry_servers**: Docker registry configurations
- **build_projects**: Build project definitions
- **upload_servers**: Guest OS upload server configurations

## Technology Stack

### Frontend
- React 18, TypeScript, Tailwind CSS, Vite
- React Router, React Context API
- Lucide React (icons), Recharts (charts)
- shadcn-ui components

### Backend
- Flask, Python 3.9+, MySQL
- Docker SDK, Paramiko (SSH), Requests
- Session tokens, Bcrypt (password hashing)
- Loguru (logging)

### Infrastructure
- Docker, Docker Compose
- Nginx (reverse proxy)
- Ubuntu/Linux (host OS)
- NVIDIA Container Toolkit (GPU support)

## Scalability Features

### Horizontal Scaling
- **Agent Distribution**: Add new Docker hosts with agent deployment
- **Load Distribution**: Automatic server selection for new containers
- **Resource Pooling**: Aggregate resource management across hosts

### Performance Optimizations
- **Caching**: Server resource caching (30s TTL)
- **Concurrent Processing**: ThreadPoolExecutor for agent queries
- **Connection Pooling**: Database connection management
- **Timeout Management**: Configurable timeouts for agent communication
- **Configuration Validation**: Startup checks to prevent runtime errors
