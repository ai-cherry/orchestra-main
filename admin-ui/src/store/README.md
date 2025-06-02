# Persona State Management & API Integration

This directory contains the Zustand store for persona state management and TanStack Query hooks for API integration.

## Overview

The persona system provides:
- **Local state management** via Zustand with persistence
- **API synchronization** via TanStack Query
- **Optimistic updates** for better UX
- **Type-safe hooks** for all operations
- **Automatic caching and refetching**

## Architecture

```
┌─────────────────┐     ┌──────────────────┐
│  Zustand Store  │────▶│  Local Storage   │
│  (personaStore) │     └──────────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│ TanStack Query  │────▶│   Backend API    │
│    (hooks)      │     └──────────────────┘
└─────────────────┘
```

## Usage Examples

### Basic Persona Management

```typescript
import { usePersonaStore, useActivePersona, usePersonaActions } from '@/store/personaStore';
import { usePersonas, useCreatePersona } from '@/hooks/usePersonaApi';

function MyComponent() {
  // Get active persona
  const activePersona = useActivePersona();
  
  // Get all personas from API (with local fallback)
  const { data: personas, isLoading } = usePersonas();
  
  // Get actions
  const { setActivePersona, updatePersona } = usePersonaActions();
  
  // Create new persona
  const createMutation = useCreatePersona();
  
  const handleCreate = async () => {
    await createMutation.mutateAsync({
      name: 'New Assistant',
      domain: 'General',
      role: 'Helper',
      description: 'A helpful assistant',
      color: '#FF0000',
      capabilities: ['chat', 'search'],
      configuration: {
        model: 'gpt-4',
        temperature: 0.7,
      }
    });
  };
  
  return (
    <div>
      <h1>Active: {activePersona?.name}</h1>
      <button onClick={() => setActivePersona('sophia')}>
        Switch to Sophia
      </button>
    </div>
  );
}
```

### Using Persona Context

```typescript
import { usePersonaContext } from '@/hooks/usePersonaContext';

function Dashboard() {
  const {
    persona,
    workflows,
    agents,
    stats,
    isLoading,
    switchPersona,
    refresh
  } = usePersonaContext();
  
  if (isLoading) return <div>Loading...</div>;
  
  return (
    <div>
      <h1>{persona?.name}'s Dashboard</h1>
      <div>
        <p>Active Workflows: {stats.activeWorkflows}</p>
        <p>Active Agents: {stats.activeAgents}</p>
      </div>
      <button onClick={() => switchPersona('karen')}>
        Switch to Karen
      </button>
      <button onClick={refresh}>Refresh All</button>
    </div>
  );
}
```

### Persona-Aware Workflows

```typescript
import { useWorkflows, useCreateWorkflow } from '@/hooks/useWorkflowApi';
import { useActivePersona } from '@/store/personaStore';

function WorkflowManager() {
  const activePersona = useActivePersona();
  
  // Workflows are automatically filtered by active persona
  const { data: workflows } = useWorkflows();
  
  const createWorkflow = useCreateWorkflow();
  
  const handleCreate = async () => {
    // Workflow will be associated with active persona
    await createWorkflow.mutateAsync({
      name: 'Daily Report',
      description: 'Generate daily reports',
      steps: [
        {
          name: 'Collect Data',
          type: 'action',
          config: { source: 'database' },
          nextSteps: ['process']
        }
      ]
    });
  };
  
  return (
    <div>
      <h2>{activePersona?.name}'s Workflows</h2>
      {workflows?.map(w => (
        <div key={w.id}>{w.name}</div>
      ))}
    </div>
  );
}
```

### Theme Integration

```typescript
import { usePersonaTheme } from '@/hooks/usePersonaContext';

function ThemedComponent() {
  const theme = usePersonaTheme();
  
  return (
    <div style={{
      backgroundColor: theme.primaryColor,
      fontFamily: theme.fontFamily
    }}>
      Themed content
    </div>
  );
}
```

### Permission Checking

```typescript
import { useHasPermission, usePersonaPermissions } from '@/hooks/usePersonaContext';

function AdminPanel() {
  const hasAdminAccess = useHasPermission('admin');
  const permissions = usePersonaPermissions();
  
  if (!hasAdminAccess) {
    return <div>Access Denied</div>;
  }
  
  return (
    <div>
      <h1>Admin Panel</h1>
      <p>Your permissions: {permissions.join(', ')}</p>
    </div>
  );
}
```

