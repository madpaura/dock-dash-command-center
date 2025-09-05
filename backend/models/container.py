from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class ContainerInfo:
    """Detailed container information for management interface"""
    id: str
    name: str
    image: str
    status: str
    state: str
    created: str
    started: str
    finished: Optional[str]
    uptime: str
    cpu_usage: float
    memory_usage: float
    memory_used_mb: float
    memory_limit_mb: float
    disk_usage: Optional[float]
    network_rx_bytes: int
    network_tx_bytes: int
    ports: List[Dict[str, Any]]
    volumes: List[Dict[str, str]]
    environment: List[str]
    command: str
    labels: Dict[str, str]
    restart_count: int
    platform: str
    
@dataclass
class ContainerAction:
    """Container action request"""
    action: str  # 'start', 'stop', 'restart', 'delete'
    container_id: str
    force: bool = False

@dataclass
class ContainerListRequest:
    """Request for listing containers"""
    server_id: str
    include_stopped: bool = True
    search_term: Optional[str] = None

@dataclass
class ContainerListResponse:
    """Response for container listing"""
    success: bool
    server_id: str
    server_ip: str
    containers: List[ContainerInfo]
    total_count: int
    running_count: int
    stopped_count: int
    error: Optional[str] = None

@dataclass
class ContainerActionResponse:
    """Response for container actions"""
    success: bool
    action: str
    container_id: str
    container_name: str
    message: str
    new_status: Optional[str] = None
    error: Optional[str] = None
