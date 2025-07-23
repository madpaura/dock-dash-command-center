"""
Helper utility functions.
"""
import secrets
import hashlib
import os
from typing import List, Optional
from loguru import logger


def generate_session_token() -> str:
    """
    Generate a secure session token.
    
    Returns:
        str: Secure random token
    """
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()


def read_agents_file(agents_file: str = "agents.txt") -> List[str]:
    """
    Read agents from file.
    
    Args:
        agents_file: Path to agents file
        
    Returns:
        List[str]: List of agent IP addresses
    """
    if not os.path.exists(agents_file):
        return []
    
    try:
        with open(agents_file, 'r') as file:
            agents = file.read().splitlines()
            return [agent.strip() for agent in agents if agent.strip()]
    except Exception as e:
        logger.error(f"Error reading agents file {agents_file}: {e}")
        return []


def write_agents_file(agents: List[str], agents_file: str = "agents.txt") -> bool:
    """
    Write agents to file.
    
    Args:
        agents: List of agent IP addresses
        agents_file: Path to agents file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(agents_file, 'w') as file:
            file.write('\n'.join(agents))
        return True
    except Exception as e:
        logger.error(f"Error writing agents file {agents_file}: {e}")
        return False


def get_client_ip(request) -> Optional[str]:
    """
    Extract client IP address from Flask request.
    
    Args:
        request: Flask request object
        
    Returns:
        Optional[str]: Client IP address
    """
    # Check for forwarded headers first
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes into human readable format.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        str: Formatted string (e.g., "1.5 GB")
    """
    if bytes_value == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while bytes_value >= 1024 and i < len(size_names) - 1:
        bytes_value /= 1024.0
        i += 1
    
    return f"{bytes_value:.1f} {size_names[i]}"


def safe_json_loads(json_str: str, default=None):
    """
    Safely load JSON string with fallback.
    
    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default value
    """
    try:
        import json
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        str: Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix
