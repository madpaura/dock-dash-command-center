"""Traffic analytics API routes."""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from services.traffic_service import TrafficService
from utils.auth_helpers import require_admin_auth


traffic_bp = Blueprint('traffic', __name__)
traffic_service = TrafficService()


@traffic_bp.route('/api/admin/traffic/analytics', methods=['GET'])
def get_traffic_analytics():
    """Get traffic analytics with filtering options."""
    # Check admin authentication
    session, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Get query parameters
        period = request.args.get('period', 'daily')  # daily, weekly, monthly
        days = int(request.args.get('days', 30))
        ip_filter = request.args.get('ip_filter')
        user_filter = request.args.get('user_filter')
        
        # Validate period
        if period not in ['daily', 'weekly', 'monthly']:
            return jsonify({'error': 'Invalid period. Must be daily, weekly, or monthly'}), 400
        
        # Get analytics data
        analytics = traffic_service.get_traffic_analytics(
            period=period,
            days=days,
            ip_filter=ip_filter,
            user_filter=user_filter
        )
        
        return jsonify({
            'success': True,
            'data': analytics,
            'filters': {
                'period': period,
                'days': days,
                'ip_filter': ip_filter,
                'user_filter': user_filter
            }
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to get traffic analytics: {str(e)}'}), 500


@traffic_bp.route('/api/admin/traffic/real-time', methods=['GET'])
def get_real_time_stats():
    """Get real-time traffic statistics."""
    # Check admin authentication
    session, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        stats = traffic_service.get_real_time_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get real-time stats: {str(e)}'}), 500


@traffic_bp.route('/api/admin/traffic/user/<int:user_id>', methods=['GET'])
def get_user_activity(user_id):
    """Get activity timeline for a specific user."""
    # Check admin authentication
    session, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        days = int(request.args.get('days', 7))
        activity = traffic_service.get_user_activity_timeline(user_id=user_id, days=days)
        
        return jsonify({
            'success': True,
            'data': activity,
            'user_id': user_id,
            'days': days
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to get user activity: {str(e)}'}), 500


@traffic_bp.route('/api/admin/traffic/ip/<path:ip_address>', methods=['GET'])
def get_ip_analytics(ip_address):
    """Get analytics for a specific IP address."""
    # Check admin authentication
    session, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        days = int(request.args.get('days', 30))
        analytics = traffic_service.get_ip_analytics(ip_address=ip_address, days=days)
        
        return jsonify({
            'success': True,
            'data': analytics,
            'ip_address': ip_address,
            'days': days
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to get IP analytics: {str(e)}'}), 500


@traffic_bp.route('/api/admin/traffic/endpoints', methods=['GET'])
def get_top_endpoints():
    """Get most accessed endpoints."""
    # Check admin authentication
    session, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        days = int(request.args.get('days', 7))
        endpoints = traffic_service.get_top_endpoints(days=days)
        
        return jsonify({
            'success': True,
            'data': endpoints,
            'days': days
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to get endpoint stats: {str(e)}'}), 500


@traffic_bp.route('/api/admin/traffic/summary', methods=['GET'])
def get_traffic_summary():
    """Get overall traffic summary."""
    # Check admin authentication
    session, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Get real-time stats which includes summary
        stats = traffic_service.get_real_time_stats()
        
        return jsonify({
            'success': True,
            'data': stats.get('overall_summary', {}),
            'timestamp': stats.get('timestamp')
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get traffic summary: {str(e)}'}), 500
