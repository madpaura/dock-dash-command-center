
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class ServerInfo:
    
    server_id: str
    ip_address: str
    port: int
    status: str  # online, offline, maintenance
    last_seen: Optional[datetime] = None
    server_type: Optional[str] = None


@dataclass
class ServerResources:
    
    server_id: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    uptime: str
    running_containers: int
    total_containers: int
    cpu_cores: Optional[int] = None
    memory_total: Optional[float] = None
    disk_total: Optional[float] = None
    architecture: Optional[str] = None
    os_info: Optional[str] = None


@dataclass
class ServerStats:
    
    total_servers: int
    online_servers: int
    offline_servers: int
    maintenance_servers: int
    total_containers: int
    total_cpu_usage: float
    total_memory_usage: float
    total_disk_usage: float


@dataclass
class AgentInfo:
    
    ip_address: str
    port: int
    status: str
    last_contact: Optional[datetime] = None
    version: Optional[str] = None


@dataclass
class ServerActionRequest:
    
    action: str  # start, stop, restart, maintenance, remove
    server_id: str
    user_id: Optional[int] = None
    additional_params: Optional[Dict[str, Any]] = None


@dataclass
class AddServerRequest:
    
    ip_address: str
    port: int = 5000
    server_type: Optional[str] = None
    description: Optional[str] = None
