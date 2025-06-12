// API Types for Orchestra AI Integration

export type Persona = 'cherry' | 'sophia' | 'karen'

export interface Message {
  id: string
  content: string
  persona: Persona | 'user'
  timestamp: Date
  type: 'text' | 'image' | 'file' | 'code' | 'command'
  metadata?: {
    command?: string
    result?: any
    attachments?: string[]
    processing_time_ms?: number
    cross_domain_data?: Record<string, any>
  }
}

export interface ChatRequest {
  persona: Persona
  message: string
  context?: {
    conversation_id?: string
    task_type?: string
    urgency_level?: number
    technical_complexity?: number
    cross_domain_required?: string[]
  }
}

export interface ChatResponse {
  id: string
  content: string
  persona: Persona
  timestamp: string
  type: 'text' | 'image' | 'file' | 'code' | 'command'
  metadata?: {
    processing_time_ms?: number
    cross_domain_data?: Record<string, any>
    memory_compression_ratio?: number
    confidence_score?: number
  }
}

export interface PersonaStatus {
  persona: Persona
  status: 'active' | 'busy' | 'offline'
  current_task?: string
  load_level: number
  capabilities: string[]
  memory_usage: {
    current: number
    max: number
    compression_ratio: number
  }
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  service: string
  personas: Persona[]
  timestamp: string
  features: string[]
  performance_metrics?: {
    average_response_time: number
    total_interactions: number
    uptime_hours: number
  }
}

export interface MemoryMetrics {
  total_interactions: number
  average_response_time: number
  cross_domain_queries: number
  memory_compressions: number
  persona_states: Record<Persona, any>
  tier_performance: {
    L0_CPU_CACHE: { hits: number; misses: number; avg_time_ns: number }
    L1_PROCESS: { hits: number; misses: number; avg_time_ns: number }
    L2_SHARED: { hits: number; misses: number; avg_time_ns: number }
    L3_POSTGRESQL: { hits: number; misses: number; avg_time_ms: number }
    L4_WEAVIATE: { hits: number; misses: number; avg_time_ms: number }
  }
}

export interface SystemCommand {
  command: string
  target?: 'ui' | 'persona' | 'system'
  parameters?: Record<string, any>
}

export interface CommandResult {
  success: boolean
  result?: any
  error?: string
  ui_actions?: UIAction[]
}

export interface UIAction {
  type: 'navigate' | 'open_panel' | 'show_modal' | 'update_state'
  target: string
  parameters?: Record<string, any>
}

export interface WebSocketMessage {
  type: 'message' | 'typing' | 'persona_switch' | 'system_update' | 'error'
  data: any
  timestamp: string
  from?: Persona | 'system'
}

export interface AuthCredentials {
  username?: string
  email?: string
  password: string
}

export interface AuthResult {
  success: boolean
  token?: string
  user?: User
  error?: string
}

export interface User {
  id: string
  username: string
  email: string
  roles: string[]
  preferences: {
    default_persona: Persona
    theme: string
    notifications: boolean
  }
}

export interface APIError {
  code: string
  message: string
  details?: any
  timestamp: string
} 