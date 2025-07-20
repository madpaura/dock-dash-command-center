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


# if __name__ == "__main__":
#     servers = ["0.0.0.0", "0.0.0.0", "0.0.0.0"]
#     print(query_available_agents(servers))
