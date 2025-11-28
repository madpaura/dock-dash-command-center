"""API routes for Docker registry management."""

from flask import Blueprint, request, jsonify
from services.registry_service import RegistryService
from database import UserDatabase
from utils.permissions import check_permission_for_session

registry_bp = Blueprint('registry', __name__)
registry_service = RegistryService()
db = UserDatabase()


def get_auth_info():
    """Extract authentication info from request."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    return token, ip_address


@registry_bp.route('/api/admin/registries', methods=['GET'])
def get_registries():
    """Get all registry servers."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_registries')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    result = registry_service.get_all_registries(include_inactive)
    
    return jsonify(result), 200 if result['success'] else 500


@registry_bp.route('/api/admin/registries/<int:registry_id>', methods=['GET'])
def get_registry(registry_id):
    """Get a specific registry server."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_registries')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    result = registry_service.get_registry(registry_id)
    
    return jsonify(result), 200 if result['success'] else 404


@registry_bp.route('/api/admin/registries', methods=['POST'])
def create_registry():
    """Create a new registry server."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'manage_registries')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    # Add created_by from session
    data['created_by'] = session.get('user_id')
    
    result = registry_service.create_registry(
        data,
        admin_username=session.get('username', 'Admin'),
        ip_address=ip_address
    )
    
    return jsonify(result), 201 if result['success'] else 400


@registry_bp.route('/api/admin/registries/<int:registry_id>', methods=['PUT'])
def update_registry(registry_id):
    """Update a registry server."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'manage_registries')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    result = registry_service.update_registry(
        registry_id,
        data,
        admin_username=session.get('username', 'Admin'),
        ip_address=ip_address
    )
    
    return jsonify(result), 200 if result['success'] else 400


@registry_bp.route('/api/admin/registries/<int:registry_id>', methods=['DELETE'])
def delete_registry(registry_id):
    """Delete a registry server."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'manage_registries')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    result = registry_service.delete_registry(
        registry_id,
        admin_username=session.get('username', 'Admin'),
        ip_address=ip_address
    )
    
    return jsonify(result), 200 if result['success'] else 400


@registry_bp.route('/api/admin/registries/<int:registry_id>/images', methods=['GET'])
def get_registry_images(registry_id):
    """Get images from a registry."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_registries')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    result = registry_service.get_registry_images(registry_id)
    
    return jsonify(result), 200 if result['success'] else 400


@registry_bp.route('/api/admin/registries/<int:registry_id>/images/<path:image_name>/tags', methods=['GET'])
def get_image_tags(registry_id, image_name):
    """Get tags for an image in a registry."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_registries')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    result = registry_service.get_image_tags(registry_id, image_name)
    
    return jsonify(result), 200 if result['success'] else 400


@registry_bp.route('/api/admin/registries/<int:registry_id>/test', methods=['POST'])
def test_registry_connection(registry_id):
    """Test connection to a registry."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_registries')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    result = registry_service.test_connection(registry_id)
    
    return jsonify(result), 200 if result['success'] else 400
