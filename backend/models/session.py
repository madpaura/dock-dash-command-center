
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class SessionData:
    
    session_id: str
    user_id: int
    username: str
    token: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    ip_address: Optional[str] = None


@dataclass
class LoginRequest:
    
    email: str
    password: str
    ip_address: Optional[str] = None


@dataclass
class LoginResponse:
    
    success: bool
    message: str
    token: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None
    user_type: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None


@dataclass
class RegisterRequest:
    
    username: str
    email: str
    password: str
    ip_address: Optional[str] = None
