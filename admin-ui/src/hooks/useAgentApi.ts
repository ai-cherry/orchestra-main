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
export interface Agent {
  id: string;
  name: string;
  description: string;
  type: 'assistant' | 'specialist' | 'orchestrator' | 'custom';
  personaId: string;
  status: 'active' | 'inactive' | 'maintenance';
  capabilities: string[];
  configuration: AgentConfiguration;
  performance: AgentPerformance;
  metadata?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface AgentConfiguration {
  model: string;
  temperature?: number;
  maxTokens?: number;
  systemPrompt?: string;
  tools?: AgentTool[];
  memory?: {
    type: 'short-term' | 'long-term' | 'both';
    maxItems?: number;
  };
  integrations?: string[];
}

export interface AgentTool {
  id: string;
  name: string;
  description: string;
  parameters?: Record<string, any>;
  enabled: boolean;
}

export interface AgentPerformance {
  totalRequests: number;
  successRate: number;
  averageResponseTime: number;
  lastActiveAt?: string;
  errorRate: number;
  metrics?: Record<string, number>;
}

export interface AgentCreateRequest {
  name: string;
  description: string;
  type: 'assistant' | 'specialist' | 'orchestrator' | 'custom';
  personaId?: string;
  capabilities: string[];
  configuration: Partial<AgentConfiguration>;
  metadata?: Record<string, any>;
}

export interface AgentUpdateRequest {
  name?: string;
  description?: string;
  status?: 'active' | 'inactive' | 'maintenance';
  capabilities?: string[];
  configuration?: Partial<AgentConfiguration>;
  metadata?: Record<string, any>;
}

export interface AgentMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface AgentChatRequest {
  message: string;
  context?: Record<string, any>;
  sessionId?: string;
  stream?: boolean;
}

export interface AgentChatResponse {
  response: string;
  sessionId: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  metadata?: Record<string, any>;
}

// Error handling
class AgentApiError extends Error {
  constructor(public status: number, message: string, public details?: any) {
    super(message);
    this.name = 'AgentApiError';
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

      throw new AgentApiError(
        response.status,
        validationErrors.join(', '),
        errorData
      );
    }

    throw new AgentApiError(
      response.status,
      errorData.message || errorData.detail || `API Error: ${response.statusText}`,
      errorData
    );
  }
  return response.json();
}

// Query Keys
export const agentQueryKeys = {
  all: ['agents'] as const,
  lists: () => [...agentQueryKeys.all, 'list'] as const,
  list: (filters?: { personaId?: string; type?: string; status?: string }) =>
    [...agentQueryKeys.lists(), filters] as const,
  details: () => [...agentQueryKeys.all, 'detail'] as const,
  detail: (id: string) => [...agentQueryKeys.details(), id] as const,
  performance: (id: string) => [...agentQueryKeys.detail(id), 'performance'] as const,
  sessions: (agentId: string) => [...agentQueryKeys.detail(agentId), 'sessions'] as const,
  session: (agentId: string, sessionId: string) =>
    [...agentQueryKeys.sessions(agentId), sessionId] as const,
};

// Hooks

/**
 * Fetch agents with optional filtering by persona
 */
