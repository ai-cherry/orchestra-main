import { useState, useCallback, useEffect } from 'react';
import { CommandIntent, CommandType, Suggestion, NLPResult } from '@/types/command';
import { 
  Search, 
  Navigation, 
  Settings, 
  Plus, 
  BarChart, 
  FileText,
  Zap
} from 'lucide-react';

/**
 * Mock NLP processor for command intent recognition
 * In production, this would call an actual NLP service
 */
export function useNLPProcessor() {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  /**
   * Process query to extract intent and generate suggestions
   */
  const processQuery = useCallback(async (query: string): Promise<CommandIntent> => {
    setIsProcessing(true);
    
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Simple intent classification based on keywords
      const lowerQuery = query.toLowerCase();
      let type: CommandType = CommandType.QUERY;
      let confidence = 0.8;
      
      if (lowerQuery.includes('navigate') || lowerQuery.includes('go to')) {
        type = CommandType.NAVIGATION;
        confidence = 0.95;
      } else if (lowerQuery.includes('search') || lowerQuery.includes('find')) {
        type = CommandType.SEARCH;
        confidence = 0.9;
      } else if (lowerQuery.includes('create') || lowerQuery.includes('new')) {
        type = CommandType.CREATION;
        confidence = 0.9;
      } else if (lowerQuery.includes('analyze') || lowerQuery.includes('report')) {
        type = CommandType.ANALYSIS;
        confidence = 0.85;
      } else if (lowerQuery.includes('config') || lowerQuery.includes('setting')) {
        type = CommandType.CONFIGURATION;
        confidence = 0.9;
      } else if (
        lowerQuery.includes('run') || 
        lowerQuery.includes('execute') || 
        lowerQuery.includes('start')
      ) {
        type = CommandType.ACTION;
        confidence = 0.85;
      }
      
      // Extract entities (simplified version)
      const entities = [];
      
      // Extract model names
      const modelPattern = /(gpt-4|claude|gemini|llama)/gi;
      const modelMatches = query.match(modelPattern);
      if (modelMatches) {
        modelMatches.forEach(match => {
          const index = query.indexOf(match);
          entities.push({
            type: 'model',
            value: match,
            confidence: 0.9,
            position: { start: index, end: index + match.length }
          });
        });
      }
      
      // Extract numbers
      const numberPattern = /\d+/g;
      const numberMatches = query.match(numberPattern);
      if (numberMatches) {
        numberMatches.forEach(match => {
          const index = query.indexOf(match);
          entities.push({
            type: 'number',
            value: match,
            confidence: 0.95,
            position: { start: index, end: index + match.length }
          });
        });
      }
      
      return {
        type,
        confidence,
        entities,
        parameters: {
          originalQuery: query,
          processedAt: new Date().toISOString()
        }
      };
    } finally {
      setIsProcessing(false);
    }
  }, []);

  /**
   * Generate suggestions based on partial query
   */
  const generateSuggestions = useCallback((query: string): Suggestion[] => {
    if (!query.trim()) return [];
    
    const lowerQuery = query.toLowerCase();
    const allSuggestions: Suggestion[] = [
      {
        text: 'Search for models',
        type: CommandType.SEARCH,
        icon: Search,
        description: 'Search available LLM models',
        confidence: 0.8
      },
      {
        text: 'Navigate to dashboard',
        type: CommandType.NAVIGATION,
        icon: Navigation,
        description: 'Go to main dashboard',
        shortcut: 'Cmd+D',
        confidence: 0.9
      },
      {
        text: 'Create new research',
        type: CommandType.CREATION,
        icon: Plus,
        description: 'Start a new research project',
        confidence: 0.85
      },
      {
        text: 'Analyze performance',
        type: CommandType.ANALYSIS,
        icon: BarChart,
        description: 'View performance analytics',
        confidence: 0.8
      },
      {
        text: 'Configure settings',
        type: CommandType.CONFIGURATION,
        icon: Settings,
        description: 'Open configuration panel',
        shortcut: 'Cmd+,',
        confidence: 0.9
      },
      {
        text: 'Generate report',
        type: CommandType.ACTION,
        icon: FileText,
        description: 'Generate analytics report',
        confidence: 0.75
      },
      {
        text: 'Run optimization',
        type: CommandType.ACTION,
        icon: Zap,
        description: 'Optimize routing performance',
        confidence: 0.7
      }
    ];
    
    // Filter and score suggestions based on query
    return allSuggestions
      .filter(suggestion => 
        suggestion.text.toLowerCase().includes(lowerQuery) ||
        suggestion.description?.toLowerCase().includes(lowerQuery)
      )
      .map(suggestion => ({
        ...suggestion,
        confidence: calculateSuggestionScore(suggestion, query)
      }))
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, 5);
  }, []);

  /**
   * Calculate relevance score for suggestion
   */
  const calculateSuggestionScore = (suggestion: Suggestion, query: string): number => {
    const lowerQuery = query.toLowerCase();
    const lowerText = suggestion.text.toLowerCase();
    
    // Exact match
    if (lowerText === lowerQuery) return 1.0;
    
    // Starts with query
    if (lowerText.startsWith(lowerQuery)) return 0.9;
    
    // Contains query
    if (lowerText.includes(lowerQuery)) return 0.7;
    
    // Description contains query
    if (suggestion.description?.toLowerCase().includes(lowerQuery)) return 0.5;
    
    return 0.3;
  };

  /**
   * Update suggestions when query changes
   */
  useEffect(() => {
    // This would typically be triggered by the debounced query
    // For now, we'll generate suggestions on demand
  }, []);

  return {
    processQuery,
    generateSuggestions,
    suggestions,
    isProcessing
  };
}