import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/hooks/useAuth';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Badge } from '@/components/ui/badge';
import { 
  Search, 
  Trash2, 
  Download, 
  ChevronDown, 
  ChevronRight,
  History,
  Layers,
  HardDrive,
  Calendar,
  Hash
} from 'lucide-react';
import { StatCard } from '@/components/StatCard';
import { dockerApi, DockerImage as BackendDockerImage, DockerImagesResponse, ServerListItem } from '@/lib/docker-api';

export const AdminImages: React.FC = () => {
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [images, setImages] = useState<BackendDockerImage[]>([]);
  const [servers, setServers] = useState<ServerListItem[]>([]);
  const [selectedServer, setSelectedServer] = useState<string>('all');
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Load servers list on component mount
  useEffect(() => {
    loadServers();
  }, []);

  // Load images when server selection changes
  useEffect(() => {
    if (servers.length > 0) {
      loadImages();
    }
  }, [selectedServer, servers]);

  const loadServers = async () => {
    if (!user?.token) return;
    
    try {
      setLoading(true);
      const response = await dockerApi.getServersList(user.token);
      if (response.success && response.data) {
        setServers(response.data.servers);
      } else {
        setError(response.error || 'Failed to load servers');
      }
    } catch (err) {
      setError('Failed to load servers');
    } finally {
      setLoading(false);
    }
  };

  const loadImages = async () => {
    if (!user?.token) return;
    
    try {
      setLoading(true);
      setError(null);
      const serverId = selectedServer === 'all' ? undefined : selectedServer;
      const response = await dockerApi.getDockerImages(user.token, serverId);
      
      if (response.success && response.data) {
        // Flatten images from all servers
        const allImages: BackendDockerImage[] = [];
        response.data.servers.forEach(server => {
          if (server.images) {
            allImages.push(...server.images);
          }
        });
        setImages(allImages);
      } else {
        setError(response.error || 'Failed to load Docker images');
      }
    } catch (err) {
      setError('Failed to load Docker images');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadImages();
    setRefreshing(false);
  };

  const filteredImages = images.filter(image =>
    image.repository.toLowerCase().includes(searchTerm.toLowerCase()) ||
    image.tag.toLowerCase().includes(searchTerm.toLowerCase()) ||
    image.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const toggleRowExpansion = (imageId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(imageId)) {
      newExpanded.delete(imageId);
    } else {
      newExpanded.add(imageId);
    }
    setExpandedRows(newExpanded);
  };

  const handleDeleteImage = (imageId: string) => {
    console.log('Deleting image:', imageId);
    // Implement delete logic
  };

  const handlePullImage = (repository: string, tag: string) => {
    console.log('Pulling image:', `${repository}:${tag}`);
    // Implement pull logic
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const totalSize = images.reduce((sum, image) => sum + (image.size || 0), 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Docker Images</h1>
          <p className="text-muted-foreground">Manage Docker images, layers, and history</p>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Images"
          value={images.length.toString()}
          icon={HardDrive}
        />
        <StatCard
          title="Total Size"
          value={formatBytes(totalSize)}
          icon={Layers}
        />
        <StatCard
          title="Latest Tag"
          value={images.filter(img => img.tag === 'latest').length.toString()}
          icon={Hash}
        />
        <StatCard
          title="Last Updated"
          value="2h ago"
          icon={Calendar}
        />
      </div>

      {/* Search and Actions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Docker Images</CardTitle>
            <div className="flex items-center space-x-2">
              <Select value={selectedServer} onValueChange={setSelectedServer}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Select server" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Servers</SelectItem>
                  {servers.map((server) => (
                    <SelectItem key={server.id} value={server.id}>
                      {server.name} ({server.status})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search images..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8 w-[250px]"
                />
              </div>
              <Button onClick={handleRefresh} disabled={loading || refreshing}>
                <Download className="h-4 w-4 mr-2" />
                {refreshing ? 'Refreshing...' : 'Refresh'}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-8"></TableHead>
                <TableHead>Repository</TableHead>
                <TableHead>Tag</TableHead>
                <TableHead>Image ID</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredImages.map((image) => (
                <React.Fragment key={image.id}>
                  <TableRow className="hover:bg-muted/50">
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleRowExpansion(image.id)}
                      >
                        {expandedRows.has(image.id) ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </Button>
                    </TableCell>
                    <TableCell className="font-medium">{image.repository}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{image.tag}</Badge>
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {image.short_id || image.id.substring(0, 20)}...
                    </TableCell>
                    <TableCell>{formatBytes(image.size || 0)}</TableCell>
                    <TableCell>{formatDate(image.created)}</TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => console.log('View details for:', image.id)}
                        >
                          <Layers className="h-4 w-4 mr-1" />
                          Details
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDeleteImage(image.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};