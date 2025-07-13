import React from 'react';
import { Server, RefreshCw, Plus, Settings, Monitor, Play, Square, Trash2, AlertTriangle } from 'lucide-react';
import { StatCard } from '../components/StatCard';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';

export const AdminServers: React.FC = () => {
  // Mock data
  const stats = [
    { title: 'Total Servers', value: 24, change: '+2', icon: Server, color: 'blue' as const },
    { title: 'Online', value: 21, change: '+1', icon: Monitor, color: 'green' as const },
    { title: 'Offline', value: 2, change: '0', icon: AlertTriangle, color: 'red' as const },
    { title: 'Maintenance', value: 1, change: '-1', icon: Settings, color: 'orange' as const },
  ];

  const servers = [
    {
      id: 'web-server-01',
      ip: '192.168.1.100',
      status: 'online' as const,
      cpu: 65,
      memory: 78,
      disk: 45,
      uptime: '15d 4h',
      type: 'web'
    },
    {
      id: 'db-server-01',
      ip: '192.168.1.101',
      status: 'online' as const,
      cpu: 42,
      memory: 89,
      disk: 67,
      uptime: '8d 12h',
      type: 'database'
    },
    {
      id: 'api-server-01',
      ip: '192.168.1.102',
      status: 'offline' as const,
      cpu: 0,
      memory: 0,
      disk: 0,
      uptime: '-',
      type: 'api'
    },
    {
      id: 'cache-server-01',
      ip: '192.168.1.103',
      status: 'maintenance' as const,
      cpu: 15,
      memory: 34,
      disk: 23,
      uptime: '2d 6h',
      type: 'cache'
    },
  ];

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
          <Button variant="outline" className="gap-2">
            <RefreshCw className="w-4 h-4" />
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
        {stats.map((stat, index) => (
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
                        <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                          <Play className="w-4 h-4" />
                        </Button>
                      ) : (
                        <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                          <Square className="w-4 h-4" />
                        </Button>
                      )}
                      <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                        <Monitor className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                        <Settings className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-red-400 hover:text-red-300">
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