"""
Docker service for managing Docker images and containers across servers.
"""
import time
import os
from typing import List, Dict, Any, Optional
from loguru import logger

from database import UserDatabase
from services.agent_service import AgentService
from models.docker import DockerImage, DockerImagesResponse, DockerImageDetailsResponse, DockerImagesRequest
from utils.helpers import read_agents_file


class DockerService:
    """Service for managing Docker operations across servers."""
    
    def __init__(self, db: UserDatabase, agent_service: AgentService):
        self.db = db
        self.agent_service = agent_service
    
    def get_docker_images(self, server_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get Docker images from all servers or a specific server.
        
        Args:
            server_id: Specific server ID to query, or None for all servers
            
        Returns:
            Dict[str, Any]: Docker images response
        """
        try:
            # Get list of available agents
            agents = read_agents_file()
            query_port = int(os.getenv('AGENT_PORT', 8510)) + 1
            
            if server_id:
                # Query specific server
                if server_id not in agents:
                    return {
                        'servers': [],
                        'total_servers': 0,
                        'error': 'Server not found',
                        'timestamp': time.time()
                    }
                
                result = self.agent_service.query_agent_docker_images(server_id, query_port)
                if result:
                    return {
                        'servers': [result],
                        'total_servers': 1,
                        'timestamp': time.time()
                    }
                else:
                    return {
                        'servers': [],
                        'total_servers': 0,
                        'error': f'Failed to get Docker images from server {server_id}',
                        'timestamp': time.time()
                    }
            else:
                # Query all servers
                results = self.agent_service.query_multiple_agents_docker_images(agents, query_port)
                
                return {
                    'servers': results,
                    'total_servers': len(results),
                    'timestamp': time.time()
                }
        
        except Exception as e:
            logger.error(f"Error getting Docker images: {e}")
            return {
                'servers': [],
                'total_servers': 0,
                'error': 'Internal server error',
                'timestamp': time.time()
            }
    
    def get_docker_image_details(self, server_id: str, image_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific Docker image from a server.
        
        Args:
            server_id: Server ID
            image_id: Docker image ID
            
        Returns:
            Dict[str, Any]: Docker image details response
        """
        try:
            # Check if server exists
            agents = read_agents_file()
            query_port = int(os.getenv('AGENT_PORT', 8510)) + 1
            if server_id not in agents:
                return {'error': 'Server not found'}
            
            # Query image details from specific server
            result = self.agent_service.query_agent_docker_image_details(server_id, image_id, query_port)
            
            if result:
                return result
            else:
                return {
                    'error': f'Failed to get image details from server {server_id}'
                }
        
        except Exception as e:
            logger.error(f"Error getting Docker image details: {e}")
            return {'error': 'Internal server error'}
    
    def get_servers_list(self) -> List[Dict[str, Any]]:
        """
        Get list of available servers for Docker images management.
        
        Returns:
            List[Dict[str, Any]]: List of available servers
        """
        try:
            # Get list of available agents
            agents = read_agents_file()
            query_port = int(os.getenv('AGENT_PORT', 8510)) + 1
            
            # Query servers for basic info
            servers_resources = self.agent_service.query_available_agents(agents, query_port)
            
            # Create server list with status information
            servers_list = []
            resource_map = {res['server_id']: res for res in servers_resources}
            
            for agent_ip in agents:
                if agent_ip in resource_map:
                    # Server is online
                    servers_list.append({
                        'id': agent_ip,
                        'name': f'Server {agent_ip}',
                        'ip': agent_ip,
                        'status': 'online',
                        'containers': resource_map[agent_ip].get('running_containers', 0)
                    })
                else:
                    # Server is offline
                    servers_list.append({
                        'id': agent_ip,
                        'name': f'Server {agent_ip}',
                        'ip': agent_ip,
                        'status': 'offline',
                        'containers': 0
                    })
            
            return servers_list
        
        except Exception as e:
            logger.error(f"Error getting servers list: {e}")
            return []
    
    def get_docker_statistics(self) -> Dict[str, Any]:
        """
        Get Docker statistics across all servers.
        
        Returns:
            Dict[str, Any]: Docker statistics
        """
        try:
            # Get Docker images from all servers
            images_data = self.get_docker_images()
            
            total_images = 0
            total_size = 0
            servers_with_docker = 0
            
            for server_data in images_data.get('servers', []):
                if 'images' in server_data:
                    server_images = server_data['images']
                    total_images += len(server_images)
                    servers_with_docker += 1
                    
                    # Calculate total size
                    for image in server_images:
                        total_size += image.get('size', 0)
            
            return {
                'total_images': total_images,
                'total_size': total_size,
                'servers_with_docker': servers_with_docker,
                'total_servers': len(read_agents_file())
            }
        
        except Exception as e:
            logger.error(f"Error getting Docker statistics: {e}")
            return {
                'total_images': 0,
                'total_size': 0,
                'servers_with_docker': 0,
                'total_servers': 0
            }
    
    def search_docker_images(self, query: str, server_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Search Docker images across servers.
        
        Args:
            query: Search query
            server_id: Specific server ID to search, or None for all servers
            
        Returns:
            Dict[str, Any]: Search results
        """
        try:
            # Get all Docker images
            images_data = self.get_docker_images(server_id)
            
            # Filter images based on query
            filtered_servers = []
            for server_data in images_data.get('servers', []):
                if 'images' in server_data:
                    filtered_images = []
                    for image in server_data['images']:
                        # Search in repository, tag, and ID
                        if (query.lower() in image.get('repository', '').lower() or
                            query.lower() in image.get('tag', '').lower() or
                            query.lower() in image.get('id', '').lower()):
                            filtered_images.append(image)
                    
                    if filtered_images:
                        server_copy = server_data.copy()
                        server_copy['images'] = filtered_images
                        filtered_servers.append(server_copy)
            
            return {
                'servers': filtered_servers,
                'total_servers': len(filtered_servers),
                'query': query,
                'timestamp': time.time()
            }
        
        except Exception as e:
            logger.error(f"Error searching Docker images: {e}")
            return {
                'servers': [],
                'total_servers': 0,
                'query': query,
                'error': 'Search failed',
                'timestamp': time.time()
            }
    
    def get_image_history(self, server_id: str, image_id: str) -> Dict[str, Any]:
        """
        Get Docker image history and layers.
        
        Args:
            server_id: Server ID
            image_id: Docker image ID
            
        Returns:
            Dict[str, Any]: Image history and layers
        """
        try:
            # Get detailed image information
            details = self.get_docker_image_details(server_id, image_id)
            
            if 'error' in details:
                return details
            
            # Extract history and layers information
            history = details.get('history', [])
            layers = details.get('layers', [])
            
            return {
                'success': True,
                'server_id': server_id,
                'image_id': image_id,
                'history': history,
                'layers': layers,
                'total_layers': len(layers),
                'total_history_entries': len(history)
            }
        
        except Exception as e:
            logger.error(f"Error getting image history: {e}")
            return {'error': 'Failed to get image history'}
    
    def cleanup_unused_images(self, server_id: str, admin_username: str, 
                            ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Cleanup unused Docker images on a server.
        Note: This is a placeholder for future implementation.
        
        Args:
            server_id: Server ID
            admin_username: Username of admin performing cleanup
            ip_address: Client IP address
            
        Returns:
            Dict[str, Any]: Cleanup result
        """
        try:
            # Log the cleanup action
            self.db.log_audit_event(
                username=admin_username,
                action_type='docker_cleanup',
                action_details={
                    'message': f'Docker cleanup initiated on server {server_id}',
                    'server_id': server_id,
                    'action': 'cleanup_unused_images'
                },
                ip_address=ip_address
            )
            
            # Placeholder for actual cleanup implementation
            return {
                'success': True,
                'message': f'Docker cleanup initiated on server {server_id}',
                'note': 'This is a placeholder implementation'
            }
        
        except Exception as e:
            logger.error(f"Error cleaning up Docker images: {e}")
            return {'success': False, 'error': 'Failed to cleanup Docker images'}
