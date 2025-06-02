/**
 * API Types and Interfaces for Orchestra AI Admin Interface
 */

// Authentication Types
export interface LoginRequest {
    username: string;
    password: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    expires_in: number;
    user_email: string;
}

export interface User {
    username: string;
    email: string;
    is_active: boolean;
}

// LLM Provider Types
export interface LLMProvider {
    id: number;
    name: string;
    api_key_env_var: string | null;
    is_active: boolean;
    priority: number;
    created_at: string;
    updated_at: string;
}

export interface LLMModel {
    id: number;
    provider_id: number;
    model_identifier: string;
    display_name: string;
    is_available: boolean;
    model_type: string;
    context_window: number;
    max_tokens: number;
    supports_streaming: boolean;
    supports_functions: boolean;
    cost_per_input_token: number | null;
    cost_per_output_token: number | null;
    last_checked: string;
    provider?: LLMProvider;
}

export interface LLMUseCase {
    id: number;
    use_case: string;
    description: string;
    default_temperature: number;
    default_max_tokens: number;
    default_system_prompt: string | null;
    assignments?: LLMModelAssignment[];
}

export interface LLMModelAssignment {
    id: number;
    use_case_id: number;
    tier: string;
    primary_model_id: number;
    temperature_override: number | null;
    max_tokens_override: number | null;
    system_prompt_override: string | null;
    use_case?: LLMUseCase;
    primary_model?: LLMModel;
    fallback_models?: LLMFallbackModel[];
}

export interface LLMFallbackModel {
    id: number;
    assignment_id: number;
    model_id: number;
    priority: number;
    model?: LLMModel;
}

export interface LLMMetric {
    id: number;
    model_id: number;
    use_case_id: number | null;
    date: string;
    request_count: number;
    success_count: number;
    failure_count: number;
    total_tokens: number;
    avg_latency_ms: number | null;
    total_cost: number | null;
    model?: LLMModel;
    use_case?: LLMUseCase;
}

// Orchestration Types
export interface AgentStatus {
    id: string;
    name: string;
    type: string;
    status: string;
    created_at: string;
    last_activity: string;
    tasks_completed: number;
}

export interface WorkflowTask {
    id: string;
    type: string;
    data: Record<string, unknown>;
    status: string;
    created_at: string;
    completed_at?: string;
    result?: Record<string, unknown>;
    error?: string;
}

export interface Workflow {
    id: string;
    name: string;
    status: string;
    tasks: WorkflowTask[];
    context?: Record<string, unknown>;
    created_at: string;
    started_at?: string;
    completed_at?: string;
}

// Dashboard Metrics Types
export interface SystemMetrics {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    active_connections: number;
    request_rate: number;
    error_rate: number;
    timestamp: string;
}

export interface LLMUsageMetrics {
    total_requests: number;
    total_successes: number;
    total_failures: number;
    success_rate: number;
    total_tokens: number;
    total_cost: number;
    by_model: Record<string, {
        requests: number;
        successes: number;
        failures: number;
        tokens: number;
        cost: number;
        avg_latency_ms: number;
    }>;
    metrics: LLMMetric[];
}

export interface RoutingAnalytics {
    total_queries_routed: number;
    query_type_distribution: Record<string, number>;
    model_performance: Record<string, {
        total_queries: number;
        avg_latency: number;
        success_rate: number;
    }>;
}

export interface PersonaMetrics {
    total_personas: number;
    active_personas: number;
    total_conversations: number;
    avg_conversation_length: number;
    by_persona: Record<string, {
        conversations: number;
        avg_length: number;
        user_satisfaction: number;
    }>;
}

// API Response Wrappers
export interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    per_page: number;
    pages: number;
}

// Component Props Types
export interface LoadingState {
    isLoading: boolean;
    error?: string | null;
}

export interface RefreshableState extends LoadingState {
    lastRefresh?: Date;
    refreshing?: boolean;
}

// Request/Response Types for specific endpoints
export interface ProviderUpdateRequest {
    api_key_env_var?: string;
    is_active?: boolean;
    priority?: number;
}

export interface ModelAssignmentCreateRequest {
    use_case: string;
    tier: string;
    primary_model_id: number;
    fallback_model_ids: number[];
    temperature_override?: number;
    max_tokens_override?: number;
    system_prompt_override?: string;
}

export interface ModelTestRequest {
    model_identifier: string;
    provider: string;
    test_prompt?: string;
    temperature?: number;
    max_tokens?: number;
}

export interface BulkModelUpdateRequest {
    model_ids: number[];
    is_available: boolean;
}

// Configuration Types
export interface LLMConfiguration {
    providers: LLMProvider[];
    models: LLMModel[];
    use_cases: LLMUseCase[];
    assignments: LLMModelAssignment[];
}

export interface SystemHealth {
    status: "healthy" | "degraded" | "unhealthy";
    components: Record<string, string>;
    timestamp: string;
} 