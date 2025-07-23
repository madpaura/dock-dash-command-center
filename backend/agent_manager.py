"""
Backward compatibility wrapper for agent_manager.py
This file now imports from the new services architecture while maintaining the same API.
"""

# Import from the new services architecture
from services.agent_service import (
    query_agent_resources,
    query_available_agents,
    query_agent_docker_images,
    query_agent_docker_image_details,
    query_multiple_agents_docker_images
)

# Re-export all functions for backward compatibility
__all__ = [
    'query_agent_resources',
    'query_available_agents', 
    'query_agent_docker_images',
    'query_agent_docker_image_details',
    'query_multiple_agents_docker_images'
]

# Note: All functionality has been moved to services/agent_service.py
# This file exists only for backward compatibility with existing imports
