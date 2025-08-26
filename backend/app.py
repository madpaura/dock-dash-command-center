"""
Main Flask application using refactored services architecture.
This replaces the monolithic auth_service.py with a clean, modular structure.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import toml
from loguru import logger

# Import database
from database import UserDatabase

# Import services
from services.auth_service import AuthService
from services.user_service import UserService
from services.server_service import ServerService
from services.ssh_service import SSHService
from services.docker_service import DockerService
from services.audit_service import AuditService
from services.agent_service import AgentService
from services.cleanup_service import CleanupService

# Import utilities
from utils.helpers import get_client_ip
from utils.validators import is_valid_email
import json
from datetime import datetime
from collections import deque

# Configure logger
logger.add("manager_backend.log", rotation="500 MB", retention="10 days", level="INFO")

# In-memory log storage for real-time logs (max 1000 entries)
app_logs = deque(maxlen=1000)

def add_app_log(level, message, username=None, ip_address=None):
    """Add a log entry to the in-memory log storage"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'level': level,
        'message': message,
        'username': username,
        'ip_address': ip_address
    }
    app_logs.append(log_entry)
    
    # Also log to file
    if level == 'ERROR':
        logger.error(f"{message} | User: {username} | IP: {ip_address}")
    elif level == 'WARNING':
        logger.warning(f"{message} | User: {username} | IP: {ip_address}")
    else:
        logger.info(f"{message} | User: {username} | IP: {ip_address}")

# Load environment variables
from dotenv import load_dotenv
load_dotenv(".env", override=True)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize database
db = UserDatabase()
db.initialize_database()
agent_port = int(os.getenv('AGENT_PORT', '8510'))
nginx_config_file=os.getenv('NGINX_CONFIG_FILE', 'backend/nginx/sites-available/dev-services')

# Initialize services
agent_service = AgentService(agent_port, 20)
auth_service = AuthService(db)
user_service = UserService(db, nginx_config_file, agent_port)
server_service = ServerService(db, agent_service, agent_port)
ssh_service = SSHService(db)
docker_service = DockerService(db, agent_service, agent_port)
audit_service = AuditService(db)
cleanup_service = CleanupService(db)

# Import nginx service
from services.nginx_service import NginxService
nginx_service = NginxService(nginx_config_file)

# Authentication endpoints
@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    ip_address = get_client_ip(request)
    
    result = auth_service.login(email, password, ip_address)
    
    if result.success:
        return jsonify({
            'success': True,
            'data': {
                'user_id': result.user_id,
                'name': result.username,
                'role': result.role,
                'email': email,
                'token': result.token
            }
        })
    else:
        return jsonify({'success': False, 'error': result.message}), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    """User logout endpoint."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    ip_address = get_client_ip(request)
    
    success = auth_service.logout(token, ip_address)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Logout failed'}), 500


@app.route('/api/register', methods=['POST'])
def register():
    """User registration endpoint."""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    ip_address = get_client_ip(request)
    
    result = auth_service.register(username, password, email, ip_address)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@app.route('/api/validate-session', methods=['GET'])
def validate_session():
    """Session validation endpoint."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    session = auth_service.validate_session(token)
    
    if session:
        return jsonify({'success': True, 'session': session})
    else:
        return jsonify({'success': False, 'error': 'Invalid session'}), 401


