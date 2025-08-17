import React, { useState, useEffect } from 'react';
import { Monitor, Terminal, Cpu, HardDrive, MemoryStick, Activity, ExternalLink } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { VSCodeIcon } from '../components/icons/VSCodeIcon';
import { JupyterIcon } from '../components/icons/JupyterIcon';
import { ProgressBar } from '../components/ui/progress-bar';

interface SystemStats {
  cpu: {
    usage: number;
    cores: number;
  };
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  disk: {
    used: number;
    total: number;
    percentage: number;
  };
  host: {
    cpuUsage: number;
    memoryUsage: number;
    loadAverage: number;
    swapUsage: number;
  };
}

interface Application {
  id: string;
  name: string;
  icon: React.ComponentType<any>;
  status: 'running' | 'stopped' | 'starting';
  port?: number;
  url?: string;
  description: string;
}

export const UserDashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<SystemStats>({
    cpu: { usage: 0.418, cores: 12 },
    memory: { used: 0.186, total: 32, percentage: 60 },
    disk: { used: 229, total: 467, percentage: 49 },
    host: {
      cpuUsage: 19,
      memoryUsage: 70,
      loadAverage: 0.31,
      swapUsage: 17.5
    }
  });

  const applications: Application[] = [
    {
      id: 'code-server',
      name: 'code-server',
      icon: VSCodeIcon,
      status: 'running',
      port: 8081,
      url: '/code-server',
      description: 'VS Code in the browser'
    },
    {
      id: 'jupyter',
      name: 'Jupyter Notebook',
      icon: JupyterIcon,
      status: 'running',
      port: 8888,
      url: '/jupyter',
      description: 'Python data science environment'
    },
    {
      id: 'intellij',
      name: 'IntelliJ IDEA Ultimate',
      icon: Monitor,
      status: 'stopped',
      port: 8082,
      url: '/intellij',
      description: 'IntelliJ IDEA Ultimate IDE'
    },
    {
      id: 'terminal',
      name: 'Terminal',
      icon: Terminal,
      status: 'running',
      port: 8083,
      url: '/terminal',
      description: 'Web-based terminal access'
    }
  ];

  const handleApplicationClick = (app: Application) => {
    if (app.status === 'running' && app.url) {
      window.open(app.url, '_blank');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-500';
      case 'stopped':
        return 'bg-red-500';
      case 'starting':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  const formatBytes = (bytes: number, decimals = 1) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          <span className="text-lg font-medium">Dashboard</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-muted-foreground">Connect via SSH</span>
          <button className="text-muted-foreground hover:text-foreground">
            <ExternalLink className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Applications Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {applications.map((app) => (
          <div
            key={app.id}
            onClick={() => handleApplicationClick(app)}
            className={`
              relative bg-card rounded-lg p-4 border border-border transition-all duration-200
              ${app.status === 'running' ? 'hover:bg-accent cursor-pointer' : 'opacity-60 cursor-not-allowed'}
            `}
          >
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-primary rounded">
                <app.icon className="w-5 h-5 text-primary-foreground" />
              </div>
              <div className={`w-2 h-2 rounded-full ${getStatusColor(app.status)}`}></div>
            </div>
            <h3 className="font-medium text-sm mb-1">{app.name}</h3>
            <p className="text-xs text-muted-foreground">{app.description}</p>
          </div>
        ))}
      </div>

      {/* System Statistics */}
      <div className="space-y-6 mb-6">
        {/* Container Statistics */}
        <div>
          <h3 className="text-lg font-semibold text-foreground mb-3">Container Resources</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-card rounded-lg p-4 border border-border">
              <div className="flex items-center gap-2 mb-3">
                <Cpu className="w-4 h-4 text-blue-500" />
                <span className="text-xs text-muted-foreground">CPU Usage</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">{stats.cpu.usage} cores</span>
                  <span className="text-xs text-muted-foreground">{((stats.cpu.usage / stats.cpu.cores) * 100).toFixed(1)}%</span>
                </div>
                <ProgressBar 
                  value={stats.cpu.usage} 
                  max={stats.cpu.cores} 
                  size="md"
                />
              </div>
            </div>

            <div className="bg-card rounded-lg p-4 border border-border">
              <div className="flex items-center gap-2 mb-3">
                <MemoryStick className="w-4 h-4 text-purple-500" />
                <span className="text-xs text-muted-foreground">RAM Usage</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">{stats.memory.used}/{stats.memory.total} GiB</span>
                  <span className="text-xs text-muted-foreground">{stats.memory.percentage.toFixed(1)}%</span>
                </div>
                <ProgressBar 
                  value={stats.memory.percentage} 
                  max={100} 
                  size="md"
                />
              </div>
            </div>

            <div className="bg-card rounded-lg p-4 border border-border">
              <div className="flex items-center gap-2 mb-3">
                <HardDrive className="w-4 h-4 text-yellow-500" />
                <span className="text-xs text-muted-foreground">Home Disk</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">{stats.disk.used}/{stats.disk.total} GiB</span>
                  <span className="text-xs text-muted-foreground">{stats.disk.percentage}%</span>
                </div>
                <ProgressBar 
                  value={stats.disk.percentage} 
                  max={100} 
                  size="md"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Host Statistics */}
        <div>
          <h3 className="text-lg font-semibold text-foreground mb-3">Host Resources</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-card rounded-lg p-4 border border-border">
              <div className="flex items-center gap-2 mb-3">
                <Cpu className="w-4 h-4 text-red-500" />
                <span className="text-xs text-muted-foreground">CPU Usage</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">{stats.cpu.cores}/12 cores</span>
                  <span className="text-xs text-muted-foreground">{stats.host.cpuUsage}%</span>
                </div>
                <ProgressBar 
                  value={stats.host.cpuUsage} 
                  max={100} 
                  size="md"
                />
              </div>
            </div>

            <div className="bg-card rounded-lg p-4 border border-border">
              <div className="flex items-center gap-2 mb-3">
                <MemoryStick className="w-4 h-4 text-blue-500" />
                <span className="text-xs text-muted-foreground">Memory Usage</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">10.7/15.3 GiB</span>
                  <span className="text-xs text-muted-foreground">{stats.host.memoryUsage}%</span>
                </div>
                <ProgressBar 
                  value={stats.host.memoryUsage} 
                  max={100} 
                  size="md"
                />
              </div>
            </div>

            <div className="bg-card rounded-lg p-4 border border-border">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-4 h-4 text-green-500" />
                <span className="text-xs text-muted-foreground">Load Average</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">{stats.host.loadAverage}</span>
                  <span className="text-xs text-muted-foreground">{((stats.host.loadAverage / stats.cpu.cores) * 100).toFixed(1)}%</span>
                </div>
                <ProgressBar 
                  value={stats.host.loadAverage} 
                  max={stats.cpu.cores} 
                  size="md"
                  color="success"
                />
              </div>
            </div>

            <div className="bg-card rounded-lg p-4 border border-border">
              <div className="flex items-center gap-2 mb-3">
                <HardDrive className="w-4 h-4 text-orange-500" />
                <span className="text-xs text-muted-foreground">Swap Usage</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">{stats.host.swapUsage}%</span>
                  <span className="text-xs text-muted-foreground">0.7/4.0 GiB</span>
                </div>
                <ProgressBar 
                  value={stats.host.swapUsage} 
                  max={100} 
                  size="md"
                  color="warning"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Logs Section */}
      <div className="bg-card rounded-lg border border-border">
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Logs</span>
          </div>
          <button className="text-xs text-primary hover:text-primary/80">
            Download logs
          </button>
        </div>
        <div className="p-4">
          <div className="font-mono text-xs text-muted-foreground space-y-1">
            <div>[{new Date().toISOString()}] Container started successfully</div>
            <div>[{new Date().toISOString()}] VS Code Desktop initialized</div>
            <div>[{new Date().toISOString()}] code-server listening on port 8081</div>
            <div>[{new Date().toISOString()}] Jupyter Notebook started on port 8888</div>
            <div>[{new Date().toISOString()}] System resources within normal limits</div>
          </div>
        </div>
      </div>
    </div>
  );
};
