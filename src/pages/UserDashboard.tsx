
import React from 'react';
import { Container, Activity, Clock, AlertCircle } from 'lucide-react';
import { StatCard } from '../components/StatCard';
import { ContainerCard } from '../components/ContainerCard';

export const UserDashboard: React.FC = () => {
  const stats = [
    { title: 'My Containers', value: 3, change: '0', icon: Container, color: 'blue' as const },
    { title: 'Running', value: 2, change: '+1', icon: Activity, color: 'green' as const },
    { title: 'Stopped', value: 1, change: '0', icon: Clock, color: 'red' as const },
    { title: 'Alerts', value: 1, change: '0', icon: AlertCircle, color: 'orange' as const },
  ];

  const myContainers = [
    {
      id: 'u1a2b3c4d5e6',
      name: 'my-webapp',
      image: 'nginx:latest',
      status: 'running' as const,
      ports: ['80:3000'],
      created: '3 hours ago',
      cpuUsage: 15.2,
      memoryUsage: 45.6,
    },
    {
      id: 'u2f1g2h3i4j5',
      name: 'dev-api',
      image: 'node:18-alpine',
      status: 'running' as const,
      ports: ['8080:8080'],
      created: '1 day ago',
      cpuUsage: 32.7,
      memoryUsage: 28.3,
    },
    {
      id: 'u3l1m2n3o4p5',
      name: 'test-db',
      image: 'postgres:15',
      status: 'stopped' as const,
      ports: ['5432:5432'],
      created: '2 days ago',
      cpuUsage: 0,
      memoryUsage: 0,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">My Dashboard</h1>
        <p className="text-slate-400">Manage your assigned containers and monitor their performance</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <StatCard key={index} {...stat} />
        ))}
      </div>

      {/* Resource Usage Overview */}
      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Resource Usage Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400 mb-1">23.9%</div>
            <div className="text-sm text-slate-400">Average CPU</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400 mb-1">36.9%</div>
            <div className="text-sm text-slate-400">Average Memory</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-400 mb-1">1.2GB</div>
            <div className="text-sm text-slate-400">Network I/O</div>
          </div>
        </div>
      </div>

      {/* My Containers */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-6">My Containers</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {myContainers.map((container) => (
            <ContainerCard
              key={container.id}
              {...container}
              onStart={() => console.log('Start', container.name)}
              onStop={() => console.log('Stop', container.name)}
              onRestart={() => console.log('Restart', container.name)}
              onDelete={() => console.log('Delete', container.name)}
              showActions={container.status !== 'stopped'} // Limited actions for users
            />
          ))}
        </div>
      </div>
    </div>
  );
};