# User management endpoints
@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users endpoint."""
    users = user_service.get_all_users()
    if users:
        return jsonify({'success': True, 'users': users})
    return jsonify({'success': False, 'error': 'No users found'}), 404


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_info(user_id):
    """Get user info endpoint."""
    user = user_service.get_user_by_id(user_id)
    if user:
        return jsonify({'success': True, 'redirect_url': user.get('redirect_url', '')})
    return jsonify({'success': False, 'error': 'User not found'}), 404


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    admin_username = auth_service.get_admin_username_from_token()
    result = user_service.delete_user(user_id, admin_username)
    
    if result['success']:
        return jsonify({
            'success': True,
            'message': result['message'],
            'user_deleted': result['user_deleted'],
            'container_deleted': result['container_deleted'],
            'container_details': result.get('container_details')
        })
    else:
        return jsonify({
            'success': False, 
            'error': result['message'],
            'user_deleted': result['user_deleted'],
            'container_deleted': result['container_deleted'],
            'container_details': result.get('container_details')
        }), 400


@app.route('/api/users/pending', methods=['GET'])
def get_pending_users():
    """Get pending users endpoint."""
    users = user_service.get_pending_users()
    if users:
        return jsonify({'success': True, 'users': users})
    return jsonify({'success': False, 'error': 'No pending users'}), 200


@app.route('/api/admin/users/<int:user_id>/approve', methods=['POST'])
def approve_user(user_id):
    """Approve user endpoint."""
    # Check admin authentication
    session, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    data = request.get_json()
    server_id = data.get('server')
    resources = data.get('resources', {})
    admin_username = session.get('username')
    ip_address = get_client_ip(request)
    
    result = user_service.approve_user(user_id, server_id, admin_username, agent_port, ip_address, resources)
    
    if result.get('success'):
        return jsonify(result)
    return jsonify(result), 400


# Admin user management endpoints
@app.route('/api/admin/users', methods=['GET'])
def get_admin_users():
    """Get admin users endpoint."""
    try:
        users = user_service.get_admin_users()
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        logger.error(f"Error fetching admin users: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch users'}), 500


@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    """Get admin stats endpoint."""
    try:
        stats = user_service.get_admin_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"Error fetching admin stats: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch statistics'}), 500


@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
def update_admin_user(user_id):
    """Update admin user endpoint."""
    try:
        data = request.get_json()
        admin_username = auth_service.get_admin_username_from_token()
        ip_address = get_client_ip(request)
        
        success = user_service.update_admin_user(user_id, data, admin_username, ip_address)
        
        if success:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return jsonify({'success': False, 'error': 'Failed to update user'}), 500


@app.route('/api/admin/users', methods=['POST'])
def create_admin_user():
    """Create admin user endpoint."""
    try:
        data = request.get_json()
        admin_username = auth_service.get_admin_username_from_token()
        ip_address = get_client_ip(request)
        
        result = user_service.create_admin_user(data, admin_username)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'success': False, 'error': 'Failed to create user'}), 500


# Server management endpoints
@app.route('/api/server-resources', methods=['GET'])
def get_server_resources():
    """Get server resources endpoint."""
    servers = server_service.get_server_resources()
    if servers:
        return jsonify({'success': True, 'servers': servers})
    return jsonify({'success': False, 'error': 'No servers available'}), 404


@app.route('/api/admin/servers', methods=['GET'])
def get_admin_servers():
    """Get admin servers endpoint."""
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    try:
        servers_data = server_service.get_admin_servers()
        return jsonify({'success': True, 'servers': servers_data})
    except Exception as e:
        logger.error(f"Error fetching server data: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch server data'}), 500


@app.route('/api/admin/servers/stats', methods=['GET'])
def get_server_stats():
    """Get server stats endpoint."""
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    try:
        stats = server_service.get_server_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"Error fetching server stats: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch server stats'}), 500


@app.route('/api/admin/servers/<server_id>/action', methods=['POST'])
def server_action(server_id):
    """Server action endpoint."""
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    data = request.get_json()
    action = data.get('action')
    
    if not action:
        return jsonify({'success': False, 'error': 'Action required'}), 400
    
    admin_username = auth_service.get_admin_username_from_token()
    ip_address = get_client_ip(request)
    
    result = server_service.perform_server_action(server_id, action, admin_username, ip_address)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@app.route('/api/admin/servers', methods=['POST'])
def add_server():
    """Add server endpoint."""
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Request data required'}), 400
    
    admin_username = auth_service.get_admin_username_from_token()
    ip_address = get_client_ip(request)
    
    result = server_service.add_server(data, admin_username, ip_address)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


# SSH management endpoints
@app.route('/api/admin/servers/<server_id>/ssh/connect', methods=['POST'])
def ssh_connect(server_id):
    """SSH connect endpoint."""
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    data = request.get_json()
    ssh_config = data.get('ssh_config', {})
    admin_username = auth_service.get_admin_username_from_token()
    ip_address = get_client_ip(request)
    
    result = ssh_service.create_ssh_connection(server_id, ssh_config, admin_username, ip_address)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@app.route('/api/admin/servers/ssh/<session_id>/execute', methods=['POST'])
def ssh_execute(session_id):
    """SSH execute endpoint."""
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    data = request.get_json()
    command = data.get('command', '')
    admin_username = auth_service.get_admin_username_from_token()
    ip_address = get_client_ip(request)
    
    result = ssh_service.execute_ssh_command(session_id, command, admin_username, ip_address)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@app.route('/api/admin/servers/ssh/<session_id>/output', methods=['GET'])
def ssh_get_output(session_id):
    """SSH get output endpoint."""
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    result = ssh_service.get_ssh_output(session_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 404


@app.route('/api/admin/servers/ssh/<session_id>/status', methods=['GET'])
def ssh_status(session_id):
    """SSH status endpoint."""
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    result = ssh_service.get_ssh_session_status(session_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500


@app.route('/api/admin/servers/ssh/<session_id>/disconnect', methods=['POST'])
def ssh_disconnect(session_id):
    """SSH disconnect endpoint."""
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    admin_username = auth_service.get_admin_username_from_token()
    ip_address = get_client_ip(request)
    
    result = ssh_service.disconnect_ssh_session(session_id, admin_username, ip_address)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 404


# Docker management endpoints
@app.route('/api/admin/docker-images', methods=['GET'])
def get_docker_images():
    """Get Docker images endpoint."""
    session, error_response, status_code = require_session_auth_docker()
    if error_response:
        return error_response, status_code
    
    server_id = request.args.get('server_id')
    result = docker_service.get_docker_images(server_id)
    
    return jsonify(result)


@app.route('/api/admin/docker-images/<server_id>/<image_id>/details', methods=['GET'])
def get_docker_image_details(server_id, image_id):
    """Get Docker image details endpoint."""
    session, error_response, status_code = require_session_auth_docker()
    if error_response:
        return error_response, status_code
    
    result = docker_service.get_docker_image_details(server_id, image_id)
    
    if 'error' in result:
        return jsonify(result), 500
    else:
        return jsonify(result)


@app.route('/api/admin/servers/list', methods=['GET'])
def get_servers_list():
    """Get servers list endpoint."""
    session, error_response, status_code = require_session_auth_docker()
    if error_response:
        return error_response, status_code
    
    try:
        servers_list = server_service.get_servers_list()
        return jsonify({'servers': servers_list})
    except Exception as e:
        logger.error(f"Error getting servers list: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/servers/for-users', methods=['GET'])
def get_servers_for_users():
    """Get servers list for user management with capacity information."""
    session, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        servers_list = server_service.get_servers_for_user_management()
        return jsonify({'success': True, 'servers': servers_list})
    except Exception as e:
        logger.error(f"Error getting servers for user management: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


# Audit logs endpoints
@app.route('/api/audit-logs', methods=['GET'])
def get_audit_logs():
    """Get audit logs endpoint."""
    try:
        logs = audit_service.get_audit_logs()
        return jsonify({'success': True, 'logs': logs})
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch logs'}), 500


@app.route('/api/audit-logs', methods=['DELETE'])
def clear_audit_logs():
    """Clear audit logs endpoint."""
    try:
        user_info, error_response, status_code = require_admin_auth_with_db()
        if error_response:
            return error_response, status_code
        
        admin_username = user_info.get('username', 'admin')
        ip_address = get_client_ip(request)
        
        success = audit_service.clear_audit_logs(admin_username, ip_address)
        
        if success:
            return jsonify({'success': True, 'message': 'All audit logs cleared successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to clear logs'}), 500
            
    except Exception as e:
        logger.error(f"Error clearing audit logs: {e}")
        return jsonify({'success': False, 'error': 'Failed to clear logs'}), 500


def require_admin_auth():
    """Require admin authentication for protected endpoints."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session = auth_service.validate_session(token)
    if not session:
        return None, jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    if not session.get('is_admin'):
        return None, jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    return session, None, None


