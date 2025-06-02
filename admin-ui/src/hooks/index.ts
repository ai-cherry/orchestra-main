// Re-export all hooks from individual files for convenient importing

// Persona API hooks
export {
  usePersonas,
  usePersona,
  useCreatePersona,
  useUpdatePersona,
  useDeletePersona,
  useUpdatePersonaSettings,
  useBatchUpdatePersonas,
  useSyncPersonas,
  usePrefetchPersona,
  useOptimisticPersonaUpdate,
  personaQueryKeys,
  type PersonaResponse,
  type PersonaCreateRequest,
  type PersonaUpdateRequest,
} from './usePersonaApi';

// Workflow API hooks
export {
  useWorkflows,
  useWorkflow,
  useCreateWorkflow,
  useUpdateWorkflow,
  useDeleteWorkflow,
  useExecuteWorkflow,
  useWorkflowExecutions,
  useWorkflowExecution,
  useCancelWorkflowExecution,
  useCloneWorkflow,
  useImportWorkflow,
  useExportWorkflow,
  workflowQueryKeys,
  type Workflow,
  type WorkflowStep,
  type WorkflowTrigger,
  type WorkflowCreateRequest,
  type WorkflowUpdateRequest,
  type WorkflowExecutionRequest,
  type WorkflowExecution,
  type WorkflowExecutionStep,
} from './useWorkflowApi';

// Agent API hooks
export {
  useAgents,
  useAgent,
  useCreateAgent,
  useUpdateAgent,
  useDeleteAgent,
  useChatWithAgent,
  useStreamChatWithAgent,
  useAgentPerformance,
  useAgentSessions,
  useAgentSession,
  useCloneAgent,
  useTestAgent,
  useBatchAgentOperations,
  agentQueryKeys,
  type Agent,
  type AgentConfiguration,
  type AgentTool,
  type AgentPerformance,
  type AgentCreateRequest,
  type AgentUpdateRequest,
  type AgentMessage,
  type AgentChatRequest,
  type AgentChatResponse,
} from './useAgentApi';

// Persona context hooks
export {
  usePersonaContext,
  usePersonaTheme,
  usePersonaFeature,
  usePersonaPermissions,
  useHasPermission,
  usePersonaNavigation,
  usePrefetchPersonaData,
  type PersonaContext,
  type PersonaStats,
} from './usePersonaContext';

// Existing hooks from the original API file
export {
  useQueryApi,
  useUpload,
  useIntegrations,
  useResources,
  useLogs,
  type QueryBody,
} from '@/lib/api';