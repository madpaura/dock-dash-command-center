from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import hashlib
import secrets
import paramiko
import threading
import uuid
import queue
from user_database import UserDatabase
from dotenv import load_dotenv
import os
from loguru import logger
import json
import toml
import ipaddress

# Configure logger
logger.add("manager_backend.log", rotation="500 MB", retention="10 days", level="INFO")

# Load environment variables
load_dotenv(".env", override=True)

app = Flask(__name__)
CORS(app)

# Initialize database connection
db = UserDatabase()
db.initialize_database()

# Agent configuration
AGENTS_FILE = "agents.txt"

def generate_session_token():
    return secrets.token_urlsafe(32)

def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def read_agents():
    if not os.path.exists(AGENTS_FILE):
        return []
    with open(AGENTS_FILE, 'r') as file:
        agents = file.read().splitlines()
        return agents

def write_agents(agents):
    with open(AGENTS_FILE, 'w') as file:
        for agent in agents:
            file.write(f"{agent}\n")

def get_admin_username_from_token():
    """Get admin username from authorization token, fallback to 'admin'"""
    admin_username = 'admin'  # Default fallback
    try:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            session = db.verify_session(token)
            if session and session.get('username'):
                admin_username = session['username']
    except:
        pass  # Use default fallback
    return admin_username

# Authentication endpoints
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user = db.verify_login(email, password)

    if user and user["is_approved"]:
        session_token = generate_session_token()
        expires_at = datetime.now() + timedelta(hours=24)
        
        if db.create_session(user["id"], session_token, expires_at):
            # Log successful login
            db.log_audit_event(
                user["username"],
                'login',
                {'message': f'User {user["username"]} logged in successfully', 'email': email},
                request.remote_addr
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'user_id': user["id"],
                    'name': user["username"],
                    'role': 'admin' if user["is_admin"] else 'user',
                    'email': user["email"],
                    'token': session_token
                }
            })
    
    # Log failed login attempt
    db.log_audit_event(
        email if email else 'Unknown',
        'login_failed',
        {'message': f'Failed login attempt for email: {email}', 'reason': 'Invalid credentials or account not approved'},
        request.remote_addr
    )
    
    return jsonify({'success': False, 'error': 'Invalid credentials or account not approved'}), 401

def invalidate_session_by_token(token):
    try:
        session = db.verify_session(token)
        db.remove_session(token)
        return True
    except Exception as e:
        logger.error(f"Error invalidating session: {e}")
        return False

@app.route('/api/logout', methods=['POST'])
def logout():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Invalid or missing token'}), 401
    
    token = auth_header.split(' ')[1]
    
    # Get user info before invalidating session for logging
    try:
        session = db.verify_session(token)
        username = session.get('username', 'Unknown') if session else 'Unknown'
    except:
        username = 'Unknown'
    
    if invalidate_session_by_token(token):
        # Log successful logout
        db.log_audit_event(
            username,
            'logout',
            {'message': f'User {username} logged out successfully'},
            request.remote_addr
        )
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to logout'}), 400

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'success': False, 'error': 'Please fill in all fields'}), 400
    
    user_data = {
        "username": username,
        "password": hashlib.sha256(password.encode()).hexdigest(),
        "email": email,
        "metadata": {"registration_source": "web"},
    }
    
    if db.create_user(user_data):
        # Log successful registration
        db.log_audit_event(
            username,
            'register',
            {'message': f'New user {username} registered successfully', 'email': email},
            request.remote_addr
        )
        return jsonify({'success': True})
    
    # Log failed registration
    db.log_audit_event(
        username if username else 'Unknown',
        'register_failed',
        {'message': f'Failed registration attempt for username: {username}, email: {email}', 'reason': 'Username or email already exists'},
        request.remote_addr
    )
    
    return jsonify({'success': False, 'error': 'Username or email already exists'}), 400

