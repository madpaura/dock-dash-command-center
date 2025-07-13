import React, { useState } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { 
  Download, 
  Trash2, 
  Search,
  Eye,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown
} from 'lucide-react';

interface LogEntry {
  id: string;
  level: 'ERROR' | 'WARN' | 'INFO' | 'DEBUG';
  timestamp: string;
  user: string;
  source: string;
  message: string;
}

const mockLogs: LogEntry[] = [
  {
    id: '1',
    level: 'ERROR',
    timestamp: '2024-01-15 14:32:15',
    user: 'John Doe',
    source: 'auth.service',
    message: 'Failed login attempt from IP 192.168.1.100'
  },
  {
    id: '2',
    level: 'WARN',
    timestamp: '2024-01-15 14:31:42',
    user: 'System',
    source: 'db.connection',
    message: 'Database connection pool reaching capacity (85%)'
  },
  {
    id: '3',
    level: 'INFO',
    timestamp: '2024-01-15 14:30:15',
    user: 'Jane Smith',
    source: 'user.service',
    message: 'User profile updated successfully'
  },
  {
    id: '4',
    level: 'DEBUG',
    timestamp: '2024-01-15 14:29:33',
    user: 'Admin',
    source: 'api.gateway',
    message: 'Request processed in 245ms - GET /api/users'
  },
  {
    id: '5',
    level: 'INFO',
    timestamp: '2024-01-15 14:28:12',
    user: 'System',
    source: 'scheduler',
    message: 'Daily backup job completed successfully'
  },
  {
    id: '6',
    level: 'ERROR',
    timestamp: '2024-01-15 14:27:45',
    user: 'John Doe',
    source: 'file.service',
    message: 'File upload failed: insufficient storage space'
  }
];

const getLogLevelColor = (level: string) => {
  switch (level) {
    case 'ERROR':
      return 'bg-red-500/10 text-red-700 border-red-500/20';
    case 'WARN':
      return 'bg-yellow-500/10 text-yellow-700 border-yellow-500/20';
    case 'INFO':
      return 'bg-blue-500/10 text-blue-700 border-blue-500/20';
    case 'DEBUG':
      return 'bg-green-500/10 text-green-700 border-green-500/20';
    default:
      return 'bg-gray-500/10 text-gray-700 border-gray-500/20';
  }
};

export const AdminLogs: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [logLevel, setLogLevel] = useState('all');
  const [userFilter, setUserFilter] = useState('all');
  const [sortBy, setSortBy] = useState('timestamp');
  const [currentPage, setCurrentPage] = useState(1);

  const totalLogs = 1247;
  const logsPerPage = 6;
  const totalPages = Math.ceil(totalLogs / logsPerPage);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-foreground">System Logs</h1>
          <p className="text-muted-foreground mt-1">Monitor and analyze system activity</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2">
            <Download className="w-4 h-4" />
            Export
          </Button>
          <Button variant="outline" className="gap-2">
            <Trash2 className="w-4 h-4" />
            Clear All
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex gap-4 items-center">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input 
                placeholder="Search logs..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={logLevel} onValueChange={setLogLevel}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Log Level" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value="error">ERROR</SelectItem>
                <SelectItem value="warn">WARN</SelectItem>
                <SelectItem value="info">INFO</SelectItem>
                <SelectItem value="debug">DEBUG</SelectItem>
              </SelectContent>
            </Select>

            <Select value={userFilter} onValueChange={setUserFilter}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="User" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Users</SelectItem>
                <SelectItem value="john">John Doe</SelectItem>
                <SelectItem value="jane">Jane Smith</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="system">System</SelectItem>
              </SelectContent>
            </Select>

            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="timestamp">Timestamp</SelectItem>
                <SelectItem value="level">Level</SelectItem>
                <SelectItem value="user">User</SelectItem>
                <SelectItem value="source">Source</SelectItem>
              </SelectContent>
            </Select>

            <Button variant="ghost" size="sm" className="h-9 w-9 p-0">
              <ArrowUpDown className="w-4 h-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Level</TableHead>
                <TableHead>Timestamp</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Message</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockLogs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell>
                    <Badge className={getLogLevelColor(log.level)}>
                      {log.level}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {log.timestamp}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-muted flex items-center justify-center text-xs font-medium">
                        {log.user === 'System' ? 'SY' : log.user.split(' ').map(n => n[0]).join('')}
                      </div>
                      <span>{log.user}</span>
                    </div>
                  </TableCell>
                  <TableCell className="font-mono text-sm text-muted-foreground">
                    {log.source}
                  </TableCell>
                  <TableCell className="max-w-md">
                    <span className="text-sm">{log.message}</span>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <Eye className="w-4 h-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          Showing {logsPerPage} of {totalLogs.toLocaleString()} logs
        </div>
        
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            disabled={currentPage === 1}
            onClick={() => setCurrentPage(currentPage - 1)}
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </Button>
          
          <div className="flex gap-1">
            {[1, 2, 3].map((page) => (
              <Button
                key={page}
                variant={currentPage === page ? "default" : "outline"}
                size="sm"
                className="w-8 h-8 p-0"
                onClick={() => setCurrentPage(page)}
              >
                {page}
              </Button>
            ))}
            {totalPages > 3 && (
              <>
                <span className="px-2 py-1 text-sm text-muted-foreground">...</span>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-8 h-8 p-0"
                  onClick={() => setCurrentPage(totalPages)}
                >
                  {totalPages}
                </Button>
              </>
            )}
          </div>
          
          <Button 
            variant="outline" 
            size="sm" 
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage(currentPage + 1)}
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};