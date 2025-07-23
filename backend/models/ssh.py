"""
SSH session-related data models and schemas.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
import queue


@dataclass
class SSHConnectionInfo:
    """Data class for SSH connection information."""
    session_id: str
    host: str
    port: int
    username: str
    password: Optional[str] = None
    key_path: Optional[str] = None


@dataclass
class SSHSessionStatus:
    """Data class for SSH session status."""
    session_id: str
    connected: bool
    host: str
    port: int
    username: str
    created_at: Optional[str] = None
    last_activity: Optional[str] = None


@dataclass
class SSHCommandRequest:
    """Data class for SSH command execution request."""
    session_id: str
    command: str
    timeout: Optional[int] = None


@dataclass
class SSHCommandResponse:
    """Data class for SSH command execution response."""
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: Optional[int] = None


@dataclass
class SSHConnectRequest:
    """Data class for SSH connection request."""
    server_id: str
    username: str
    password: Optional[str] = None
    key_path: Optional[str] = None
    port: int = 22
