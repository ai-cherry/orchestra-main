import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/authStore';
import usePersonaStore from '@/store/personaStore';

// API configuration
const API_URL = import.meta.env.VITE_API_URL || window.location.origin;
const API_KEY = import.meta.env.VITE_API_KEY;
const DEFAULT_API_KEY = '4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd';

// Helper function to get headers
function getHeaders() {
  const { token } = useAuthStore.getState();
  const activePersona = usePersonaStore.getState().getActivePersona();

  return {
    'Content-Type': 'application/json',
    'X-API-Key': token || API_KEY || DEFAULT_API_KEY,
    'X-Persona-Id': activePersona?.id || '',
  };
}

// Types
export interface Workflow {
  id: string;
  name: string;
  description: string;
  personaId: string;
  status: 'active' | 'inactive' | 'draft';
  steps: WorkflowStep[];
  triggers: WorkflowTrigger[];
  metadata?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface WorkflowStep {
  id: string;
  name: string;
  type: 'action' | 'condition' | 'loop' | 'parallel';
  config: Record<string, any>;
  nextSteps: string[];
}

export interface WorkflowTrigger {
  id: string;
  type: 'manual' | 'schedule' | 'event' | 'webhook';
  config: Record<string, any>;
  enabled: boolean;
}

export interface WorkflowCreateRequest {
  name: string;
  description: string;
  personaId?: string;
  steps: Omit<WorkflowStep, 'id'>[];
  triggers?: Omit<WorkflowTrigger, 'id'>[];
  metadata?: Record<string, any>;
}

export interface WorkflowUpdateRequest {
  name?: string;
  description?: string;
  status?: 'active' | 'inactive' | 'draft';
  steps?: WorkflowStep[];
  triggers?: WorkflowTrigger[];
  metadata?: Record<string, any>;
}

export interface WorkflowExecutionRequest {
  input?: Record<string, any>;
  context?: Record<string, any>;
}

export interface WorkflowExecution {
  id: string;
  workflowId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  input: Record<string, any>;
  output?: Record<string, any>;
  error?: string;
  startedAt: string;
  completedAt?: string;
  steps: WorkflowExecutionStep[];
}

export interface WorkflowExecutionStep {
  stepId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  startedAt?: string;
  completedAt?: string;
  output?: Record<string, any>;
  error?: string;
}

// Error handling
class WorkflowApiError extends Error {
  constructor(public status: number, message: string, public details?: any) {
    super(message);
    this.name = 'WorkflowApiError';
  }
}

async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));

    // Handle Pydantic validation errors (422 status)
    if (response.status === 422 && errorData.detail && Array.isArray(errorData.detail)) {
      // Convert validation errors to readable messages
      const validationErrors = errorData.detail.map((err: any) => {
        if (err.loc && err.msg) {
          const location = err.loc.join(' → ');
          return `${location}: ${err.msg}`;
        }
        return err.msg || 'Validation error';
      });

      throw new WorkflowApiError(
        response.status,
        validationErrors.join(', '),
        errorData
      );
    }

    throw new WorkflowApiError(
      response.status,
      errorData.message || errorData.detail || `API Error: ${response.statusText}`,
      errorData
    );
  }
  return response.json();
}

// Query Keys
export const workflowQueryKeys = {
  all: ['workflows'] as const,
  lists: () => [...workflowQueryKeys.all, 'list'] as const,
  list: (filters?: { personaId?: string; status?: string }) =>
    [...workflowQueryKeys.lists(), filters] as const,
  details: () => [...workflowQueryKeys.all, 'detail'] as const,
  detail: (id: string) => [...workflowQueryKeys.details(), id] as const,
  executions: (workflowId: string) =>
    [...workflowQueryKeys.detail(workflowId), 'executions'] as const,
  execution: (workflowId: string, executionId: string) =>
    [...workflowQueryKeys.executions(workflowId), executionId] as const,
};

// Hooks

