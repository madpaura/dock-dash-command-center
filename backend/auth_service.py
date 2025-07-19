from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import hashlib
import secrets
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

# Authentication endpoints
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    print(email, password)
    user = db.verify_login(email, password)
    print(user)

    if user and user["is_approved"]:
        session_token = generate_session_token()
        expires_at = datetime.now() + timedelta(hours=24)
        
        if db.create_session(user["id"], session_token, expires_at):
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
    
    return jsonify({'success': False, 'error': 'Invalid credentials or account not approved'}), 401

def invalidate_session_by_token(token):
    try:
        session = db.verify_session(token)
        db.remove_session(token)
        return True
    except Exception as e:
        print(f"Error invalidating session: {e}")
        return False

@app.route('/api/logout', methods=['POST'])
def logout():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Invalid or missing token'}), 401
    
    token = auth_header.split(' ')[1]
    
    if invalidate_session_by_token(token):
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
        return jsonify({'success': True})
    
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
    user = db.get_user_by_id(user_id)
    if user and db.delete_user_by_username(user['username']):
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
    
    if db.update_user(user_id, {
        'is_approved': True,
        'redirect_url': f"http://{server_id}:{os.getenv('AGENT_PORT', 8510)}"
    }):
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
        if 'status' in data:
            update_fields['is_approved'] = data['status'].lower() == 'running'
        
        if db.update_user(user_id, update_fields):
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
        
        if db.update_user(user_id, update_fields):
            logger.info(f"User {user_id} approved with server {server_assignment} and resources {resources}")
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        logger.error(f"Error approving user {user_id}: {e}")
        return jsonify({'success': False, 'error': 'Failed to approve user'}), 500

# Audit logs endpoint
@app.route('/api/audit-logs', methods=['GET'])
def get_audit_logs():
    username = request.args.get('username')
    limit = request.args.get('limit', default=100, type=int)
    
    logger.info(f"Fetching audit logs for username: {username}, limit: {limit}")
    logs = db.get_audit_logs(username=username, limit=limit)
    if logs:
        logger.success(f"Found {len(logs)} audit logs")
        return jsonify({'success': True, 'logs': logs})
    logger.info("No audit logs found")
    return jsonify({'success': False, 'error': 'No logs found'}), 404

from agent_manager import query_available_agents

# Server resources endpoint
@app.route('/api/server-resources', methods=['GET'])
def get_server_resources():
    agents_list = read_agents()
    query_port = int(os.getenv('AGENT_PORT', 8510)) + 1
    servers = query_available_agents(agents_list, query_port)
    
    if servers:
        return jsonify({'success': True, 'servers': servers})
    return jsonify({'success': False, 'error': 'No servers available'}), 404

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
    return jsonify({"valid": True, "message": "Agent unregistered successfully"}), 200

if __name__ == '__main__':
    config_path = os.path.join('.streamlit', 'config.toml')
    if os.path.exists(config_path):
        config = toml.load(config_path)
        port = config.get('server', {}).get('backend_port', 8500)
    else:
        port = 8500
    
    app.run(host='0.0.0.0', port=port)