# User management endpoints
@app.route('/api/users', methods=['GET'])
def get_users():
    logger.info("Fetching all users")
    users = db.get_all_users()
    if users:
        logger.success(f"Found {len(users)} users")
        return jsonify({'success': True, 'users': users})
    logger.warning("No users found in database")
    return jsonify({'success': False, 'error': 'No users found'}), 404

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_info(user_id):
    logger.info("Fetching all users")
    user = db.get_user_by_id(user_id)
    if user:
        logger.success(f"Found {len(user)} user")
        return jsonify({'success': True, 'redirect_url': user['redirect_url']})

    logger.warning("No users found in database")
    return jsonify({'success': False, 'error': 'No users found'}), 404

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    admin_username = get_admin_username_from_token()
    
    user = db.get_user_by_id(user_id)
    if user and db.delete_user_by_username(user['username']):
        # Log successful user deletion
        db.log_audit_event(
            admin_username,
            'delete_user',
            {'message': f'User {user["username"]} (ID: {user_id}) deleted by {admin_username}', 'deleted_user': user['username']},
            request.remote_addr
        )
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'User not found'}), 404

@app.route('/api/users/pending', methods=['GET'])
def get_pending_users():
    users = db.get_pending_users()
    if users:
        return jsonify({'success': True, 'users': users})
    return jsonify({'success': False, 'error': 'No pending users'}), 200

@app.route('/api/users/<int:user_id>/approve', methods=['POST'])
def approve_user(user_id):
    data = request.get_json()
    server_id = data.get('server_id')
    
    # Get user info before approval
    user = db.get_user_by_id(user_id)
    
    if db.update_user(user_id, {
        'is_approved': True,
        'redirect_url': f"http://{server_id}:{os.getenv('AGENT_PORT', 8510)}"
    }):
        # Log successful user approval
        if user:
            admin_username = get_admin_username_from_token()
            db.log_audit_event(
                admin_username,
                'approve_user',
                {
                    'message': f'User {user["username"]} (ID: {user_id}) approved by {admin_username}',
                    'approved_user': user['username'],
                    'server_id': server_id
                },
                request.remote_addr
            )
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'User not found'}), 404

