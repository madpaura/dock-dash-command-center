import socket
import json
from loguru import logger
import requests

def query_agent_resources(agent_ip, agent_port=5000, timeout=30):
    """
    Query a single agent for its resource information.
    """
    try:
        logger.info(f"Querying resources from : {agent_ip} : {agent_port}")

        url = f"http://{agent_ip}:{agent_port}/get_resources"

        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Agent {agent_ip}:{agent_port} returned status code {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error querying agent {agent_ip}:{agent_port}: {e}")
        return None

def query_available_agents(server_list, port):
    """
    Query multiple servers for their resource information.
    """
    servers_resources = []
    for agent in server_list:
        resources = query_agent_resources(agent, agent_port=port)
        if resources:
            resources["server_id"] = agent
            servers_resources.append(resources)
    return servers_resources


# if __name__ == "__main__":
#     servers = ["0.0.0.0", "0.0.0.0", "0.0.0.0"]
#     print(query_available_agents(servers))
