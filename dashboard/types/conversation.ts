/**
 * Conversation-related type definitions
 * 
 * Core types for the conversational interface and messaging system
 */

/**
 * Message roles in conversation
 */
export type MessageRole = 'user' | 'assistant' | 'system';

/**
 * Individual message in conversation
 */
export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  isError?: boolean;
  metadata?: {
    agent_id?: string;
    tokens_used?: number;
    execution_time?: number;
    [key: string]: any;
  };
}

/**
 * Conversation context maintaining state
 */
export interface ConversationContext {
  activeAgents: string[];
  recentActions: string[];
  systemStatus: 'ready' | 'processing' | 'error';
  currentWorkflow?: string;
  userPreferences?: {
    voiceEnabled?: boolean;
    theme?: 'light' | 'dark';
    language?: string;
  };
}

/**
 * Agent information
 */
export interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'idle' | 'error';
  capabilities: string[];
  lastActivity?: string;
}

/**
 * System metrics
 */
export interface SystemMetrics {
  cpuUsage: number;
  memoryUsage: number;
  activeAgents: number;
  tasksCompleted: number;
  uptime: number;
}

/**
 * Action result from agent execution
 */
export interface ActionResult {
  success: boolean;
  message: string;
  data?: any;
  error?: string;
}