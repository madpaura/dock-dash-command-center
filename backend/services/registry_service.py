"""Service for Docker registry operations."""

import requests
from typing import Dict, List, Optional, Any
from loguru import logger
from database import RegistryRepository, UserDatabase


class RegistryService:
    """Service for managing Docker registry servers and their contents."""
    
    def __init__(self):
        self.registry_repo = RegistryRepository()
        self.db = UserDatabase()
    
    def create_registry(self, registry_data: Dict[str, Any], 
                       admin_username: str = "Admin",
                       ip_address: str = None) -> Dict[str, Any]:
        """
        Create a new registry server.
        
        Args:
            registry_data: Registry configuration
            admin_username: Username of admin creating the registry
            ip_address: IP address of the request
            
        Returns:
            Result dictionary with success status
        """
        try:
            # Validate required fields
            if not registry_data.get('name'):
                return {'success': False, 'error': 'Registry name is required'}
            if not registry_data.get('url'):
                return {'success': False, 'error': 'Registry URL is required'}
            
            # Test connection to registry if credentials provided
            if registry_data.get('username') and registry_data.get('password'):
                test_result = self._test_registry_connection(
                    registry_data['url'],
                    registry_data.get('username'),
                    registry_data.get('password')
                )
                if not test_result['success']:
                    logger.warning(f"Registry connection test failed: {test_result.get('error')}")
                    # Don't fail creation, just log warning
            
            registry_id = self.registry_repo.create_registry(registry_data)
            
            if registry_id:
                # Log audit event
                self.db.log_audit_event(
                    admin_username,
                    'create_registry',
                    {
                        'message': f'{admin_username} created registry {registry_data["name"]}',
                        'registry_name': registry_data['name'],
                        'registry_url': registry_data['url']
                    },
                    ip_address
                )
                
                return {
                    'success': True,
                    'message': f'Registry {registry_data["name"]} created successfully',
                    'registry_id': registry_id
                }
            else:
                return {'success': False, 'error': 'Failed to create registry'}
                
        except Exception as e:
            logger.error(f"Error creating registry: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_registry(self, registry_id: int) -> Dict[str, Any]:
        """Get a registry by ID with additional stats."""
        try:
            registry = self.registry_repo.get_registry_by_id(registry_id)
            if not registry:
                return {'success': False, 'error': 'Registry not found'}
            
            # Try to get registry stats
            stats = self._get_registry_stats(registry)
            registry['stats'] = stats
            
            return {'success': True, 'data': registry}
        except Exception as e:
            logger.error(f"Error fetching registry: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_all_registries(self, include_inactive: bool = False) -> Dict[str, Any]:
        """Get all registries with stats."""
        try:
            registries = self.registry_repo.get_all_registries(include_inactive)
            
            # Add basic stats to each registry
            for registry in registries:
                registry['stats'] = self._get_registry_stats(registry)
            
            return {'success': True, 'data': {'registries': registries}}
        except Exception as e:
            logger.error(f"Error fetching registries: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_registry(self, registry_id: int, update_data: Dict[str, Any],
                       admin_username: str = "Admin",
                       ip_address: str = None) -> Dict[str, Any]:
        """Update a registry server."""
        try:
            registry = self.registry_repo.get_registry_by_id(registry_id)
            if not registry:
                return {'success': False, 'error': 'Registry not found'}
            
            if self.registry_repo.update_registry(registry_id, update_data):
                # Log audit event
                self.db.log_audit_event(
                    admin_username,
                    'update_registry',
                    {
                        'message': f'{admin_username} updated registry {registry["name"]}',
                        'registry_id': registry_id,
                        'updated_fields': list(update_data.keys())
                    },
                    ip_address
                )
                
                return {'success': True, 'message': 'Registry updated successfully'}
            else:
                return {'success': False, 'error': 'Failed to update registry'}
                
        except Exception as e:
            logger.error(f"Error updating registry: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_registry(self, registry_id: int,
                       admin_username: str = "Admin",
                       ip_address: str = None) -> Dict[str, Any]:
        """Delete a registry server."""
        try:
            registry = self.registry_repo.get_registry_by_id(registry_id)
            if not registry:
                return {'success': False, 'error': 'Registry not found'}
            
            if self.registry_repo.delete_registry(registry_id):
                # Log audit event
                self.db.log_audit_event(
                    admin_username,
                    'delete_registry',
                    {
                        'message': f'{admin_username} deleted registry {registry["name"]}',
                        'registry_name': registry['name']
                    },
                    ip_address
                )
                
                return {'success': True, 'message': 'Registry deleted successfully'}
            else:
                return {'success': False, 'error': 'Failed to delete registry'}
                
        except Exception as e:
            logger.error(f"Error deleting registry: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_registry_images(self, registry_id: int) -> Dict[str, Any]:
        """Get list of images from a registry."""
        try:
            registry = self.registry_repo.get_registry_by_id(registry_id)
            if not registry:
                return {'success': False, 'error': 'Registry not found'}
            
            images = self._fetch_registry_images(registry)
            return {'success': True, 'data': {'images': images}}
            
        except Exception as e:
            logger.error(f"Error fetching registry images: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_image_tags(self, registry_id: int, image_name: str) -> Dict[str, Any]:
        """Get tags for a specific image in a registry."""
        try:
            registry = self.registry_repo.get_registry_by_id(registry_id)
            if not registry:
                return {'success': False, 'error': 'Registry not found'}
            
            tags = self._fetch_image_tags(registry, image_name)
            return {'success': True, 'data': {'tags': tags}}
            
        except Exception as e:
            logger.error(f"Error fetching image tags: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_connection(self, registry_id: int) -> Dict[str, Any]:
        """Test connection to a registry."""
        try:
            registry = self.registry_repo.get_registry_by_id(registry_id)
            if not registry:
                return {'success': False, 'error': 'Registry not found'}
            
            # Get actual credentials for testing
            full_registry = self._get_registry_with_credentials(registry_id)
            
            result = self._test_registry_connection(
                full_registry['url'],
                full_registry.get('username'),
                full_registry.get('password')
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing registry connection: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_registry_with_credentials(self, registry_id: int) -> Optional[Dict[str, Any]]:
        """Get registry with actual credentials (internal use only)."""
        query = "SELECT * FROM registry_servers WHERE id = %s"
        conn = self.registry_repo.db_manager.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (registry_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()
    
    def _test_registry_connection(self, url: str, username: str = None, 
                                  password: str = None) -> Dict[str, Any]:
        """Test connection to a Docker registry."""
        auth = (username, password) if username and password else None
        
        # Determine URLs to try
        urls_to_try = []
        if url.startswith(('http://', 'https://')):
            urls_to_try.append(url)
            # Also try the other protocol
            if url.startswith('https://'):
                urls_to_try.append(url.replace('https://', 'http://'))
            else:
                urls_to_try.append(url.replace('http://', 'https://'))
        else:
            # For local registries (localhost, 127.0.0.1, or IP:port), try HTTP first
            if 'localhost' in url or '127.0.0.1' in url or ':' in url:
                urls_to_try.append(f'http://{url}')
                urls_to_try.append(f'https://{url}')
            else:
                urls_to_try.append(f'https://{url}')
                urls_to_try.append(f'http://{url}')
        
        last_error = None
        for test_url in urls_to_try:
            try:
                response = requests.get(
                    f'{test_url}/v2/',
                    auth=auth,
                    timeout=10,
                    verify=False  # Many private registries use self-signed certs
                )
                
                if response.status_code == 200:
                    return {'success': True, 'message': f'Connection successful ({test_url})'}
                elif response.status_code == 401:
                    return {'success': False, 'error': 'Authentication failed'}
                else:
                    last_error = f'Unexpected status: {response.status_code}'
                    
            except requests.exceptions.ConnectionError as e:
                last_error = f'Connection failed: {str(e)}'
                continue
            except Exception as e:
                last_error = str(e)
                continue
        
        return {'success': False, 'error': last_error or 'Connection failed'}
    
    def _get_registry_stats(self, registry: Dict[str, Any]) -> Dict[str, Any]:
        """Get statistics for a registry."""
        stats = {
            'image_count': 0,
            'total_size': 0,
            'status': 'unknown'
        }
        
        try:
            # Quick connection test
            full_registry = self._get_registry_with_credentials(registry['id'])
            if not full_registry:
                stats['status'] = 'error'
                return stats
            
            test_result = self._test_registry_connection(
                full_registry['url'],
                full_registry.get('username'),
                full_registry.get('password')
            )
            
            if test_result['success']:
                stats['status'] = 'online'
                # Try to get image count
                images = self._fetch_registry_images(full_registry)
                stats['image_count'] = len(images)
            else:
                stats['status'] = 'offline'
                
        except Exception as e:
            logger.debug(f"Error getting registry stats: {e}")
            stats['status'] = 'error'
        
        return stats
    
    def _get_registry_url(self, url: str) -> str:
        """Get the proper URL for a registry, trying HTTP for local registries."""
        if url.startswith(('http://', 'https://')):
            return url
        # For local registries, use HTTP
        if 'localhost' in url or '127.0.0.1' in url or ':' in url:
            return f'http://{url}'
        return f'https://{url}'
    
    def _fetch_registry_images(self, registry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch list of images from a registry."""
        images = []
        
        try:
            url = self._get_registry_url(registry['url'])
            
            auth = None
            if registry.get('username') and registry.get('password'):
                auth = (registry['username'], registry['password'])
            
            response = requests.get(
                f'{url}/v2/_catalog',
                auth=auth,
                timeout=10,
                verify=False  # Many private registries use self-signed certs
            )
            
            if response.status_code == 200:
                data = response.json()
                repositories = data.get('repositories', [])
                
                for repo in repositories:
                    images.append({
                        'name': repo,
                        'full_name': f"{registry['url']}/{repo}"
                    })
                    
        except Exception as e:
            logger.debug(f"Error fetching registry images: {e}")
        
        return images
    
    def _fetch_image_tags(self, registry: Dict[str, Any], 
                         image_name: str) -> List[Dict[str, Any]]:
        """Fetch tags for an image from a registry."""
        tags = []
        
        try:
            url = self._get_registry_url(registry['url'])
            
            auth = None
            if registry.get('username') and registry.get('password'):
                auth = (registry['username'], registry['password'])
            
            response = requests.get(
                f'{url}/v2/{image_name}/tags/list',
                auth=auth,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                tag_list = data.get('tags', [])
                
                for tag in tag_list:
                    tags.append({
                        'name': tag,
                        'full_name': f"{registry['url']}/{image_name}:{tag}"
                    })
                    
        except Exception as e:
            logger.debug(f"Error fetching image tags: {e}")
        
        return tags
