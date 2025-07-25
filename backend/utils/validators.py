
import ipaddress
import re
from typing import Optional


def is_valid_ip(ip: str) -> bool:
    
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_valid_email(email: str) -> bool:
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_port(port: int) -> bool:
    
    return 1 <= port <= 65535


def is_valid_username(username: str) -> bool:
    
    if not username or len(username) < 3 or len(username) > 50:
        return False
    
    # Username should contain only alphanumeric characters, underscores, and hyphens
    pattern = r'^[a-zA-Z0-9_-]+$'
    return re.match(pattern, username) is not None


def is_valid_password(password: str) -> bool:
    
    if not password or len(password) < 3:
        return False
    
    return True


def sanitize_string(input_str: str, max_length: Optional[int] = None) -> str:
    
    if not input_str:
        return ""
    
    # Remove null bytes and control characters
    sanitized = input_str.replace('\x00', '').strip()
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized
