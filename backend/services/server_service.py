import time
import os
from typing import List, Dict, Any, Optional
from loguru import logger

from database import UserDatabase
from services.agent_service import AgentService
from models.server import ServerInfo, ServerResources, ServerStats, ServerActionRequest, AddServerRequest
from utils.helpers import read_agents_file, write_agents_file
from utils.validators import is_valid_ip


class ServerService:
    
    def __init__(self, db: UserDatabase, agent_service: AgentService):
        self.db = db
        self.agent_service = agent_service
        self.cache = {
            'data': None,
            'timestamp': 0,
            'cache_duration': 30
        }
    
    def get_cached_server_data(self) -> Dict[str, Any]:
        current_time = time.time()
        
        # Check if cache is valid
        if (self.cache['data'] is not None and 
            current_time - self.cache['timestamp'] < self.cache['cache_duration']):
            logger.debug("Using cached server data")
            return self.cache['data']
        
        # Cache is expired or empty, fetch new data
        logger.info("Fetching fresh server data")
        agents_list = read_agents_file()
        query_port = int(os.getenv('AGENT_PORT', 8510)) + 1
        
        # Query all agents concurrently (this is the optimization!)
        servers_resources = self.agent_service.query_available_agents(agents_list, query_port)
        
        # Process the data
        servers_data = []
        stats_data = {
            'totalServers': len(agents_list),
            'onlineServers': 0,
            'offlineServers': 0,
            'maintenanceServers': 0,
            'totalServersChange': 0,
            'onlineServersChange': 0,
            'offlineServersChange': 0,
            'maintenanceServersChange': 0
        }
        
        # Create a map of successful responses
        resource_map = {res['server_id']: res for res in servers_resources}
        
        for agent_ip in agents_list:
            if agent_ip in resource_map:
                resource_data = resource_map[agent_ip]
                status = 'online'
                stats_data['onlineServers'] += 1
                
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
                    'uptime': resource_data.get('uptime', 'Unknown'),
                    'containers': resource_data.get('running_containers', 0),
                    'lastSeen': current_time
                }
            else:
                # Server is offline
                stats_data['offlineServers'] += 1
                server_info = {
                    'id': f'server-{agent_ip.replace(".", "-")}',
                    'ip': agent_ip,
                    'status': 'offline',
                    'cpu': 0,
                    'memory': 0,
                    'disk': 0,
                    'uptime': 'Offline',
                    'containers': 0,
                    'lastSeen': 0
                }
            
            servers_data.append(server_info)
        
        # Cache the results
        cached_data = {
            'servers': servers_data,
            'stats': stats_data
        }
        
        self.cache['data'] = cached_data
        self.cache['timestamp'] = current_time
        
        return cached_data
    
    def get_server_resources(self) -> List[Dict[str, Any]]:
        try:
            agents_list = read_agents_file()
            query_port = int(os.getenv('AGENT_PORT', 8510)) + 1
            servers = self.agent_service.query_available_agents(agents_list, query_port)
            return servers if servers else []
        except Exception as e:
            logger.error(f"Error fetching server resources: {e}")
            return []
    
    def get_admin_servers(self) -> List[Dict[str, Any]]:
        try:
            # Use cached data for better performance
            cached_data = self.get_cached_server_data()
            return cached_data['servers']
        except Exception as e:
            logger.error(f"Error fetching server data: {e}")
            return []
    
    def get_server_stats(self) -> Dict[str, Any]:
        try:
            # Use cached data for better performance
            cached_data = self.get_cached_server_data()
            return cached_data['stats']
        except Exception as e:
            logger.error(f"Error fetching server stats: {e}")
            return {}
    
    def perform_server_action(self, server_id: str, action: str, username: str, ip_address: str = None) -> Dict[str, Any]:
        try:
            # Extract IP from server_id
            server_ip = server_id.replace('server-', '').replace('-', '.')
            
            # Handle delete action
            if action == 'delete':
                return self._delete_server(server_id, server_ip, username, ip_address)
            
            # Log the action
            self.db.log_audit_event(
                username=username,
                action_type='server_action',
                action_details={
                    'message': f'Performed {action} action on server {server_ip}',
                    'server_id': server_id,
                    'server_ip': server_ip,
                    'action': action
                },
                ip_address=ip_address
            )
            
            return {
                'success': True,
                'message': f'Action {action} initiated for server {server_ip}'
            }
            
        except Exception as e:
            logger.error(f"Error performing server action: {e}")
            return {'success': False, 'error': 'Failed to perform server action'}
    
    def _delete_server(self, server_id: str, server_ip: str, username: str, ip_address: str = None) -> Dict[str, Any]:
        """Delete a server from the system."""
        try:
            # Read existing agents (list of IP addresses as strings)
            agents = read_agents_file()
            
            # Check if the server exists
            if server_ip not in agents:
                return {'success': False, 'error': f'Server {server_ip} not found'}
            
            # Remove the server from the list
            agents = [agent for agent in agents if agent != server_ip]
            
            # Write the updated agents file
            if not write_agents_file(agents):
                return {'success': False, 'error': 'Failed to update agents file'}
            
            # Clear cache to force refresh
            self.cache['data'] = None
            self.cache['timestamp'] = 0
            
            # Log the deletion
            self.db.log_audit_event(
                username=username,
                action_type='server_delete',
                action_details={
                    'message': f'Deleted server {server_ip}',
                    'server_id': server_id,
                    'server_ip': server_ip,
                    'action': 'delete'
                },
                ip_address=ip_address
            )
            
            logger.info(f"Server {server_ip} deleted successfully by {username}")
            
            return {
                'success': True,
                'message': f'Server {server_ip} deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error deleting server {server_ip}: {e}")
            return {'success': False, 'error': f'Failed to delete server: {str(e)}'}
    
    def add_server(self, server_data: AddServerRequest) -> Dict[str, Any]:    
        try:
            # Validate required fields
            name = server_data.name.strip()
            ip = server_data.ip.strip()
            port = server_data.port.strip()
            description = server_data.description.strip()
            tags = server_data.tags
            ip = server_data.get('ip', '').strip()
            port = server_data.get('port', '8511').strip()
            description = server_data.get('description', '').strip()
            tags = server_data.get('tags', [])
            
            if not name:
                return {'success': False, 'error': 'Server name is required'}
            
            if not ip:
                return {'success': False, 'error': 'IP address is required'}
            
            # Validate IP address
            if not is_valid_ip(ip):
                return {'success': False, 'error': 'Invalid IP address format'}
            
            # Validate port
            try:
                port_num = int(port)
                if port_num < 1 or port_num > 65535:
                    return {'success': False, 'error': 'Port must be between 1 and 65535'}
            except ValueError:
                return {'success': False, 'error': 'Invalid port number'}
            
            # Read existing agents
            agents = read_agents_file()
            
            # Check if IP already exists
            if ip in agents:
                return {'success': False, 'error': 'Server with this IP already exists'}
            
            # Add new server to agents list
            agents.append(ip)
            if not write_agents_file(agents):
                return {'success': False, 'error': 'Failed to save server configuration'}
            
            # Invalidate cache so fresh data is fetched
            self.cache['data'] = None
            self.cache['timestamp'] = 0
            
            # Log the action
            self.db.log_audit_event(
                username=admin_username,
                action_type='server_added',
                action_details={
                    'message': f'Added new server: {name} ({ip}:{port})',
                    'server_name': name,
                    'server_ip': ip,
                    'server_port': port,
                    'description': description,
                    'tags': tags
                },
                ip_address=ip_address
            )
            
            logger.info(f"Server added by {admin_username}: {name} ({ip}:{port})")
            
            return {
                'success': True,
                'message': f'Server {name} added successfully',
                'server': {
                    'name': name,
                    'ip': ip,
                    'port': port,
                    'description': description,
                    'tags': tags
                }
            }
            
        except Exception as e:
            logger.error(f"Error adding server: {e}")
            return {'success': False, 'error': 'Failed to add server'}
    
    def get_servers_list(self) -> List[Dict[str, Any]]:
        """
        Get list of available servers for Docker images management.
        
        Returns:
            List[Dict[str, Any]]: List of available servers
        """
        try:
            # Use cached data for better performance
            cached_data = self.get_cached_server_data()
            servers_data = cached_data['servers']
            
            # Transform to simple server list format
            servers_list = []
            for server in servers_data:
                servers_list.append({
                    'id': server['id'],
                    'ip': server['ip'],
                    'status': server['status'],
                    'name': f"Server {server['ip']}"
                })
            
            return servers_list
            
        except Exception as e:
            logger.error(f"Error fetching servers list: {e}")
            return []
    
    def invalidate_cache(self):
        """Invalidate the server data cache."""
        self.cache['data'] = None
        self.cache['timestamp'] = 0
