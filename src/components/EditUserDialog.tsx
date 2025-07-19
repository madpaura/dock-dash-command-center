import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Separator } from './ui/separator';
import { AdminUser } from '../lib/api';
import { CheckCircle, XCircle, Server, Cpu, HardDrive, Zap } from 'lucide-react';

interface EditUserDialogProps {
  user: AdminUser | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (userId: string, userData: Partial<AdminUser>) => Promise<void>;
  onApprove?: (userId: string, serverAssignment: string, resources: ResourceAllocation) => Promise<void>;
  onCreate?: (userData: {
    name: string;
    email: string;
    password?: string;
    role: string;
    status: string;
    server: string;
    resources: ResourceAllocation;
  }) => Promise<void>;
  mode?: 'edit' | 'create';
}

interface ResourceAllocation {
  cpu: string;
  ram: string;
  gpu: string;
}

const resourcePresets = {
  basic: { cpu: '2 cores', ram: '4GB', gpu: '0 cores, 0GB' },
  standard: { cpu: '4 cores', ram: '8GB', gpu: '1 core, 12GB' },
  premium: { cpu: '8 cores', ram: '16GB', gpu: '2 cores, 24GB' },
  custom: { cpu: '', ram: '', gpu: '' }
};

const serverOptions = [
  { id: 'server-1', name: 'Server 1', location: 'us-east-1', status: 'online' },
  { id: 'server-2', name: 'Server 2', location: 'us-west-2', status: 'online' },
  { id: 'server-3', name: 'Server 3', location: 'eu-west-1', status: 'online' },
  { id: 'server-4', name: 'Server 4', location: 'ap-south-1', status: 'online' }
];

