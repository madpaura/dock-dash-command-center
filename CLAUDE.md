# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Dock Dash Command Center** is a full-stack application for managing Docker containers, servers, and user access with a web-based interface. The system includes:

- **Frontend**: React + TypeScript + Vite + shadcn-ui
- **Backend**: Flask + Python with modular service architecture
- **Database**: MySQL with SQLAlchemy ORM
- **Features**: User authentication, Docker management, SSH access, auditing, real-time monitoring

## Development Commands

### Frontend (React/TypeScript)
```bash
# Start development server
npm run dev

# Build for production
npm run build

# Build for development
npm run build:dev

# Lint code
npm run lint

# Preview production build
npm run preview
```

### Backend (Flask/Python)
```bash
# Run Flask development server (from backend/ directory)
cd backend
python app.py

# Install Python dependencies
pip install -r requirements.txt

# For Docker deployment requirements
pip install -r requirements-docker.txt
```

### Docker Deployment
```bash
# Full stack with Docker Compose
./scripts/docker-compose-up.sh

# Backend only
./scripts/build-docker.sh
./scripts/run-docker.sh

# Stop services
./scripts/docker-stop.sh --compose
```

## Architecture

### Frontend Structure
- `src/App.tsx`: Main application with routing
- `src/components/`: Reusable UI components
- `src/pages/`: Route-specific page components
- `src/hooks/`: Custom React hooks (auth, theme)
- `src/lib/`: Utilities and configurations

### Backend Structure
- `backend/app.py`: Main Flask application
- `backend/services/`: Modular service classes (auth, docker, ssh, etc.)
- `backend/database/`: Database models and repositories
- `backend/models/`: Data models
- `backend/utils/`: Helper functions and validators
- `backend/nginx/`: Nginx configuration and routing management
- `backend/agent/`: Agent services for container management

### Key Services
- `AuthService`: User authentication and session management
- `UserService`: User CRUD operations and permissions
- `DockerService`: Docker container management
- `SSHService`: SSH connection handling
- `ServerService`: Server management and monitoring
- `AgentService`: Container agent coordination
- `AuditService`: Activity logging and auditing
- `CleanupService`: Resource cleanup and maintenance

## Testing

### Frontend Testing
No test framework currently configured. Consider adding:
- Vitest for unit testing
- React Testing Library for component testing
- Playwright for E2E testing

### Backend Testing
Basic unittest framework exists in `backend/nginx/test/`:
```bash
# Run nginx routing tests
cd backend/nginx/test
python test_nginx_routing.py
```

Consider adding:
- pytest for comprehensive testing
- unittest coverage for all services
- Integration tests for API endpoints

## Development Practices

### Code Style
- **Frontend**: ESLint with TypeScript/React rules
- **Backend**: Follow PEP 8 standards
- Use proper TypeScript typing throughout

### Database
- MySQL database with SQLAlchemy ORM
- Database models in `backend/database/`
- Repository pattern for data access

### API Design
- RESTful API endpoints in Flask
- JSON responses with consistent error handling
- Authentication via JWT tokens

### Real-time Features
- WebSocket support for real-time logs
- In-memory log storage with deque
- Real-time container status updates

## Deployment

### Docker Configuration
- Multi-stage Docker builds
- MySQL container for database
- Nginx reverse proxy
- Health checks and monitoring

### Environment Variables
- Backend uses `.env` file for configuration
- Frontend uses Vite environment variables
- Docker-specific configurations in `config.toml`

## Common Development Tasks

1. **Adding new API endpoints**:
   - Add route in `app.py`
   - Create corresponding service method
   - Update frontend API client

2. **Creating new components**:
   - Follow shadcn-ui patterns
   - Use TypeScript interfaces
   - Implement proper error handling

3. **Database changes**:
   - Update models in `backend/database/`
   - Create migration scripts if needed
   - Update repository classes

4. **Testing**:
   - Add unit tests for new functionality
   - Test both frontend and backend
   - Verify API contract consistency