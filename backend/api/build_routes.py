"""API routes for Docker image build operations."""

from flask import Blueprint, request, jsonify
from services.build_service import BuildService
from database import UserDatabase
from utils.permissions import check_permission_for_session

build_bp = Blueprint('build', __name__)
build_service = BuildService()
db = UserDatabase()


def get_auth_info():
    """Extract authentication info from request."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    return token, ip_address


# ==================== Project Routes ====================

@build_bp.route('/api/admin/projects', methods=['GET'])
def get_projects():
    """Get all build projects."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_projects')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    result = build_service.get_all_projects(include_inactive)
    
    return jsonify(result), 200 if result['success'] else 500


@build_bp.route('/api/admin/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific build project."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_projects')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    result = build_service.get_project(project_id)
    
    return jsonify(result), 200 if result['success'] else 404


@build_bp.route('/api/admin/projects', methods=['POST'])
def create_project():
    """Create a new build project."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'manage_projects')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    # Add created_by from session
    data['created_by'] = session.get('user_id')
    
    result = build_service.create_project(
        data,
        admin_username=session.get('username', 'Admin'),
        ip_address=ip_address
    )
    
    return jsonify(result), 201 if result['success'] else 400


@build_bp.route('/api/admin/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Update a build project."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'manage_projects')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    result = build_service.update_project(
        project_id,
        data,
        admin_username=session.get('username', 'Admin'),
        ip_address=ip_address
    )
    
    return jsonify(result), 200 if result['success'] else 400


@build_bp.route('/api/admin/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a build project."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'manage_projects')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    result = build_service.delete_project(
        project_id,
        admin_username=session.get('username', 'Admin'),
        ip_address=ip_address
    )
    
    return jsonify(result), 200 if result['success'] else 400


# ==================== Dockerfile Routes ====================

@build_bp.route('/api/admin/projects/<int:project_id>/dockerfile', methods=['GET'])
def get_dockerfile(project_id):
    """Get Dockerfile content for a project."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_projects')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    result = build_service.get_dockerfile(project_id)
    
    return jsonify(result), 200 if result['success'] else 400


@build_bp.route('/api/admin/projects/<int:project_id>/dockerfile', methods=['PUT'])
def save_dockerfile(project_id):
    """Save Dockerfile content and push to git."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'manage_projects')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'success': False, 'error': 'Dockerfile content is required'}), 400
    
    result = build_service.save_dockerfile(
        project_id,
        data['content'],
        commit_message=data.get('commit_message', 'Update Dockerfile'),
        admin_username=session.get('username', 'Admin'),
        ip_address=ip_address
    )
    
    return jsonify(result), 200 if result['success'] else 400


# ==================== Build Routes ====================

@build_bp.route('/api/admin/projects/<int:project_id>/build', methods=['POST'])
def start_build(project_id):
    """Start a Docker image build."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'build_images')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    data = request.get_json() or {}
    
    result = build_service.start_build(
        project_id,
        tag=data.get('tag'),
        registry_id=data.get('registry_id'),
        admin_username=session.get('username', 'Admin'),
        user_id=session.get('user_id'),
        ip_address=ip_address
    )
    
    return jsonify(result), 202 if result['success'] else 400


@build_bp.route('/api/admin/projects/<int:project_id>/builds', methods=['GET'])
def get_project_builds(project_id):
    """Get build history for a project."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_projects')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    limit = request.args.get('limit', 50, type=int)
    result = build_service.get_project_builds(project_id, limit)
    
    return jsonify(result), 200 if result['success'] else 400


@build_bp.route('/api/admin/builds/<int:build_id>', methods=['GET'])
def get_build_status(build_id):
    """Get status of a specific build."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_projects')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    result = build_service.get_build_status(build_id)
    
    return jsonify(result), 200 if result['success'] else 404


@build_bp.route('/api/admin/builds/<int:build_id>/logs', methods=['GET'])
def get_build_logs(build_id):
    """Get logs for a specific build."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'view_projects')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    result = build_service.get_build_logs(build_id)
    
    return jsonify(result), 200 if result['success'] else 404


# ==================== Push Routes ====================

@build_bp.route('/api/admin/builds/<int:build_id>/push', methods=['POST'])
def push_image(build_id):
    """Push a built image to a registry."""
    token, ip_address = get_auth_info()
    
    has_perm, session, error = check_permission_for_session(db, token, 'push_images')
    if not has_perm:
        return jsonify({'success': False, 'error': error}), 403 if session else 401
    
    data = request.get_json() or {}
    
    result = build_service.push_image(
        build_id,
        registry_id=data.get('registry_id'),
        admin_username=session.get('username', 'Admin'),
        ip_address=ip_address
    )
    
    return jsonify(result), 200 if result['success'] else 400
