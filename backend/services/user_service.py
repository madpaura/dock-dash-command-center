import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

from database import UserDatabase
from utils.helpers import hash_password, get_client_ip
from utils.validators import is_valid_email, is_valid_username


class UserService:
    
    def __init__(self, db: UserDatabase):
        self.db = db
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        try:
            users = self.db.get_all_users()
            return users if users else []
        except Exception as e:
            logger.error(f"Error fetching all users: {e}")
            return []
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            return self.db.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None
    
    def delete_user(self, user_id: int, admin_username: str, ip_address: Optional[str] = None) -> bool:
        try:
            user = self.db.get_user_by_id(user_id)
            if user and self.db.delete_user_by_username(user['username']):
                self.db.log_audit_event(
                    admin_username,
                    'delete_user',
                    {'message': f'User {user["username"]} (ID: {user_id}) deleted by {admin_username}', 'deleted_user': user['username']},
                    ip_address
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    def get_pending_users(self) -> List[Dict[str, Any]]:
        try:
            users = self.db.get_pending_users()
            return users if users else []
        except Exception as e:
            logger.error(f"Error fetching pending users: {e}")
            return []
    
    def approve_user(self, user_id: int, server_assignment: str, admin_username: str, 
                     agent_port: str = "8510", ip_address: Optional[str] = None) -> bool:
        try:
            user = self.db.get_user_by_id(user_id)
            if not user:
                return False
            
            # Parse existing metadata
            metadata = {}
            if user.get('metadata'):
                try:
                    # Handle double-encoded JSON
                    metadata_str = user['metadata']
                    if isinstance(metadata_str, str) and metadata_str.startswith('"'):
                        # Double-encoded JSON, decode twice
                        metadata_str = json.loads(metadata_str)
                    metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
                    
                    # Ensure metadata is a dictionary
                    if not isinstance(metadata, dict):
                        metadata = {}
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse metadata for user {user_id}: {e}")
                    metadata = {}
            
            # Update metadata with server assignment and approval info
            metadata.update({
                'server_assignment': server_assignment,
                'approved_by': admin_username,
                'approved_at': datetime.now().isoformat(),
                'resources': metadata.get('resources', {
                    'cpu': '4 cores',
                    'ram': '8GB', 
                    'gpu': '1 core, 12GB'
                })
            })
            
            # Map server assignment to server ID for redirect URL
            server_id_map = {
                'Server 1': 'server-1',
                'Server 2': 'server-2',
                'Server 3': 'server-3',
                'Server 4': 'server-4'
            }
            
            # If server_assignment is already an IP or server ID, use it directly
            if server_assignment.startswith(('server-', '127.', '192.', '10.')):
                redirect_server = server_assignment
            else:
                redirect_server = server_id_map.get(server_assignment, 'server-1')
            
            if self.db.update_user(user_id, {
                'is_approved': True,
                'redirect_url': f"http://{redirect_server}:{agent_port}",
                'metadata': json.dumps(metadata)
            }):
                self.db.log_audit_event(
                    admin_username,
                    'approve_user',
                    {
                        'message': f'User {user["username"]} (ID: {user_id}) approved by {admin_username}',
                        'approved_user': user['username'],
                        'server_assignment': server_assignment,
                        'redirect_server': redirect_server
                    },
                    ip_address
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Error approving user {user_id}: {e}")
            return False
    
    def get_admin_users(self) -> List[Dict[str, Any]]:
        try:
            users = self.db.get_all_users()
            
            admin_users = []
            for user in users:
                # Skip system user
                if user.get('username') == 'System' or user.get('status') == 'system':
                    continue
                
                # Parse metadata if available
                metadata = {}
                if user.get('metadata'):
                    try:
                        # Handle double-encoded JSON
                        metadata_str = user['metadata']
                        if isinstance(metadata_str, str) and metadata_str.startswith('"'):
                            # Double-encoded JSON, decode twice
                            metadata_str = json.loads(metadata_str)
                        metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Failed to parse metadata for user {user.get('username')}: {e}")
                        metadata = {}
                
                # Determine if user came through registration or was created by admin
                is_new_registration = not metadata.get('created_by_admin', False)
                
                # Set container, resources, and server based on user status
                if is_new_registration and not user.get('is_approved'):
                    # New registration - show NA until approved
                    container_name = 'NA'
                    container_status = 'pending'
                    resources = {'cpu': 'NA', 'ram': 'NA', 'gpu': 'NA'}
                    server_assignment = 'NA'
                    server_location = 'NA'
                else:
                    # Approved user or admin-created user
                    container_name = f"container-{user['username'][:2].lower()}-{user['id']:03d}"
                    container_status = 'running' if user.get('is_approved') else 'stopped'
                    
                    # Get resources from metadata or use defaults
                    if metadata.get('resources'):
                        resources = metadata['resources']
                    else:
                        if user.get('is_admin'):
                            resources = {'cpu': '8 cores', 'ram': '16GB', 'gpu': '2 cores, 24GB'}
                        else:
                            resources = {'cpu': '4 cores', 'ram': '8GB', 'gpu': '1 core, 12GB'}
                    
                    # Get server assignment from metadata or use fallback
                    server_assignment = metadata.get('server_assignment', 'NA')
                    if server_assignment == 'NA' or not server_assignment:
                        # Fallback to old logic for backward compatibility
                        server_num = (user['id'] % 4) + 1
                        server_assignment = f'Server {server_num}'
                    
                    # Get server location
                    server_locations = {
                        'Server 1': 'us-east-1',
                        'Server 2': 'us-west-2', 
                        'Server 3': 'eu-west-1',
                        'Server 4': 'ap-south-1'
                    }
                    
                    # Handle IP-based server assignments
                    if server_assignment.startswith(('127.', '192.', '10.', 'server-')):
                        server_location = 'localhost' if server_assignment.startswith('127.') else 'unknown'
                    else:
                        server_location = server_locations.get(server_assignment, 'unknown')
                    
                # Determine role
                if user.get('is_admin'):
                    role = 'Admin'
                elif user.get('is_approved'):
                    role = 'Developer'
                else:
                    role = 'Pending'
                
                admin_user = {
                    'id': str(user['id']),
                    'name': user['username'],
                    'email': user['email'],
                    'role': role,
                    'container': container_name,
                    'containerStatus': container_status,
                    'resources': resources,
                    'server': server_assignment,
                    'serverLocation': server_location,
                    'status': 'Running' if user.get('is_approved') else ('Pending' if is_new_registration else 'Stopped'),
                    'isNewRegistration': is_new_registration
                }
                admin_users.append(admin_user)
            
            return admin_users
        except Exception as e:
            logger.error(f"Error fetching admin users: {e}")
            return []
    
    def get_admin_stats(self) -> Dict[str, Any]:
        try:
            users = self.db.get_all_users()
            # Filter out system user
            real_users = [user for user in (users or []) if user.get('username') != 'System' and user.get('status') != 'system']
            total_users = len(real_users) if real_users else 4  
            active_containers = sum(1 for user in real_users if user.get('is_approved', False))
            if not users:
                active_containers = 3  
            
            stats = {
                'totalUsers': total_users,
                'totalUsersChange': '+2 from last month',
                'activeContainers': active_containers,
                'containerUtilization': f'{int((active_containers / max(total_users, 1)) * 100)}% utilization',
                'availableServers': 4,
                'serverStatus': 'All regions online'
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error fetching admin stats: {e}")
            return {}
    
    def update_admin_user(self, user_id: int, update_data: Dict[str, Any], 
                         admin_username: str = "Admin", ip_address: Optional[str] = None) -> bool:
        try:
            update_fields = {}
            if 'name' in update_data:
                update_fields['username'] = update_data['name']
            if 'email' in update_data:
                update_fields['email'] = update_data['email']
            if 'role' in update_data:
                update_fields['is_admin'] = update_data['role'].lower() == 'admin'

            # Get user info before update
            user = self.db.get_user_by_id(user_id)
            
            if self.db.update_user(user_id, update_fields):
                # Log successful user update
                if user:
                    self.db.log_audit_event(
                        admin_username,
                        'update_admin_user',
                        {
                            'message': f'User {user["username"]} (ID: {user_id}) updated by {admin_username}',
                            'updated_user': user['username'],
                            'updated_fields': list(update_fields.keys())
                        },
                        ip_address
                    )
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return False
    
    def create_admin_user(self, user_data: Dict[str, Any], admin_username: str = "Admin", 
                         agent_port: str = "8510", ip_address: Optional[str] = None) -> Dict[str, Any]:
        try:
            # Extract user data
            name = user_data.get('name', '').strip()
            email = user_data.get('email', '').strip()
            password = user_data.get('password', 'defaultpass123')  # Default password
            role = user_data.get('role', 'User')
            status = user_data.get('status', 'Stopped')
            server_assignment = user_data.get('server', 'Server 1')
            resources = user_data.get('resources', {
                'cpu': '4 cores',
                'ram': '8GB',
                'gpu': '1 core, 12GB'
            })
            
            # Validate required fields
            if not name or not email:
                return {'success': False, 'error': 'Name and email are required'}
            
            # Check if user already exists
            existing_user = self.db.get_user_by_username(name)
            if existing_user:
                return {'success': False, 'error': 'User with this name already exists'}
            
            # Hash password
            password_hash = hash_password(password)
            
            # Prepare user data
            create_data = {
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
            if create_data['is_approved']:
                create_data['redirect_url'] = f"http://{server_assignment}:{agent_port}"
            
            # Create user
            if self.db.create_user(create_data):
                logger.info(f"Admin created new user: {name} ({email}) with role {role}")
                
                # Log successful user creation
                self.db.log_audit_event(
                    admin_username,
                    'create_admin_user',
                    {
                        'message': f'{admin_username} created new user {name} ({email}) with role {role}',
                        'created_user': name,
                        'email': email,
                        'role': role,
                        'server_assignment': server_assignment
                    },
                    ip_address
                )
                
                return {
                    'success': True, 
                    'message': f'User {name} created successfully',
                    'defaultPassword': password
                }
            else:
                return {'success': False, 'error': 'Failed to create user'}
                
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return {'success': False, 'error': 'Failed to create user'}
    
    def approve_admin_user(self, user_id: int, approval_data: Dict[str, Any], 
                          admin_username: str = "Admin", ip_address: Optional[str] = None) -> Dict[str, Any]: 
        try:
            server_assignment = approval_data.get('server', 'Server 1')
            resources = approval_data.get('resources', {
                'cpu': '4 cores',
                'ram': '8GB', 
                'gpu': '1 core, 12GB'
            })
            
            # Get user info
            user = self.db.get_user_by_id(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Parse existing metadata
            metadata = {}
            if user.get('metadata'):
                try:
                    metadata = json.loads(user['metadata'])
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            
            # Update metadata with approval info
            metadata.update({
                'server_assignment': server_assignment,
                'resources': resources,
                'approved_by': admin_username,
                'approved_at': datetime.now().isoformat()
            })
            
            # Update user with approval and resource assignment
            update_data = {
                'is_approved': True,
                'redirect_url': f"http://{server_assignment}:8510",
                'metadata': json.dumps(metadata)
            }
            
            if self.db.update_user(user_id, update_data):
                # Log successful approval
                self.db.log_audit_event(
                    admin_username,
                    'approve_admin_user',
                    {
                        'message': f'User {user["username"]} (ID: {user_id}) approved by {admin_username}',
                        'approved_user': user['username'],
                        'server_assignment': server_assignment,
                        'resources': resources
                    },
                    ip_address
                )
                
                return {
                    'success': True,
                    'message': f'User {user["username"]} approved successfully',
                    'server_assignment': server_assignment,
                    'redirect_url': update_data['redirect_url']
                }
            else:
                return {'success': False, 'error': 'Failed to approve user'}
                
        except Exception as e:
            logger.error(f"Error approving user {user_id}: {e}")
            return {'success': False, 'error': 'Failed to approve user'}
