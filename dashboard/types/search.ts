/**
 * Search-related type definitions
 * 
 * Defines the core types used throughout the OmniSearch system
 * for type safety and better developer experience.
 */

/**
 * Available search modes
 */
export type SearchMode = 'auto' | 'search' | 'generate' | 'command';

/**
 * Types of search intents that can be detected
 */
export type IntentType = 
  | 'agent_creation'
  | 'workflow'
  | 'search'
  | 'generate'
  | 'command'
  | 'document'
  | 'media_generation'
  | 'deep_search'
  | 'workflow_orchestration';

/**
 * Detected intent from user query
 */
export interface DetectedIntent {
  type: IntentType;
  confidence: number;
  entities?: Record<string, any>;
}

/**
 * Individual search suggestion
 */
export interface SearchSuggestion {
  text: string;
  type: IntentType;
  description?: string;
  metadata?: Record<string, any>;
  score?: number;
}

/**
 * Search result item
 */
export interface SearchResult {
  id: string;
  title: string;
  description?: string;
  type: string;
  url?: string;
  thumbnail?: string;
  metadata?: Record<string, any>;
  relevanceScore: number;
  timestamp: string;
}

/**
 * Search API response
 */
export interface SearchResponse {
  results: SearchResult[];
  totalCount: number;
  hasMore: boolean;
  nextCursor?: string;
  executionTime: number;
}

/**
 * Voice input state
 */
export interface VoiceInputState {
  isListening: boolean;
  transcript: string;
  confidence: number;
  error?: string;
}

/**
 * Search context for maintaining state
 */
export interface SearchContext {
  recentQueries: string[];
  activeFilters: Record<string, any>;
  preferredMode: SearchMode;
  voiceEnabled: boolean;
}