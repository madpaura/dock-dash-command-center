
import React, { useState, useEffect } from 'react';
import { Container, Image, Users, Activity, AlertTriangle, CheckCircle, Cpu, Database, Server, RefreshCw, UserCheck } from 'lucide-react';
import { StatCard } from '../components/StatCard';
import { ContainerCard } from '../components/ContainerCard';
import { dashboardApi, userApi, DashboardStats } from '../lib/api';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/ui/button';

export const AdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [pendingUsers, setPendingUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboardData = async () => {
    if (!user?.token) return;
    
    try {
      setError(null);
      const [statsResponse, pendingResponse] = await Promise.all([
        dashboardApi.getDashboardStats(user.token),
        userApi.getPendingUsers(user.token)
      ]);

      if (statsResponse.success) {
        setStats(statsResponse.data!);
      } else {
        setError(statsResponse.error || 'Failed to fetch dashboard stats');
      }

      if (pendingResponse.success) {
        setPendingUsers(pendingResponse.data || []);
      }
    } catch (err) {
      setError('Network error occurred');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboardData();
  };

  useEffect(() => {
    fetchDashboardData();
  }, [user?.token]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-400 mr-2" />
            <span className="text-red-800">Error: {error}</span>
          </div>
          <button
            onClick={handleRefresh}
            className="text-red-600 hover:text-red-800 font-medium"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center text-gray-500 py-8">
        No dashboard data available
      </div>
    );
  }

  // Create stats cards from real data
  const statCards = [
    { 
      title: 'Total Users', 
      value: stats.totalUsers, 
      change: stats.pendingUsers > 0 ? `${stats.pendingUsers} pending` : 'All approved', 
      icon: Users, 
      color: 'blue' as const,
      onClick: stats.pendingUsers > 0 ? () => window.location.href = '/admin/users' : undefined
    },
    { 
      title: 'Active Users', 
      value: stats.activeUsers, 
      change: `${Math.round((stats.activeUsers / Math.max(stats.totalUsers, 1)) * 100)}% active`, 
      icon: UserCheck, 
      color: 'green' as const 
    },
    { 
      title: 'Total Servers', 
      value: stats.totalServers, 
      change: `${stats.onlineServers} online`, 
      icon: Server, 
      color: 'purple' as const 
    },
    { 
      title: 'Running Containers', 
      value: stats.runningContainers, 
      change: `Across ${stats.onlineServers} servers`, 
      icon: Container, 
      color: 'orange' as const 
    },
  ];

  // System resource stats from real data
  const resourceStats = [
    { 
      title: 'Avg CPU Usage', 
      value: `${stats.avgCpuUsage}%`, 
      change: stats.avgCpuUsage > 80 ? 'High usage' : stats.avgCpuUsage > 50 ? 'Moderate' : 'Low usage', 
      icon: Cpu, 
      color: stats.avgCpuUsage > 80 ? 'red' as const : stats.avgCpuUsage > 50 ? 'orange' as const : 'green' as const 
    },
    { 
      title: 'Memory Usage', 
      value: `${stats.usedMemoryGB}GB`, 
      change: `${stats.avgMemoryUsage}% of ${stats.totalMemoryGB}GB`, 
      icon: Database, 
      color: stats.avgMemoryUsage > 80 ? 'red' as const : stats.avgMemoryUsage > 50 ? 'orange' as const : 'green' as const 
    },
  ];

  // Recent containers will be implemented later
  const recentContainers: any[] = [];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Admin Dashboard</h1>
          <p className="text-muted-foreground">Monitor and manage your Docker infrastructure</p>
        </div>
        <div className="flex gap-3">
          <Button 
            variant="outline" 
            className="gap-2"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Pending Users Alert */}
      {pendingUsers.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-yellow-400 mr-2" />
            <span className="text-yellow-800">
              {pendingUsers.length} user{pendingUsers.length > 1 ? 's' : ''} pending approval.
            </span>
            <button
              onClick={() => window.location.href = '/admin/users'}
              className="ml-4 text-yellow-600 hover:text-yellow-800 font-medium"
            >
              Review →
            </button>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => (
          <StatCard key={index} {...stat} />
        ))}
      </div>

      {/* Resource Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {resourceStats.map((stat, index) => (
          <StatCard key={index} {...stat} />
        ))}
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-card backdrop-blur-sm border border-border rounded-xl p-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">System Health</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Servers Online</span>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  stats.onlineServers > 0 ? 'bg-green-400' : 'bg-red-400'
                }`}></div>
                <span className={`text-sm ${
                  stats.onlineServers > 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {stats.onlineServers}/{stats.totalServers}
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Avg CPU Usage</span>
              <span className="text-foreground">{stats.avgCpuUsage}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Avg Memory Usage</span>
              <span className="text-foreground">{stats.avgMemoryUsage}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Total Memory</span>
              <span className="text-foreground">{stats.totalMemoryGB}GB</span>
            </div>
          </div>
        </div>

        <div className="bg-card backdrop-blur-sm border border-border rounded-xl p-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">Recent Alerts</h2>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-3 bg-orange-500/10 border border-orange-500/20 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-orange-400 mt-0.5" />
              <div>
                <p className="text-sm text-foreground">High memory usage detected</p>
                <p className="text-xs text-muted-foreground mt-1">Container: webapp-frontend</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-400 mt-0.5" />
              <div>
                <p className="text-sm text-foreground">Backup completed successfully</p>
                <p className="text-xs text-muted-foreground mt-1">Database: postgres-main</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Containers */}
      <div>
        <h2 className="text-xl font-semibold text-foreground mb-6">Recent Containers</h2>
        {recentContainers.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {recentContainers.map((container) => (
              <ContainerCard
                key={container.id}
                {...container}
                onStart={() => console.log('Start', container.name)}
                onStop={() => console.log('Stop', container.name)}
                onRestart={() => console.log('Restart', container.name)}
                onDelete={() => console.log('Delete', container.name)}
              />
            ))}
          </div>
        ) : (
          <div className="bg-card backdrop-blur-sm border border-border rounded-xl p-8 text-center">
            <Container className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">Recent Containers</h3>
            <p className="text-muted-foreground mb-4">
              Recent container activity will be displayed here.
            </p>
            <p className="text-sm text-muted-foreground">
              This feature will be implemented in a future update.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
