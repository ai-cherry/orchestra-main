import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { 
  usePersonas, 
  useCreatePersona, 
  useUpdatePersona, 
  useDeletePersona,
  useSyncPersonas,
  PersonaCreateRequest,
  PersonaUpdateRequest
} from '@/hooks/usePersonaApi';
import usePersonaStore, { 
  useActivePersona, 
  useAllPersonas, 
  usePersonaActions 
} from '@/store/personaStore';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  MoreVertical, 
  Plus, 
  Edit, 
  Trash, 
  RefreshCw, 
  Check,
  User,
  Settings
} from 'lucide-react';

interface PersonaFormData {
  name: string;
  domain: string;
  role: string;
  description: string;
  color: string;
  icon?: string;
}

export function PersonaManager() {
  const queryClient = useQueryClient();
  
  // Store hooks
  const activePersona = useActivePersona();
  const localPersonas = useAllPersonas();
  const { setActivePersona } = usePersonaActions();
  const { syncStatus, error: storeError } = usePersonaStore();
  
  // API hooks
  const { data: apiData, isLoading, error: apiError, refetch } = usePersonas();
  const createPersonaMutation = useCreatePersona();
  const syncPersonasMutation = useSyncPersonas();
  
  // Local state
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<PersonaFormData>({
    name: '',
    domain: '',
    role: '',
    description: '',
    color: '#000000',
    icon: '',
  });

  // Use API data if available, otherwise fall back to local store
  const personas = apiData?.personas || localPersonas;
  const error = apiError || storeError;

  const handleCreatePersona = async () => {
    try {
      const newPersona: PersonaCreateRequest = {
        ...formData,
        permissions: [], // Default empty permissions
        settings: {
          theme: {
            primaryColor: formData.color,
          },
          features: {},
        },
      };
      
      await createPersonaMutation.mutateAsync(newPersona);
      setIsCreating(false);
      resetForm();
    } catch (error) {
      console.error('Failed to create persona:', error);
    }
  };

  const handleSyncPersonas = async () => {
    try {
      await syncPersonasMutation.mutateAsync();
    } catch (error) {
      console.error('Failed to sync personas:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      domain: '',
      role: '',
      description: '',
      color: '#000000',
      icon: '',
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-6 w-6 animate-spin" />
        <span className="ml-2">Loading personas...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Persona Management</h2>
          <p className="text-muted-foreground">
            Manage AI personas and their configurations
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSyncPersonas}
            disabled={syncStatus.isSyncing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${syncStatus.isSyncing ? 'animate-spin' : ''}`} />
            Sync
          </Button>
          <Button
            size="sm"
            onClick={() => setIsCreating(true)}
          >
            <Plus className="h-4 w-4 mr-2" />
            New Persona
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
          <p className="text-sm text-destructive">
            {typeof error === 'string' ? error : error.message}
          </p>
        </div>
      )}

      {/* Sync Status */}
      {syncStatus.lastSyncedAt && (
        <div className="text-sm text-muted-foreground">
          Last synced: {new Date(syncStatus.lastSyncedAt).toLocaleString()}
        </div>
      )}

      {/* Create Persona Form */}
      {isCreating && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Create New Persona</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Assistant"
              />
            </div>
            <div>
              <Label htmlFor="domain">Domain</Label>
              <Input
                id="domain"
                value={formData.domain}
                onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                placeholder="e.g., Healthcare"
              />
            </div>
            <div>
              <Label htmlFor="role">Role</Label>
              <Input
                id="role"
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                placeholder="e.g., Medical Assistant"
              />
            </div>
            <div>
              <Label htmlFor="icon">Icon (Emoji)</Label>
              <Input
                id="icon"
                value={formData.icon}
                onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                placeholder="e.g., 🏥"
              />
            </div>
            <div className="col-span-2">
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Brief description of the persona"
              />
            </div>
            <div>
              <Label htmlFor="color">Theme Color</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="color"
                  type="color"
                  value={formData.color}
                  onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                  className="w-20 h-10"
                />
                <Input
                  value={formData.color}
                  onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                  placeholder="#000000"
                />
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button
              variant="outline"
              onClick={() => {
                setIsCreating(false);
                resetForm();
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreatePersona}
              disabled={createPersonaMutation.isPending || !formData.name || !formData.domain}
            >
              {createPersonaMutation.isPending ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Persona'
              )}
            </Button>
          </div>
        </Card>
      )}

      {/* Personas Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {personas.map((persona) => (
          <PersonaCard
            key={persona.id}
            persona={persona}
            isActive={activePersona?.id === persona.id}
            onActivate={() => setActivePersona(persona.id)}
            onEdit={() => setEditingId(persona.id)}
            onDelete={async () => {
              // Implementation for delete would go here
              console.log('Delete persona:', persona.id);
            }}
          />
        ))}
      </div>
    </div>
  );
}

interface PersonaCardProps {
  persona: any; // Using any to avoid importing Persona type
  isActive: boolean;
  onActivate: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

function PersonaCard({ persona, isActive, onActivate, onEdit, onDelete }: PersonaCardProps) {
  const updatePersonaMutation = useUpdatePersona(persona.id);
  const deletePersonaMutation = useDeletePersona();

  const handleDelete = async () => {
    if (window.confirm(`Are you sure you want to delete ${persona.name}?`)) {
      try {
        await deletePersonaMutation.mutateAsync(persona.id);
      } catch (error) {
        console.error('Failed to delete persona:', error);
      }
    }
  };

  return (
    <Card 
      className={`p-6 cursor-pointer transition-all ${
        isActive ? 'ring-2 ring-primary' : 'hover:shadow-lg'
      }`}
      onClick={onActivate}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">{persona.icon || <User className="h-6 w-6" />}</span>
            <h3 className="text-lg font-semibold">{persona.name}</h3>
            {isActive && (
              <Badge variant="default" className="ml-auto">
                <Check className="h-3 w-3 mr-1" />
                Active
              </Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground mb-2">{persona.role}</p>
          <p className="text-sm">{persona.description}</p>
          <div className="flex items-center gap-2 mt-3">
            <Badge variant="outline">{persona.domain}</Badge>
            <div 
              className="w-4 h-4 rounded-full border"
              style={{ backgroundColor: persona.color }}
            />
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
            <Button variant="ghost" size="sm">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={(e) => {
              e.stopPropagation();
              onEdit();
            }}>
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem onClick={(e) => {
              e.stopPropagation();
              // Navigate to settings
              console.log('Settings for:', persona.id);
            }}>
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuItem 
              className="text-destructive"
              onClick={(e) => {
                e.stopPropagation();
                handleDelete();
              }}
              disabled={deletePersonaMutation.isPending}
            >
              <Trash className="h-4 w-4 mr-2" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </Card>
  );
}

export default PersonaManager;