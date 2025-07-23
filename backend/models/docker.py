"""
Docker-related data models and schemas.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class DockerImage:
    """Data class for Docker image information."""
    id: str
    short_id: str
    repository: str
    tag: str
    size: int
    virtual_size: int
    created: str
    architecture: Optional[str] = None
    os: Optional[str] = None
    parent: Optional[str] = None
    comment: Optional[str] = None
    author: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


@dataclass
class DockerImageLayer:
    """Data class for Docker image layer information."""
    id: str
    size: int
    created: str
    created_by: str


@dataclass
class DockerImageHistory:
    """Data class for Docker image history information."""
    id: str
    created: str
    created_by: str
    size: int
    comment: Optional[str] = None


@dataclass
class DockerImagesResponse:
    """Data class for Docker images response."""
    success: bool
    server_id: str
    images: List[DockerImage]
    total_images: int
    total_size: int
    error: Optional[str] = None


@dataclass
class DockerImageDetailsResponse:
    """Data class for Docker image details response."""
    success: bool
    server_id: str
    image_id: str
    image: Optional[DockerImage] = None
    layers: Optional[List[DockerImageLayer]] = None
    history: Optional[List[DockerImageHistory]] = None
    error: Optional[str] = None


@dataclass
class DockerImagesRequest:
    """Data class for Docker images request."""
    server_id: Optional[str] = None  # If None, query all servers
    include_details: bool = False