### Optimistic Updates

```typescript
import { useUpdatePersona, useOptimisticPersonaUpdate } from '@/hooks/usePersonaApi';

function PersonaEditor({ personaId }: { personaId: string }) {
  const updateMutation = useUpdatePersona(personaId);
  const { updatePersona } = useOptimisticPersonaUpdate();
  
  const handleUpdate = async (updates: any) => {
    // Optimistically update UI
    updatePersona(personaId, updates);
    
    try {
      // Then sync with server
      await updateMutation.mutateAsync(updates);
    } catch (error) {
      // Revert on error (TanStack Query handles this)
      console.error('Update failed:', error);
    }
  };
  
  return (
    <button onClick={() => handleUpdate({ name: 'Updated Name' })}>
      Update Name
    </button>
  );
}
```

## Store Structure

### Persona Interface

```typescript
interface Persona {
  id: string;
  name: string;
  domain: string;
  role: string;
  description: string;
  color: string;
  icon?: string;
  permissions?: string[];
  settings?: PersonaSettings;
  metadata?: Record<string, any>;
  createdAt?: string;
  updatedAt?: string;
}

interface PersonaSettings {
  theme?: {
    primaryColor?: string;
    secondaryColor?: string;
    fontFamily?: string;
  };
  preferences?: {
    language?: string;
    timezone?: string;
    dateFormat?: string;
  };
  features?: {
    [key: string]: boolean;
  };
}
```

### Store State

```typescript
interface PersonaState {
  // State
  personas: Persona[];
  activePersonaId: string | null;
  isLoading: boolean;
  error: string | null;
  syncStatus: SyncStatus;
  
  // Computed
  activePersona: Persona | null;
  
  // Actions
  setPersonas: (personas: Persona[]) => void;
  setActivePersona: (personaId: string) => void;
  addPersona: (persona: Persona) => void;
  updatePersona: (personaId: string, updates: Partial<Persona>) => void;
  removePersona: (personaId: string) => void;
  // ... and more
}
```

## API Hooks

### Query Hooks
- `usePersonas()` - Fetch all personas
- `usePersona(id)` - Fetch single persona
- `useWorkflows()` - Fetch workflows for active persona
- `useAgents()` - Fetch agents for active persona

### Mutation Hooks
- `useCreatePersona()` - Create new persona
- `useUpdatePersona(id)` - Update existing persona
- `useDeletePersona()` - Delete persona
- `useSyncPersonas()` - Sync with backend

### Utility Hooks
- `usePersonaContext()` - Complete persona context
- `usePersonaTheme()` - Get theme configuration
- `usePersonaFeature(name)` - Check feature flags
- `useHasPermission(perm)` - Check permissions

## Best Practices

1. **Always use hooks** - Don't access store directly in components
2. **Handle loading states** - Show appropriate UI during data fetching
3. **Handle errors** - Display user-friendly error messages
4. **Use optimistic updates** - For better perceived performance
5. **Prefetch data** - When switching personas for smooth transitions

## Testing

```typescript
import { renderHook, act } from '@testing-library/react-hooks';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import usePersonaStore from '@/store/personaStore';

describe('PersonaStore', () => {
  beforeEach(() => {
    // Reset store before each test
    usePersonaStore.getState().reset();
  });
  
  it('should set active persona', () => {
    const { result } = renderHook(() => usePersonaStore());
    
    act(() => {
      result.current.setActivePersona('sophia');
    });
    
    expect(result.current.activePersonaId).toBe('sophia');
  });
});
```

## Migration Guide

If migrating from the old persona system:

1. Replace direct API calls with hooks
2. Replace local state with store hooks
3. Update permission checks to use new hooks
4. Update theme access to use `usePersonaTheme()`

## Troubleshooting

### Store not syncing
- Check if `markAsSynced()` is called after API updates
- Verify localStorage permissions in browser

### Queries not refetching
- Check query keys are correct
- Verify `invalidateQueries` is called after mutations

### Optimistic updates not working
- Ensure you're using the correct query keys
- Check if the update structure matches the expected format