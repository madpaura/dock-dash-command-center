"""Traffic analytics service for user access tracking."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from database.traffic_repository import TrafficRepository


class TrafficService:
    """Service for traffic analytics and user access tracking."""

    def __init__(self, traffic_repo=None):
        """Initialize traffic service."""
        self.traffic_repo = traffic_repo or TrafficRepository()

    def get_traffic_analytics(self, 
                            period: str = 'daily',
                            days: int = 30,
                            ip_filter: str = None,
                            user_filter: str = None) -> Dict[str, Any]:
        """Get traffic analytics with period grouping."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get raw analytics data
        analytics = self.traffic_repo.get_traffic_analytics(
            start_date=start_date,
            end_date=end_date,
            ip_filter=ip_filter,
            user_filter=user_filter
        )
        
        # Process data based on period
        if period == 'weekly':
            analytics['weekly_stats'] = self._group_by_week(analytics.get('daily_stats', []))
        elif period == 'monthly':
            analytics['monthly_stats'] = self._group_by_month(analytics.get('daily_stats', []))
        
        # Add summary statistics
        analytics['summary'] = self._calculate_summary_stats(analytics.get('daily_stats', []))
        
        return analytics

    def get_user_activity_timeline(self, user_id: int = None, days: int = 7) -> List[Dict[str, Any]]:
        """Get detailed user activity timeline."""
        sessions = self.traffic_repo.get_user_sessions(user_id=user_id)
        
        # Filter by date range
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_sessions = []
        
        for session in sessions:
            session_start = session.get('session_start')
            if session_start and isinstance(session_start, str):
                session_start = datetime.fromisoformat(session_start.replace('Z', '+00:00'))
            
            if session_start and session_start >= cutoff_date:
                filtered_sessions.append(session)
        
        return filtered_sessions

    def get_ip_analytics(self, ip_address: str, days: int = 30) -> Dict[str, Any]:
        """Get detailed analytics for a specific IP address."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics = self.traffic_repo.get_traffic_analytics(
            start_date=start_date,
            end_date=end_date,
            ip_filter=ip_address
        )
        
        # Get sessions for this IP
        sessions = self.traffic_repo.get_user_sessions(ip_address=ip_address)
        
        analytics['sessions'] = sessions
        analytics['ip_address'] = ip_address
        
        return analytics

    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time traffic statistics."""
        # Get stats for last 24 hours
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=24)
        
        analytics = self.traffic_repo.get_traffic_analytics(
            start_date=start_date,
            end_date=end_date
        )
        
        # Get overall summary
        summary = self.traffic_repo.get_traffic_summary()
        
        return {
            'last_24_hours': analytics,
            'overall_summary': summary,
            'timestamp': datetime.now().isoformat()
        }

    def get_top_endpoints(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get most accessed endpoints."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analytics = self.traffic_repo.get_traffic_analytics(
            start_date=start_date,
            end_date=end_date
        )
        
        return analytics.get('endpoint_stats', [])

    def _group_by_week(self, daily_stats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group daily stats by week."""
        weekly_data = {}
        
        for day in daily_stats:
            date_obj = datetime.fromisoformat(str(day['date']))
            # Get Monday of the week
            week_start = date_obj - timedelta(days=date_obj.weekday())
            week_key = week_start.strftime('%Y-%m-%d')
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    'week_start': week_key,
                    'total_requests': 0,
                    'unique_ips': set(),
                    'unique_users': set(),
                    'total_duration': 0,
                    'total_bytes_sent': 0,
                    'total_bytes_received': 0,
                    'error_count': 0,
                    'days_count': 0
                }
            
            weekly_data[week_key]['total_requests'] += day.get('total_requests', 0)
            weekly_data[week_key]['unique_ips'].add(day.get('unique_ips', 0))
            weekly_data[week_key]['unique_users'].add(day.get('unique_users', 0))
            weekly_data[week_key]['total_duration'] += day.get('avg_duration', 0) * day.get('total_requests', 0)
            weekly_data[week_key]['total_bytes_sent'] += day.get('total_bytes_sent', 0)
            weekly_data[week_key]['total_bytes_received'] += day.get('total_bytes_received', 0)
            weekly_data[week_key]['error_count'] += day.get('error_count', 0)
            weekly_data[week_key]['days_count'] += 1
        
        # Convert sets to counts and calculate averages
        result = []
        for week_data in weekly_data.values():
            week_data['unique_ips'] = len(week_data['unique_ips'])
            week_data['unique_users'] = len(week_data['unique_users'])
            if week_data['total_requests'] > 0:
                week_data['avg_duration'] = week_data['total_duration'] / week_data['total_requests']
            else:
                week_data['avg_duration'] = 0
            del week_data['total_duration']
            del week_data['days_count']
            result.append(week_data)
        
        return sorted(result, key=lambda x: x['week_start'], reverse=True)

    def _group_by_month(self, daily_stats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group daily stats by month."""
        monthly_data = {}
        
        for day in daily_stats:
            date_obj = datetime.fromisoformat(str(day['date']))
            month_key = date_obj.strftime('%Y-%m')
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'month': month_key,
                    'total_requests': 0,
                    'unique_ips': set(),
                    'unique_users': set(),
                    'total_duration': 0,
                    'total_bytes_sent': 0,
                    'total_bytes_received': 0,
                    'error_count': 0,
                    'days_count': 0
                }
            
            monthly_data[month_key]['total_requests'] += day.get('total_requests', 0)
            monthly_data[month_key]['unique_ips'].add(day.get('unique_ips', 0))
            monthly_data[month_key]['unique_users'].add(day.get('unique_users', 0))
            monthly_data[month_key]['total_duration'] += day.get('avg_duration', 0) * day.get('total_requests', 0)
            monthly_data[month_key]['total_bytes_sent'] += day.get('total_bytes_sent', 0)
            monthly_data[month_key]['total_bytes_received'] += day.get('total_bytes_received', 0)
            monthly_data[month_key]['error_count'] += day.get('error_count', 0)
            monthly_data[month_key]['days_count'] += 1
        
        # Convert sets to counts and calculate averages
        result = []
        for month_data in monthly_data.values():
            month_data['unique_ips'] = len(month_data['unique_ips'])
            month_data['unique_users'] = len(month_data['unique_users'])
            if month_data['total_requests'] > 0:
                month_data['avg_duration'] = month_data['total_duration'] / month_data['total_requests']
            else:
                month_data['avg_duration'] = 0
            del month_data['total_duration']
            del month_data['days_count']
            result.append(month_data)
        
        return sorted(result, key=lambda x: x['month'], reverse=True)

    def _calculate_summary_stats(self, daily_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics from daily stats."""
        if not daily_stats:
            return {
                'total_requests': 0,
                'total_unique_ips': 0,
                'total_unique_users': 0,
                'avg_daily_requests': 0,
                'avg_session_duration': 0,
                'total_errors': 0,
                'error_rate': 0
            }
        
        total_requests = sum(day.get('total_requests', 0) for day in daily_stats)
        total_errors = sum(day.get('error_count', 0) for day in daily_stats)
        
        # Calculate unique totals (approximate)
        all_ips = set()
        all_users = set()
        total_duration = 0
        
        for day in daily_stats:
            all_ips.add(day.get('unique_ips', 0))
            all_users.add(day.get('unique_users', 0))
            total_duration += day.get('avg_duration', 0) * day.get('total_requests', 0)
        
        return {
            'total_requests': total_requests,
            'total_unique_ips': len(all_ips),
            'total_unique_users': len(all_users),
            'avg_daily_requests': total_requests / len(daily_stats) if daily_stats else 0,
            'avg_session_duration': total_duration / total_requests if total_requests > 0 else 0,
            'total_errors': total_errors,
            'error_rate': (total_errors / total_requests * 100) if total_requests > 0 else 0
        }
