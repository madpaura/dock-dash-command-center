"""
Audit service for managing audit logs and security monitoring.
"""
import json
from typing import List, Dict, Any, Optional
from loguru import logger

from database import UserDatabase


class AuditService:
    """Service for handling audit logging and monitoring operations."""
    
    def __init__(self, db: UserDatabase):
        self.db = db
    
    def get_audit_logs(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get all audit logs with transformation for frontend display.
        
        Args:
            limit: Maximum number of logs to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of transformed audit logs
        """
        try:
            logger.info("Fetching all audit logs")
            
            logs = self.db.get_audit_logs(limit=limit) 
            transformed_logs = []
            
            for log in logs:
                action_details = {}
                if log.get('action_details'):
                    try:
                        action_details = json.loads(log['action_details']) if isinstance(log['action_details'], str) else log['action_details']
                    except:
                        action_details = {}
                
                # Determine log level based on action type
                level = self._get_log_level(log.get('action_type', ''))
                
                # Determine source based on action type
                source = self._get_log_source(log.get('action_type', ''))
                
                transformed_log = {
                    'id': str(log['id']),
                    'level': level,
                    'timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(log['timestamp'], 'strftime') else str(log['timestamp']),
                    'user': log.get('username', 'System'),
                    'source': source,
                    'message': action_details.get('message', f"{log.get('action_type', 'Unknown action')}"),
                    'ip_address': log.get('ip_address', 'N/A'),
                    'action_type': log.get('action_type', 'unknown')
                }
                transformed_logs.append(transformed_log)
            
            return transformed_logs
            
        except Exception as e:
            logger.error(f"Error fetching audit logs: {e}")
            return []
    
    def _get_log_level(self, action_type: str) -> str:
        """
        Determine log level based on action type.
        
        Args:
            action_type: Type of action
            
        Returns:
            str: Log level (INFO, WARN, ERROR, DEBUG)
        """
        if action_type in ['login_failed', 'error', 'delete_user', 'security_violation']:
            return 'ERROR'
        elif action_type in ['login_attempt', 'update_user', 'warning', 'ssh_connect']:
            return 'WARN'
        elif action_type in ['debug', 'query', 'cache_hit']:
            return 'DEBUG'
        else:
            return 'INFO'
    
    def _get_log_source(self, action_type: str) -> str:
        """
        Determine log source based on action type.
        
        Args:
            action_type: Type of action
            
        Returns:
            str: Log source identifier
        """
        source_map = {
            'login': 'auth.service',
            'login_failed': 'auth.service',
            'logout': 'auth.service',
            'register': 'auth.service',
            'create_user': 'user.service',
            'create_admin_user': 'user.service',
            'update_user': 'user.service',
            'update_admin_user': 'user.service',
            'delete_user': 'user.service',
            'approve_user': 'user.service',
            'approve_admin_user': 'user.service',
            'server_action': 'server.service',
            'server_added': 'server.service',
            'ssh_connect': 'ssh.service',
            'ssh_command': 'ssh.service',
            'ssh_disconnect': 'ssh.service',
            'docker_cleanup': 'docker.service',
            'register_agent': 'agent.service',
            'unregister_agent': 'agent.service',
            'clear_logs': 'audit.service',
            'system_start': 'system',
            'api_call': 'api.gateway'
        }
        return source_map.get(action_type, 'system')
    
    def clear_audit_logs(self, admin_username: str, ip_address: Optional[str] = None) -> bool:
        """
        Clear all audit logs (admin only operation).
        
        Args:
            admin_username: Username of admin clearing logs
            ip_address: Client IP address
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Admin {admin_username} clearing all audit logs")
            
            # Clear all audit logs
            result = self.db.clear_audit_logs()
            
            if result:
                # Log this action (this will be the only log after clearing)
                self.db.log_audit_event(
                    admin_username,
                    'clear_logs',
                    {'message': f'All audit logs cleared by {admin_username}'},
                    ip_address
                )
                
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error clearing audit logs: {e}")
            return False
    
    def log_security_event(self, username: str, event_type: str, details: Dict[str, Any], 
                          ip_address: Optional[str] = None, severity: str = 'medium'):
        """
        Log security-related events with enhanced details.
        
        Args:
            username: Username associated with the event
            event_type: Type of security event
            details: Event details
            ip_address: Client IP address
            severity: Severity level (low, medium, high, critical)
        """
        try:
            enhanced_details = {
                **details,
                'severity': severity,
                'event_category': 'security',
                'requires_attention': severity in ['high', 'critical']
            }
            
            self.db.log_audit_event(
                username=username,
                action_type=f'security_{event_type}',
                action_details=enhanced_details,
                ip_address=ip_address
            )
            
            # Log to application logger as well for immediate attention
            if severity in ['high', 'critical']:
                logger.warning(f"SECURITY EVENT [{severity.upper()}]: {details.get('message', event_type)} - User: {username}, IP: {ip_address}")
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
    
    def log_system_event(self, event_type: str, details: Dict[str, Any], 
                        ip_address: Optional[str] = None):
        """
        Log system-level events.
        
        Args:
            event_type: Type of system event
            details: Event details
            ip_address: Source IP address
        """
        try:
            self.db.log_audit_event(
                username='System',
                action_type=f'system_{event_type}',
                action_details=details,
                ip_address=ip_address
            )
            
        except Exception as e:
            logger.error(f"Error logging system event: {e}")
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """
        Get audit log statistics for monitoring dashboard.
        
        Returns:
            Dict[str, Any]: Audit statistics
        """
        try:
            # Get recent logs for analysis
            recent_logs = self.db.get_audit_logs(limit=1000)
            
            if not recent_logs:
                return {
                    'total_logs': 0,
                    'error_count': 0,
                    'warning_count': 0,
                    'info_count': 0,
                    'unique_users': 0,
                    'unique_ips': 0,
                    'recent_activity': []
                }
            
            # Analyze logs
            error_count = 0
            warning_count = 0
            info_count = 0
            unique_users = set()
            unique_ips = set()
            
            for log in recent_logs:
                action_type = log.get('action_type', '')
                level = self._get_log_level(action_type)
                
                if level == 'ERROR':
                    error_count += 1
                elif level == 'WARN':
                    warning_count += 1
                else:
                    info_count += 1
                
                if log.get('username'):
                    unique_users.add(log['username'])
                if log.get('ip_address'):
                    unique_ips.add(log['ip_address'])
            
            # Get recent activity (last 10 logs)
            recent_activity = []
            for log in recent_logs[:10]:
                action_details = {}
                if log.get('action_details'):
                    try:
                        action_details = json.loads(log['action_details']) if isinstance(log['action_details'], str) else log['action_details']
                    except:
                        action_details = {}
                
                recent_activity.append({
                    'timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(log['timestamp'], 'strftime') else str(log['timestamp']),
                    'user': log.get('username', 'System'),
                    'action': log.get('action_type', 'unknown'),
                    'message': action_details.get('message', f"{log.get('action_type', 'Unknown action')}")
                })
            
            return {
                'total_logs': len(recent_logs),
                'error_count': error_count,
                'warning_count': warning_count,
                'info_count': info_count,
                'unique_users': len(unique_users),
                'unique_ips': len(unique_ips),
                'recent_activity': recent_activity
            }
            
        except Exception as e:
            logger.error(f"Error getting audit statistics: {e}")
            return {
                'total_logs': 0,
                'error_count': 0,
                'warning_count': 0,
                'info_count': 0,
                'unique_users': 0,
                'unique_ips': 0,
                'recent_activity': []
            }
    
    def search_audit_logs(self, query: str, filters: Optional[Dict[str, Any]] = None, 
                         limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search audit logs with filters.
        
        Args:
            query: Search query
            filters: Additional filters (user, action_type, date_range, etc.)
            limit: Maximum number of results
            
        Returns:
            List[Dict[str, Any]]: Filtered audit logs
        """
        try:
            # Get all logs first (in a real implementation, this would be done at DB level)
            all_logs = self.get_audit_logs(limit=1000)
            
            # Apply search and filters
            filtered_logs = []
            for log in all_logs:
                # Text search in message, user, and action_type
                if query and query.lower() not in log.get('message', '').lower() and \
                   query.lower() not in log.get('user', '').lower() and \
                   query.lower() not in log.get('action_type', '').lower():
                    continue
                
                # Apply filters
                if filters:
                    if 'user' in filters and filters['user'] != log.get('user'):
                        continue
                    if 'level' in filters and filters['level'] != log.get('level'):
                        continue
                    if 'source' in filters and filters['source'] != log.get('source'):
                        continue
                    if 'action_type' in filters and filters['action_type'] != log.get('action_type'):
                        continue
                
                filtered_logs.append(log)
                
                # Limit results
                if len(filtered_logs) >= limit:
                    break
            
            return filtered_logs
            
        except Exception as e:
            logger.error(f"Error searching audit logs: {e}")
            return []
