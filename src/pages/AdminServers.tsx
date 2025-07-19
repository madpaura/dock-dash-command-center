import React, { useState, useEffect } from 'react';
import { Server, RefreshCw, Plus, Settings, Monitor, Play, Square, Trash2, AlertTriangle } from 'lucide-react';
import { StatCard } from '../components/StatCard';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { serverApi, ServerInfo, ServerStats } from '../lib/api';
import { useAuth } from '../hooks/useAuth';

export const AdminServers: React.FC = () => {
  const { user } = useAuth();
  const token = user?.token;
  const [servers, setServers] = useState<ServerInfo[]>([]);
  const [stats, setStats] = useState<ServerStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchServerData = async () => {
    if (!token) return;
    
    try {
      setError(null);
      const [serversResponse, statsResponse] = await Promise.all([
        serverApi.getServers(token),
        serverApi.getServerStats(token)
      ]);

      if (serversResponse.success && serversResponse.data) {
        setServers(serversResponse.data.servers);
      } else {
        setError(serversResponse.error || 'Failed to fetch servers');
      }

      if (statsResponse.success && statsResponse.data) {
        setStats(statsResponse.data.stats);
      } else {
        console.warn('Failed to fetch server stats:', statsResponse.error);
      }
    } catch (err) {
      setError('Network error occurred');
      console.error('Error fetching server data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchServerData();
  };

  const handleServerAction = async (serverId: string, action: string) => {
    if (!token) return;
    
    try {
      const response = await serverApi.performServerAction(serverId, action, token);
      if (response.success) {
        // Refresh server data after action
        await fetchServerData();
      } else {
        setError(response.error || 'Failed to perform server action');
      }
    } catch (err) {
      setError('Failed to perform server action');
      console.error('Error performing server action:', err);
    }
  };

  useEffect(() => {
    fetchServerData();
  }, [token]);

  // Convert stats to StatCard format
  const statCards = stats ? [
    { 
      title: 'Total Servers', 
      value: stats.totalServers, 
      change: stats.totalServersChange, 
      icon: Server, 
      color: 'blue' as const 
    },
    { 
      title: 'Online', 
      value: stats.onlineServers, 
      change: stats.onlineServersChange, 
      icon: Monitor, 
      color: 'green' as const 
    },
    { 
      title: 'Offline', 
      value: stats.offlineServers, 
      change: stats.offlineServersChange, 
      icon: AlertTriangle, 
      color: 'red' as const 
    },
    { 
      title: 'Maintenance', 
      value: stats.maintenanceServers, 
      change: stats.maintenanceServersChange, 
      icon: Settings, 
      color: 'orange' as const 
    },
  ] : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">Loading server data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="w-8 h-8 mx-auto mb-4 text-red-400" />
          <p className="text-red-400 mb-4">{error}</p>
          <Button onClick={handleRefresh} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'online':
        return <Badge className="bg-green-500/10 text-green-400 border-green-500/20">Online</Badge>;
      case 'offline':
        return <Badge className="bg-red-500/10 text-red-400 border-red-500/20">Offline</Badge>;
      case 'maintenance':
        return <Badge className="bg-orange-500/10 text-orange-400 border-orange-500/20">Maintenance</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getServerIcon = (type: string) => {
    const iconProps = { className: "w-4 h-4" };
    switch (type) {
      case 'web':
        return <div className="w-3 h-3 bg-blue-500 rounded-sm" />;
      case 'database':
        return <div className="w-3 h-3 bg-green-500 rounded-sm" />;
      case 'api':
        return <div className="w-3 h-3 bg-red-500 rounded-sm" />;
      case 'cache':
        return <div className="w-3 h-3 bg-orange-500 rounded-sm" />;
      default:
        return <div className="w-3 h-3 bg-muted rounded-sm" />;
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Server Management</h1>
          <p className="text-muted-foreground">Monitor and manage your server infrastructure</p>
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
          <Button className="gap-2">
            <Plus className="w-4 h-4" />
            Add Server
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => (
          <StatCard key={index} {...stat} />
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-card backdrop-blur-sm border border-border rounded-xl p-6">
          <h3 className="text-lg font-semibold text-foreground mb-4">CPU Usage</h3>
          <div className="h-48 flex items-center justify-center border border-dashed border-border rounded-lg">
            <span className="text-muted-foreground">CPU Usage Chart</span>
          </div>
        </div>
        <div className="bg-card backdrop-blur-sm border border-border rounded-xl p-6">
          <h3 className="text-lg font-semibold text-foreground mb-4">Memory Usage</h3>
          <div className="h-48 flex items-center justify-center border border-dashed border-border rounded-lg">
            <span className="text-muted-foreground">Memory Usage Chart</span>
          </div>
        </div>
      </div>

      {/* Server List */}
      <div className="bg-card backdrop-blur-sm border border-border rounded-xl p-6">
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-foreground mb-2">Server List</h2>
          <p className="text-muted-foreground">Manage your server infrastructure</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Server</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Status</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">CPU</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Memory</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Disk</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Uptime</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody>
              {servers.map((server) => (
                <tr key={server.id} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-3">
                      {getServerIcon(server.type)}
                      <div>
                        <div className="font-medium text-foreground">{server.id}</div>
                        <div className="text-sm text-muted-foreground">{server.ip}</div>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    {getStatusBadge(server.status)}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <Progress value={server.cpu} className="w-16 h-2" />
                      <span className="text-sm text-foreground">{server.cpu}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <Progress value={server.memory} className="w-16 h-2" />
                      <span className="text-sm text-foreground">{server.memory}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <Progress value={server.disk} className="w-16 h-2" />
                      <span className="text-sm text-foreground">{server.disk}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-foreground">{server.uptime}</span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1">
                      {server.status === 'offline' ? (
                        <Button 
                          size="sm" 
                          variant="ghost" 
                          className="h-8 w-8 p-0"
                          onClick={() => handleServerAction(server.id, 'start')}
                          title="Start Server"
                        >
                          <Play className="w-4 h-4" />
                        </Button>
                      ) : (
                        <Button 
                          size="sm" 
                          variant="ghost" 
                          className="h-8 w-8 p-0"
                          onClick={() => handleServerAction(server.id, 'stop')}
                          title="Stop Server"
                        >
                          <Square className="w-4 h-4" />
                        </Button>
                      )}
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="h-8 w-8 p-0"
                        onClick={() => handleServerAction(server.id, 'monitor')}
                        title="Monitor Server"
                      >
                        <Monitor className="w-4 h-4" />
                      </Button>
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="h-8 w-8 p-0"
                        onClick={() => handleServerAction(server.id, 'maintenance')}
                        title="Maintenance Mode"
                      >
                        <Settings className="w-4 h-4" />
                      </Button>
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="h-8 w-8 p-0 text-red-400 hover:text-red-300"
                        onClick={() => handleServerAction(server.id, 'remove')}
                        title="Remove Server"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};