def require_admin_auth_with_db():
    """Require admin authentication using database validation for audit endpoints."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, jsonify({'success': False, 'error': 'No authorization token provided'}), 401
    
    token = auth_header.split(' ')[1]
    user_info = db.validate_session(token)
    
    if not user_info or user_info.get('role') != 'admin':
        return None, jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    return user_info, None, None


def require_session_auth():
    """Require basic session authentication for protected endpoints."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, jsonify({'success': False, 'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    session = db.verify_session(token)
    if not session:
        return None, jsonify({'success': False, 'error': 'Invalid session'}), 401
    
    return session, None, None


def require_session_auth_docker():
    """Require session authentication for Docker endpoints with specific error format."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, jsonify({'error': 'No authorization token provided'}), 401
    
    token = auth_header.split(' ')[1]
    session = db.verify_session(token)
    if not session:
        return None, jsonify({'error': 'Invalid session token'}), 401
    
    return session, None, None


# Cleanup management endpoints
@app.route('/api/admin/servers/<server_id>/cleanup/summary', methods=['POST'])
def get_cleanup_summary(server_id):
    """Get cleanup summary endpoint."""
    try:
        session, error_response, status_code = require_admin_auth()
        if error_response:
            return error_response, status_code
        
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        ssh_port = data.get('ssh_port', 22)
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'SSH credentials required'}), 400
        
        # Extract IP from server_id
        server_ip = server_id.replace('server-', '').replace('-', '.')
        
        # Get cleanup summary
        result = cleanup_service.get_cleanup_summary(
            server_ip=server_ip,
            username=username,
            password=password,
            ssh_port=ssh_port
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error getting cleanup summary: {e}")
        return jsonify({'success': False, 'error': 'Failed to get cleanup summary'}), 500


@app.route('/api/admin/servers/<server_id>/cleanup/execute', methods=['POST'])
def execute_cleanup(server_id):
    """Execute cleanup endpoint."""
    try:
        session, error_response, status_code = require_admin_auth()
        if error_response:
            return error_response, status_code
        
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        ssh_port = data.get('ssh_port', 22)
        cleanup_options = data.get('cleanup_options', {})
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'SSH credentials required'}), 400
        
        if not cleanup_options:
            return jsonify({'success': False, 'error': 'Cleanup options required'}), 400
        
        # Extract IP from server_id
        server_ip = server_id.replace('server-', '').replace('-', '.')
        
        # Execute cleanup
        result = cleanup_service.execute_cleanup(
            server_ip=server_ip,
            username=username,
            password=password,
            cleanup_options=cleanup_options,
            admin_username=session.get('username'),
            ssh_port=ssh_port,
            ip_address=get_client_ip(request)
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error executing cleanup: {e}")
        return jsonify({'success': False, 'error': 'Failed to execute cleanup'}), 500


# Agent management endpoints (for backward compatibility)
@app.route('/api/register_agent', methods=['POST'])
def register_agent():
    """Register agent endpoint."""
    data = request.get_json()
    agent_ip = data.get('agent_ip')
    
    if not agent_ip:
        return jsonify({'success': False, 'error': 'Agent IP required'}), 400
    
    try:
        from utils.helpers import read_agents_file, write_agents_file
        agents = read_agents_file()
        
        if agent_ip not in agents:
            agents.append(agent_ip)
            write_agents_file(agents)
            
            # Log agent registration
            db.log_audit_event(
                'System',
                'register_agent',
                {'message': f'New agent registered: {agent_ip}', 'agent_ip': agent_ip},
                get_client_ip(request)
            )
        
        return jsonify({'success': True, 'message': f'Agent {agent_ip} registered'})
    except Exception as e:
        logger.error(f"Error registering agent: {e}")
        return jsonify({'success': False, 'error': 'Failed to register agent'}), 500


@app.route('/api/unregister_agent', methods=['POST'])
def unregister_agent():
    """Unregister agent endpoint."""
    data = request.get_json()
    agent_ip = data.get('agent_ip')
    
    if not agent_ip:
        return jsonify({'success': False, 'error': 'Agent IP required'}), 400
    
    try:
        from utils.helpers import read_agents_file, write_agents_file
        agents = read_agents_file()
        
        if agent_ip in agents:
            agents.remove(agent_ip)
            write_agents_file(agents)
            
            # Log agent unregistration
            db.log_audit_event(
                'System',
                'unregister_agent',
                {'message': f'Agent unregistered: {agent_ip}', 'agent_ip': agent_ip},
                get_client_ip(request)
            )
        
        return jsonify({'success': True, 'message': f'Agent {agent_ip} unregistered'})
    except Exception as e:
        logger.error(f"Error unregistering agent: {e}")
        return jsonify({'success': False, 'error': 'Failed to unregister agent'}), 500


@app.route('/api/user/services', methods=['GET'])
def get_user_services():
    # Check session authentication
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    username = session.get('username')
    
    try:
        # Add login log
        add_app_log('INFO', f'User {username} accessed services dashboard', username, get_client_ip(request))
        
        # Get user's nginx route information
        route_info = nginx_service.get_user_routes_info(username)
        logger.debug(f"Route info: {route_info}")

        # Get user data for container and server information
        user_data = db.get_user_by_username(username)
        if not user_data:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Parse user metadata for container and server info
        metadata = user_service._parse_user_metadata(user_data.get('metadata'))
        logger.debug(f"Metadata: {metadata}")
        
        # Get real-time container status from Docker agent
        container_name = metadata.get('container', {}).get('name')
        real_container_status = 'stopped'
        container_id = None
        
        if container_name:
            server_assignment = metadata.get('server_assignment')
            if server_assignment and server_assignment != 'NA':
                try:
                    server_ip = user_service._get_server_ip_from_assignment(server_assignment)
                    if server_ip:
                        # Query agent for real-time container status
                        container_status_response = agent_service.query_agent_container_status(server_ip, container_name)
                        if container_status_response and container_status_response.get('success'):
                            real_container_status = container_status_response.get('status', 'stopped')
                            container_id = container_status_response.get('id')
                except Exception as e:
                    logger.debug(f"Could not fetch real-time container status for {username}: {e}")
        
        # Build service URLs based on nginx routes and container status
        services = {
            'vscode': {
                'available': False,
                'url': None,
                'status': 'stopped'
            },
            'jupyter': {
                'available': False,
                'url': None,
                'status': 'stopped'
            },
            'intellij': {
                'available': False,
                'url': None,
                'status': 'stopped'
            },
            'terminal': {
                'available': False,
                'url': None,
                'status': 'stopped'
            }
        }
        
        # If user has nginx routes configured and container is running
        if route_info.get('has_routes') and real_container_status == 'running':
            if route_info.get('vscode_url'):
                services['vscode'] = {
                    'available': True,
                    'url': f"http://localhost{route_info['vscode_url']}",
                    'status': 'running'
                }
            
            if route_info.get('jupyter_url'):
                services['jupyter'] = {
                    'available': True,
                    'url': f"http://localhost{route_info['jupyter_url']}",
                    'status': 'running'
                }
            
            # For now, IntelliJ and Terminal use same base URL pattern
            # These can be extended when those services are implemented
            services['intellij'] = {
                'available': True,
                'url': f"http://localhost/user/{username}/intellij/",
                'status': 'running'
            }
            
            services['terminal'] = {
                'available': False,
                'url': f"http://localhost/user/{username}/terminal/",
                'status': 'running' 
            }
        
        # Get server information for system stats
        server_assignment = metadata.get('server_assignment')
        server_stats = None
        
        if server_assignment and server_assignment != 'NA':
            try:
                # Try to get server stats from agent
                server_ip = user_service._get_server_ip_from_assignment(server_assignment)
                if server_ip:
                    server_stats = agent_service.query_agent_resources(server_ip)
            except Exception as e:
                logger.debug(f"Could not fetch server stats for user {username}: {e}")
        
        return jsonify({
            'success': True,
            'data': {
                'username': username,
                'services': services,
                'container': {
                    'name': container_name or 'NA',
                    'id': container_id,
                    'status': real_container_status,
                    'server': server_assignment or 'NA'
                },
                'server_stats': server_stats,
                'nginx_available': route_info.get('nginx_available', False)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user services for {username}: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch user services'}), 500


@app.route('/api/user/container/start', methods=['POST'])
def start_user_container():
    """Start user's container"""
    # Check session authentication
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    username = session.get('username')
    
    try:
        # Get user data for container and server information
        user_data = db.get_user_by_username(username)
        if not user_data:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Parse user metadata for container and server info
        metadata = user_service._parse_user_metadata(user_data.get('metadata'))
        container_name = metadata.get('container', {}).get('name')
        server_assignment = metadata.get('server_assignment')
        
        if not container_name:
            return jsonify({'success': False, 'error': 'No container assigned to user'}), 400
        
        if not server_assignment or server_assignment == 'NA':
            return jsonify({'success': False, 'error': 'No server assigned to user'}), 400
        
        # Get server IP
        server_ip = user_service._get_server_ip_from_assignment(server_assignment)
        if not server_ip:
            return jsonify({'success': False, 'error': 'Could not determine server IP'}), 400
        
        # Start container via agent
        result = agent_service.manage_user_container(server_ip, container_name, 'start')
        
        if result and result.get('success'):
            # Log the action
            db.log_audit_event(
                username=username,
                action_type='container_start',
                action_details={
                    'message': f'User {username} started container {container_name}',
                    'container_name': container_name,
                    'server_ip': server_ip
                },
                ip_address=get_client_ip(request)
            )
            
            # Add to app logs
            add_app_log('INFO', f'Container {container_name} started successfully', username, get_client_ip(request))
            
            return jsonify({'success': True, 'message': 'Container started successfully'})
        else:
            error_msg = result.get('error', 'Failed to start container') if result else 'Agent not available'
            add_app_log('ERROR', f'Failed to start container {container_name}: {error_msg}', username, get_client_ip(request))
            return jsonify({'success': False, 'error': error_msg}), 500
            
    except Exception as e:
        logger.error(f"Error starting container for user {username}: {e}")
        return jsonify({'success': False, 'error': 'Failed to start container'}), 500


