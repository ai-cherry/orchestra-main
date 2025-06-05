"use client";

import { useState, useCallback, useRef, useEffect } from 'react';
import type { 
  SearchSuggestion, 
  DetectedIntent, 
  SearchMode,
  SearchResponse 
} from '@/types/search';

/**
 * Custom hook for OmniSearch functionality
 * 
 * Manages search state, API calls, and caching for optimal performance.
 * Implements intelligent caching and request deduplication.
 */
export const useOmniSearch = () => {
  // State management
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [detectedIntent, setDetectedIntent] = useState<DetectedIntent | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Cache management
  const cache = useRef<Map<string, SearchSuggestion[]>>(new Map());
  const pendingRequests = useRef<Map<string, Promise<SearchSuggestion[]>>>(new Map());
  
  // API endpoint
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

  /**
   * Detect intent from query using NLP
   */
  const detectIntent = useCallback(async (query: string): Promise<DetectedIntent | null> => {
    try {
      const response = await fetch(`${apiUrl}/api/intent/detect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || ''
        },
        body: JSON.stringify({ query })
      });

      if (!response.ok) {
        throw new Error(`Intent detection failed: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Intent detection error:', error);
      return null;
    }
  }, [apiUrl]);

  /**
   * Fetch search suggestions with caching and deduplication
   */
  const fetchSuggestions = useCallback(async (
    query: string, 
    mode: SearchMode
  ): Promise<SearchSuggestion[]> => {
    const cacheKey = `${mode}:${query}`;
    
    // Check cache first
    if (cache.current.has(cacheKey)) {
      return cache.current.get(cacheKey)!;
    }
    
    // Check if request is already pending
    if (pendingRequests.current.has(cacheKey)) {
      return pendingRequests.current.get(cacheKey)!;
    }
    
    // Create new request
    const requestPromise = (async () => {
      try {
        const response = await fetch(`${apiUrl}/api/suggestions?` + new URLSearchParams({
          partial_query: query,
          mode: mode,
          limit: '10'
        }), {
          headers: {
            'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || ''
          }
        });

        if (!response.ok) {
          throw new Error(`Suggestions fetch failed: ${response.statusText}`);
        }

        const data = await response.json();
        const suggestions = data.suggestions || [];
        
        // Cache the results
        cache.current.set(cacheKey, suggestions);
        
        // Clean up old cache entries if cache is getting large
        if (cache.current.size > 100) {
          const firstKey = cache.current.keys().next().value;
          cache.current.delete(firstKey);
        }
        
        return suggestions;
      } finally {
        // Remove from pending requests
        pendingRequests.current.delete(cacheKey);
      }
    })();
    
    // Store pending request
    pendingRequests.current.set(cacheKey, requestPromise);
    
    return requestPromise;
  }, [apiUrl]);

  /**
   * Perform search with intent detection and suggestions
   */
  const performSearch = useCallback(async (
    query: string,
    mode: SearchMode = 'auto',
    execute: boolean = false
  ) => {
    // Reset error state
    setError(null);
    
    // Don't search for empty queries
    if (!query.trim()) {
      setSuggestions([]);
      setDetectedIntent(null);
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Parallel execution for better performance
      const [intentResult, suggestionsResult] = await Promise.all([
        detectIntent(query),
        fetchSuggestions(query, mode)
      ]);
      
      setDetectedIntent(intentResult);
      setSuggestions(suggestionsResult);
      
      // If execute is true, perform the actual search
      if (execute) {
        await executeSearch(query, intentResult?.type || 'search');
      }
    } catch (error) {
      console.error('Search error:', error);
      setError(error instanceof Error ? error.message : 'Search failed');
      setSuggestions([]);
    } finally {
      setIsLoading(false);
    }
  }, [detectIntent, fetchSuggestions]);

  /**
   * Execute the actual search/command
   */
  const executeSearch = useCallback(async (
    query: string,
    intentType: string
  ) => {
    try {
      const response = await fetch(`${apiUrl}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || ''
        },
        body: JSON.stringify({
          query,
          intent: intentType
        })
      });

      if (!response.ok) {
        throw new Error(`Search execution failed: ${response.statusText}`);
      }

      const result = await response.json();
      
      // Handle different intent types
      switch (intentType) {
        case 'agent_creation':
          // Redirect to agent creation wizard
          window.location.href = '/agents/create';
          break;
        case 'command':
          // Execute command and show result
          // console.log('Command result:', result);
          break;
        default:
          // Handle search results
          // console.log('Search results:', result);
      }
    } catch (error) {
      console.error('Search execution error:', error);
      setError(error instanceof Error ? error.message : 'Execution failed');
    }
  }, [apiUrl]);

  /**
   * Clear suggestions and reset state
   */
  const clearSuggestions = useCallback(() => {
    setSuggestions([]);
    setDetectedIntent(null);
    setError(null);
  }, []);

  /**
   * Clear cache (useful for forcing fresh results)
   */
  const clearCache = useCallback(() => {
    cache.current.clear();
    pendingRequests.current.clear();
  }, []);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      // Cancel any pending requests
      pendingRequests.current.clear();
    };
  }, []);

  return {
    suggestions,
    isLoading,
    detectedIntent,
    error,
    performSearch,
    clearSuggestions,
    clearCache
  };
};