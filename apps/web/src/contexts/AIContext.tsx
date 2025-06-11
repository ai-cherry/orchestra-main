import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';

// AI Context Types
interface AIFeature {
  id: string;
  name: string;
  enabled: boolean;
  loading: boolean;
  error?: string;
}

interface AIState {
  features: AIFeature[];
  conversationMode: boolean;
  workflowMode: boolean;
  aiAssistantActive: boolean;
  realtimeCollaboration: boolean;
  performanceMetrics: {
    responseTime: number;
    buildTime: number;
    aiResponseTime: number;
  };
}

interface AIContextType {
  state: AIState;
  toggleFeature: (featureId: string) => void;
  setConversationMode: (enabled: boolean) => void;
  setWorkflowMode: (enabled: boolean) => void;
  toggleAIAssistant: () => void;
  updatePerformanceMetrics: (metrics: Partial<AIState['performanceMetrics']>) => void;
}

// Initial State
const initialState: AIState = {
  features: [
    { id: 'conversational-interface', name: 'Conversational Interface', enabled: true, loading: false },
    { id: 'workflow-canvas', name: 'Workflow Canvas', enabled: true, loading: false },
    { id: 'real-time-collaboration', name: 'Real-time Collaboration', enabled: false, loading: false },
    { id: 'ai-autocomplete', name: 'AI Autocomplete', enabled: true, loading: false },
    { id: 'smart-suggestions', name: 'Smart Suggestions', enabled: true, loading: false }
  ],
  conversationMode: false,
  workflowMode: false,
  aiAssistantActive: true,
  realtimeCollaboration: false,
  performanceMetrics: {
    responseTime: 0,
    buildTime: 0,
    aiResponseTime: 0
  }
};

// Reducer
type AIAction = 
  | { type: 'TOGGLE_FEATURE'; payload: string }
  | { type: 'SET_CONVERSATION_MODE'; payload: boolean }
  | { type: 'SET_WORKFLOW_MODE'; payload: boolean }
  | { type: 'TOGGLE_AI_ASSISTANT' }
  | { type: 'UPDATE_PERFORMANCE_METRICS'; payload: Partial<AIState['performanceMetrics']> }
  | { type: 'SET_FEATURE_LOADING'; payload: { id: string; loading: boolean } }
  | { type: 'SET_FEATURE_ERROR'; payload: { id: string; error?: string } };

const aiReducer = (state: AIState, action: AIAction): AIState => {
  switch (action.type) {
    case 'TOGGLE_FEATURE':
      return {
        ...state,
        features: state.features.map(feature =>
          feature.id === action.payload
            ? { ...feature, enabled: !feature.enabled }
            : feature
        )
      };
    
    case 'SET_CONVERSATION_MODE':
      return { ...state, conversationMode: action.payload };
    
    case 'SET_WORKFLOW_MODE':
      return { ...state, workflowMode: action.payload };
    
    case 'TOGGLE_AI_ASSISTANT':
      return { ...state, aiAssistantActive: !state.aiAssistantActive };
    
    case 'UPDATE_PERFORMANCE_METRICS':
      return {
        ...state,
        performanceMetrics: { ...state.performanceMetrics, ...action.payload }
      };
    
    case 'SET_FEATURE_LOADING':
      return {
        ...state,
        features: state.features.map(feature =>
          feature.id === action.payload.id
            ? { ...feature, loading: action.payload.loading }
            : feature
        )
      };
    
    case 'SET_FEATURE_ERROR':
      return {
        ...state,
        features: state.features.map(feature =>
          feature.id === action.payload.id
            ? { ...feature, error: action.payload.error, loading: false }
            : feature
        )
      };
    
    default:
      return state;
  }
};

// Context
const AIContext = createContext<AIContextType | undefined>(undefined);

// Provider Component
export const AIProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(aiReducer, initialState);

  // Actions
  const toggleFeature = useCallback((featureId: string) => {
    dispatch({ type: 'TOGGLE_FEATURE', payload: featureId });
  }, []);

  const setConversationMode = useCallback((enabled: boolean) => {
    dispatch({ type: 'SET_CONVERSATION_MODE', payload: enabled });
  }, []);

  const setWorkflowMode = useCallback((enabled: boolean) => {
    dispatch({ type: 'SET_WORKFLOW_MODE', payload: enabled });
  }, []);

  const toggleAIAssistant = useCallback(() => {
    dispatch({ type: 'TOGGLE_AI_ASSISTANT' });
  }, []);

  const updatePerformanceMetrics = useCallback((metrics: Partial<AIState['performanceMetrics']>) => {
    dispatch({ type: 'UPDATE_PERFORMANCE_METRICS', payload: metrics });
  }, []);

  // Performance tracking effect
  useEffect(() => {
    const startTime = performance.now();
    
    const handleLoad = () => {
      const loadTime = performance.now() - startTime;
      updatePerformanceMetrics({ responseTime: loadTime });
    };

    window.addEventListener('load', handleLoad);
    return () => window.removeEventListener('load', handleLoad);
  }, [updatePerformanceMetrics]);

  const contextValue: AIContextType = {
    state,
    toggleFeature,
    setConversationMode,
    setWorkflowMode,
    toggleAIAssistant,
    updatePerformanceMetrics
  };

  return (
    <AIContext.Provider value={contextValue}>
      {children}
    </AIContext.Provider>
  );
};

// Custom Hook
export const useAI = (): AIContextType => {
  const context = useContext(AIContext);
  if (!context) {
    throw new Error('useAI must be used within an AIProvider');
  }
  return context;
};

// AI Feature Hook
export const useAIFeature = (featureId: string) => {
  const { state, toggleFeature } = useAI();
  const feature = state.features.find(f => f.id === featureId);
  
  return {
    feature,
    enabled: feature?.enabled ?? false,
    loading: feature?.loading ?? false,
    error: feature?.error,
    toggle: () => toggleFeature(featureId)
  };
};

export default AIContext; 