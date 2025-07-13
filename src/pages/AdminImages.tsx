import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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

interface DockerImage {
  id: string;
  repository: string;
  tag: string;
  imageId: string;
  size: string;
  created: string;
  layers: ImageLayer[];
  history: ImageHistory[];
}

interface ImageLayer {
  id: string;
  size: string;
  command: string;
  created: string;
}

interface ImageHistory {
  id: string;
  created: string;
  createdBy: string;
  size: string;
  comment?: string;
}

// Mock data
const mockImages: DockerImage[] = [
  {
    id: '1',
    repository: 'nginx',
    tag: 'latest',
    imageId: 'sha256:abc123...',
    size: '142MB',
    created: '2024-01-15T10:30:00Z',
    layers: [
      { id: 'layer1', size: '80MB', command: 'FROM debian:bullseye-slim', created: '2024-01-15T10:25:00Z' },
      { id: 'layer2', size: '35MB', command: 'RUN apt-get update && apt-get install -y nginx', created: '2024-01-15T10:27:00Z' },
      { id: 'layer3', size: '27MB', command: 'COPY nginx.conf /etc/nginx/', created: '2024-01-15T10:30:00Z' },
    ],
    history: [
      { id: 'hist1', created: '2024-01-15T10:25:00Z', createdBy: 'FROM debian:bullseye-slim', size: '80MB' },
      { id: 'hist2', created: '2024-01-15T10:27:00Z', createdBy: 'RUN apt-get update && apt-get install -y nginx', size: '35MB' },
      { id: 'hist3', created: '2024-01-15T10:30:00Z', createdBy: 'COPY nginx.conf /etc/nginx/', size: '27MB' },
    ]
  },
  {
    id: '2',
    repository: 'mysql',
    tag: '8.0',
    imageId: 'sha256:def456...',
    size: '521MB',
    created: '2024-01-14T15:20:00Z',
    layers: [
      { id: 'layer4', size: '200MB', command: 'FROM ubuntu:20.04', created: '2024-01-14T15:15:00Z' },
      { id: 'layer5', size: '221MB', command: 'RUN apt-get update && apt-get install -y mysql-server', created: '2024-01-14T15:18:00Z' },
      { id: 'layer6', size: '100MB', command: 'COPY my.cnf /etc/mysql/', created: '2024-01-14T15:20:00Z' },
    ],
    history: [
      { id: 'hist4', created: '2024-01-14T15:15:00Z', createdBy: 'FROM ubuntu:20.04', size: '200MB' },
      { id: 'hist5', created: '2024-01-14T15:18:00Z', createdBy: 'RUN apt-get update && apt-get install -y mysql-server', size: '221MB' },
      { id: 'hist6', created: '2024-01-14T15:20:00Z', createdBy: 'COPY my.cnf /etc/mysql/', size: '100MB' },
    ]
  },
  {
    id: '3',
    repository: 'redis',
    tag: 'alpine',
    imageId: 'sha256:ghi789...',
    size: '32MB',
    created: '2024-01-13T08:45:00Z',
    layers: [
      { id: 'layer7', size: '5MB', command: 'FROM alpine:3.18', created: '2024-01-13T08:40:00Z' },
      { id: 'layer8', size: '27MB', command: 'RUN apk add --no-cache redis', created: '2024-01-13T08:45:00Z' },
    ],
    history: [
      { id: 'hist7', created: '2024-01-13T08:40:00Z', createdBy: 'FROM alpine:3.18', size: '5MB' },
      { id: 'hist8', created: '2024-01-13T08:45:00Z', createdBy: 'RUN apk add --no-cache redis', size: '27MB' },
    ]
  },
];

