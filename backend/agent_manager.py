import socket
import json
from loguru import logger
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def query_agent_resources(agent_ip, agent_port=5000, timeout=5):
    """
    Query a single agent for its resource information.
    Optimized with shorter timeout for faster failure detection.
    """
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

def query_single_agent_with_id(agent_ip, port):
    """
    Helper function to query a single agent and return with server_id.
    """
    resources = query_agent_resources(agent_ip, agent_port=port)
    if resources:
        resources["server_id"] = agent_ip
        return resources
    return None

def query_available_agents(server_list, port, max_workers=10, timeout_per_agent=5):
    """
    Query multiple servers for their resource information concurrently.
    Optimized for speed with parallel processing and shorter timeouts.
    """
    if not server_list:
        return []
    
    start_time = time.time()
    servers_resources = []
    
    # Use ThreadPoolExecutor for concurrent requests
    with ThreadPoolExecutor(max_workers=min(max_workers, len(server_list))) as executor:
        # Submit all requests concurrently
        future_to_agent = {
            executor.submit(query_single_agent_with_id, agent, port): agent 
            for agent in server_list
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_agent, timeout=timeout_per_agent * 2):
            agent = future_to_agent[future]
            try:
                result = future.result(timeout=timeout_per_agent)
                if result:
                    servers_resources.append(result)
            except Exception as e:
                logger.warning(f"Failed to get result for agent {agent}: {e}")
    
    elapsed_time = time.time() - start_time
    logger.info(f"Queried {len(server_list)} agents in {elapsed_time:.2f}s, {len(servers_resources)} responded")
    
    return servers_resources


def query_agent_docker_images(agent_ip, agent_port=5000, timeout=10):
    """
    Query a single agent for its Docker images information.
    """
    try:
        logger.debug(f"Querying Docker images from: {agent_ip}:{agent_port}")
        
        url = f"http://{agent_ip}:{agent_port}/get_docker_images"
        
        # Use longer timeout for Docker images as it can be slower
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            data["server_id"] = agent_ip
            return data
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

def query_agent_docker_image_details(agent_ip, image_id, agent_port=5000, timeout=10):
    """
    Query a single agent for detailed information about a specific Docker image.
    """
    try:
        logger.debug(f"Querying Docker image details from: {agent_ip}:{agent_port} for image {image_id}")
        
        url = f"http://{agent_ip}:{agent_port}/get_docker_image_details/{image_id}"
        
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            data["server_id"] = agent_ip
            return data
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

def query_multiple_agents_docker_images(server_list, port=5000, max_workers=10, timeout_per_agent=10):
    """
    Query multiple servers for their Docker images concurrently.
    """
    if not server_list:
        return []
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all queries
        future_to_server = {
            executor.submit(query_agent_docker_images, server, port, timeout_per_agent): server 
            for server in server_list
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_server):
            server = future_to_server[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
                else:
                    logger.debug(f"No Docker images data from server {server}")
            except Exception as e:
                logger.error(f"Exception querying Docker images from server {server}: {e}")
    
    return results

# if __name__ == "__main__":
#     servers = ["0.0.0.0", "0.0.0.0", "0.0.0.0"]
#     print(query_available_agents(servers))