@app.route('/api/user/container/restart', methods=['POST'])
def restart_user_container():
    """Restart user's container"""
    # Check session authentication
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    username = session.get('username')
    
    try:
        # Get user data for container and server information
        user_data = db.get_user_by_username(username)
        if not user_data:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Parse user metadata for container and server info
        metadata = user_service._parse_user_metadata(user_data.get('metadata'))
        container_name = metadata.get('container', {}).get('name')
        server_assignment = metadata.get('server_assignment')
        
        if not container_name:
            return jsonify({'success': False, 'error': 'No container assigned to user'}), 400
        
        if not server_assignment or server_assignment == 'NA':
            return jsonify({'success': False, 'error': 'No server assigned to user'}), 400
        
        # Get server IP
        server_ip = user_service._get_server_ip_from_assignment(server_assignment)
        if not server_ip:
            return jsonify({'success': False, 'error': 'Could not determine server IP'}), 400
        
        # Restart container via agent
        result = agent_service.manage_user_container(server_ip, container_name, 'restart')
        
        if result and result.get('success'):
            # Log the action
            db.log_audit_event(
                username=username,
                action_type='container_restart',
                action_details={
                    'message': f'User {username} restarted container {container_name}',
                    'container_name': container_name,
                    'server_ip': server_ip
                },
                ip_address=get_client_ip(request)
            )
            
            # Add to app logs
            add_app_log('INFO', f'Container {container_name} restarted successfully', username, get_client_ip(request))
            
            return jsonify({'success': True, 'message': 'Container restarted successfully'})
        else:
            error_msg = result.get('error', 'Failed to restart container') if result else 'Agent not available'
            add_app_log('ERROR', f'Failed to restart container {container_name}: {error_msg}', username, get_client_ip(request))
            return jsonify({'success': False, 'error': error_msg}), 500
            
    except Exception as e:
        logger.error(f"Error restarting container for user {username}: {e}")
        return jsonify({'success': False, 'error': 'Failed to restart container'}), 500


