import { useEffect, useMemo } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import usePersonaStore, { Persona } from '@/store/personaStore';
import { usePersonas } from '@/hooks/usePersonaApi';
import { useWorkflows } from '@/hooks/useWorkflowApi';
import { useAgents } from '@/hooks/useAgentApi';

/**
 * Context data for the active persona including related resources
 */
export interface PersonaContext {
  persona: Persona | null;
  workflows: any[]; // Workflow type from useWorkflowApi
  agents: any[]; // Agent type from useAgentApi
  stats: PersonaStats;
  isLoading: boolean;
  error: string | null;
}

export interface PersonaStats {
  totalWorkflows: number;
  activeWorkflows: number;
  totalAgents: number;
  activeAgents: number;
  lastActivityAt?: string;
}

/**
 * Hook that provides complete context for the active persona
 * including related workflows, agents, and statistics
 */
export function usePersonaContext() {
  const queryClient = useQueryClient();
  
  // Store state
  const activePersona = usePersonaStore((state) => state.getActivePersona());
  const { setActivePersona, setLoading, setError } = usePersonaStore();
  
  // API queries - only fetch if we have an active persona
  const personasQuery = usePersonas();
  const workflowsQuery = useWorkflows({ 
    personaId: activePersona?.id,
    includeShared: true 
  });
  const agentsQuery = useAgents({ 
    personaId: activePersona?.id,
    includeShared: true 
  });

  // Sync API personas with store when they load
  useEffect(() => {
    if (personasQuery.data?.personas) {
      const { setPersonas, markAsSynced } = usePersonaStore.getState();
      setPersonas(personasQuery.data.personas);
      markAsSynced();
    }
  }, [personasQuery.data]);

  // Calculate stats
  const stats = useMemo<PersonaStats>(() => {
    const workflows = workflowsQuery.data || [];
    const agents = agentsQuery.data || [];
    
    return {
      totalWorkflows: workflows.length,
      activeWorkflows: workflows.filter((w: any) => w.status === 'active').length,
      totalAgents: agents.length,
      activeAgents: agents.filter((a: any) => a.status === 'active').length,
      lastActivityAt: activePersona?.updatedAt,
    };
  }, [workflowsQuery.data, agentsQuery.data, activePersona]);

  // Combined loading state
  const isLoading = personasQuery.isLoading || 
                   workflowsQuery.isLoading || 
                   agentsQuery.isLoading;

  // Combined error state
  const error = personasQuery.error?.message || 
                workflowsQuery.error?.message || 
                agentsQuery.error?.message || 
                null;

  // Update store loading/error states
  useEffect(() => {
    setLoading(isLoading);
    setError(error);
  }, [isLoading, error, setLoading, setError]);

  return {
    // Current persona
    persona: activePersona,
    
    // Related resources
    workflows: workflowsQuery.data || [],
    agents: agentsQuery.data || [],
    
    // Statistics
    stats,
    
    // State
    isLoading,
    error,
    
    // Actions
    switchPersona: async (personaId: string) => {
      setActivePersona(personaId);
      
      // Invalidate queries to refetch with new persona
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['workflows'] }),
        queryClient.invalidateQueries({ queryKey: ['agents'] }),
      ]);
    },
    
    // Refresh all data
    refresh: async () => {
      await Promise.all([
        personasQuery.refetch(),
        workflowsQuery.refetch(),
        agentsQuery.refetch(),
      ]);
    },
  };
}

/**
 * Hook to get persona-specific theme configuration
 */
export function usePersonaTheme() {
  const activePersona = usePersonaStore((state) => state.getActivePersona());
  
  return useMemo(() => {
    if (!activePersona?.settings?.theme) {
      return {
        primaryColor: '#000000',
        secondaryColor: '#666666',
        fontFamily: 'system-ui',
      };
    }
    
    return {
      primaryColor: activePersona.settings.theme.primaryColor || activePersona.color,
      secondaryColor: activePersona.settings.theme.secondaryColor || '#666666',
      fontFamily: activePersona.settings.theme.fontFamily || 'system-ui',
    };
  }, [activePersona]);
}

/**
 * Hook to check if a feature is enabled for the current persona
 */
export function usePersonaFeature(featureName: string): boolean {
  const activePersona = usePersonaStore((state) => state.getActivePersona());
  
  return useMemo(() => {
    if (!activePersona?.settings?.features) {
      return false;
    }
    
    return activePersona.settings.features[featureName] === true;
  }, [activePersona, featureName]);
}

/**
 * Hook to get persona permissions
 */
export function usePersonaPermissions(): string[] {
  const activePersona = usePersonaStore((state) => state.getActivePersona());
  
  return useMemo(() => {
    return activePersona?.permissions || [];
  }, [activePersona]);
}

/**
 * Hook to check if the current persona has a specific permission
 */
export function useHasPermission(permission: string): boolean {
  const permissions = usePersonaPermissions();
  
  return useMemo(() => {
    return permissions.includes(permission);
  }, [permissions, permission]);
}

/**
 * Hook for persona-aware navigation
 */
export function usePersonaNavigation() {
  const activePersona = usePersonaStore((state) => state.getActivePersona());
  const permissions = usePersonaPermissions();
  
  return useMemo(() => {
    // Define navigation items based on persona and permissions
    const baseItems = [
      { path: '/dashboard', label: 'Dashboard', icon: 'home' },
    ];
    
    const personaItems = [];
    
    // Add persona-specific navigation
    if (activePersona) {
      switch (activePersona.id) {
        case 'cherry':
          personaItems.push(
            { path: '/health', label: 'Health Tracker', icon: 'heart' },
            { path: '/habits', label: 'Habit Coach', icon: 'target' },
            { path: '/media', label: 'Media Generator', icon: 'image' }
          );
          break;
          
        case 'sophia':
          personaItems.push(
            { path: '/finance', label: 'Financial Dashboard', icon: 'dollar-sign' },
            { path: '/transactions', label: 'Transactions', icon: 'credit-card' },
            { path: '/compliance', label: 'Compliance', icon: 'shield' }
          );
          break;
          
        case 'karen':
          personaItems.push(
            { path: '/clinical', label: 'Clinical Workspace', icon: 'clipboard' },
            { path: '/patients', label: 'Patient Management', icon: 'users' },
            { path: '/prescriptions', label: 'Prescriptions', icon: 'pill' }
          );
          break;
      }
    }
    
    // Add permission-based items
    const permissionItems = [];
    if (permissions.includes('admin')) {
      permissionItems.push(
        { path: '/settings', label: 'Settings', icon: 'settings' },
        { path: '/personas', label: 'Personas', icon: 'users' }
      );
    }
    
    return [...baseItems, ...personaItems, ...permissionItems];
  }, [activePersona, permissions]);
}

/**
 * Hook to prefetch persona data
 */
export function usePrefetchPersonaData() {
  const queryClient = useQueryClient();
  
  return {
    prefetchPersonaContext: async (personaId: string) => {
      // Prefetch all related data for smooth persona switching
      await Promise.all([
        queryClient.prefetchQuery({
          queryKey: ['workflows', 'list', { personaId }],
          queryFn: async () => {
            // This would be the actual fetch function
            return [];
          },
          staleTime: 2 * 60 * 1000,
        }),
        queryClient.prefetchQuery({
          queryKey: ['agents', 'list', { personaId }],
          queryFn: async () => {
            // This would be the actual fetch function
            return [];
          },
          staleTime: 2 * 60 * 1000,
        }),
      ]);
    },
  };
}