export const AdminImages: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [images] = useState<DockerImage[]>(mockImages);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const filteredImages = images.filter(image =>
    image.repository.toLowerCase().includes(searchTerm.toLowerCase()) ||
    image.tag.toLowerCase().includes(searchTerm.toLowerCase()) ||
    image.imageId.toLowerCase().includes(searchTerm.toLowerCase())
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

  const totalSize = images.reduce((sum, image) => {
    const size = parseFloat(image.size.replace(/[^\d.]/g, ''));
    const unit = image.size.replace(/[\d.]/g, '');
    return sum + (unit === 'GB' ? size * 1024 : size);
  }, 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Docker Images</h1>
          <p className="text-muted-foreground">Manage Docker images, layers, and history</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Images"
          value={images.length.toString()}
          icon={HardDrive}
        />
        <StatCard
          title="Total Size"
          value={`${(totalSize / 1024).toFixed(1)} GB`}
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
            <CardTitle>Images</CardTitle>
            <div className="flex items-center space-x-2">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search images..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8 w-[250px]"
                />
              </div>
              <Button>
                <Download className="h-4 w-4 mr-2" />
                Pull Image
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
                      {image.imageId.substring(0, 20)}...
                    </TableCell>
                    <TableCell>{image.size}</TableCell>
                    <TableCell>{formatDate(image.created)}</TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button variant="outline" size="sm">
                              <Layers className="h-4 w-4 mr-1" />
                              Layers
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-4xl">
                            <DialogHeader>
                              <DialogTitle>Image Layers - {image.repository}:{image.tag}</DialogTitle>
                            </DialogHeader>
                            <div className="space-y-2">
                              {image.layers.map((layer, index) => (
                                <div key={layer.id} className="border rounded-lg p-3">
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-2">
                                      <Badge variant="outline">Layer {index + 1}</Badge>
                                      <span className="font-mono text-sm">{layer.id}</span>
                                    </div>
                                    <Badge>{layer.size}</Badge>
                                  </div>
                                  <p className="text-sm text-muted-foreground mt-2">{layer.command}</p>
                                  <p className="text-xs text-muted-foreground">{formatDate(layer.created)}</p>
                                </div>
                              ))}
                            </div>
                          </DialogContent>
                        </Dialog>

                        <Dialog>
                          <DialogTrigger asChild>
                            <Button variant="outline" size="sm">
                              <History className="h-4 w-4 mr-1" />
                              History
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-4xl">
                            <DialogHeader>
                              <DialogTitle>Image History - {image.repository}:{image.tag}</DialogTitle>
                            </DialogHeader>
                            <div className="space-y-2">
                              {image.history.map((entry, index) => (
                                <div key={entry.id} className="border rounded-lg p-3">
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-2">
                                      <Badge variant="outline">Step {index + 1}</Badge>
                                      <span className="text-sm">{formatDate(entry.created)}</span>
                                    </div>
                                    <Badge>{entry.size}</Badge>
                                  </div>
                                  <p className="text-sm text-muted-foreground mt-2">{entry.createdBy}</p>
                                  {entry.comment && (
                                    <p className="text-xs text-muted-foreground mt-1">{entry.comment}</p>
                                  )}
                                </div>
                              ))}
                            </div>
                          </DialogContent>
                        </Dialog>

                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handlePullImage(image.repository, image.tag)}
                        >
                          <Download className="h-4 w-4 mr-1" />
                          Pull
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
                  
                  {expandedRows.has(image.id) && (
                    <TableRow>
                      <TableCell colSpan={7} className="bg-muted/30">
                        <div className="p-4 space-y-4">
                          <div>
                            <h4 className="font-semibold mb-2">Quick Layer Overview</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                              {image.layers.slice(0, 4).map((layer, index) => (
                                <div key={layer.id} className="bg-background border rounded p-2">
                                  <div className="flex items-center justify-between text-sm">
                                    <span>Layer {index + 1}</span>
                                    <Badge variant="secondary" className="text-xs">{layer.size}</Badge>
                                  </div>
                                  <p className="text-xs text-muted-foreground mt-1 truncate">
                                    {layer.command}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                            <span>Total Layers: {image.layers.length}</span>
                            <span>•</span>
                            <span>Created: {formatDate(image.created)}</span>
                            <span>•</span>
                            <span>ID: {image.imageId}</span>
                          </div>
                        </div>
                      </TableCell>
                    </TableRow>
                  )}
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};