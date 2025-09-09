"""Traffic tracking middleware for user access analytics."""

from functools import wraps
from flask import request, g, session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import threading
import time


class TrafficTracker:
    """Middleware to track user access and session analytics."""
    
    def __init__(self):
        """Initialize traffic tracker."""
        self.active_sessions = {}
        self.session_lock = threading.Lock()
        
    def track_request(self, app):
        """Flask middleware to track all requests."""
        
        @app.before_request
        def before_request():
            """Track request start."""
            g.request_start_time = time.time()
            g.request_data = {
                'ip_address': self._get_client_ip(),
                'user_agent': request.headers.get('User-Agent', ''),
                'endpoint': request.endpoint,
                'method': request.method,
                'access_time': datetime.now()
            }
            
            # Get user info from session or token
            user_info = self._get_user_info()
            if user_info:
                g.request_data['user_id'] = user_info.get('user_id')
                g.request_data['session_token'] = user_info.get('session_token')
                
                # Track session start
                self._track_session_start(user_info.get('session_token'), g.request_data)
        
        @app.after_request
        def after_request(response):
            """Track request completion."""
            if hasattr(g, 'request_data'):
                # Calculate request duration
                duration = time.time() - g.request_start_time
                
                # Get response size
                content_length = response.headers.get('Content-Length')
                bytes_sent = int(content_length) if content_length else len(response.get_data())
                
                # Update request data
                g.request_data.update({
                    'status_code': response.status_code,
                    'bytes_sent': bytes_sent,
                    'duration_seconds': int(duration)
                })
                
                # Log the access asynchronously
                self._log_access_async(g.request_data)
                
            return response
            
        return app
    
    def _get_client_ip(self) -> str:
        """Get the real client IP address."""
        # Check for forwarded headers first
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or 'unknown'
    
    def _get_user_info(self) -> Optional[Dict[str, Any]]:
        """Extract user information from request."""
        user_info = {}
        
        # Try to get from Authorization header (Bearer token)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            user_info['session_token'] = token
            
            # Try to get user info from token validation
            try:
                from database import UserDatabase
                db = UserDatabase()
                session_data = db.verify_session(token)
                if session_data:
                    user_info['user_id'] = session_data.get('id')
                    user_info['username'] = session_data.get('username')
            except Exception as e:
                print(f"Error validating session token: {e}")
        
        # Try to get from Flask session
        elif 'user_id' in session:
            user_info['user_id'] = session['user_id']
            user_info['session_token'] = session.get('session_token')
        
        return user_info if user_info else None
    
    def _track_session_start(self, session_token: str, request_data: Dict[str, Any]):
        """Track when a session starts."""
        if not session_token:
            return
            
        with self.session_lock:
            if session_token not in self.active_sessions:
                self.active_sessions[session_token] = {
                    'start_time': datetime.now(),
                    'ip_address': request_data['ip_address'],
                    'user_id': request_data.get('user_id'),
                    'last_activity': datetime.now()
                }
                
                # Update request data with session start
                request_data['session_start'] = self.active_sessions[session_token]['start_time']
            else:
                # Update last activity
                self.active_sessions[session_token]['last_activity'] = datetime.now()
                request_data['session_start'] = self.active_sessions[session_token]['start_time']
    
    def _log_access_async(self, access_data: Dict[str, Any]):
        """Log access data asynchronously."""
        def log_access():
            try:
                from database.traffic_repository import TrafficRepository
                traffic_repo = TrafficRepository()
                traffic_repo.log_access(access_data)
            except Exception as e:
                print(f"Error logging access: {e}")
        
        # Run in background thread to avoid blocking request
        thread = threading.Thread(target=log_access)
        thread.daemon = True
        thread.start()
    
    def cleanup_inactive_sessions(self, inactive_threshold_minutes: int = 30):
        """Clean up inactive sessions and update their end times."""
        cutoff_time = datetime.now() - timedelta(minutes=inactive_threshold_minutes)
        
        with self.session_lock:
            inactive_sessions = []
            for session_token, session_info in self.active_sessions.items():
                if session_info['last_activity'] < cutoff_time:
                    inactive_sessions.append(session_token)
            
            # Update database with session end times
            if inactive_sessions:
                try:
                    from database.traffic_repository import TrafficRepository
                    traffic_repo = TrafficRepository()
                    
                    for session_token in inactive_sessions:
                        session_info = self.active_sessions[session_token]
                        traffic_repo.update_session_end(
                            session_token, 
                            session_info['last_activity']
                        )
                        del self.active_sessions[session_token]
                        
                except Exception as e:
                    print(f"Error cleaning up sessions: {e}")
    
    def end_session(self, session_token: str):
        """Manually end a session (e.g., on logout)."""
        if not session_token:
            return
            
        with self.session_lock:
            if session_token in self.active_sessions:
                try:
                    from database.traffic_repository import TrafficRepository
                    traffic_repo = TrafficRepository()
                    traffic_repo.update_session_end(session_token)
                    del self.active_sessions[session_token]
                except Exception as e:
                    print(f"Error ending session: {e}")


# Global traffic tracker instance
traffic_tracker = TrafficTracker()


def track_endpoint(func):
    """Decorator to explicitly track specific endpoints."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # The middleware already tracks all requests
        # This decorator can be used for additional endpoint-specific tracking
        return func(*args, **kwargs)
    return wrapper


def setup_traffic_tracking(app):
    """Setup traffic tracking for Flask app."""
    traffic_tracker.track_request(app)
    
    # Setup periodic cleanup of inactive sessions
    import atexit
    from threading import Timer
    
    def periodic_cleanup():
        traffic_tracker.cleanup_inactive_sessions()
        # Schedule next cleanup in 10 minutes
        timer = Timer(600, periodic_cleanup)
        timer.daemon = True
        timer.start()
    
    # Start periodic cleanup
    timer = Timer(600, periodic_cleanup)  # 10 minutes
    timer.daemon = True
    timer.start()
    
    # Cleanup on app shutdown
    atexit.register(lambda: traffic_tracker.cleanup_inactive_sessions(0))
    
    return traffic_tracker
