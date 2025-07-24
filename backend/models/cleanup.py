
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class CleanupSummaryRequest:
    
    server_ip: str
    username: str
    password: str
    ssh_port: int = 22


@dataclass
class ContainerInfo:
    
    id: str
    image: str
    command: str
    created: str
    status: str
    ports: str
    names: str


@dataclass
class ImageInfo:
    
    repository: str
    tag: str
    id: str
    created: str
    size: str


@dataclass
class DiskUsageInfo:
    
    opt_usage: str
    docker_system_df: str
    docker_system_df_verbose: str
    root_disk_usage: str
    docker_root_dir: str
    docker_root_usage: str
    total_used_gb: float


@dataclass
class CleanupSummary:
    """Cleanup summary model."""
    success: bool
    server_ip: str
    containers: Dict[str, Any]
    disk_usage: DiskUsageInfo
    docker_images: Dict[str, Any]
    summary: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class CleanupOptions:
    
    remove_stopped_containers: bool = False
    remove_dangling_images: bool = False
    remove_unused_volumes: bool = False
    remove_unused_networks: bool = False
    docker_system_prune: bool = False
    remove_specific_containers: Optional[List[str]] = None
    remove_specific_images: Optional[List[str]] = None


@dataclass
class CleanupExecutionRequest:
    
    server_ip: str
    username: str
    password: str
    cleanup_options: CleanupOptions
    ssh_port: int = 22


@dataclass
class CleanupResult:
    
    operation: str
    success: bool
    output: str
    error: Optional[str] = None
    containers: Optional[List[str]] = None
    images: Optional[List[str]] = None


@dataclass
class CleanupExecutionResponse:
    
    success: bool
    server_ip: str
    results: List[CleanupResult]
    summary: str
    error: Optional[str] = None
