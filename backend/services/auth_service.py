from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import request
from loguru import logger

from database import UserDatabase
from models.session import SessionData, LoginRequest, LoginResponse, RegisterRequest
from utils.helpers import generate_session_token, hash_password, get_client_ip
from utils.validators import is_valid_email, is_valid_password, is_valid_username
from utils.permissions import get_role_from_user, get_user_permissions


class AuthService:
    
    def __init__(self, db: UserDatabase):
        self.db = db
    
    def get_admin_username_from_token(self) -> str:
        admin_username = 'admin'  # Default fallback
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                session = self.db.verify_session(token)
                if session and session.get('username'):
                    admin_username = session['username']
        except:
            pass  # Use default fallback
        return admin_username
    
    def login(self, email: str, password: str, ip_address: str = None) -> Dict[str, Any]:
        try:
            user = self.db.verify_login(email, password)

            if user and user["is_approved"]:
                session_token = generate_session_token()
                expires_at = datetime.now() + timedelta(hours=24)
                
                if self.db.create_session(user["id"], session_token, expires_at):
                    self.db.log_audit_event(
                        user["username"],
                        'login',
                        {'message': f'User {user["username"]} logged in successfully', 'email': email},
                        ip_address
                    )
                    
                    # Determine role from user_type (with backward compatibility)
                    role = get_role_from_user(user)
                    permissions = get_user_permissions(user.get('user_type', 'regular'))
                    
                    return LoginResponse(
                        success=True,
                        message="Login successful",
                        token=session_token,
                        user_id=user["id"],
                        username=user["username"],
                        role=role,
                        user_type=user.get('user_type', 'admin' if user['is_admin'] else 'regular'),
                        permissions=permissions
                    )
            
            self.db.log_audit_event(
                email if email else 'Unknown',
                'login_failed',
                {'message': f'Failed login attempt for email: {email}', 'reason': 'Invalid credentials or account not approved'},
                ip_address
            )
            
            return LoginResponse(
                success=False,
                message="Invalid credentials or account not approved"
            )
            
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return LoginResponse(
                success=False,
                message="Login failed due to server error"
            )
    
    def logout(self, token: str, ip_address: str = None) -> Dict[str, Any]:
        try:
            session = self.db.verify_session(token)
            username = session.get('username', 'Unknown') if session else 'Unknown'
            
            success = self.db.remove_session(token)
            
            if success:
                self.db.log_audit_event(
                    username,
                    'logout',
                    {'message': f'User {username} logged out successfully'},
                    ip_address
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return False
    
    def register(self, username: str, password: str, email: str, ip_address: str = None) -> Dict[str, Any]:
        try:
            if not is_valid_username(username):
                return {'success': False, 'error': 'Invalid username format'}
            
            if not is_valid_email(email):
                return {'success': False, 'error': 'Invalid email format'}
            
            if not is_valid_password(password):
                return {'success': False, 'error': 'Password must be at least 6 characters long'}
            
            if self.db.get_user_by_email(email):
                return {'success': False, 'error': 'User with this email already exists'}
            
            hashed_password = hash_password(password)
            user_id = self.db.create_user(username, email, hashed_password)
            
            if user_id:
                self.db.log_audit_event(
                    username,
                    'register',
                    {'message': f'New user {username} registered successfully', 'email': email},
                    ip_address
                )
                
                return {
                    'success': True,
                    'message': 'Registration successful. Please wait for admin approval.',
                    'user_id': user_id
                }
            else:
                return {'success': False, 'error': 'Failed to create user'}
                
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            self.db.log_audit_event(
                username if username else 'Unknown',
                'register_failed',
                {'message': f'Failed registration attempt', 'email': email, 'error': str(e)},
                ip_address
            )
            return {'success': False, 'error': 'Registration failed due to server error'}
    
    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            return self.db.verify_session(token)
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None
    
    def invalidate_session_by_token(self, token: str) -> bool:
        """
        Invalidate session by token.
        
        Args:
            token: Session token
            
        Returns:
            bool: True if successful
        """
        try:
            session = self.db.verify_session(token)
            self.db.remove_session(token)
            return True
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
            return False
