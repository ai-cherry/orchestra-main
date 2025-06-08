import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import ServiceManager from '../services/ServiceManager';
import ContextDB, { ContextData } from '../utils/ContextDB';

interface ContextManagerType {
  contexts: ContextData[];
  currentContext: ContextData | null;
  addContext: (content: string, type: ContextData['type'], metadata?: Record<string, any>) => void;
  switchContext: (contextId: string) => void;
  searchContexts: (query: string) => ContextData[];
  getRelatedContexts: (contextId: string) => ContextData[];
  clearContexts: () => void;
  persistContext: () => void;
  loadPersistedContext: () => void;
}

const ContextManagerContext = createContext<ContextManagerType | undefined>(undefined);

export const useContextManager = () => {
  const context = useContext(ContextManagerContext);
  if (context === undefined) {
    throw new Error('useContextManager must be used within a ContextManagerProvider');
  }
  return context;
};

interface ContextManagerProviderProps {
  children: ReactNode;
}

export const ContextManagerProvider: React.FC<ContextManagerProviderProps> = ({ children }) => {
  const [contexts, setContexts] = useState<ContextData[]>([]);
  const [currentContext, setCurrentContext] = useState<ContextData | null>(null);

  useEffect(() => {
    loadPersistedContext();
  }, []);

  useEffect(() => {
    // Auto-persist contexts when they change
    const timeoutId = setTimeout(() => {
      persistContext();
    }, 1000); // Debounce saves

    return () => clearTimeout(timeoutId);
  }, [contexts]);

  const addContext = async (content: string, type: ContextData['type'], metadata: Record<string, any> = {}) => {
    const newContext: ContextData = {
      id: `context_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      content,
      type,
      timestamp: new Date().toISOString(),
      metadata: {
        ...metadata,
        wordCount: content.split(' ').length,
        characterCount: content.length
      }
    };

    await ContextDB.addContext(newContext);
    const recent = await ContextDB.getRecentContexts(100);
    setContexts(recent);
    setCurrentContext(newContext);
  };

  const switchContext = (contextId: string) => {
    const context = contexts.find(c => c.id === contextId);
    if (context) {
      setCurrentContext(context);
    }
  };

  const searchContexts = (query: string): ContextData[] => {
    const lowercaseQuery = query.toLowerCase();
    return contexts.filter(context => 
      context.content.toLowerCase().includes(lowercaseQuery) ||
      Object.values(context.metadata).some(value => 
        typeof value === 'string' && value.toLowerCase().includes(lowercaseQuery)
      )
    );
  };

  const getRelatedContexts = (contextId: string): ContextData[] => {
    const targetContext = contexts.find(c => c.id === contextId);
    if (!targetContext) return [];

    // Simple similarity based on content overlap and type
    return contexts
      .filter(c => c.id !== contextId)
      .map(context => ({
        context,
        similarity: calculateSimilarity(targetContext, context)
      }))
      .filter(({ similarity }) => similarity > 0.3)
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, 5)
      .map(({ context }) => context);
  };

  const calculateSimilarity = (context1: ContextData, context2: ContextData): number => {
    // Type similarity
    const typeSimilarity = context1.type === context2.type ? 0.3 : 0;

    // Content similarity (simple word overlap)
    const words1 = new Set(context1.content.toLowerCase().split(/\s+/));
    const words2 = new Set(context2.content.toLowerCase().split(/\s+/));
    const intersection = new Set([...words1].filter(x => words2.has(x)));
    const union = new Set([...words1, ...words2]);
    const contentSimilarity = intersection.size / union.size * 0.7;

    return typeSimilarity + contentSimilarity;
  };

  const clearContexts = async () => {
    await ContextDB.clearContexts();
    setContexts([]);
    setCurrentContext(null);
  };

  const persistContext = async () => {
    // No-op: Dexie handles persistence
    // Optionally, could trigger a backup or sync here
  };

  const loadPersistedContext = async () => {
    try {
      const recent = await ContextDB.getRecentContexts(100);
      setContexts(recent);
      if (recent.length > 0) {
        setCurrentContext(recent[0]);
      }
    } catch (error) {
      console.error('Failed to load persisted contexts:', error);
    }
  };

  const value = {
    contexts,
    currentContext,
    addContext,
    switchContext,
    searchContexts,
    getRelatedContexts,
    clearContexts,
    persistContext,
    loadPersistedContext
  };

  return <ContextManagerContext.Provider value={value}>{children}</ContextManagerContext.Provider>;
};