export function useAgents(options?: {
  personaId?: string;
  type?: 'assistant' | 'specialist' | 'orchestrator' | 'custom';
  status?: 'active' | 'inactive' | 'maintenance';
  includeShared?: boolean;
}) {
  const activePersona = usePersonaStore((state) => state.getActivePersona());
  const personaId = options?.personaId || activePersona?.id;

  return useQuery({
    queryKey: agentQueryKeys.list({
      personaId,
      type: options?.type,
      status: options?.status
    }),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (personaId) params.append('personaId', personaId);
      if (options?.type) params.append('type', options.type);
      if (options?.status) params.append('status', options.status);
      if (options?.includeShared) params.append('includeShared', 'true');

      const response = await fetch(`${API_URL}/api/agents?${params}`, {
        headers: getHeaders(),
      });

      return handleApiResponse<Agent[]>(response);
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Fetch a single agent by ID
 */
export function useAgent(agentId: string) {
  return useQuery({
    queryKey: agentQueryKeys.detail(agentId),
    queryFn: async () => {
      const response = await fetch(`${API_URL}/api/agents/${agentId}`, {
        headers: getHeaders(),
      });

      return handleApiResponse<Agent>(response);
    },
    enabled: !!agentId,
    staleTime: 2 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });
}

/**
 * Create a new agent
 */
export function useCreateAgent() {
  const queryClient = useQueryClient();
  const activePersona = usePersonaStore((state) => state.getActivePersona());

  return useMutation({
    mutationFn: async (data: AgentCreateRequest) => {
      // Use active persona if not specified
      const agentData = {
        ...data,
        personaId: data.personaId || activePersona?.id,
      };

      const response = await fetch(`${API_URL}/api/agents`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(agentData),
      });

      return handleApiResponse<Agent>(response);
    },
    onSuccess: (newAgent) => {
      // Invalidate agent lists
      queryClient.invalidateQueries({ queryKey: agentQueryKeys.lists() });

      // Add to cache
      queryClient.setQueryData(agentQueryKeys.detail(newAgent.id), newAgent);
    },
  });
}

/**
 * Update an existing agent
 */
export function useUpdateAgent(agentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: AgentUpdateRequest) => {
      const response = await fetch(`${API_URL}/api/agents/${agentId}`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify(data),
      });

      return handleApiResponse<Agent>(response);
    },
    onSuccess: (updatedAgent) => {
      // Update cache
      queryClient.setQueryData(agentQueryKeys.detail(agentId), updatedAgent);

      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: agentQueryKeys.lists() });
    },
  });
}

/**
 * Delete an agent
 */
export function useDeleteAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (agentId: string) => {
      const response = await fetch(`${API_URL}/api/agents/${agentId}`, {
        method: 'DELETE',
        headers: getHeaders(),
      });

      if (!response.ok) {
        throw new AgentApiError(response.status, 'Failed to delete agent');
      }

      return agentId;
    },
    onSuccess: (agentId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: agentQueryKeys.detail(agentId) });

      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: agentQueryKeys.lists() });
    },
  });
}

/**
 * Chat with an agent
 */
export function useChatWithAgent(agentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: AgentChatRequest) => {
      const response = await fetch(`${API_URL}/api/agents/${agentId}/chat`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(data),
      });

      return handleApiResponse<AgentChatResponse>(response);
    },
    onSuccess: (response) => {
      // Invalidate session data if sessionId is provided
      if (response.sessionId) {
        queryClient.invalidateQueries({
          queryKey: agentQueryKeys.session(agentId, response.sessionId)
        });
      }
    },
  });
}

/**
 * Stream chat with an agent (returns an EventSource)
 */
export function useStreamChatWithAgent(agentId: string) {
  const activePersona = usePersonaStore((state) => state.getActivePersona());

  return {
    streamChat: (data: AgentChatRequest) => {
      const params = new URLSearchParams({
        message: data.message,
        sessionId: data.sessionId || '',
        personaId: activePersona?.id || '',
      });

      if (data.context) {
        params.append('context', JSON.stringify(data.context));
      }

      const eventSource = new EventSource(
        `${API_URL}/api/agents/${agentId}/chat/stream?${params}`,
        {
          withCredentials: true,
        }
      );

      return eventSource;
    },
  };
}

/**
 * Fetch agent performance metrics
 */
export function useAgentPerformance(agentId: string, options?: {
  timeRange?: 'hour' | 'day' | 'week' | 'month';
  metrics?: string[];
}) {
  return useQuery({
    queryKey: agentQueryKeys.performance(agentId),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (options?.timeRange) params.append('timeRange', options.timeRange);
      if (options?.metrics) params.append('metrics', options.metrics.join(','));

      const response = await fetch(
        `${API_URL}/api/agents/${agentId}/performance?${params}`,
        { headers: getHeaders() }
      );

      return handleApiResponse<AgentPerformance>(response);
    },
    enabled: !!agentId,
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 30 * 1000, // Refresh every 30 seconds
  });
}