# Admin user management endpoints
@app.route('/api/admin/users', methods=['GET'])
def get_admin_users():
    """Get all users with detailed container and server information for admin dashboard"""
    try:
        # Get basic user data
        users = db.get_all_users()
        
        # Transform real user data to match frontend expectations
        admin_users = []
        for user in users:
            # Generate container info based on user data
            container_name = f"container-{user['username'][:2].lower()}-{user['id']:03d}"
            container_status = 'running' if user.get('is_approved') else 'stopped'
            
            # Assign resources based on role
            if user.get('is_admin'):
                resources = {'cpu': '8 cores', 'ram': '16GB', 'gpu': '2 cores, 24GB'}
                role = 'Admin'
            else:
                resources = {'cpu': '4 cores', 'ram': '8GB', 'gpu': '1 core, 12GB'}
                role = 'Developer' if user.get('is_approved') else 'Pending'
            
            # Assign server based on user ID (simple distribution)
            server_num = (user['id'] % 4) + 1
            server_locations = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-south-1']
            
            admin_user = {
                'id': str(user['id']),
                'name': user['username'],
                'email': user['email'],
                'role': role,
                'container': container_name,
                'containerStatus': container_status,
                'resources': resources,
                'server': f'Server {server_num}',
                'serverLocation': server_locations[(server_num - 1) % len(server_locations)],
                'status': 'Running' if user.get('is_approved') else 'Stopped'
            }
            admin_users.append(admin_user)
        
        return jsonify({'success': True, 'users': admin_users})
    except Exception as e:
        logger.error(f"Error fetching admin users: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch users'}), 500

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    """Get statistics for admin dashboard"""
    try:
        users = db.get_all_users()
        total_users = len(users) if users else 4  # Use placeholder count if no users
        active_containers = sum(1 for user in (users or []) if user.get('is_approved', False))
        if not users:
            active_containers = 3  # Placeholder active containers
        
        stats = {
            'totalUsers': total_users,
            'totalUsersChange': '+2 from last month',
            'activeContainers': active_containers,
            'containerUtilization': f'{int((active_containers / max(total_users, 1)) * 100)}% utilization',
            'availableServers': 4,
            'serverStatus': 'All regions online'
        }
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"Error fetching admin stats: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch statistics'}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
def update_admin_user(user_id):
    """Update user information from admin panel"""
    try:
        data = request.get_json()
        
        # Extract update fields
        update_fields = {}
        if 'name' in data:
            update_fields['username'] = data['name']
        if 'email' in data:
            update_fields['email'] = data['email']
        if 'role' in data:
            update_fields['is_admin'] = data['role'].lower() == 'admin'

        # Get user info before update
        user = db.get_user_by_id(user_id)
        
        if db.update_user(user_id, update_fields):
            # Log successful user update
            if user:
                db.log_audit_event(
                    'Admin',  # Could get actual admin user from token
                    'update_user',
                    {
                        'message': f'User {user["username"]} (ID: {user_id}) updated by admin',
                        'updated_user': user['username'],
                        'updated_fields': list(update_fields.keys())
                    },
                    request.remote_addr
                )
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return jsonify({'success': False, 'error': 'Failed to update user'}), 500

@app.route('/api/admin/users', methods=['POST'])
def create_admin_user():
    """Create a new user from admin panel"""
    try:
        data = request.get_json()
        
        # Extract user data
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', 'defaultpass123')  # Default password
        role = data.get('role', 'User')
        status = data.get('status', 'Stopped')
        server_assignment = data.get('server', 'Server 1')
        resources = data.get('resources', {
            'cpu': '4 cores',
            'ram': '8GB',
            'gpu': '1 core, 12GB'
        })
        
        # Validate required fields
        if not name or not email:
            return jsonify({'success': False, 'error': 'Name and email are required'}), 400
        
        # Check if user already exists
        existing_user = db.get_user_by_username(name)
        if existing_user:
            return jsonify({'success': False, 'error': 'User with this name already exists'}), 400
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Prepare user data
        user_data = {
            'username': name,
            'password': password_hash,
            'email': email,
            'is_admin': role.lower() == 'admin',
            'is_approved': status.lower() == 'running',
            'metadata': json.dumps({
                'server_assignment': server_assignment,
                'resources': resources,
                'created_by_admin': True,
                'created_at': datetime.now().isoformat()
            })
        }
        
        # Set redirect URL if approved
        if user_data['is_approved']:
            server_map = {
                'Server 1': 'server-1',
                'Server 2': 'server-2',
                'Server 3': 'server-3',
                'Server 4': 'server-4'
            }
            server_id = server_map.get(server_assignment, 'server-1')
            user_data['redirect_url'] = f"http://{server_id}:{os.getenv('AGENT_PORT', 8510)}"
        
        # Create user
        if db.create_user(user_data):
            logger.info(f"Admin created new user: {name} ({email}) with role {role}")
            
            # Log successful user creation
            db.log_audit_event(
                'Admin',  # Could get actual admin user from token
                'create_user',
                {
                    'message': f'Admin created new user {name} ({email}) with role {role}',
                    'created_user': name,
                    'email': email,
                    'role': role,
                    'server_assignment': server_assignment
                },
                request.remote_addr
            )
            
            return jsonify({
                'success': True, 
                'message': f'User {name} created successfully',
                'defaultPassword': password
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create user'}), 500
            
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'success': False, 'error': 'Failed to create user'}), 500

@app.route('/api/admin/users/<int:user_id>/approve', methods=['POST'])
def approve_admin_user(user_id):
    """Approve user with server and resource assignment"""
    try:
        data = request.get_json()
        server_assignment = data.get('server', 'Server 1')
        resources = data.get('resources', {
            'cpu': '4 cores',
            'ram': '8GB', 
            'gpu': '1 core, 12GB'
        })
        
        # Update user approval status and metadata
        update_fields = {
            'is_approved': True,
            'metadata': json.dumps({
                'server_assignment': server_assignment,
                'resources': resources,
                'approved_at': datetime.now().isoformat()
            })
        }
        
        # Set redirect URL based on server assignment
        server_map = {
            'Server 1': 'server-1',
            'Server 2': 'server-2', 
            'Server 3': 'server-3',
            'Server 4': 'server-4'
        }
        server_id = server_map.get(server_assignment, 'server-1')
        update_fields['redirect_url'] = f"http://{server_id}:{os.getenv('AGENT_PORT', 8510)}"
        
        # Get user info before approval
        user = db.get_user_by_id(user_id)
        
        if db.update_user(user_id, update_fields):
            logger.info(f"User {user_id} approved with server {server_assignment} and resources {resources}")
            
            # Log successful user approval
            if user:
                db.log_audit_event(
                    'Admin',  # Could get actual admin user from token
                    'approve_user',
                    {
                        'message': f'Admin approved user {user["username"]} (ID: {user_id})',
                        'approved_user': user['username'],
                        'server_assignment': server_assignment,
                        'resources': resources
                    },
                    request.remote_addr
                )
            
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        logger.error(f"Error approving user {user_id}: {e}")
        return jsonify({'success': False, 'error': 'Failed to approve user'}), 500

# Audit logs endpoints
@app.route('/api/audit-logs', methods=['GET'])
def get_audit_logs():
    """Get all audit logs - filtering and sorting handled on frontend"""
    try:
        logger.info("Fetching all audit logs")
        
        logs = db.get_audit_logs(limit=1000) 
        transformed_logs = []
        for log in logs:

            action_details = {}
            if log.get('action_details'):
                try:
                    action_details = json.loads(log['action_details']) if isinstance(log['action_details'], str) else log['action_details']
                except:
                    action_details = {}
            
            level = 'INFO'
            if log.get('action_type') in ['login_failed', 'error', 'delete_user']:
                level = 'ERROR'
            elif log.get('action_type') in ['login_attempt', 'update_user', 'warning']:
                level = 'WARN'
            elif log.get('action_type') in ['debug', 'query']:
                level = 'DEBUG'
            
            # Determine source based on action type
            source_map = {
                'login': 'auth.service',
                'login_failed': 'auth.service',
                'logout': 'auth.service',
                'create_user': 'user.service',
                'update_user': 'user.service',
                'delete_user': 'user.service',
                'approve_user': 'user.service',
                'system_start': 'system',
                'api_call': 'api.gateway'
            }
            source = source_map.get(log.get('action_type', ''), 'system')
            
            transformed_log = {
                'id': str(log['id']),
                'level': level,
                'timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(log['timestamp'], 'strftime') else str(log['timestamp']),
                'user': log.get('username', 'System'),
                'source': source,
                'message': action_details.get('message', f"{log.get('action_type', 'Unknown action')}"),
                'ip_address': log.get('ip_address', 'N/A'),
                'action_type': log.get('action_type', 'unknown')
            }
            transformed_logs.append(transformed_log)
        
        return jsonify({
            'success': True,
            'logs': transformed_logs
        })
        
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch logs'}), 500


@app.route('/api/audit-logs', methods=['DELETE'])
def clear_audit_logs():
    """Clear all audit logs - admin only"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'No authorization token provided'}), 401
        
        token = auth_header.split(' ')[1]
        user_info = db.validate_session(token)
        
        if not user_info or user_info.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        logger.info(f"Admin {user_info.get('username')} clearing all audit logs")
        
        # Clear all audit logs
        result = db.clear_audit_logs()
        
        if result:
            # Log this action
            db.log_audit_event(
                user_info.get('username'),
                'clear_logs',
                {'message': 'All audit logs cleared by admin'},
                request.remote_addr
            )
            
            return jsonify({
                'success': True,
                'message': 'All audit logs cleared successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to clear logs'}), 500
            
    except Exception as e:
        logger.error(f"Error clearing audit logs: {e}")
        return jsonify({'success': False, 'error': 'Failed to clear logs'}), 500


from agent_manager import query_available_agents
import time

# Server resources endpoint
@app.route('/api/server-resources', methods=['GET'])
def get_server_resources():
    agents_list = read_agents()
    query_port = int(os.getenv('AGENT_PORT', 8510)) + 1
    servers = query_available_agents(agents_list, query_port)
    
    if servers:
        return jsonify({'success': True, 'servers': servers})
    return jsonify({'success': False, 'error': 'No servers available'}), 404

# Server management endpoints
@app.route('/api/admin/servers', methods=['GET'])
def get_admin_servers():
    """Get all servers with detailed information for admin dashboard"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    session = db.verify_session(token)
    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 401
    
    try:
        # Get registered agents
        agents_list = read_agents()
        query_port = int(os.getenv('AGENT_PORT', 8510)) + 1
        
        servers_data = []
        
        for agent_ip in agents_list:
            try:
                # Query agent for resources
                resources = query_available_agents([agent_ip], query_port)
                
                if resources and len(resources) > 0:
                    resource_data = resources[0]
                    status = 'online'
                    
                    # Calculate usage percentages
                    memory_total = resource_data.get('total_memory', 1)
                    memory_used = resource_data.get('host_memory_used', 0)
                    memory_usage = (memory_used / memory_total * 100) if memory_total > 0 else 0
                    
                    disk_total = resource_data.get('total_disk', 1)
                    disk_used = resource_data.get('used_disk', 0)
                    disk_usage = (disk_used / disk_total * 100) if disk_total > 0 else 0
                    
                    # Create server info dict with all resource data
                    server_info = {
                        'id': f'server-{agent_ip.replace(".", "-")}',
                        'ip': agent_ip,
                        'status': status,
                        'cpu': round(resource_data.get('host_cpu_used', 0), 1),
                        'memory': round(memory_usage, 1),
                        'disk': round(disk_usage, 1),
                        'uptime': resource_data.get('uptime', '-'),
                        'type': 'compute',  # Could be enhanced based on actual server role
                        'containers': resource_data.get('docker_instances', 0),
                        'cpu_cores': resource_data.get('cpu_count', 0),
                        'total_memory': memory_total,
                        'allocated_cpu': resource_data.get('allocated_cpu', 0),
                        'allocated_memory': resource_data.get('allocated_memory', 0),
                        'remaining_cpu': resource_data.get('remaining_cpu', 0),
                        'remaining_memory': resource_data.get('remaining_memory', 0)
                    }
                else:
                    # Default values for offline server
                    server_info = {
                        'id': f'server-{agent_ip.replace(".", "-")}',
                        'ip': agent_ip,
                        'status': 'offline',
                        'cpu': 0,
                        'memory': 0,
                        'disk': 0,
                        'uptime': '-',
                        'type': 'unknown',
                        'containers': 0,
                        'cpu_cores': 0,
                        'total_memory': 0,
                        'allocated_cpu': 0,
                        'allocated_memory': 0,
                        'remaining_cpu': 0,
                        'remaining_memory': 0
                    }
                
                servers_data.append(server_info)
                
            except Exception as e:
                logger.error(f"Error querying server {agent_ip}: {e}")
                # Add offline server with the same structure as above
                servers_data.append({
                    'id': f'server-{agent_ip.replace(".", "-")}',
                    'ip': agent_ip,
                    'status': 'error',
                    'cpu': 0,
                    'memory': 0,
                    'disk': 0,
                    'uptime': '-',
                    'type': 'unknown',
                    'containers': 0,
                    'cpu_cores': 0,
                    'total_memory': 0,
                    'allocated_cpu': 0,
                    'allocated_memory': 0,
                    'remaining_cpu': 0,
                    'remaining_memory': 0
                })
        
        return jsonify({
            'success': True,
            'servers': servers_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching server data: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch server data'}), 500

@app.route('/api/admin/servers/stats', methods=['GET'])
def get_server_stats():
    """Get server statistics for admin dashboard"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    session = db.verify_session(token)
    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 401
    
    try:
        # Get registered agents
        agents_list = read_agents()
        query_port = int(os.getenv('AGENT_PORT', 8510)) + 1
        
        total_servers = len(agents_list)
        online_servers = 0
        offline_servers = 0
        maintenance_servers = 0
        
        # Query each server to determine status
        for agent_ip in agents_list:
            try:
                resources = query_available_agents([agent_ip], query_port)
                if resources and len(resources) > 0:
                    online_servers += 1
                else:
                    offline_servers += 1
            except Exception:
                offline_servers += 1
        
        # For now, maintenance servers are manually configured (could be enhanced)
        # maintenance_servers would be tracked separately
        
        stats = {
            'totalServers': total_servers,
            'totalServersChange': '+0',  # Would need historical data
            'onlineServers': online_servers,
            'onlineServersChange': '+0',  # Would need historical data
            'offlineServers': offline_servers,
            'offlineServersChange': '+0',  # Would need historical data
            'maintenanceServers': maintenance_servers,
            'maintenanceServersChange': '+0'  # Would need historical data
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error fetching server stats: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch server stats'}), 500

@app.route('/api/admin/servers/<server_id>/action', methods=['POST'])
def server_action(server_id):
    """Perform actions on servers (start, stop, restart, etc.)"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    session = db.verify_session(token)
    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 401
    
    data = request.get_json()
    action = data.get('action')
    
    if not action:
        return jsonify({'success': False, 'error': 'Action required'}), 400
    
    try:
        # Extract IP from server_id
        server_ip = server_id.replace('server-', '').replace('-', '.')
        
        # Log the action
        admin_username = get_admin_username_from_token()
        db.log_audit_event(
            username=admin_username,
            action_type='server_action',
            action_details={
                'message': f'Performed {action} action on server {server_ip}',
                'server_id': server_id,
                'server_ip': server_ip,
                'action': action
            },
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'message': f'Action {action} initiated for server {server_ip}'
        })
        
    except Exception as e:
        logger.error(f"Error performing server action: {e}")
        return jsonify({'success': False, 'error': 'Failed to perform server action'}), 500

# SSH session management
ssh_sessions = {}
ssh_session_outputs = {}

class SSHSession:
    def __init__(self, session_id, host, port, username, password=None, key_path=None):
        self.session_id = session_id
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_path = key_path
        self.client = None
        self.shell = None
        self.output_queue = queue.Queue()
        self.connected = False
        
    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.key_path and os.path.exists(self.key_path):
                # Use SSH key authentication
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_path,
                    timeout=10
                )
            elif self.password:
                # Use password authentication
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=10
                )
            else:
                raise Exception("No authentication method provided")
            
            # Create interactive shell
            self.shell = self.client.invoke_shell()
            self.shell.settimeout(0.1)
            self.connected = True
            
            # Start output reader thread
            threading.Thread(target=self._read_output, daemon=True).start()
            
            return True
        except Exception as e:
            logger.error(f"SSH connection failed: {e}")
            return False
    
    def _read_output(self):
        while self.connected and self.shell:
            try:
                if self.shell.recv_ready():
                    output = self.shell.recv(4096).decode('utf-8', errors='ignore')
                    self.output_queue.put(output)
            except Exception as e:
                if self.connected:
                    logger.error(f"Error reading SSH output: {e}")
                break
    
    def execute_command(self, command):
        if not self.connected or not self.shell:
            return False
        try:
            self.shell.send(command + '\n')
            return True
        except Exception as e:
            logger.error(f"Error executing SSH command: {e}")
            return False
    
    def get_output(self):
        output_lines = []
        try:
            while not self.output_queue.empty():
                output_lines.append(self.output_queue.get_nowait())
        except queue.Empty:
            pass
        return ''.join(output_lines)
    
    def disconnect(self):
        self.connected = False
        if self.shell:
            self.shell.close()
        if self.client:
            self.client.close()

