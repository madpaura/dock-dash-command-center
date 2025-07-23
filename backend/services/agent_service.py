"""
Agent service for managing communication with monitoring agents.
Refactored from agent_manager.py with improved structure and error handling.
"""
import socket
import json
from loguru import logger
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import List, Optional, Dict, Any

from models.server import ServerResources, AgentInfo
from models.docker import DockerImage, DockerImagesResponse, DockerImageDetailsResponse


class AgentService:
    """Service for managing agent communication and resource queries."""
    
    def __init__(self, default_port: int = 5000, default_timeout: int = 5):
        self.default_port = default_port
        self.default_timeout = default_timeout
    
    def query_agent_resources(self, agent_ip: str, agent_port: int = None, timeout: int = None) -> Optional[Dict[str, Any]]:
        """
        Query a single agent for its resource information.
        Optimized with shorter timeout for faster failure detection.
        
        Args:
            agent_ip: IP address of the agent
            agent_port: Port of the agent (defaults to default_port)
            timeout: Timeout in seconds (defaults to default_timeout)
            
        Returns:
            Optional[Dict[str, Any]]: Resource information or None if failed
        """
        if agent_port is None:
            agent_port = self.default_port
        if timeout is None:
            timeout = self.default_timeout
            
        try:
            logger.debug(f"Querying resources from : {agent_ip} : {agent_port}")

            url = f"http://{agent_ip}:{agent_port}/get_resources"

            # Use shorter timeout for faster failure detection
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Agent {agent_ip}:{agent_port} returned status code {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout querying agent {agent_ip}:{agent_port}")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection failed to agent {agent_ip}:{agent_port}")
            return None
        except Exception as e:
            logger.error(f"Error querying agent {agent_ip}:{agent_port}: {e}")
            return None

    def query_single_agent_with_id(self, agent_ip: str, port: int = None) -> Optional[Dict[str, Any]]:
        """
        Helper function to query a single agent and return with server_id.
        
        Args:
            agent_ip: IP address of the agent
            port: Port of the agent
            
        Returns:
            Optional[Dict[str, Any]]: Resource information with server_id or None
        """
        if port is None:
            port = self.default_port
            
        resources = self.query_agent_resources(agent_ip, agent_port=port)
        if resources:
            resources["server_id"] = agent_ip
            return resources
        return None

    def query_available_agents(self, server_list: List[str], port: int = None, 
                             max_workers: int = 10, timeout_per_agent: int = None) -> List[Dict[str, Any]]:
        """
        Query multiple servers for their resource information concurrently.
        Optimized for speed with parallel processing and shorter timeouts.
        
        Args:
            server_list: List of server IP addresses
            port: Port to use for all servers
            max_workers: Maximum number of concurrent workers
            timeout_per_agent: Timeout per agent in seconds
            
        Returns:
            List[Dict[str, Any]]: List of resource information from available agents
        """
        if port is None:
            port = self.default_port
        if timeout_per_agent is None:
            timeout_per_agent = self.default_timeout
            
        if not server_list:
            logger.warning("No servers provided to query")
            return []

        logger.debug(f"Querying {len(server_list)} agents concurrently with {max_workers} workers")
        
        available_agents = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_server = {
                executor.submit(self.query_single_agent_with_id, server_ip, port): server_ip 
                for server_ip in server_list
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_server):
                server_ip = future_to_server[future]
                try:
                    result = future.result(timeout=timeout_per_agent)
                    if result:
                        available_agents.append(result)
                        logger.debug(f"Successfully queried agent {server_ip}")
                    else:
                        logger.debug(f"Agent {server_ip} not available")
                except Exception as e:
                    logger.error(f"Error querying agent {server_ip}: {e}")
        
        logger.info(f"Successfully queried {len(available_agents)} out of {len(server_list)} agents")
        return available_agents

    def query_agent_docker_images(self, agent_ip: str, agent_port: int = None, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """
        Query a single agent for its Docker images information.
        
        Args:
            agent_ip: IP address of the agent
            agent_port: Port of the agent
            timeout: Timeout in seconds
            
        Returns:
            Optional[Dict[str, Any]]: Docker images information or None if failed
        """
        if agent_port is None:
            agent_port = self.default_port
            
        try:
            logger.debug(f"Querying Docker images from: {agent_ip}:{agent_port}")
            
            url = f"http://{agent_ip}:{agent_port}/get_docker_images"
            response = requests.get(url, timeout=timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Agent {agent_ip}:{agent_port} returned status code {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout querying Docker images from agent {agent_ip}:{agent_port}")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection failed to agent {agent_ip}:{agent_port}")
            return None
        except Exception as e:
            logger.error(f"Error querying Docker images from agent {agent_ip}:{agent_port}: {e}")
            return None

    def query_agent_docker_image_details(self, agent_ip: str, image_id: str, 
                                       agent_port: int = None, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """
        Query a single agent for detailed information about a specific Docker image.
        
        Args:
            agent_ip: IP address of the agent
            image_id: ID of the Docker image
            agent_port: Port of the agent
            timeout: Timeout in seconds
            
        Returns:
            Optional[Dict[str, Any]]: Docker image details or None if failed
        """
        if agent_port is None:
            agent_port = self.default_port
            
        try:
            logger.debug(f"Querying Docker image details for {image_id} from: {agent_ip}:{agent_port}")
            
            url = f"http://{agent_ip}:{agent_port}/get_docker_image_details/{image_id}"
            response = requests.get(url, timeout=timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Agent {agent_ip}:{agent_port} returned status code {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout querying Docker image details from agent {agent_ip}:{agent_port}")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection failed to agent {agent_ip}:{agent_port}")
            return None
        except Exception as e:
            logger.error(f"Error querying Docker image details from agent {agent_ip}:{agent_port}: {e}")
            return None

    def query_multiple_agents_docker_images(self, server_list: List[str], port: int = None, 
                                          max_workers: int = 10, timeout_per_agent: int = 10) -> List[Dict[str, Any]]:
        """
        Query multiple servers for their Docker images concurrently.
        
        Args:
            server_list: List of server IP addresses
            port: Port to use for all servers
            max_workers: Maximum number of concurrent workers
            timeout_per_agent: Timeout per agent in seconds
            
        Returns:
            List[Dict[str, Any]]: List of Docker images information from available agents
        """
        if port is None:
            port = self.default_port
            
        if not server_list:
            logger.warning("No servers provided to query for Docker images")
            return []

        logger.debug(f"Querying Docker images from {len(server_list)} agents concurrently")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_server = {
                executor.submit(self.query_agent_docker_images, server_ip, port, timeout_per_agent): server_ip 
                for server_ip in server_list
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_server):
                server_ip = future_to_server[future]
                try:
                    result = future.result(timeout=timeout_per_agent + 1)
                    if result:
                        result["server_id"] = server_ip
                        results.append(result)
                        logger.debug(f"Successfully queried Docker images from agent {server_ip}")
                    else:
                        logger.debug(f"Agent {server_ip} Docker images not available")
                except Exception as e:
                    logger.error(f"Error querying Docker images from agent {server_ip}: {e}")
        
        logger.info(f"Successfully queried Docker images from {len(results)} out of {len(server_list)} agents")
        return results


# Global instance for backward compatibility
agent_service = AgentService()

# Backward compatibility functions
def query_agent_resources(agent_ip: str, agent_port: int = 5000, timeout: int = 5) -> Optional[Dict[str, Any]]:
    """Backward compatibility wrapper."""
    return agent_service.query_agent_resources(agent_ip, agent_port, timeout)

def query_available_agents(server_list: List[str], port: int, max_workers: int = 10, timeout_per_agent: int = 5) -> List[Dict[str, Any]]:
    """Backward compatibility wrapper."""
    return agent_service.query_available_agents(server_list, port, max_workers, timeout_per_agent)

def query_agent_docker_images(agent_ip: str, agent_port: int = 5000, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Backward compatibility wrapper."""
    return agent_service.query_agent_docker_images(agent_ip, agent_port, timeout)

def query_agent_docker_image_details(agent_ip: str, image_id: str, agent_port: int = 5000, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """Backward compatibility wrapper."""
    return agent_service.query_agent_docker_image_details(agent_ip, image_id, agent_port, timeout)

def query_multiple_agents_docker_images(server_list: List[str], port: int = 5000, max_workers: int = 10, timeout_per_agent: int = 10) -> List[Dict[str, Any]]:
    """Backward compatibility wrapper."""
    return agent_service.query_multiple_agents_docker_images(server_list, port, max_workers, timeout_per_agent)
