import { LucideIcon } from 'lucide-react';

/**
 * Represents a processed command with intent and routing information
 */
export interface ProcessedCommand {
  query: string;
  intent: CommandIntent;
  routing: RoutingDecision;
  timestamp: Date;
}

/**
 * Command intent classification
 */
export interface CommandIntent {
  type: CommandType;
  confidence: number;
  entities: CommandEntity[];
  parameters: Record<string, any>;
}

/**
 * Types of commands that can be processed
 */
export enum CommandType {
  NAVIGATION = 'navigation',
  SEARCH = 'search',
  ACTION = 'action',
  QUERY = 'query',
  CREATION = 'creation',
  CONFIGURATION = 'configuration',
  ANALYSIS = 'analysis'
}

/**
 * Extracted entities from command
 */
export interface CommandEntity {
  type: string;
  value: string;
  confidence: number;
  position: {
    start: number;
    end: number;
  };
}

/**
 * Routing decision for command execution
 */
export interface RoutingDecision {
  model: ModelSelection;
  reasoning: string;
  alternativeModels: ModelSelection[];
  estimatedCost: number;
  estimatedLatency: number;
  confidence: number;
}

/**
 * Selected model information
 */
export interface ModelSelection {
  id: string;
  name: string;
  provider: string;
  capabilities: string[];
  costPerToken: number;
  maxTokens: number;
}

/**
 * Command suggestion
 */
export interface Suggestion {
  text: string;
  type: CommandType;
  icon: LucideIcon;
  description?: string;
  shortcut?: string;
  confidence: number;
}

/**
 * Command registry entry
 */
export interface Command {
  id: string;
  name: string;
  description: string;
  icon: LucideIcon;
  type: CommandType;
  shortcut?: string;
  handler: (params?: any) => void | Promise<void>;
  enabled?: boolean;
  category?: string;
}

/**
 * NLP processing result
 */
export interface NLPResult {
  intent: CommandIntent;
  suggestions: Suggestion[];
  confidence: number;
  processingTime: number;
}

/**
 * Model routing parameters
 */
export interface RoutingParams {
  queryType: CommandType;
  models: ModelSelection[];
  performance: ModelPerformanceMetrics;
  constraints?: RoutingConstraints;
}

/**
 * Routing constraints
 */
export interface RoutingConstraints {
  maxCost?: number;
  maxLatency?: number;
  requiredCapabilities?: string[];
  preferredProviders?: string[];
}

/**
 * Model performance metrics
 */
export interface ModelPerformanceMetrics {
  [modelId: string]: {
    avgLatency: number;
    p95Latency: number;
    p99Latency: number;
    successRate: number;
    errorRate: number;
    lastUpdated: Date;
  };
}