@app.route('/api/user/logs', methods=['GET'])
def get_user_logs():
    """Get user-specific logs"""
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    username = session.get('username')
    limit = request.args.get('limit', 100, type=int)
    level = request.args.get('level', None)  # Filter by log level
    
    try:
        # Filter logs for this user or system-wide logs
        user_logs = []
        for log_entry in reversed(list(app_logs)):
            # Include logs for this user or system logs without specific user
            if log_entry.get('username') == username or log_entry.get('username') is None:
                if level is None or log_entry.get('level') == level:
                    user_logs.append(log_entry)
                    if len(user_logs) >= limit:
                        break
        
        return jsonify({
            'success': True,
            'logs': user_logs,
            'total': len(user_logs)
        })
        
    except Exception as e:
        logger.error(f"Error retrieving logs for user {username}: {e}")
        return jsonify({'success': False, 'error': 'Failed to retrieve logs'}), 500


@app.route('/api/user/logs/download', methods=['GET'])
def download_user_logs():
    """Download user logs as a file"""
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    username = session.get('username')
    
    try:
        # Generate log file content
        log_content = []
        for log_entry in app_logs:
            if log_entry.get('username') == username or log_entry.get('username') is None:
                timestamp = log_entry.get('timestamp', '')
                level = log_entry.get('level', 'INFO')
                message = log_entry.get('message', '')
                log_line = f"[{timestamp}] {level}: {message}"
                log_content.append(log_line)
        
        # Create response with file content
        from flask import Response
        
        log_text = '\n'.join(log_content)
        filename = f"logs_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        add_app_log('INFO', f'User {username} downloaded logs', username, get_client_ip(request))
        
        return Response(
            log_text,
            mimetype='text/plain',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        logger.error(f"Error downloading logs for user {username}: {e}")
        return jsonify({'success': False, 'error': 'Failed to download logs'}), 500


# Health check endpoint for Docker
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Docker container monitoring."""
    try:
        # Check database connection
        db_status = "healthy"
        try:
            # Simple database connectivity test
            db.get_user_by_id(1)  # This will test DB connection
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        # Check if services are initialized
        services_status = {
            "auth_service": "healthy" if auth_service else "unhealthy",
            "user_service": "healthy" if user_service else "unhealthy", 
            "server_service": "healthy" if server_service else "unhealthy",
            "agent_service": "healthy" if agent_service else "unhealthy"
        }
        
        # Overall health status
        overall_status = "healthy" if db_status == "healthy" and all(status == "healthy" for status in services_status.values()) else "unhealthy"
        
        response = {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "database": db_status,
            "services": services_status,
            "uptime": "running"
        }
        
        status_code = 200 if overall_status == "healthy" else 503
        return jsonify(response), status_code
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 503


if __name__ == '__main__':
    config_path = os.path.join('config.toml')
    if os.path.exists(config_path):
        config = toml.load(config_path)
        port = config.get('server', {}).get('port', 8500)
    else:
        port = 8500
    
    logger.info(f"Starting Flask application on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
