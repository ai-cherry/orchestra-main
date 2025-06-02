import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/authStore';
import usePersonaStore, { Persona, PersonaSettings } from '@/store/personaStore';

// API configuration
const API_URL = import.meta.env.VITE_API_URL || window.location.origin;
const API_KEY = import.meta.env.VITE_API_KEY;
const DEFAULT_API_KEY = '4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd';

// Helper function to get headers
function getHeaders() {
  const { token } = useAuthStore.getState();
  return {
    'Content-Type': 'application/json',
    'X-API-Key': token || API_KEY || DEFAULT_API_KEY,
  };
}

// API response types
export interface PersonaResponse {
  personas: Persona[];
  total: number;
  page: number;
  pageSize: number;
}

export interface PersonaCreateRequest {
  name: string;
  domain: string;
  role: string;
  description: string;
  color: string;
  icon?: string;
  permissions?: string[];
  settings?: PersonaSettings;
  metadata?: Record<string, any>;
}

export interface PersonaUpdateRequest {
  name?: string;
  domain?: string;
  role?: string;
  description?: string;
  color?: string;
  icon?: string;
  permissions?: string[];
  settings?: PersonaSettings;
  metadata?: Record<string, any>;
}

// Error handling
class PersonaApiError extends Error {
  constructor(public status: number, message: string, public details?: any) {
    super(message);
    this.name = 'PersonaApiError';
  }
}

async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new PersonaApiError(
      response.status,
      errorData.message || `API Error: ${response.statusText}`,
      errorData
    );
  }
  return response.json();
}

// Query Keys
export const personaQueryKeys = {
  all: ['personas'] as const,
  lists: () => [...personaQueryKeys.all, 'list'] as const,
  list: (filters?: Record<string, any>) => [...personaQueryKeys.lists(), filters] as const,
  details: () => [...personaQueryKeys.all, 'detail'] as const,
  detail: (id: string) => [...personaQueryKeys.details(), id] as const,
  settings: (id: string) => [...personaQueryKeys.detail(id), 'settings'] as const,
  permissions: (id: string) => [...personaQueryKeys.detail(id), 'permissions'] as const,
};

// Hooks

/**
 * Fetch all personas with optional filtering and pagination
 */
export function usePersonas(options?: {
  page?: number;
  pageSize?: number;
  domain?: string;
  search?: string;
}) {
  const queryClient = useQueryClient();
  const { setPersonas, setLoading, setError, markAsSynced } = usePersonaStore();

  return useQuery({
    queryKey: personaQueryKeys.list(options),
    queryFn: async () => {
      setLoading(true);
      setError(null);

      try {
        const params = new URLSearchParams();
        if (options?.page) params.append('page', options.page.toString());
        if (options?.pageSize) params.append('pageSize', options.pageSize.toString());
        if (options?.domain) params.append('domain', options.domain);
        if (options?.search) params.append('search', options.search);

        const response = await fetch(`${API_URL}/api/personas?${params}`, {
          headers: getHeaders(),
        });

        const data = await handleApiResponse<PersonaResponse>(response);
        
        // Update store with fetched personas
        setPersonas(data.personas);
        markAsSynced();
        
        return data;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to fetch personas';
        setError(errorMessage);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}

/**
 * Fetch a single persona by ID
 */
export function usePersona(personaId: string) {
  const { updatePersona, setError } = usePersonaStore();

  return useQuery({
    queryKey: personaQueryKeys.detail(personaId),
    queryFn: async () => {
      try {
        const response = await fetch(`${API_URL}/api/personas/${personaId}`, {
          headers: getHeaders(),
        });

        const persona = await handleApiResponse<Persona>(response);
        
        // Update store with fetched persona
        updatePersona(personaId, persona);
        
        return persona;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to fetch persona';
        setError(errorMessage);
        throw error;
      }
    },
    enabled: !!personaId,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });
}

/**
 * Create a new persona
 */
export function useCreatePersona() {
  const queryClient = useQueryClient();
  const { addPersona, setError } = usePersonaStore();

  return useMutation({
    mutationFn: async (data: PersonaCreateRequest) => {
      const response = await fetch(`${API_URL}/api/personas`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(data),
      });

      return handleApiResponse<Persona>(response);
    },
    onSuccess: (newPersona) => {
      // Update store
      addPersona(newPersona);
      
      // Invalidate and refetch personas list
      queryClient.invalidateQueries({ queryKey: personaQueryKeys.lists() });
      
      // Add the new persona to the cache
      queryClient.setQueryData(personaQueryKeys.detail(newPersona.id), newPersona);
    },
    onError: (error) => {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create persona';
      setError(errorMessage);
    },
  });
}

/**
 * Update an existing persona
 */
export function useUpdatePersona(personaId: string) {
  const queryClient = useQueryClient();
  const { updatePersona, setError } = usePersonaStore();

  return useMutation({
    mutationFn: async (data: PersonaUpdateRequest) => {
      const response = await fetch(`${API_URL}/api/personas/${personaId}`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify(data),
      });

      return handleApiResponse<Persona>(response);
    },
    onSuccess: (updatedPersona) => {
      // Update store
      updatePersona(personaId, updatedPersona);
      
      // Update cache
      queryClient.setQueryData(personaQueryKeys.detail(personaId), updatedPersona);
      
      // Invalidate list queries to ensure consistency
      queryClient.invalidateQueries({ queryKey: personaQueryKeys.lists() });
    },
    onError: (error) => {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update persona';
      setError(errorMessage);
    },
  });
}

/**
 * Delete a persona
 */
export function useDeletePersona() {
  const queryClient = useQueryClient();
  const { removePersona, setError } = usePersonaStore();

  return useMutation({
    mutationFn: async (personaId: string) => {
      const response = await fetch(`${API_URL}/api/personas/${personaId}`, {
        method: 'DELETE',
        headers: getHeaders(),
      });

      if (!response.ok) {
        throw new PersonaApiError(response.status, 'Failed to delete persona');
      }

      return personaId;
    },
    onSuccess: (personaId) => {
      // Update store
      removePersona(personaId);
      
      // Remove from cache
      queryClient.removeQueries({ queryKey: personaQueryKeys.detail(personaId) });
      
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: personaQueryKeys.lists() });
    },
    onError: (error) => {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete persona';
      setError(errorMessage);
    },
  });
}