/**
 * Fetch agent chat sessions
 */
export function useAgentSessions(agentId: string, options?: {
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: agentQueryKeys.sessions(agentId),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (options?.limit) params.append('limit', options.limit.toString());
      if (options?.offset) params.append('offset', options.offset.toString());

      const response = await fetch(
        `${API_URL}/api/agents/${agentId}/sessions?${params}`,
        { headers: getHeaders() }
      );

      return handleApiResponse<Array<{
        sessionId: string;
        startedAt: string;
        lastMessageAt: string;
        messageCount: number;
        metadata?: Record<string, any>;
      }>>(response);
    },
    enabled: !!agentId,
    staleTime: 2 * 60 * 1000,
  });
}

/**
 * Fetch a specific chat session
 */
export function useAgentSession(agentId: string, sessionId: string) {
  return useQuery({
    queryKey: agentQueryKeys.session(agentId, sessionId),
    queryFn: async () => {
      const response = await fetch(
        `${API_URL}/api/agents/${agentId}/sessions/${sessionId}`,
        { headers: getHeaders() }
      );

      return handleApiResponse<{
        sessionId: string;
        messages: AgentMessage[];
        metadata?: Record<string, any>;
      }>(response);
    },
    enabled: !!agentId && !!sessionId,
    staleTime: 60 * 1000,
  });
}

/**
 * Clone an agent
 */
export function useCloneAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ agentId, name }: { agentId: string; name: string }) => {
      const response = await fetch(`${API_URL}/api/agents/${agentId}/clone`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ name }),
      });

      return handleApiResponse<Agent>(response);
    },
    onSuccess: (newAgent) => {
      // Invalidate agent lists
      queryClient.invalidateQueries({ queryKey: agentQueryKeys.lists() });

      // Add to cache
      queryClient.setQueryData(agentQueryKeys.detail(newAgent.id), newAgent);
    },
  });
}

/**
 * Test agent configuration
 */
export function useTestAgent() {
  return useMutation({
    mutationFn: async (config: Partial<AgentConfiguration>) => {
      const response = await fetch(`${API_URL}/api/agents/test`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(config),
      });

      return handleApiResponse<{
        success: boolean;
        response?: string;
        error?: string;
        latency: number;
      }>(response);
    },
  });
}

/**
 * Batch operations for agents
 */
export function useBatchAgentOperations() {
  const queryClient = useQueryClient();

  return {
    batchUpdate: useMutation({
      mutationFn: async (operations: Array<{
        agentId: string;
        updates: AgentUpdateRequest;
      }>) => {
        const response = await fetch(`${API_URL}/api/agents/batch/update`, {
          method: 'POST',
          headers: getHeaders(),
          body: JSON.stringify({ operations }),
        });

        return handleApiResponse<Agent[]>(response);
      },
      onSuccess: (updatedAgents) => {
        // Update cache for each agent
        updatedAgents.forEach(agent => {
          queryClient.setQueryData(agentQueryKeys.detail(agent.id), agent);
        });

        // Invalidate lists
        queryClient.invalidateQueries({ queryKey: agentQueryKeys.lists() });
      },
    }),

    batchDelete: useMutation({
      mutationFn: async (agentIds: string[]) => {
        const response = await fetch(`${API_URL}/api/agents/batch/delete`, {
          method: 'POST',
          headers: getHeaders(),
          body: JSON.stringify({ agentIds }),
        });

        return handleApiResponse<{ deleted: string[] }>(response);
      },
      onSuccess: (result) => {
        // Remove from cache
        result.deleted.forEach(agentId => {
          queryClient.removeQueries({ queryKey: agentQueryKeys.detail(agentId) });
        });

        // Invalidate lists
        queryClient.invalidateQueries({ queryKey: agentQueryKeys.lists() });
      },
    }),
  };
}