"""API routes for guest OS upload management."""

from flask import Blueprint, request, jsonify
from services.upload_service import UploadService
from database import UserDatabase
from utils.permissions import check_permission_for_session

upload_bp = Blueprint('upload', __name__)
db = UserDatabase()
upload_service = UploadService()


def get_auth_info():
    """Get authentication info from request."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    return token, ip_address


# ==================== Upload Server Routes ====================

@upload_bp.route('/api/admin/upload-servers', methods=['GET'])
def get_upload_servers():
    """Get all upload servers."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_upload_servers')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    result = upload_service.get_all_servers(include_inactive)
    
    return jsonify(result), 200 if result['success'] else 500


@upload_bp.route('/api/admin/upload-servers/<int:server_id>', methods=['GET'])
def get_upload_server(server_id):
    """Get a specific upload server."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_upload_servers')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    result = upload_service.get_server(server_id)
    
    return jsonify(result), 200 if result['success'] else 404


@upload_bp.route('/api/admin/upload-servers', methods=['POST'])
def create_upload_server():
    """Create a new upload server."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'manage_upload_servers')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    required_fields = ['name', 'ip_address', 'base_path']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    result = upload_service.create_server(
        data,
        admin_username=session.get('username', 'Admin'),
        user_id=session.get('user_id'),
        ip_address=ip_address
    )
    
    return jsonify(result), 201 if result['success'] else 400


@upload_bp.route('/api/admin/upload-servers/<int:server_id>', methods=['PUT'])
def update_upload_server(server_id):
    """Update an upload server."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'manage_upload_servers')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    result = upload_service.update_server(
        server_id,
        data,
        admin_username=session.get('username', 'Admin'),
        ip_address=ip_address
    )
    
    return jsonify(result), 200 if result['success'] else 400


@upload_bp.route('/api/admin/upload-servers/<int:server_id>', methods=['DELETE'])
def delete_upload_server(server_id):
    """Delete an upload server."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'manage_upload_servers')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    result = upload_service.delete_server(
        server_id,
        admin_username=session.get('username', 'Admin'),
        ip_address=ip_address
    )
    
    return jsonify(result), 200 if result['success'] else 400


@upload_bp.route('/api/admin/upload-servers/<int:server_id>/test', methods=['POST'])
def test_upload_server_connection(server_id):
    """Test connection to an upload server."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_upload_servers')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    result = upload_service.test_connection(server_id)
    
    return jsonify(result), 200 if result['success'] else 400


# ==================== File Browser Routes ====================

@upload_bp.route('/api/admin/upload-servers/<int:server_id>/browse', methods=['GET'])
def browse_files(server_id):
    """Browse files and folders on an upload server."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_upload_servers')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    path = request.args.get('path', '')
    result = upload_service.browse_files(server_id, path)
    
    return jsonify(result), 200 if result['success'] else 400


@upload_bp.route('/api/admin/upload-servers/<int:server_id>/files', methods=['DELETE'])
def delete_file(server_id):
    """Delete a file or folder on the server."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'manage_upload_servers')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    data = request.get_json()
    if not data or not data.get('path'):
        return jsonify({'success': False, 'error': 'File path is required'}), 400
    
    result = upload_service.delete_file(
        server_id,
        data['path'],
        admin_username=session.get('username', 'Admin'),
        ip_address=ip_address
    )
    
    return jsonify(result), 200 if result['success'] else 400


# ==================== Version Routes ====================

@upload_bp.route('/api/admin/upload-servers/<int:server_id>/versions', methods=['GET'])
def get_versions(server_id):
    """Get version.json content from server."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_upload_servers')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    result = upload_service.get_versions(server_id)
    
    return jsonify(result), 200 if result['success'] else 400


@upload_bp.route('/api/admin/upload-servers/<int:server_id>/versions/<image_name>/next', methods=['GET'])
def get_next_version(server_id, image_name):
    """Get the next version number for an image."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_upload_servers')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    result = upload_service.get_next_version(server_id, image_name)
    
    return jsonify(result), 200 if result['success'] else 400


# ==================== Upload Routes ====================

@upload_bp.route('/api/admin/upload-servers/<int:server_id>/upload', methods=['POST'])
def upload_file(server_id):
    """Upload a guest OS image file."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'upload_guest_os')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Get form data
    image_name = request.form.get('image_name')
    version = request.form.get('version')
    changelog = request.form.get('changelog')
    
    if not image_name:
        return jsonify({'success': False, 'error': 'Image name is required'}), 400
    if not version:
        return jsonify({'success': False, 'error': 'Version is required'}), 400
    
    # Read file data
    file_data = file.read()
    
    result = upload_service.upload_file(
        server_id,
        file_data,
        file.filename,
        image_name,
        version,
        changelog,
        user_id=session.get('user_id'),
        admin_username=session.get('username', 'Admin'),
        ip_address=ip_address
    )
    
    return jsonify(result), 200 if result['success'] else 400


@upload_bp.route('/api/admin/upload-servers/<int:server_id>/uploads', methods=['GET'])
def get_upload_history(server_id):
    """Get upload history for a server."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_upload_servers')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    limit = request.args.get('limit', 50, type=int)
    result = upload_service.get_upload_history(server_id, limit)
    
    return jsonify(result), 200 if result['success'] else 400
