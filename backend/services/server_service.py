"""
Server service for managing server operations and monitoring.
"""
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
    """Service for handling server management operations."""
    
    def __init__(self, db: UserDatabase, agent_service: AgentService):
        self.db = db
        self.agent_service = agent_service
        self.cache = {
            'data': None,
            'timestamp': 0,
            'cache_duration': 30  # Cache for 30 seconds
        }
    
    def get_cached_server_data(self) -> Dict[str, Any]:
        """
        Get cached server data or fetch new data if cache is expired.
        
        Returns:
            Dict[str, Any]: Server data with servers and stats
        """
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
        """
        Get server resources from all agents.
        
        Returns:
            List[Dict[str, Any]]: List of server resources
        """
        try:
            agents_list = read_agents_file()
            query_port = int(os.getenv('AGENT_PORT', 8510)) + 1
            servers = self.agent_service.query_available_agents(agents_list, query_port)
            return servers if servers else []
        except Exception as e:
            logger.error(f"Error fetching server resources: {e}")
            return []
    
    def get_admin_servers(self) -> List[Dict[str, Any]]:
        """
        Get all servers with detailed information for admin dashboard.
        
        Returns:
            List[Dict[str, Any]]: List of server information
        """
        try:
            # Use cached data for better performance
            cached_data = self.get_cached_server_data()
            return cached_data['servers']
        except Exception as e:
            logger.error(f"Error fetching server data: {e}")
            return []
    
    def get_server_stats(self) -> Dict[str, Any]:
        """
        Get server statistics for admin dashboard.
        
        Returns:
            Dict[str, Any]: Server statistics
        """
        try:
            # Use cached data for better performance
            cached_data = self.get_cached_server_data()
            return cached_data['stats']
        except Exception as e:
            logger.error(f"Error fetching server stats: {e}")
            return {}
    
    def perform_server_action(self, server_id: str, action: str, admin_username: str, 
                            ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform actions on servers (start, stop, restart, etc.).
        
        Args:
            server_id: Server ID
            action: Action to perform
            admin_username: Username of admin performing action
            ip_address: Client IP address
            
        Returns:
            Dict[str, Any]: Action result
        """
        try:
            # Extract IP from server_id
            server_ip = server_id.replace('server-', '').replace('-', '.')
            
            # Log the action
            self.db.log_audit_event(
                username=admin_username,
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
    
    def add_server(self, server_data: Dict[str, Any], admin_username: str, 
                  ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a new server to the agents list.
        
        Args:
            server_data: Server information
            admin_username: Username of admin adding server
            ip_address: Client IP address
            
        Returns:
            Dict[str, Any]: Addition result
        """
        try:
            # Validate required fields
            name = server_data.get('name', '').strip()
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