@app.route('/api/admin/servers/<server_id>/ssh/connect', methods=['POST'])
def ssh_connect(server_id):
    """Establish SSH connection to server"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    session = db.verify_session(token)
    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 401
    
    data = request.get_json()
    ssh_config = data.get('ssh_config', {})
    
    logger.info(f"SSH connection requested for server {ssh_config}")
    
    # Extract server IP from server_id
    server_ip = server_id.replace('server-', '').replace('-', '.')
    
    # Create SSH session
    session_id = str(uuid.uuid4())
    ssh_session = SSHSession(
        session_id=session_id,
        host=ssh_config.get('host', server_ip),
        port=int(ssh_config.get('port', 22)),
        username=ssh_config.get('username', 'root'),
        password=ssh_config.get('password'),
        key_path=ssh_config.get('key_path')
    )
    
    if ssh_session.connect():
        ssh_sessions[session_id] = ssh_session
        
        # Log SSH connection
        admin_username = get_admin_username_from_token()
        db.log_audit_event(
            username=admin_username,
            action_type='ssh_connect',
            action_details={
                'message': f'SSH connection established to server {server_ip}',
                'server_id': server_id,
                'server_ip': server_ip,
                'ssh_user': ssh_config.get('username', 'root')
            },
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': f'SSH connection established to {server_ip}'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to establish SSH connection'
        }), 500

@app.route('/api/admin/servers/ssh/<session_id>/execute', methods=['POST'])
def ssh_execute(session_id):
    """Execute command via SSH"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    session = db.verify_session(token)
    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 401
    
    if session_id not in ssh_sessions:
        return jsonify({'success': False, 'error': 'SSH session not found'}), 404
    
    data = request.get_json()
    command = data.get('command', '')
    
    ssh_session = ssh_sessions[session_id]
    
    if ssh_session.execute_command(command):
        # Log command execution
        admin_username = get_admin_username_from_token()
        db.log_audit_event(
            username=admin_username,
            action_type='ssh_command',
            action_details={
                'message': f'SSH command executed: {command}',
                'command': command,
                'session_id': session_id,
                'server_ip': ssh_session.host
            },
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'message': 'Command executed'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to execute command'
        }), 500

