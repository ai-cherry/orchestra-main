import { useState, useCallback } from 'react';
import { 
  CommandIntent, 
  RoutingDecision, 
  ModelSelection, 
  CommandType,
  ModelPerformanceMetrics,
  RoutingConstraints 
} from '@/types/command';

/**
 * Hook for intelligent LLM model routing
 * Selects optimal models based on query type, performance, and cost
 */
export function useModelRouter() {
  const [isRouting, setIsRouting] = useState(false);
  
  /**
   * Available models with their capabilities
   */
  const availableModels: ModelSelection[] = [
    {
      id: 'gpt-4-turbo',
      name: 'GPT-4 Turbo',
      provider: 'OpenAI',
      capabilities: ['reasoning', 'coding', 'analysis', 'creative'],
      costPerToken: 0.00003,
      maxTokens: 128000
    },
    {
      id: 'claude-3-opus',
      name: 'Claude 3 Opus',
      provider: 'Anthropic',
      capabilities: ['reasoning', 'coding', 'analysis', 'creative', 'long-context'],
      costPerToken: 0.00015,
      maxTokens: 200000
    },
    {
      id: 'claude-3-sonnet',
      name: 'Claude 3 Sonnet',
      provider: 'Anthropic',
      capabilities: ['reasoning', 'coding', 'analysis'],
      costPerToken: 0.00003,
      maxTokens: 200000
    },
    {
      id: 'gemini-pro',
      name: 'Gemini Pro',
      provider: 'Google',
      capabilities: ['reasoning', 'analysis', 'multimodal'],
      costPerToken: 0.00001,
      maxTokens: 32000
    },
    {
      id: 'mixtral-8x7b',
      name: 'Mixtral 8x7B',
      provider: 'Mistral',
      capabilities: ['reasoning', 'coding', 'fast'],
      costPerToken: 0.000007,
      maxTokens: 32000
    }
  ];
  
  /**
   * Mock performance metrics
   */
  const performanceMetrics: ModelPerformanceMetrics = {
    'gpt-4-turbo': {
      avgLatency: 1200,
      p95Latency: 2000,
      p99Latency: 3000,
      successRate: 0.98,
      errorRate: 0.02,
      lastUpdated: new Date()
    },
    'claude-3-opus': {
      avgLatency: 1500,
      p95Latency: 2500,
      p99Latency: 3500,
      successRate: 0.97,
      errorRate: 0.03,
      lastUpdated: new Date()
    },
    'claude-3-sonnet': {
      avgLatency: 800,
      p95Latency: 1200,
      p99Latency: 1800,
      successRate: 0.99,
      errorRate: 0.01,
      lastUpdated: new Date()
    },
    'gemini-pro': {
      avgLatency: 600,
      p95Latency: 1000,
      p99Latency: 1500,
      successRate: 0.96,
      errorRate: 0.04,
      lastUpdated: new Date()
    },
    'mixtral-8x7b': {
      avgLatency: 400,
      p95Latency: 700,
      p99Latency: 1000,
      successRate: 0.95,
      errorRate: 0.05,
      lastUpdated: new Date()
    }
  };
  
  /**
   * Calculate model score based on multiple factors
   */
  const calculateModelScore = (
    model: ModelSelection,
    intent: CommandIntent,
    constraints?: RoutingConstraints
  ): number => {
    let score = 0;
    
    // Capability match score (40%)
    const requiredCapabilities = getRequiredCapabilities(intent.type);
    const capabilityMatch = requiredCapabilities.filter(cap => 
      model.capabilities.includes(cap)
    ).length / requiredCapabilities.length;
    score += capabilityMatch * 0.4;
    
    // Performance score (30%)
    const perf = performanceMetrics[model.id];
    if (perf) {
      const latencyScore = 1 - (perf.avgLatency / 3000); // Normalize to 0-1
      const reliabilityScore = perf.successRate;
      score += (latencyScore * 0.15 + reliabilityScore * 0.15);
    }
    
    // Cost score (20%)
    const costScore = 1 - (model.costPerToken / 0.0002); // Normalize based on max cost
    score += costScore * 0.2;
    
    // Confidence boost (10%)
    score += intent.confidence * 0.1;
    
    // Apply constraints
    if (constraints) {
      if (constraints.maxCost && model.costPerToken > constraints.maxCost) {
        score *= 0.5; // Penalize expensive models
      }
      if (constraints.maxLatency && perf && perf.avgLatency > constraints.maxLatency) {
        score *= 0.7; // Penalize slow models
      }
      if (constraints.requiredCapabilities) {
        const hasRequired = constraints.requiredCapabilities.every(cap =>
          model.capabilities.includes(cap)
        );
        if (!hasRequired) score *= 0.1; // Heavily penalize missing capabilities
      }
    }
    
    return Math.max(0, Math.min(1, score)); // Clamp to 0-1
  };
  
  /**
   * Get required capabilities for command type
   */
  const getRequiredCapabilities = (type: CommandType): string[] => {
    switch (type) {
      case CommandType.CREATION:
        return ['creative', 'reasoning'];
      case CommandType.ANALYSIS:
        return ['analysis', 'reasoning'];
      case CommandType.CONFIGURATION:
        return ['reasoning'];
      case CommandType.ACTION:
        return ['reasoning', 'coding'];
      case CommandType.SEARCH:
        return ['reasoning', 'fast'];
      default:
        return ['reasoning'];
    }
  };
  
  /**
   * Route query to optimal model
   */
  const routeQuery = useCallback(async (
    intent: CommandIntent,
    constraints?: RoutingConstraints
  ): Promise<RoutingDecision> => {
    setIsRouting(true);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 50));
      
      // Score all models
      const scoredModels = availableModels.map(model => ({
        model,
        score: calculateModelScore(model, intent, constraints)
      })).sort((a, b) => b.score - a.score);
      
      const selected = scoredModels[0];
      const alternatives = scoredModels.slice(1, 4).map(s => s.model);
      
      // Generate reasoning
      const reasoning = generateRoutingReasoning(
        selected.model,
        intent,
        selected.score
      );
      
      return {
        model: selected.model,
        reasoning,
        alternativeModels: alternatives,
        estimatedCost: estimateCost(selected.model, intent),
        estimatedLatency: performanceMetrics[selected.model.id]?.avgLatency || 1000,
        confidence: selected.score
      };
    } finally {
      setIsRouting(false);
    }
  }, []);
  
  /**
   * Generate human-readable routing reasoning
   */
  const generateRoutingReasoning = (
    model: ModelSelection,
    intent: CommandIntent,
    score: number
  ): string => {
    const reasons = [];
    
    if (score > 0.8) {
      reasons.push(`${model.name} is highly suitable for ${intent.type} queries`);
    } else if (score > 0.6) {
      reasons.push(`${model.name} is a good match for this query type`);
    } else {
      reasons.push(`${model.name} can handle this query`);
    }
    
    if (model.capabilities.includes('fast')) {
      reasons.push('optimized for low latency');
    }
    
    if (model.costPerToken < 0.00002) {
      reasons.push('cost-effective choice');
    }
    
    if (intent.confidence > 0.9) {
      reasons.push('high confidence in query classification');
    }
    
    return reasons.join(', ') + '.';
  };
  
  /**
   * Estimate cost for query
   */
  const estimateCost = (model: ModelSelection, intent: CommandIntent): number => {
    // Estimate tokens based on query type
    let estimatedTokens = 1000; // Default
    
    switch (intent.type) {
      case CommandType.ANALYSIS:
        estimatedTokens = 2000;
        break;
      case CommandType.CREATION:
        estimatedTokens = 1500;
        break;
      case CommandType.SEARCH:
        estimatedTokens = 500;
        break;
    }
    
    return model.costPerToken * estimatedTokens;
  };
  
  return {
    routeQuery,
    isRouting,
    availableModels,
    performanceMetrics
  };
}