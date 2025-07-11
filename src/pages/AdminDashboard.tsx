
import React from 'react';
import { Container, Image, Users, Activity, AlertTriangle, CheckCircle } from 'lucide-react';
import { StatCard } from '../components/StatCard';
import { ContainerCard } from '../components/ContainerCard';

export const AdminDashboard: React.FC = () => {
  // Mock data
  const stats = [
    { title: 'Total Containers', value: 12, change: '+2', icon: Container, color: 'blue' as const },
    { title: 'Running Containers', value: 8, change: '+1', icon: CheckCircle, color: 'green' as const },
    { title: 'Docker Images', value: 24, change: '+3', icon: Image, color: 'purple' as const },
    { title: 'Active Users', value: 5, change: '0', icon: Users, color: 'orange' as const },
  ];

  const recentContainers = [
    {
      id: 'c1a2b3c4d5e6',
      name: 'webapp-frontend',
      image: 'nginx:latest',
      status: 'running' as const,
      ports: ['80:3000'],
      created: '2 hours ago',
      cpuUsage: 25.4,
      memoryUsage: 67.2,
    },
    {
      id: 'f1g2h3i4j5k6',
      name: 'api-backend',
      image: 'node:18-alpine',
      status: 'running' as const,
      ports: ['8080:8080'],
      created: '5 hours ago',
      cpuUsage: 45.1,
      memoryUsage: 23.8,
    },
    {
      id: 'l1m2n3o4p5q6',
      name: 'database',
      image: 'postgres:15',
      status: 'stopped' as const,
      ports: ['5432:5432'],
      created: '1 day ago',
      cpuUsage: 0,
      memoryUsage: 0,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Admin Dashboard</h1>
        <p className="text-muted-foreground">Monitor and manage your Docker infrastructure</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <StatCard key={index} {...stat} />
        ))}
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-card backdrop-blur-sm border border-border rounded-xl p-6">
          <h2 className="text-xl font-semibold text-foreground mb-4">System Health</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Docker Daemon</span>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-green-400 text-sm">Running</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">CPU Usage</span>
              <span className="text-foreground">34%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Memory Usage</span>
              <span className="text-foreground">67%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Disk Usage</span>
              <span className="text-foreground">45%</span>
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
      </div>
    </div>
  );
};