export const EditUserDialog: React.FC<EditUserDialogProps> = ({
  user,
  isOpen,
  onClose,
  onSave,
  onApprove,
  onCreate,
  mode = 'edit'
}) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    role: '',
    status: '',
    password: ''
  });
  
  const [selectedServer, setSelectedServer] = useState('');
  const [resourcePreset, setResourcePreset] = useState<keyof typeof resourcePresets>('standard');
  const [customResources, setCustomResources] = useState<ResourceAllocation>(resourcePresets.standard);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (mode === 'create') {
      // Reset form for create mode
      setFormData({
        name: '',
        email: '',
        role: 'User',
        status: 'Stopped',
        password: ''
      });
      setSelectedServer('server-1');
      setResourcePreset('standard');
      setCustomResources(resourcePresets.standard);
    } else if (user) {
      setFormData({
        name: user.name,
        email: user.email,
        role: user.role,
        status: user.status,
        password: ''
      });
      
      // Set default server based on current assignment
      const currentServer = serverOptions.find(s => s.name === user.server);
      setSelectedServer(currentServer?.id || 'server-1');
      
      // Set resources based on current allocation
      const currentResources = { cpu: user.resources.cpu, ram: user.resources.ram, gpu: user.resources.gpu };
      setCustomResources(currentResources);
      
      // Try to match with a preset
      const matchingPreset = Object.entries(resourcePresets).find(([key, preset]) => 
        key !== 'custom' && 
        preset.cpu === currentResources.cpu && 
        preset.ram === currentResources.ram && 
        preset.gpu === currentResources.gpu
      );
      
      setResourcePreset(matchingPreset ? matchingPreset[0] as keyof typeof resourcePresets : 'custom');
    }
  }, [user, mode]);

  const handleResourcePresetChange = (preset: keyof typeof resourcePresets) => {
    setResourcePreset(preset);
    if (preset !== 'custom') {
      setCustomResources(resourcePresets[preset]);
    }
  };

  const handleSave = async () => {
    if (mode === 'create') {
      await handleCreate();
      return;
    }
    
    if (!user) return;
    
    setIsLoading(true);
    try {
      const userData: Partial<AdminUser> = {
        name: formData.name,
        email: formData.email,
        role: formData.role,
        status: formData.status
      };
      
      await onSave(user.id, userData);
      onClose();
    } catch (error) {
      console.error('Error saving user:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!onCreate) return;
    
    setIsLoading(true);
    try {
      const selectedServerData = serverOptions.find(s => s.id === selectedServer);
      const userData = {
        name: formData.name,
        email: formData.email,
        password: formData.password || undefined,
        role: formData.role,
        status: formData.status,
        server: selectedServerData?.name || 'Server 1',
        resources: customResources
      };
      
      await onCreate(userData);
      onClose();
    } catch (error) {
      console.error('Error creating user:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!user || !onApprove) return;
    
    setIsLoading(true);
    try {
      const selectedServerData = serverOptions.find(s => s.id === selectedServer);
      await onApprove(user.id, selectedServerData?.name || 'Server 1', customResources);
      onClose();
    } catch (error) {
      console.error('Error approving user:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const isPendingApproval = mode === 'edit' && (user?.role === 'Pending' || user?.status === 'Stopped');
  const isCreateMode = mode === 'create';
  const selectedServerData = serverOptions.find(s => s.id === selectedServer);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {isCreateMode ? 'Create New User' : `Edit User: ${user?.name}`}
            {isPendingApproval && (
              <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
                Pending Approval
              </Badge>
            )}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Enter user name"
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="Enter email address"
                  />
                </div>
              </div>
              
              {isCreateMode && (
                <div>
                  <Label htmlFor="password">Password (optional)</Label>
                  <Input
                    id="password"
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder="Leave empty for default password (defaultpass123)"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    If left empty, default password "defaultpass123" will be used
                  </p>
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="role">Role</Label>
                  <Select value={formData.role} onValueChange={(value) => setFormData({ ...formData, role: value })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Admin">Admin</SelectItem>
                      <SelectItem value="Developer">Developer</SelectItem>
                      <SelectItem value="User">User</SelectItem>
                      <SelectItem value="Pending">Pending</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="status">Status</Label>
                  <Select value={formData.status} onValueChange={(value) => setFormData({ ...formData, status: value })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Running">Running</SelectItem>
                      <SelectItem value="Stopped">Stopped</SelectItem>
                      <SelectItem value="Error">Error</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Server Assignment */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Server className="w-5 h-5" />
                Server Assignment
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div>
                <Label htmlFor="server">Assigned Server</Label>
                <Select value={selectedServer} onValueChange={setSelectedServer}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {serverOptions.map((server) => (
                      <SelectItem key={server.id} value={server.id}>
                        <div className="flex items-center justify-between w-full">
                          <span>{server.name}</span>
                          <span className="text-sm text-muted-foreground ml-2">
                            {server.location}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedServerData && (
                  <div className="mt-2 p-3 bg-muted rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{selectedServerData.name}</span>
                      <Badge variant={selectedServerData.status === 'online' ? 'default' : 'destructive'}>
                        {selectedServerData.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      Location: {selectedServerData.location}
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Resource Allocation */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="w-5 h-5" />
                Resource Allocation
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="preset">Resource Preset</Label>
                <Select value={resourcePreset} onValueChange={handleResourcePresetChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="basic">Basic (2 CPU, 4GB RAM, No GPU)</SelectItem>
                    <SelectItem value="standard">Standard (4 CPU, 8GB RAM, 1 GPU)</SelectItem>
                    <SelectItem value="premium">Premium (8 CPU, 16GB RAM, 2 GPU)</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="cpu" className="flex items-center gap-2">
                    <Cpu className="w-4 h-4" />
                    CPU
                  </Label>
                  <Input
                    id="cpu"
                    value={customResources.cpu}
                    onChange={(e) => setCustomResources({ ...customResources, cpu: e.target.value })}
                    disabled={resourcePreset !== 'custom'}
                  />
                </div>
                <div>
                  <Label htmlFor="ram" className="flex items-center gap-2">
                    <HardDrive className="w-4 h-4" />
                    RAM
                  </Label>
                  <Input
                    id="ram"
                    value={customResources.ram}
                    onChange={(e) => setCustomResources({ ...customResources, ram: e.target.value })}
                    disabled={resourcePreset !== 'custom'}
                  />
                </div>
                <div>
                  <Label htmlFor="gpu" className="flex items-center gap-2">
                    <Zap className="w-4 h-4" />
                    GPU
                  </Label>
                  <Input
                    id="gpu"
                    value={customResources.gpu}
                    onChange={(e) => setCustomResources({ ...customResources, gpu: e.target.value })}
                    disabled={resourcePreset !== 'custom'}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          
          {isPendingApproval && onApprove && (
            <Button 
              onClick={handleApprove} 
              disabled={isLoading}
              className="bg-green-600 hover:bg-green-700"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              {isLoading ? 'Approving...' : 'Approve & Assign'}
            </Button>
          )}
          
          <Button onClick={handleSave} disabled={isLoading}>
            {isLoading ? (isCreateMode ? 'Creating...' : 'Saving...') : (isCreateMode ? 'Create User' : 'Save Changes')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
