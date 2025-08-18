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

# Configure logger
logger.add("manager_backend.log", rotation="500 MB", retention="10 days", level="INFO")

# Load environment variables
from dotenv import load_dotenv
load_dotenv(".env", override=True)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize database
db = UserDatabase()
db.initialize_database()

# Initialize services
agent_service = AgentService()
auth_service = AuthService(db)
user_service = UserService(db)
server_service = ServerService(db, agent_service)
ssh_service = SSHService(db)
docker_service = DockerService(db, agent_service)
audit_service = AuditService(db)
cleanup_service = CleanupService(db)

# Import nginx service
from services.nginx_service import NginxService
nginx_service = NginxService()


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
    agent_port = int(os.getenv('AGENT_PORT', '8510')) + 1
    
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
        agent_port = os.getenv('AGENT_PORT', '8510')
        
        result = user_service.create_admin_user(data, admin_username, agent_port, ip_address)
        
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
@app.route('/api/register-agent', methods=['POST'])
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


@app.route('/api/unregister-agent', methods=['POST'])
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
        # Get user's nginx route information
        route_info = nginx_service.get_user_routes_info(username)
        logger.error(f"Route info: {route_info}")

        # Get user data for container and server information
        user_data = db.get_user_by_username(username)
        if not user_data:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Parse user metadata for container and server info
        metadata = user_service._parse_user_metadata(user_data.get('metadata'))
        logger.error(f"Metadata: {metadata}")
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
        
        # If user has nginx routes configured and container exists
        if route_info.get('has_routes') and metadata.get('container'):
            container_info = metadata['container']
            container_status = container_info.get('status', 'unknown')
            
            # Only enable services if container is running
            if container_status == 'created':
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
                    'available': True,
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
                    server_stats = agent_service.query_agent_resources(server_ip, agent_port=8511)
            except Exception as e:
                logger.debug(f"Could not fetch server stats for user {username}: {e}")
        
        return jsonify({
            'success': True,
            'data': {
                'username': username,
                'services': services,
                'container': {
                    'name': metadata.get('container', {}).get('name', 'NA'),
                    'status': 'running' if metadata.get('container', {}).get('status', 'unknown') == 'created' else 'NA',
                    'server': server_assignment or 'NA'
                },
                'server_stats': server_stats,
                'nginx_available': route_info.get('nginx_available', False)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user services for {username}: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch user services'}), 500

if __name__ == '__main__':
    config_path = os.path.join('.streamlit', 'config.toml')
    if os.path.exists(config_path):
        config = toml.load(config_path)
        port = config.get('server', {}).get('backend_port', 8500)
    else:
        port = 8500
    
    logger.info(f"Starting Flask application on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
