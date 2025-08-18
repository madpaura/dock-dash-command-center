import json
import hashlib
import requests
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

from database import UserDatabase
from utils.helpers import hash_password, get_client_ip
from utils.validators import is_valid_email, is_valid_username
from services.nginx_service import NginxService


class UserService:
    
    def __init__(self, db: UserDatabase):
        self.db = db
        self.nginx_service = NginxService()
    
    def _parse_user_metadata(self, metadata_raw: Optional[str]) -> Dict[str, Any]:
        if not metadata_raw:
            return {}
            
        try:
            metadata = json.loads(metadata_raw)
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            return metadata if isinstance(metadata, dict) else {}
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Error parsing metadata: {e}")
            return {}
    
    def _get_server_ip_from_assignment(self, server_assignment: str) -> Optional[str]:
        """Extract server IP from server assignment string."""
        try:
            # Server assignment format: "server_name (IP: x.x.x.x)"
            if "IP:" in server_assignment:
                ip_part = server_assignment.split("IP:")[1].strip()
                ip = ip_part.rstrip(")")
                return ip
            return None
        except Exception as e:
            logger.warning(f"Error parsing server assignment: {e}")
            return None
    
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
    
    def delete_user(self, user_id: int, admin_username: str) -> Dict[str, Any]:
        result = {
            'success': False,
            'message': '',
            'user_deleted': False,
            'container_deleted': False,
            'container_details': None
        }
        
        try:
            user = self.db.get_user_by_id(user_id)
            if not user:
                result['message'] = f'User with ID {user_id} not found'
                return result
            
            username = user['username']
            logger.info(user)

            # Parse user metadata
            metadata = self._parse_user_metadata(user.get('metadata'))
            logger.info(f"Parsed metadata for user {username}: {metadata}")
            
            container_info = None
            if metadata.get('container') and not metadata['container'].get('creation_failed'):
                container_info = metadata['container']
                logger.info(f"Found container for user {username}: {container_info}")
            
            if container_info and container_info.get('name'):
                container_deletion_result = self._delete_user_container(
                    container_info, 
                    user_id, 
                    metadata.get('server_assignment')
                )
                result['container_deleted'] = container_deletion_result.get('success', False)
                result['container_details'] = container_deletion_result
                
                if container_deletion_result.get('success'):
                    logger.info(f"Container {container_info['name']} deleted for user {username}")
                else:
                    logger.warning(f"Failed to delete container for user {username}: {container_deletion_result.get('message')}")
            else:
                logger.info(f"No container found for user {username}")
                result['container_deleted'] = True
            
            # Remove nginx routes for the user
            nginx_deletion_result = self.nginx_service.remove_user_route(username)
            result['nginx_routes_deleted'] = nginx_deletion_result.get('success', False)
            result['nginx_deletion_details'] = nginx_deletion_result
            
            if nginx_deletion_result.get('success'):
                logger.info(f"Nginx routes removed for user {username}")
            else:
                logger.warning(f"Failed to remove nginx routes for user {username}: {nginx_deletion_result.get('message')}")
            
            # Delete user from database
            if self.db.delete_user_by_username(username):
                result['user_deleted'] = True
                result['success'] = True
                
                # Log audit event
                audit_details = {
                    'message': f'User {username} (ID: {user_id}) deleted by {admin_username}',
                    'deleted_user': username,
                    'container_deleted': result['container_deleted'],
                    'nginx_routes_deleted': result['nginx_routes_deleted']
                }
                if container_info:
                    audit_details['container_name'] = container_info.get('name')
                    audit_details['container_deletion_details'] = result['container_details']
                
                # Add nginx deletion details to audit log
                audit_details['nginx_deletion_details'] = result['nginx_deletion_details']
                
                self.db.log_audit_event(
                    admin_username,
                    'delete_user',
                    audit_details,
                    metadata.get('server_assignment')
                )
                
                # Create comprehensive success message
                success_parts = [f'User {username}']
                if result['container_deleted']:
                    success_parts.append('container')
                if result['nginx_routes_deleted']:
                    success_parts.append('nginx routes')
                
                if len(success_parts) > 1:
                    result['message'] = f'{success_parts[0]} and associated {", ".join(success_parts[1:])} successfully deleted'
                else:
                    result['message'] = f'{success_parts[0]} successfully deleted'
                
                # Add warnings for partial failures
                warnings = []
                if not result['container_deleted']:
                    warnings.append('container deletion failed')
                if not result['nginx_routes_deleted']:
                    warnings.append('nginx route removal failed')
                
                if warnings:
                    result['message'] += f', but {" and ".join(warnings)}'
                    
                return result
            else:
                result['message'] = f'Failed to delete user {username} from database'
                return result
                
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            result['message'] = f'Unexpected error: {str(e)}'
            return result
    
    def get_pending_users(self) -> List[Dict[str, Any]]:
        try:
            users = self.db.get_pending_users()
            return users if users else []
        except Exception as e:
            logger.error(f"Error fetching pending users: {e}")
            return []
    
    def approve_user(self, user_id: int, server_assignment: str, admin_username: str, 
                     agent_port: str = "8511", ip_address: Optional[str] = None, 
                     resources: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        try:
            user = self.db.get_user_by_id(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Parse existing metadata
            metadata = self._parse_user_metadata(user.get('metadata'))
            
            # Use provided resources or defaults
            user_resources = resources or metadata.get('resources', {
                'cpu': '4 cores',
                'ram': '8GB', 
                'gpu': '1 core, 12GB'
            })
            
            # Update metadata with server assignment and approval info
            metadata.update({
                'server_assignment': server_assignment,
                'approved_by': admin_username,
                'approved_at': datetime.now().isoformat(),
                'resources': user_resources
            })
            
            redirect_server = server_assignment
            # Create Docker container for the user
            container_result = self._create_user_container(user['username'], redirect_server, user_resources, agent_port)
            redirect_url=f"NA"
            is_approved = False
            nginx_result = None

            # Update metadata with container information if container was created successfully
            if container_result.get('success') and container_result.get('container'):
                container_info = container_result['container']
                metadata['container'] = {
                    'name': container_info.get('name'),
                    'id': container_info.get('id'),
                    'status': container_info.get('status'),
                    'created_at': datetime.now().isoformat()
                }
                logger.info(f"Container {container_info.get('name')} assigned to user {user['username']}")
                redirect_url=f"http://{redirect_server}:{agent_port}"
                is_approved = True
                
                # Add nginx routes for the user using actual allocated ports
                port_map = container_info.get('port_map', {})
                if port_map:
                    vscode_port = port_map.get('code', 8080)
                    jupyter_port = port_map.get('jupyter', 8088)
                    
                    vscode_server = f"{redirect_server}:{vscode_port}"
                    jupyter_server = f"{redirect_server}:{jupyter_port}"
                    
                    nginx_result = self.nginx_service.add_user_route(
                        user['username'],
                        vscode_server,
                        jupyter_server
                    )
                    
                    # Store nginx routing information in metadata
                    metadata['nginx_routes'] = {
                        'configured': nginx_result.get('success', False),
                        'vscode_server': vscode_server,
                        'jupyter_server': jupyter_server,
                        'vscode_port': vscode_port,
                        'jupyter_port': jupyter_port,
                        'configured_at': datetime.now().isoformat(),
                        'result': nginx_result
                    }
                else:
                    # Fallback to default ports if port_map is not available
                    server_addresses = self.nginx_service.generate_user_servers(user['username'], redirect_server)
                    nginx_result = self.nginx_service.add_user_route(
                        user['username'],
                        server_addresses['vscode_server'],
                        server_addresses['jupyter_server']
                    )
                    
                    # Store nginx routing information in metadata
                    metadata['nginx_routes'] = {
                        'configured': nginx_result.get('success', False),
                        'vscode_server': server_addresses['vscode_server'],
                        'jupyter_server': server_addresses['jupyter_server'],
                        'configured_at': datetime.now().isoformat(),
                        'result': nginx_result
                    }
                
                if nginx_result.get('success'):
                    logger.success(f"Nginx routes configured for user {user['username']}")
                else:
                    logger.warning(f"Nginx route configuration failed for user {user['username']}: {nginx_result.get('message')}")
            else:
                metadata['container'] = {
                    'creation_failed': True,
                    'error': container_result.get('error', 'Unknown error'),
                    'attempted_at': datetime.now().isoformat()
                }
                logger.warning(f"Container creation failed for user {user['username']}: {container_result.get('error')}")

            # Update user approval status
            self.db.update_user(user_id, {
                'is_approved': is_approved,
                'redirect_url': redirect_url,
                'metadata': json.dumps(metadata)
            })

            # Prepare audit details
            audit_details = {
                'message': f'User {user["username"]} (ID: {user_id}) approved by {admin_username}',
                'approved_user': user['username'],
                'server_assignment': server_assignment,
                'redirect_server': redirect_server,
                'redirect_url': redirect_url,
                'container_created': container_result.get('success', False),
                'container_info': container_result.get('container', {})
            }
            
            # Add nginx routing information to audit log
            if nginx_result:
                audit_details['nginx_routes_configured'] = nginx_result.get('success', False)
                audit_details['nginx_result'] = nginx_result
            
            self.db.log_audit_event(
                admin_username,
                'approve_user',
                audit_details,
                ip_address
            )
            
            if container_result.get('success'):
                return {
                    'success': True,
                    'container_result': container_result,
                    'user_approved': True
                }
            else:
                return {'success': False, 'error': 'Failed to update user approval status'}
            
        except Exception as e:
            logger.error(f"Error approving user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_user_container(self, username: str, server_ip: str, resources: Dict[str, str], agent_port: str) -> Dict[str, Any]:
        try:
            cpu_cores = self._parse_cpu_spec(resources.get('cpu', '2 cores'))
            memory_limit = self._parse_memory_spec(resources.get('ram', '4GB'))
            
            container_data = {
                'user': username,
                'session_token': 'admin_approval',
                'resources': {
                    'cpu_count': cpu_cores,
                    'memory_limit': memory_limit,
                    'gpu': resources.get('gpu', '1 core, 8GB')
                }
            }
            
            # Make API call to create container on the assigned server
            container_api_url = f"http://{server_ip}:{agent_port}/api/containers/create"
            
            logger.info(f"Creating container for user {username} on server {server_ip}")
            # pass on authorization token
            response = requests.post(
                container_api_url,
                json=container_data,
                timeout=30,
                headers={'Authorization': f'Bearer admin_approval'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.success(f"Container created successfully for user {username}: {result.get('container', {})}")
                    return {
                        'success': True,
                        'container': result.get('container', {}),
                        'message': 'Container created successfully'
                    }
                else:
                    logger.error(f"Container creation failed for user {username}: {result.get('error')}")
                    return {
                        'success': False,
                        'error': result.get('error', 'Container creation failed'),
                        'message': 'Failed to create container'
                    }
            else:
                logger.error(f"Container API request failed for user {username}: HTTP {response.status_code}")
                return {
                    'success': False,
                    'error': f'Container API request failed: HTTP {response.status_code}',
                    'message': 'Failed to connect to container service'
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"Container creation timeout for user {username} on server {server_ip}")
            return {
                'success': False,
                'error': 'Container creation timeout',
                'message': 'Container service did not respond in time'
            }
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to container service for user {username} on server {server_ip}")
            return {
                'success': False,
                'error': 'Cannot connect to container service',
                'message': 'Container service is not available'
            }
        except Exception as e:
            logger.error(f"Unexpected error creating container for user {username}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Unexpected error during container creation'
            }
    
    def _parse_cpu_spec(self, cpu_spec: str) -> int:
        """Parse CPU specification like '4 cores' to integer."""
        try:
            # Extract number from strings like '4 cores', '2 core', etc.
            import re
            match = re.search(r'(\d+)', cpu_spec)
            if match:
                return int(match.group(1))
            return 2  # Default
        except:
            return 2
    
    def _parse_memory_spec(self, memory_spec: str) -> str:
        """Parse memory specification like '8GB' to Docker format."""
        try:
            # Convert specifications like '8GB', '4 GB', '2g' to Docker format
            import re
            match = re.search(r'(\d+)\s*([gG][bB]?)', memory_spec)
            if match:
                return f"{match.group(1)}g"
            return "4g"  # Default
        except:
            return "4g"
    
    def get_admin_users(self) -> List[Dict[str, Any]]:
        try:
            users = self.db.get_all_users()
            
            admin_users = []
            for user in users:
                # Skip system user
                if user.get('username') == 'System' or user.get('status') == 'system':
                    continue
                
                # Parse metadata if available
                metadata = self._parse_user_metadata(user.get('metadata'))
                
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
                    # Use actual container name from metadata if available
                    if metadata.get('container') and metadata['container'].get('name'):
                        container_name = metadata['container']['name']
                        container_status = metadata['container'].get('status', 'unknown')
                        # Update status based on current approval status if container creation failed
                        if metadata['container'].get('creation_failed'):
                            container_status = 'failed'
                    else:
                        # Fallback to generic name for backward compatibility
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

    def _delete_user_container(self, container_info: Dict[str, Any], user_id: int, 
                              server_assignment: Optional[str] = None) -> Dict[str, Any]:
        result = {
            'success': False,
            'message': '',
            'server_contacted': False,
            'container_found': False,
            'container_deleted': False
        }
        
        try:
            container_name = container_info.get('name')
            if not container_name:
                result['message'] = 'No container name found in user metadata'
                return result
            
            # Determine server IP from assignment
            server_ip = self._get_server_ip_from_assignment(server_assignment)
            if not server_ip:
                result['message'] = f'Could not determine server IP from assignment: {server_assignment}'
                return result
            
            # Get agent port from environment
            agent_port = int(os.getenv('AGENT_PORT', '5001')) + 1
            
            # Call the agent's delete container endpoint
            try:
                delete_url = f"http://{server_ip}:{agent_port}/api/containers/{container_name}/delete"
                payload = {'user_id': user_id,
                    'username': self.db.get_user_by_id(user_id)['username']
                }
                
                logger.info(f"Attempting to delete container {container_name} on {server_ip}:{agent_port} for user {self.db.get_user_by_id(user_id)['username']}")
                
                response = requests.post(
                    delete_url,
                    json=payload,
                    timeout=30
                )
                
                result['server_contacted'] = True
                
                if response.status_code == 200:
                    response_data = response.json()
                    result['success'] = response_data.get('success', False)
                    result['container_deleted'] = response_data.get('container_removed', False)
                    result['container_found'] = True
                    result['message'] = response_data.get('message', 'Container deleted successfully')
                    
                    # Include additional details from agent response
                    if 'container_stopped' in response_data:
                        result['container_stopped'] = response_data['container_stopped']
                    if 'ports_deallocated' in response_data:
                        result['ports_deallocated'] = response_data['ports_deallocated']
                    if 'deallocated_ports' in response_data:
                        result['deallocated_ports'] = response_data['deallocated_ports']
                        
                elif response.status_code == 400:
                    # Container might not exist or other error
                    response_data = response.json()
                    result['message'] = response_data.get('message', 'Failed to delete container')
                    # Check if it's a "not found" error
                    if 'not found' in result['message'].lower():
                        result['container_found'] = False
                        result['success'] = True  # Consider it success if container doesn't exist
                        result['message'] = f'Container {container_name} not found (may already be deleted)'
                else:
                    result['message'] = f'Server returned status {response.status_code}'
                    
            except requests.exceptions.Timeout:
                result['message'] = f'Timeout connecting to server {server_ip}:{agent_port}'
            except requests.exceptions.ConnectionError:
                result['message'] = f'Could not connect to server {server_ip}:{agent_port}'
            except requests.exceptions.RequestException as e:
                result['message'] = f'Request failed: {str(e)}'
            except Exception as e:
                result['message'] = f'Unexpected error calling agent: {str(e)}'
                
        except Exception as e:
            logger.error(f"Error deleting container {container_info}: {e}")
            result['message'] = f'Unexpected error: {str(e)}'
            
        return result
    
    def _get_server_ip_from_assignment(self, server_assignment: Optional[str]) -> Optional[str]:
        if not server_assignment:
            return None
            
        import re
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        if re.match(ip_pattern, server_assignment):
            return server_assignment
        
        return server_assignment
