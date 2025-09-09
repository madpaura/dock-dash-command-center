"""Authentication helper functions for API endpoints."""

from flask import request, jsonify


def require_admin_auth():
    """Helper function for admin authentication in traffic routes."""
    from services.auth_service import AuthService
    from database import UserDatabase
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, jsonify({'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    
    # Initialize auth service
    db = UserDatabase()
    auth_service = AuthService(db)
    
    session = auth_service.validate_session(token)
    if not session:
        return None, jsonify({'error': 'Invalid session'}), 401
    
    if not session.get('is_admin'):
        return None, jsonify({'error': 'Admin access required'}), 403
    
    return session, None, None