/**
 * Fetch workflows with optional filtering by persona
 */
export function useWorkflows(options?: {
  personaId?: string;
  status?: 'active' | 'inactive' | 'draft';
  includeShared?: boolean;
}) {
  const activePersona = usePersonaStore((state) => state.getActivePersona());
  const personaId = options?.personaId || activePersona?.id;

  return useQuery({
    queryKey: workflowQueryKeys.list({ personaId, status: options?.status }),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (personaId) params.append('personaId', personaId);
      if (options?.status) params.append('status', options.status);
      if (options?.includeShared) params.append('includeShared', 'true');

      const response = await fetch(`${API_URL}/api/workflows?${params}`, {
        headers: getHeaders(),
      });

      return handleApiResponse<Workflow[]>(response);
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Fetch a single workflow by ID
 */
export function useWorkflow(workflowId: string) {
  return useQuery({
    queryKey: workflowQueryKeys.detail(workflowId),
    queryFn: async () => {
      const response = await fetch(`${API_URL}/api/workflows/${workflowId}`, {
        headers: getHeaders(),
      });

      return handleApiResponse<Workflow>(response);
    },
    enabled: !!workflowId,
    staleTime: 2 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });
}

/**
 * Create a new workflow
 */
export function useCreateWorkflow() {
  const queryClient = useQueryClient();
  const activePersona = usePersonaStore((state) => state.getActivePersona());

  return useMutation({
    mutationFn: async (data: WorkflowCreateRequest) => {
      // Use active persona if not specified
      const workflowData = {
        ...data,
        personaId: data.personaId || activePersona?.id,
      };

      const response = await fetch(`${API_URL}/api/workflows`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(workflowData),
      });

      return handleApiResponse<Workflow>(response);
    },
    onSuccess: (newWorkflow) => {
      // Invalidate workflow lists
      queryClient.invalidateQueries({ queryKey: workflowQueryKeys.lists() });

      // Add to cache
      queryClient.setQueryData(workflowQueryKeys.detail(newWorkflow.id), newWorkflow);
    },
  });
}

/**
 * Update an existing workflow
 */
export function useUpdateWorkflow(workflowId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: WorkflowUpdateRequest) => {
      const response = await fetch(`${API_URL}/api/workflows/${workflowId}`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify(data),
      });

      return handleApiResponse<Workflow>(response);
    },
    onSuccess: (updatedWorkflow) => {
      // Update cache
      queryClient.setQueryData(workflowQueryKeys.detail(workflowId), updatedWorkflow);

      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: workflowQueryKeys.lists() });
    },
  });
}

/**
 * Delete a workflow
 */
export function useDeleteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (workflowId: string) => {
      const response = await fetch(`${API_URL}/api/workflows/${workflowId}`, {
        method: 'DELETE',
        headers: getHeaders(),
      });

      if (!response.ok) {
        throw new WorkflowApiError(response.status, 'Failed to delete workflow');
      }

      return workflowId;
    },
    onSuccess: (workflowId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: workflowQueryKeys.detail(workflowId) });

      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: workflowQueryKeys.lists() });
    },
  });
}

/**
 * Execute a workflow
 */
export function useExecuteWorkflow(workflowId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data?: WorkflowExecutionRequest) => {
      const response = await fetch(`${API_URL}/api/workflows/${workflowId}/execute`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(data || {}),
      });

      return handleApiResponse<WorkflowExecution>(response);
    },
    onSuccess: (execution) => {
      // Invalidate executions list for this workflow
      queryClient.invalidateQueries({
        queryKey: workflowQueryKeys.executions(workflowId)
      });

      // Add to cache
      queryClient.setQueryData(
        workflowQueryKeys.execution(workflowId, execution.id),
        execution
      );
    },
  });
}

/**
 * Fetch workflow executions
 */
