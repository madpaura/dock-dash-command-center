import psutil
import docker
from docker.errors import DockerException
from loguru import logger
import toml
import os
from dotenv import load_dotenv
from flask import jsonify, request
import schedule
import time
import socket
import requests
import os, sys
from loguru import logger
from dotenv import load_dotenv
import atexit

load_dotenv(".env", override=True)

def get_machine_ip():
    """
    Get both local and public IP addresses of the machine.
    Returns a tuple of (local_ip, public_ip)
    """
    # Get local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception as e:
        local_ip = "Could not determine local IP: " + str(e)

    # Get public IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        public_ip = s.getsockname()[0]
        s.close()
    except Exception as e:
        public_ip = "Could not determine public IP: " + str(e)

    return local_ip, public_ip

def register_agent(url, agent):
    """Register the agent with the given URL and agent ID."""
    try:
        response = requests.post(f"{url}/api/register_agent", json={"agent": f"{agent}"})
        logger.info(response.json())
    except Exception as e:
        logger.error(e)

def unregister_agent(url, agent):
    """Unregister the agent with the given URL and agent ID."""
    try:
        response = requests.post(f"{url}/api/unregister_agent", json={"agent": f"{agent}"})
        logger.info(response.json())
    except Exception as e:
        logger.error(e)

def register_agent_with_manager():
    """Register the agent every 5 minutes."""
    load_dotenv("../.env", override=True)
    manager_ip = os.getenv("MGMT_SERVER_IP")
    manager_port = int(os.getenv("MGMT_SERVER_PORT")) + 1
    url = f"http://{manager_ip}:{manager_port}"
    localip, publicip = get_machine_ip()
    register_agent(url, localip)

def on_exit():
    load_dotenv("../.env", override=True)
    manager_ip = os.getenv("MGMT_SERVER_IP")
    manager_port = int(os.getenv("MGMT_SERVER_PORT")) + 1
    url = f"http://{manager_ip}:{manager_port}"    
    localip, publicip = get_machine_ip()
    unregister_agent(url, localip)

atexit.register(on_exit)

# Simple cache for agent resources
_resource_cache = {
    'data': None,
    'timestamp': 0,
    'cache_duration': 10  # Cache for 10 seconds
}

def get_agent_resources():
    """
    Fetch server resource information (CPU, memory, Docker instances, etc.).
    Optimized for better performance by reducing Docker API calls.
    """
    current_time = time.time()
    
    # Check if we have valid cached data
    if (_resource_cache['data'] is not None and 
        current_time - _resource_cache['timestamp'] < _resource_cache['cache_duration']):
        return _resource_cache['data']
    
    # Cache miss or expired, fetch fresh data
    # Get system resources first (these are fast)
    cpu_count = psutil.cpu_count()
    cpu_percent = psutil.cpu_percent(interval=0.1)  # Short interval for faster response
    memory_info = psutil.virtual_memory()
    total_memory = memory_info.total / (1024**3)

    # Get disk usage information
    disk_info = psutil.disk_usage('/')
    total_disk = disk_info.total / (1024**3)  # Convert to GB
    used_disk = disk_info.used / (1024**3)    # Convert to GB
    
    # Get system uptime
    uptime_seconds = time.time() - psutil.boot_time()
    uptime_days = uptime_seconds // (24 * 3600)
    uptime_hours = (uptime_seconds % (24 * 3600)) // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    uptime = f"{int(uptime_days)}d {int(uptime_hours)}h {int(uptime_minutes)}m"

    # Initialize Docker-related variables
    docker_instances = 0
    allocated_cpu = 0
    allocated_memory = 0
    running_containers = 0

    try:
        # Use Docker client with timeout for better performance
        client = docker.from_env(timeout=5)
        
        # Get only running containers (faster than all containers)
        containers = client.containers.list(filters={'status': 'running'})
        running_containers = len(containers)
        
        # Optimized container processing - avoid expensive API calls
        code_server_containers = [c for c in containers if "code-server" in c.name]
        docker_instances = len(code_server_containers)
        
        # Only inspect containers if we need detailed resource allocation
        # For basic monitoring, we can skip the expensive inspect calls
        if docker_instances > 0:
            # Use batch processing for better performance
            for container in code_server_containers:
                try:
                    # Get container info in one call (faster than separate stats + inspect)
                    container.reload()  # Refresh container info
                    attrs = container.attrs
                    host_config = attrs.get("HostConfig", {})
                    
                    # Extract resource limits (these are set at container creation)
                    cpu_limit = host_config.get("CpuCount", 0)
                    memory_limit = host_config.get("Memory", 0)
                    
                    if cpu_limit:
                        allocated_cpu += cpu_limit
                    if memory_limit:
                        allocated_memory += memory_limit / (1024**3)
                        
                except Exception as container_error:
                    logger.debug(f"Error processing container {container.name}: {container_error}")
                    continue

    except DockerException as e:
        logger.warning(f"Docker not available or error: {e}")
        docker_instances = 0
        allocated_cpu = 0
        allocated_memory = 0
        running_containers = 0
    except Exception as e:
        logger.error(f"Unexpected error fetching Docker stats: {e}")
        docker_instances = 0
        allocated_cpu = 0
        allocated_memory = 0
        running_containers = 0
        
    remaining_cpu = cpu_count - allocated_cpu
    remaining_memory = total_memory - allocated_memory

    # Prepare the response data
    resource_data = {
        "cpu_count": cpu_count,
        "total_memory": round(total_memory, 2),
        "host_cpu_used": cpu_percent,
        "host_memory_used": round(memory_info.used / (1024**3), 2),
        "total_disk": round(total_disk, 2),
        "used_disk": round(used_disk, 2),
        "uptime": uptime,
        "docker_instances": docker_instances,
        "running_containers": running_containers,  # Total running containers
        "allocated_cpu": allocated_cpu,
        "allocated_memory": round(allocated_memory, 2),
        "remaining_cpu": remaining_cpu,
        "remaining_memory": round(remaining_memory, 2),
    }
    
    # Update cache
    _resource_cache['data'] = resource_data
    _resource_cache['timestamp'] = current_time
    
    return resource_data