@app.route('/api/admin/servers/ssh/<session_id>/output', methods=['GET'])
def ssh_get_output(session_id):
    """Get SSH session output"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    session = db.verify_session(token)
    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 401
    
    if session_id not in ssh_sessions:
        return jsonify({'success': False, 'error': 'SSH session not found'}), 404
    
    ssh_session = ssh_sessions[session_id]
    output = ssh_session.get_output()
    
    return jsonify({
        'success': True,
        'output': output,
        'connected': ssh_session.connected
    })

@app.route('/api/admin/servers/ssh/<session_id>/disconnect', methods=['POST'])
def ssh_disconnect(session_id):
    """Disconnect SSH session"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    session = db.verify_session(token)
    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 401
    
    if session_id in ssh_sessions:
        ssh_session = ssh_sessions[session_id]
        ssh_session.disconnect()
        del ssh_sessions[session_id]
        
        # Log SSH disconnection
        admin_username = get_admin_username_from_token()
        db.log_audit_event(
            username=admin_username,
            action_type='ssh_disconnect',
            action_details={
                'message': f'SSH session disconnected',
                'session_id': session_id,
                'server_ip': ssh_session.host
            },
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'message': 'SSH session disconnected'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'SSH session not found'
        }), 404

# Session validation endpoints
@app.route("/api/validate_session", methods=["POST"])
def validate_session():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Invalid or missing token'}), 401
    
    token = auth_header.split(' ')[1]
    session = db.verify_session(token)
    if session:
        return jsonify({
            'success': True,
            'data': {
                'valid': True,
            }
        })
    else:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400