export function useWorkflowExecutions(workflowId: string, options?: {
  limit?: number;
  status?: string;
}) {
  return useQuery({
    queryKey: workflowQueryKeys.executions(workflowId),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (options?.limit) params.append('limit', options.limit.toString());
      if (options?.status) params.append('status', options.status);

      const response = await fetch(
        `${API_URL}/api/workflows/${workflowId}/executions?${params}`,
        { headers: getHeaders() }
      );

      return handleApiResponse<WorkflowExecution[]>(response);
    },
    enabled: !!workflowId,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: (query) => {
      // Auto-refresh if any execution is still running
      if (!query.state.data) return false;
      const hasRunning = query.state.data.some((e: WorkflowExecution) =>
        e.status === 'running' || e.status === 'pending'
      );
      return hasRunning ? 2000 : false; // Refresh every 2 seconds if running
    },
  });
}

/**
 * Fetch a single workflow execution
 */
export function useWorkflowExecution(workflowId: string, executionId: string) {
  return useQuery({
    queryKey: workflowQueryKeys.execution(workflowId, executionId),
    queryFn: async () => {
      const response = await fetch(
        `${API_URL}/api/workflows/${workflowId}/executions/${executionId}`,
        { headers: getHeaders() }
      );

      return handleApiResponse<WorkflowExecution>(response);
    },
    enabled: !!workflowId && !!executionId,
    staleTime: 30 * 1000,
    refetchInterval: (query) => {
      // Auto-refresh if execution is still running
      if (!query.state.data) return false;
      const isRunning = query.state.data.status === 'running' || query.state.data.status === 'pending';
      return isRunning ? 1000 : false; // Refresh every second if running
    },
  });
}

/**
 * Cancel a workflow execution
 */
export function useCancelWorkflowExecution(workflowId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (executionId: string) => {
      const response = await fetch(
        `${API_URL}/api/workflows/${workflowId}/executions/${executionId}/cancel`,
        {
          method: 'POST',
          headers: getHeaders(),
        }
      );

      return handleApiResponse<WorkflowExecution>(response);
    },
    onSuccess: (execution) => {
      // Update cache
      queryClient.setQueryData(
        workflowQueryKeys.execution(workflowId, execution.id),
        execution
      );

      // Invalidate executions list
      queryClient.invalidateQueries({
        queryKey: workflowQueryKeys.executions(workflowId)
      });
    },
  });
}

/**
 * Clone a workflow
 */
export function useCloneWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ workflowId, name }: { workflowId: string; name: string }) => {
      const response = await fetch(`${API_URL}/api/workflows/${workflowId}/clone`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ name }),
      });

      return handleApiResponse<Workflow>(response);
    },
    onSuccess: (newWorkflow) => {
      // Invalidate workflow lists
      queryClient.invalidateQueries({ queryKey: workflowQueryKeys.lists() });

      // Add to cache
      queryClient.setQueryData(workflowQueryKeys.detail(newWorkflow.id), newWorkflow);
    },
  });
}

/**
 * Import workflow from JSON
 */
export function useImportWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (workflowJson: string) => {
      const response = await fetch(`${API_URL}/api/workflows/import`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ workflow: workflowJson }),
      });

      return handleApiResponse<Workflow>(response);
    },
    onSuccess: (importedWorkflow) => {
      // Invalidate workflow lists
      queryClient.invalidateQueries({ queryKey: workflowQueryKeys.lists() });

      // Add to cache
      queryClient.setQueryData(
        workflowQueryKeys.detail(importedWorkflow.id),
        importedWorkflow
      );
    },
  });
}

/**
 * Export workflow to JSON
 */
export function useExportWorkflow(workflowId: string) {
  return useQuery({
    queryKey: [...workflowQueryKeys.detail(workflowId), 'export'],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/api/workflows/${workflowId}/export`, {
        headers: getHeaders(),
      });

      return handleApiResponse<{ workflow: string }>(response);
    },
    enabled: false, // Manual trigger only
    staleTime: Infinity, // Never stale
  });
}