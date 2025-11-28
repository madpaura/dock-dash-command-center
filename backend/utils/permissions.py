"""
Permission definitions and helpers for role-based access control.
Supports three user types: regular, qvp (restricted admin), and admin (full access).
"""

from typing import Dict, Any
from functools import wraps
from flask import request, jsonify
from loguru import logger


# Permission definitions for each user type
PERMISSIONS = {
    'admin': {
        'view_dashboard': True,
        'view_servers': True,
        'view_containers': True,
        'view_images': True,
        'view_logs': True,
        'view_traffic': True,
        'manage_users': True,
        'add_server': True,
        'delete_server': True,
        'delete_image': True,
        'cleanup_server': True,
        'approve_user': True,
        'delete_user': True,
        'create_user': True,
        'update_user': True,
        'reset_password': True,
        # Docker build & registry permissions
        'view_registries': True,
        'manage_registries': True,
        'view_projects': True,
        'manage_projects': True,
        'build_images': True,
        'push_images': True,
    },
    'qvp': {
        'view_dashboard': True,
        'view_servers': True,
        'view_containers': True,
        'view_images': True,
        'view_logs': True,
        'view_traffic': True,
        'manage_users': False,      # No user management panel
        'add_server': False,        # No server addition
        'delete_server': False,     # No server deletion
        'delete_image': False,      # No image deletion
        'cleanup_server': False,    # No cleanup operations
        'approve_user': False,      # No user approval
        'delete_user': False,       # No user deletion
        'create_user': False,       # No user creation
        'update_user': False,       # No user updates
        'reset_password': False,    # No password reset
        # Docker build & registry permissions - QVP has FULL access
        'view_registries': True,
        'manage_registries': True,
        'view_projects': True,
        'manage_projects': True,
        'build_images': True,
        'push_images': True,
    },
    'regular': {
        'view_dashboard': False,
        'view_servers': False,
        'view_containers': False,
        'view_images': False,
        'view_logs': False,
        'view_traffic': False,
        'manage_users': False,
        'add_server': False,
        'delete_server': False,
        'delete_image': False,
        'cleanup_server': False,
        'approve_user': False,
        'delete_user': False,
        'create_user': False,
        'update_user': False,
        'reset_password': False,
        # Docker build & registry permissions
        'view_registries': False,
        'manage_registries': False,
        'view_projects': False,
        'manage_projects': False,
        'build_images': False,
        'push_images': False,
    }
}


def get_user_permissions(user_type: str) -> Dict[str, bool]:
    """
    Get permissions for a given user type.
    
    Args:
        user_type: One of 'admin', 'qvp', or 'regular'
        
    Returns:
        Dictionary of permission flags
    """
    return PERMISSIONS.get(user_type, PERMISSIONS['regular']).copy()


def has_permission(user_type: str, permission: str) -> bool:
    """
    Check if a user type has a specific permission.
    
    Args:
        user_type: One of 'admin', 'qvp', or 'regular'
        permission: The permission to check
        
    Returns:
        True if the user has the permission, False otherwise
    """
    permissions = PERMISSIONS.get(user_type, PERMISSIONS['regular'])
    return permissions.get(permission, False)


def get_role_from_user(user: Dict[str, Any]) -> str:
    """
    Determine the role/user_type from a user record.
    Handles backward compatibility with is_admin field.
    
    Args:
        user: User dictionary from database
        
    Returns:
        Role string: 'admin', 'qvp', or 'user'
    """
    # First check user_type field (new system)
    user_type = user.get('user_type')
    if user_type:
        if user_type == 'admin':
            return 'admin'
        elif user_type == 'qvp':
            return 'qvp'
        else:
            return 'user'
    
    # Fallback to is_admin for backward compatibility
    if user.get('is_admin'):
        return 'admin'
    
    return 'user'


def require_permission(permission: str):
    """
    Decorator to require a specific permission for an endpoint.
    Must be used after authentication middleware that sets user info.
    
    Args:
        permission: The permission required to access the endpoint
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user from request context (set by auth middleware)
            user = getattr(request, 'current_user', None)
            
            if not user:
                return jsonify({
                    'success': False, 
                    'error': 'Authentication required'
                }), 401
            
            user_type = get_role_from_user(user)
            
            if not has_permission(user_type, permission):
                logger.warning(
                    f"Permission denied: User {user.get('username')} (type: {user_type}) "
                    f"attempted to access endpoint requiring '{permission}'"
                )
                return jsonify({
                    'success': False,
                    'error': f'Permission denied. This action requires {permission} permission.'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_permission_for_session(db, token: str, permission: str) -> tuple:
    """
    Check if a session token has a specific permission.
    
    Args:
        db: Database instance
        token: Session token
        permission: Permission to check
        
    Returns:
        Tuple of (has_permission: bool, user: dict or None, error_message: str or None)
    """
    session = db.verify_session(token)
    
    if not session:
        return False, None, 'Invalid or expired session'
    
    user_type = session.get('user_type', 'regular')
    # Handle backward compatibility
    if not user_type or user_type == 'regular':
        if session.get('is_admin'):
            user_type = 'admin'
    
    if not has_permission(user_type, permission):
        return False, session, f'Permission denied. This action requires {permission} permission.'
    
    return True, session, None