# Agent management endpoints
@app.route("/api/register_agent", methods=["POST"])
def register_agent():
    data = request.get_json()
    agent = data.get("agent")
    if not agent:
        return jsonify({"valid": False, "message": "ip address required"}), 400
    
    if not is_valid_ip(agent):
        return jsonify({"valid": False, "message": "agent id must be valid IP address"}), 400
    
    agents = read_agents()
    if agent in agents:
        return jsonify({"valid": False, "message": "Agent already registered"}), 400

    logger.info(f"Registering new agent: {agent}")
    agents.append(agent)
    write_agents(agents)
    logger.success(f"Agent {agent} registered successfully")
    
    # Log agent registration
    db.log_audit_event(
        'System',
        'register_agent',
        {'message': f'New agent {agent} registered successfully', 'agent_ip': agent},
        request.remote_addr
    )
    
    return jsonify({"valid": True, "message": "Agent registered successfully"}), 200

@app.route("/api/unregister_agent", methods=["POST"])
def unregister_agent():
    data = request.get_json()
    agent = data.get("agent")
    if not agent:
        return jsonify({"valid": False, "message": "ip address required"}), 400
    
    if not is_valid_ip(agent):
        return jsonify({"valid": False, "message": "agent id must be valid IP address"}), 400
    
    agents = read_agents()
    if agent not in agents:
        return jsonify({"valid": False, "message": "Agent not found"}), 400

    agents.remove(agent)
    write_agents(agents)
    logger.success(f"Agent {agent} unregistered successfully")
    
    # Log agent unregistration
    db.log_audit_event(
        'System',
        'unregister_agent',
        {'message': f'Agent {agent} unregistered successfully', 'agent_ip': agent},
        request.remote_addr
    )
    
    return jsonify({"valid": True, "message": "Agent unregistered successfully"}), 200

if __name__ == '__main__':
    config_path = os.path.join('.streamlit', 'config.toml')
    if os.path.exists(config_path):
        config = toml.load(config_path)
        port = config.get('server', {}).get('backend_port', 8500)
    else:
        port = 8500
    
    app.run(host='0.0.0.0', port=port)