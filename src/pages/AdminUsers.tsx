import React from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { 
  Users, 
  Container, 
  Server, 
  Plus, 
  Edit, 
  Trash2,
  Circle
} from 'lucide-react';

const mockUsers = [
  {
    id: '1',
    name: 'John Doe',
    email: 'john.doe@example.com',
    role: 'Admin',
    container: 'container-jd-001',
    containerStatus: 'running',
    resources: {
      cpu: '8 cores',
      ram: '16GB',
      gpu: '2 cores, 24GB'
    },
    server: 'Server 1',
    serverLocation: 'us-east-1',
    status: 'Running'
  },
  {
    id: '2',
    name: 'Alice Smith',
    email: 'alice.smith@example.com',
    role: 'Developer',
    container: 'container-as-002',
    containerStatus: 'stopped',
    resources: {
      cpu: '4 cores',
      ram: '8GB',
      gpu: '1 core, 12GB'
    },
    server: 'Server 2',
    serverLocation: 'us-west-2',
    status: 'Stopped'
  },
  {
    id: '3',
    name: 'Bob Johnson',
    email: 'bob.johnson@example.com',
    role: 'User',
    container: 'container-bj-003',
    containerStatus: 'running',
    resources: {
      cpu: '2 cores',
      ram: '4GB',
      gpu: '0 cores, 0GB'
    },
    server: 'Server 3',
    serverLocation: 'eu-west-1',
    status: 'Running'
  },
  {
    id: '4',
    name: 'Carol Wilson',
    email: 'carol.wilson@example.com',
    role: 'Developer',
    container: 'container-cw-004',
    containerStatus: 'error',
    resources: {
      cpu: '6 cores',
      ram: '12GB',
      gpu: '1 core, 16GB'
    },
    server: 'Server 4',
    serverLocation: 'ap-south-1',
    status: 'Error'
  }
];

const getStatusColor = (status: string) => {
  switch (status.toLowerCase()) {
    case 'running':
      return 'bg-green-500/10 text-green-700 border-green-500/20';
    case 'stopped':
      return 'bg-yellow-500/10 text-yellow-700 border-yellow-500/20';
    case 'error':
      return 'bg-red-500/10 text-red-700 border-red-500/20';
    default:
      return 'bg-gray-500/10 text-gray-700 border-gray-500/20';
  }
};

const getContainerStatusIcon = (status: string) => {
  const color = status === 'running' ? 'text-green-500' : 
                status === 'stopped' ? 'text-yellow-500' : 'text-red-500';
  return <Circle className={`w-2 h-2 fill-current ${color}`} />;
};

export const AdminUsers: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-foreground">User Management</h1>
          <p className="text-muted-foreground mt-1">Manage users and their container resources</p>
        </div>
        <Button className="gap-2">
          <Plus className="w-4 h-4" />
          Add New User
        </Button>
      </div>

      {/* Users Section */}
      <div className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-foreground">Users</h2>
          <p className="text-muted-foreground text-sm">Manage existing users and their container allocations</p>
        </div>

        {/* Users Table */}
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Container</TableHead>
                  <TableHead>Resources</TableHead>
                  <TableHead>Server</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mockUsers.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="w-8 h-8">
                          <AvatarFallback className="text-xs">
                            {user.name.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="font-medium text-foreground">{user.name}</div>
                          <div className="text-sm text-muted-foreground">{user.email}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{user.role}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getContainerStatusIcon(user.containerStatus)}
                        <span className="font-mono text-sm">{user.container}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm space-y-1">
                        <div>CPU: {user.resources.cpu}</div>
                        <div>RAM: {user.resources.ram}</div>
                        <div>GPU: {user.resources.gpu}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <div className="font-medium">{user.server}</div>
                        <div className="text-muted-foreground">{user.serverLocation}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(user.status)}>
                        {user.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-destructive hover:text-destructive">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">24</div>
            <p className="text-xs text-muted-foreground">
              +2 from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Containers</CardTitle>
            <Container className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">18</div>
            <p className="text-xs text-muted-foreground">
              75% utilization
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Available Servers</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4</div>
            <p className="text-xs text-muted-foreground">
              All regions online
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};