def get_docker_images():
    """
    Fetch Docker images information from the local Docker daemon.
    Returns detailed information about each image including layers and history.
    """
    try:
        # Initialize Docker client with timeout
        client = docker.from_env(timeout=5)
        
        # Get all images
        images = client.images.list()
        image_data = []
        
        for image in images:
            try:
                # Get image attributes
                attrs = image.attrs
                
                # Extract basic image information
                image_info = {
                    'id': image.id,
                    'short_id': image.short_id,
                    'tags': image.tags or ['<none>:<none>'],
                    'size': attrs.get('Size', 0),
                    'virtual_size': attrs.get('VirtualSize', 0),
                    'created': attrs.get('Created', ''),
                    'architecture': attrs.get('Architecture', 'unknown'),
                    'os': attrs.get('Os', 'unknown'),
                    'parent': attrs.get('Parent', ''),
                    'comment': attrs.get('Comment', ''),
                    'author': attrs.get('Author', ''),
                    'config': attrs.get('Config', {}),
                }
                
                # Extract repository and tag information
                if image.tags:
                    for tag in image.tags:
                        if ':' in tag:
                            repo, tag_name = tag.rsplit(':', 1)
                        else:
                            repo, tag_name = tag, 'latest'
                        
                        image_entry = image_info.copy()
                        image_entry.update({
                            'repository': repo,
                            'tag': tag_name,
                            'full_tag': tag
                        })
                        image_data.append(image_entry)
                else:
                    # Handle untagged images
                    image_entry = image_info.copy()
                    image_entry.update({
                        'repository': '<none>',
                        'tag': '<none>',
                        'full_tag': '<none>:<none>'
                    })
                    image_data.append(image_entry)
                    
            except Exception as e:
                logger.warning(f"Error processing image {image.id}: {e}")
                continue
        
        # Sort by creation date (newest first)
        image_data.sort(key=lambda x: x.get('created', ''), reverse=True)
        
        return {
            'images': image_data,
            'total_count': len(image_data),
            'total_size': sum(img.get('size', 0) for img in image_data),
            'timestamp': time.time()
        }
        
    except DockerException as e:
        logger.error(f"Docker daemon not available: {e}")
        return {
            'error': 'Docker daemon not available',
            'images': [],
            'total_count': 0,
            'total_size': 0,
            'timestamp': time.time()
        }
    except Exception as e:
        logger.error(f"Error fetching Docker images: {e}")
        return {
            'error': f'Error fetching Docker images: {str(e)}',
            'images': [],
            'total_count': 0,
            'total_size': 0,
            'timestamp': time.time()
        }

def get_docker_image_details(image_id):
    """
    Get detailed information about a specific Docker image including layers and history.
    """
    try:
        client = docker.from_env(timeout=5)
        
        # Get the specific image
        image = client.images.get(image_id)
        attrs = image.attrs
        
        # Extract layers information
        layers = []
        if 'RootFS' in attrs and 'Layers' in attrs['RootFS']:
            for i, layer_id in enumerate(attrs['RootFS']['Layers']):
                layers.append({
                    'id': layer_id,
                    'index': i,
                    'size': 'unknown'  # Layer size is not directly available
                })
        
        # Extract history information
        history = []
        if 'History' in attrs:
            for i, hist_entry in enumerate(attrs['History']):
                history.append({
                    'id': f"hist_{i}",
                    'created': hist_entry.get('Created', ''),
                    'created_by': hist_entry.get('CreatedBy', ''),
                    'size': hist_entry.get('Size', 0),
                    'comment': hist_entry.get('Comment', ''),
                    'empty_layer': hist_entry.get('EmptyLayer', False)
                })
        
        return {
            'image_id': image_id,
            'layers': layers,
            'history': history,
            'config': attrs.get('Config', {}),
            'architecture': attrs.get('Architecture', 'unknown'),
            'os': attrs.get('Os', 'unknown'),
            'timestamp': time.time()
        }
        
    except DockerException as e:
        logger.error(f"Docker daemon not available: {e}")
        return {'error': 'Docker daemon not available'}
    except Exception as e:
        logger.error(f"Error fetching image details for {image_id}: {e}")
        return {'error': f'Error fetching image details: {str(e)}'}

def init_stats_routes(app):
    @app.route('/get_resources', methods=['GET'])
    def get_resources():
        resources = get_agent_resources()
        return jsonify(resources)
    
    @app.route('/get_docker_images', methods=['GET'])
    def get_docker_images_route():
        """Get all Docker images from this agent"""
        images_data = get_docker_images()
        return jsonify(images_data)
    
    @app.route('/get_docker_image_details/<image_id>', methods=['GET'])
    def get_docker_image_details_route(image_id):
        """Get detailed information about a specific Docker image"""
        image_details = get_docker_image_details(image_id)
        return jsonify(image_details)
