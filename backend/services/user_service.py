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
    
    def approve_user(self, user_id: int, server_id: str, admin_username: str, 
                    agent_port: str = "8510", ip_address: Optional[str] = None) -> bool:
        try:
            user = self.db.get_user_by_id(user_id)
            
            if self.db.update_user(user_id, {
                'is_approved': True,
                'redirect_url': f"http://{server_id}:{agent_port}"
            }):
                if user:
                    self.db.log_audit_event(
                        admin_username,
                        'approve_user',
                        {
                            'message': f'User {user["username"]} (ID: {user_id}) approved by {admin_username}',
                            'approved_user': user['username'],
                            'server_id': server_id
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
                container_name = f"container-{user['username'][:2].lower()}-{user['id']:03d}"
                container_status = 'running' if user.get('is_approved') else 'stopped'
                
                if user.get('is_admin'):
                    resources = {'cpu': '8 cores', 'ram': '16GB', 'gpu': '2 cores, 24GB'}
                    role = 'Admin'
                else:
                    resources = {'cpu': '4 cores', 'ram': '8GB', 'gpu': '1 core, 12GB'}
                    role = 'Developer' if user.get('is_approved') else 'Pending'
                
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
                server_map = {
                    'Server 1': 'server-1',
                    'Server 2': 'server-2',
                    'Server 3': 'server-3',
                    'Server 4': 'server-4'
                }
                server_id = server_map.get(server_assignment, 'server-1')
                create_data['redirect_url'] = f"http://{server_id}:{agent_port}"
            
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
    
    def approve_admin_user(self, user_id: int, approval_data: Dict[str, Any]): 
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
            
            # Map server assignment to server ID
            server_map = {
                'Server 1': 'server-1',
                'Server 2': 'server-2', 
                'Server 3': 'server-3',
                'Server 4': 'server-4'
            }
            server_id = server_map.get(server_assignment, 'server-1')
            
            # Update user with approval and resource assignment
            update_data = {
                'is_approved': True,
                'redirect_url': f"http://{server_id}:8510",
                'metadata': json.dumps({
                    'server_assignment': server_assignment,
                    'resources': resources,
                    'approved_by': admin_username,
                    'approved_at': datetime.now().isoformat()
                })
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