/**
 * Update persona settings
 */
export function useUpdatePersonaSettings(personaId: string) {
  const queryClient = useQueryClient();
  const { updatePersonaSettings, setError } = usePersonaStore();

  return useMutation({
    mutationFn: async (settings: Partial<PersonaSettings>) => {
      const response = await fetch(`${API_URL}/api/personas/${personaId}/settings`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify(settings),
      });

      return handleApiResponse<PersonaSettings>(response);
    },
    onSuccess: (updatedSettings) => {
      // Update store
      updatePersonaSettings(personaId, updatedSettings);
      
      // Update cache
      queryClient.setQueryData(personaQueryKeys.settings(personaId), updatedSettings);
      
      // Invalidate the persona detail to ensure consistency
      queryClient.invalidateQueries({ queryKey: personaQueryKeys.detail(personaId) });
    },
    onError: (error) => {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update persona settings';
      setError(errorMessage);
    },
  });
}

/**
 * Batch update multiple personas
 */
export function useBatchUpdatePersonas() {
  const queryClient = useQueryClient();
  const { updateMultiplePersonas, setError } = usePersonaStore();

  return useMutation({
    mutationFn: async (updates: Array<{ id: string; updates: PersonaUpdateRequest }>) => {
      const response = await fetch(`${API_URL}/api/personas/batch`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify({ updates }),
      });

      return handleApiResponse<Persona[]>(response);
    },
    onSuccess: (updatedPersonas) => {
      // Update store
      const updates = updatedPersonas.map(persona => ({
        id: persona.id,
        updates: persona,
      }));
      updateMultiplePersonas(updates);
      
      // Update cache for each persona
      updatedPersonas.forEach(persona => {
        queryClient.setQueryData(personaQueryKeys.detail(persona.id), persona);
      });
      
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: personaQueryKeys.lists() });
    },
    onError: (error) => {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update personas';
      setError(errorMessage);
    },
  });
}

/**
 * Sync personas with the backend
 */
export function useSyncPersonas() {
  const queryClient = useQueryClient();
  const { setPersonas, setSyncStatus, markAsSynced, setError } = usePersonaStore();

  return useMutation({
    mutationFn: async () => {
      setSyncStatus({ isSyncing: true });
      
      const response = await fetch(`${API_URL}/api/personas/sync`, {
        method: 'POST',
        headers: getHeaders(),
      });

      return handleApiResponse<{ personas: Persona[] }>(response);
    },
    onSuccess: (data) => {
      // Update store with synced personas
      setPersonas(data.personas);
      markAsSynced();
      
      // Invalidate all persona queries
      queryClient.invalidateQueries({ queryKey: personaQueryKeys.all });
    },
    onError: (error) => {
      const errorMessage = error instanceof Error ? error.message : 'Failed to sync personas';
      setError(errorMessage);
      setSyncStatus({ 
        isSyncing: false, 
        error: errorMessage 
      });
    },
  });
}

/**
 * Prefetch persona data
 */
export function usePrefetchPersona() {
  const queryClient = useQueryClient();

  return async (personaId: string) => {
    await queryClient.prefetchQuery({
      queryKey: personaQueryKeys.detail(personaId),
      queryFn: async () => {
        const response = await fetch(`${API_URL}/api/personas/${personaId}`, {
          headers: getHeaders(),
        });
        return handleApiResponse<Persona>(response);
      },
      staleTime: 5 * 60 * 1000,
    });
  };
}

// Optimistic update helper
export function useOptimisticPersonaUpdate() {
  const queryClient = useQueryClient();

  return {
    updatePersona: (personaId: string, updates: PersonaUpdateRequest) => {
      // Optimistically update the cache
      queryClient.setQueryData<Persona>(
        personaQueryKeys.detail(personaId),
        (old) => old ? { ...old, ...updates, updatedAt: new Date().toISOString() } : old
      );

      // Also update in list queries
      queryClient.setQueriesData<PersonaResponse>(
        { queryKey: personaQueryKeys.lists() },
        (old) => {
          if (!old) return old;
          return {
            ...old,
            personas: old.personas.map(p => 
              p.id === personaId 
                ? { ...p, ...updates, updatedAt: new Date().toISOString() }
                : p
            ),
          };
        }
      );
    },
  };
}