from flask import Blueprint, request, jsonify
from services.container_service import ContainerService
from services.agent_service import AgentService
from utils.auth import require_session_auth
from loguru import logger

container_bp = Blueprint('container', __name__)

# Initialize services
agent_service = AgentService()
container_service = ContainerService(agent_service)

@container_bp.route('/api/admin/containers/<server_id>', methods=['GET'])
def get_containers(server_id):
    """Get containers from a specific server"""
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Convert server_id back to IP format
        server_ip = server_id.replace('-', '.')
        
        # Get search parameter
        search_term = request.args.get('search', None)
        if search_term and search_term.strip() == '':
            search_term = None
        
        logger.info(f"Getting containers from server {server_ip} for user {session.get('username')}")
        
        # Get containers from the specified server
        result = container_service.get_containers_from_server(server_ip, search_term)
        
        if result.success:
            return jsonify({
                'success': True,
                'server_id': result.server_id,
                'server_ip': result.server_ip,
                'containers': [
                    {
                        'id': c.id,
                        'name': c.name,
                        'image': c.image,
                        'status': c.status,
                        'state': c.state,
                        'created': c.created,
                        'started': c.started,
                        'finished': c.finished,
                        'uptime': c.uptime,
                        'cpu_usage': c.cpu_usage,
                        'memory_usage': c.memory_usage,
                        'memory_used_mb': c.memory_used_mb,
                        'memory_limit_mb': c.memory_limit_mb,
                        'disk_usage': c.disk_usage,
                        'network_rx_bytes': c.network_rx_bytes,
                        'network_tx_bytes': c.network_tx_bytes,
                        'ports': c.ports,
                        'volumes': c.volumes,
                        'environment': c.environment,
                        'command': c.command,
                        'labels': c.labels,
                        'restart_count': c.restart_count,
                        'platform': c.platform
                    } for c in result.containers
                ],
                'total_count': result.total_count,
                'running_count': result.running_count,
                'stopped_count': result.stopped_count
            })
        else:
            return jsonify({
                'success': False,
                'error': result.error,
                'server_id': result.server_id,
                'server_ip': result.server_ip,
                'containers': [],
                'total_count': 0,
                'running_count': 0,
                'stopped_count': 0
            }), 500
            
    except Exception as e:
        logger.error(f"Error in get_containers endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'containers': [],
            'total_count': 0,
            'running_count': 0,
            'stopped_count': 0
        }), 500

@container_bp.route('/api/admin/containers/<server_id>/<container_id>/action', methods=['POST'])
def container_action(server_id, container_id):
    """Perform an action on a container"""
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    try:
        data = request.get_json() or {}
        action = data.get('action')
        force = data.get('force', False)
        
        if not action:
            return jsonify({
                'success': False,
                'error': 'Action is required'
            }), 400
        
        if action not in ['start', 'stop', 'restart', 'delete']:
            return jsonify({
                'success': False,
                'error': f'Invalid action: {action}'
            }), 400
        
        # Convert server_id back to IP format
        server_ip = server_id.replace('-', '.')
        
        logger.info(f"User {session.get('username')} performing {action} on container {container_id} at server {server_ip}")
        
        # Perform the action
        result = container_service.perform_container_action(server_ip, container_id, action, force)
        
        if result.success:
            return jsonify({
                'success': True,
                'action': result.action,
                'container_id': result.container_id,
                'container_name': result.container_name,
                'message': result.message,
                'new_status': result.new_status
            })
        else:
            return jsonify({
                'success': False,
                'action': result.action,
                'container_id': result.container_id,
                'message': result.message,
                'error': result.error
            }), 400
            
    except Exception as e:
        logger.error(f"Error in container_action endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@container_bp.route('/api/admin/containers/cache/clear', methods=['POST'])
def clear_container_cache():
    """Clear the container cache"""
    session, error_response, status_code = require_session_auth()
    if error_response:
        return error_response, status_code
    
    try:
        container_service.clear_cache()
        logger.info(f"Container cache cleared by user {session.get('username')}")
        
        return jsonify({
            'success': True,
            'message': 'Container cache cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Error clearing container cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
