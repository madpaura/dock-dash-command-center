"""
Validation utilities for input validation.
"""
import ipaddress
import re
from typing import Optional


def is_valid_ip(ip: str) -> bool:
    """
    Validate if the given string is a valid IP address.
    
    Args:
        ip: IP address string to validate
        
    Returns:
        bool: True if valid IP address, False otherwise
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_valid_email(email: str) -> bool:
    """
    Validate if the given string is a valid email address.
    
    Args:
        email: Email address string to validate
        
    Returns:
        bool: True if valid email address, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_port(port: int) -> bool:
    """
    Validate if the given port number is valid.
    
    Args:
        port: Port number to validate
        
    Returns:
        bool: True if valid port number, False otherwise
    """
    return 1 <= port <= 65535


def is_valid_username(username: str) -> bool:
    """
    Validate if the given username is valid.
    
    Args:
        username: Username string to validate
        
    Returns:
        bool: True if valid username, False otherwise
    """
    if not username or len(username) < 3 or len(username) > 50:
        return False
    
    # Username should contain only alphanumeric characters, underscores, and hyphens
    pattern = r'^[a-zA-Z0-9_-]+$'
    return re.match(pattern, username) is not None


def is_valid_password(password: str) -> bool:
    """
    Validate if the given password meets security requirements.
    
    Args:
        password: Password string to validate
        
    Returns:
        bool: True if valid password, False otherwise
    """
    if not password or len(password) < 6:
        return False
    
    return True


def sanitize_string(input_str: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize input string by removing potentially harmful characters.
    
    Args:
        input_str: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized string
    """
    if not input_str:
        return ""
    
    # Remove null bytes and control characters
    sanitized = input_str.replace('\x00', '').strip()
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized
