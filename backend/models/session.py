"""
Session-related data models and schemas.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class SessionData:
    """Data class for session information."""
    session_id: str
    user_id: int
    username: str
    token: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    ip_address: Optional[str] = None


@dataclass
class LoginRequest:
    """Data class for login request."""
    email: str
    password: str
    ip_address: Optional[str] = None


@dataclass
class LoginResponse:
    """Data class for login response."""
    success: bool
    message: str
    token: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None


@dataclass
class RegisterRequest:
    """Data class for user registration request."""
    username: str
    email: str
    password: str
    ip_address: Optional[str] = None
