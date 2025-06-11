import { useState, useCallback, useRef } from 'react'
import { usePersona } from '@/contexts/PersonaContext'

export type SearchMode = 
  | 'normal' 
  | 'deep' 
  | 'super-deep' 
  | 'creative' 
  | 'private' 
  | 'analytical' 
  | 'research'

export interface SearchModeConfig {
  id: SearchMode
  name: string
  description: string
  icon: string
  estimatedTime: string
  costLevel: 'Low' | 'Medium' | 'High' | 'Premium'
  complexity: number
  capabilities: string[]
  useCase: string
}

export interface SearchResult {
  id: string
  title: string
  snippet: string
  source: string
  relevance: number
  metadata: {
    searchMode: SearchMode
    processingTime: number
    sourceType: string
    confidence: number
  }
}

export interface ActiveSearch {
  id: string
  query: string
  mode: SearchMode
  startTime: Date
  status: 'processing' | 'completed' | 'failed'
  progress: number
  estimatedCompletion: Date
  results: SearchResult[]
  cost: number
}

const searchModeConfigs: SearchModeConfig[] = [
  {
    id: 'normal',
    name: 'Normal Search',
    description: 'Quick, straightforward search across primary data sources',
    icon: '🔍',
    estimatedTime: '1-3 seconds',
    costLevel: 'Low',
    complexity: 1,
    capabilities: ['Basic keyword matching', 'Simple ranking', 'Fast results'],
    useCase: 'Quick information lookup and basic queries'
  },
  {
    id: 'deep',
    name: 'Deep Search',
    description: 'Multi-step iterative search with context building',
    icon: '🌊',
    estimatedTime: '10-30 seconds',
    costLevel: 'Medium',
    complexity: 3,
    capabilities: ['Multi-source analysis', 'Context building', 'Iterative refinement'],
    useCase: 'Complex research requiring multiple perspectives'
  },
  {
    id: 'super-deep',
    name: 'Super Deep Search',
    description: 'Exhaustive multi-source search with comprehensive analysis',
    icon: '🏔️',
    estimatedTime: '1-3 minutes',
    costLevel: 'High',
    complexity: 5,
    capabilities: ['Exhaustive source coverage', 'Cross-reference validation', 'Deep synthesis'],
    useCase: 'Critical decisions requiring maximum thoroughness'
  },
  {
    id: 'creative',
    name: 'Creative Search',
    description: 'Brainstorming and idea generation with lateral thinking',
    icon: '🎨',
    estimatedTime: '30-60 seconds',
    costLevel: 'Medium',
    complexity: 4,
    capabilities: ['Lateral connections', 'Idea generation', 'Creative synthesis'],
    useCase: 'Innovation, problem-solving, and creative projects'
  },
  {
    id: 'private',
    name: 'Private Search',
    description: 'Privacy-focused search using only local and secure sources',
    icon: '🔒',
    estimatedTime: '5-15 seconds',
    costLevel: 'Low',
    complexity: 2,
    capabilities: ['Local data only', 'Privacy preservation', 'Secure processing'],
    useCase: 'Sensitive information requiring maximum privacy'
  },
  {
    id: 'analytical',
    name: 'Analytical Search',
    description: 'Data-driven search with statistical analysis and insights',
    icon: '📊',
    estimatedTime: '20-45 seconds',
    costLevel: 'Medium',
    complexity: 4,
    capabilities: ['Statistical analysis', 'Trend identification', 'Data insights'],
    useCase: 'Business intelligence and data-driven decisions'
  },
  {
    id: 'research',
    name: 'Research Search',
    description: 'Academic-grade search with citation and peer review analysis',
    icon: '🔬',
    estimatedTime: '2-5 minutes',
    costLevel: 'Premium',
    complexity: 5,
    capabilities: ['Academic sources', 'Citation analysis', 'Peer review integration'],
    useCase: 'Scientific research and academic work'
  }
]

export function useSearchOrchestrator() {
  const [activeSearches, setActiveSearches] = useState<ActiveSearch[]>([])
  const [searchHistory, setSearchHistory] = useState<ActiveSearch[]>([])
  const { activePersona, updatePersonaState, personaStates } = usePersona()
  const searchIdCounter = useRef(0)

  const getSearchModeConfig = useCallback((mode: SearchMode): SearchModeConfig => {
    return searchModeConfigs.find(config => config.id === mode) || searchModeConfigs[0]
  }, [])

  const determineOptimalMode = useCallback((query: string): SearchMode => {
    const queryLower = query.toLowerCase()
    
    // Keywords that suggest specific search modes
    if (queryLower.includes('research') || queryLower.includes('study') || queryLower.includes('paper')) {
      return 'research'
    }
    if (queryLower.includes('creative') || queryLower.includes('idea') || queryLower.includes('brainstorm')) {
      return 'creative'
    }
    if (queryLower.includes('private') || queryLower.includes('confidential') || queryLower.includes('secure')) {
      return 'private'
    }
    if (queryLower.includes('analyze') || queryLower.includes('data') || queryLower.includes('trend')) {
      return 'analytical'
    }
    if (queryLower.includes('comprehensive') || queryLower.includes('thorough') || queryLower.includes('detailed')) {
      return 'super-deep'
    }
    if (query.split(' ').length > 10 || queryLower.includes('complex')) {
      return 'deep'
    }
    
    return 'normal'
  }, [])

  const simulateSearchProcessing = useCallback(async (search: ActiveSearch): Promise<SearchResult[]> => {
    const config = getSearchModeConfig(search.mode)
    const processingSteps = config.complexity * 2
    
    // Simulate processing with progress updates
    for (let step = 0; step < processingSteps; step++) {
      await new Promise(resolve => setTimeout(resolve, 500))
      
      setActiveSearches(prev => prev.map(s => 
        s.id === search.id 
          ? { ...s, progress: Math.round((step + 1) / processingSteps * 100) }
          : s
      ))
    }

    // Generate realistic results based on search mode
    const resultCount = config.complexity === 1 ? 5 : config.complexity * 3
    const results: SearchResult[] = []

    for (let i = 0; i < resultCount; i++) {
      results.push({
        id: `${search.id}-result-${i}`,
        title: `${search.mode} search result ${i + 1} for "${search.query}"`,
        snippet: `This is a comprehensive result from ${config.name} demonstrating ${config.capabilities[i % config.capabilities.length]}.`,
        source: config.id === 'private' ? 'Local Database' : 
                config.id === 'research' ? 'Academic Source' :
                config.id === 'analytical' ? 'Data Warehouse' : 'Web Source',
        relevance: Math.random() * 0.3 + 0.7, // 0.7 to 1.0
        metadata: {
          searchMode: search.mode,
          processingTime: config.complexity * 1000,
          sourceType: config.id === 'research' ? 'academic' : 'general',
          confidence: Math.random() * 0.2 + 0.8
        }
      })
    }

    return results
  }, [getSearchModeConfig])

  const executeSearch = useCallback(async (
    query: string, 
    mode?: SearchMode,
    options?: {
      priority?: 'low' | 'normal' | 'high'
      costLimit?: number
      autoRoute?: boolean
    }
  ): Promise<string> => {
    const searchId = `search-${++searchIdCounter.current}`
    const selectedMode = mode || (options?.autoRoute !== false ? determineOptimalMode(query) : 'normal')
    const config = getSearchModeConfig(selectedMode)
    
    const newSearch: ActiveSearch = {
      id: searchId,
      query,
      mode: selectedMode,
      startTime: new Date(),
      status: 'processing',
      progress: 0,
      estimatedCompletion: new Date(Date.now() + config.complexity * 10000),
      results: [],
      cost: config.complexity * 0.05
    }

    setActiveSearches(prev => [...prev, newSearch])
    
    // Update persona state
    updatePersonaState(activePersona, {
      activeSearches: personaStates[activePersona].activeSearches + 1
    })

    try {
      const results = await simulateSearchProcessing(newSearch)
      
      const completedSearch: ActiveSearch = {
        ...newSearch,
        status: 'completed',
        progress: 100,
        results
      }

      setActiveSearches(prev => prev.filter(s => s.id !== searchId))
      setSearchHistory(prev => [completedSearch, ...prev.slice(0, 49)]) // Keep last 50
      
      // Update persona state
      updatePersonaState(activePersona, {
        activeSearches: Math.max(0, personaStates[activePersona].activeSearches - 1)
      })

      return searchId
    } catch (error) {
      const failedSearch: ActiveSearch = {
        ...newSearch,
        status: 'failed',
        progress: 0
      }

      setActiveSearches(prev => prev.filter(s => s.id !== searchId))
      setSearchHistory(prev => [failedSearch, ...prev.slice(0, 49)])
      
      updatePersonaState(activePersona, {
        activeSearches: Math.max(0, personaStates[activePersona].activeSearches - 1)
      })

      throw error
    }
  }, [determineOptimalMode, getSearchModeConfig, simulateSearchProcessing, updatePersonaState, activePersona, personaStates])

  const cancelSearch = useCallback((searchId: string) => {
    setActiveSearches(prev => prev.filter(s => s.id !== searchId))
    updatePersonaState(activePersona, {
      activeSearches: Math.max(0, personaStates[activePersona].activeSearches - 1)
    })
  }, [updatePersonaState, activePersona, personaStates])

  const getSearchById = useCallback((searchId: string): ActiveSearch | undefined => {
    return activeSearches.find(s => s.id === searchId) || 
           searchHistory.find(s => s.id === searchId)
  }, [activeSearches, searchHistory])

  return {
    // Core functionality
    executeSearch,
    cancelSearch,
    getSearchById,
    
    // Search configuration
    searchModeConfigs,
    getSearchModeConfig,
    determineOptimalMode,
    
    // State
    activeSearches,
    searchHistory,
    
    // Metrics
    totalSearches: searchHistory.length + activeSearches.length,
    averageResponseTime: searchHistory.reduce((acc, s) => 
      acc + (s.results.length > 0 ? s.results[0].metadata.processingTime : 0), 0
    ) / Math.max(1, searchHistory.length),
    successRate: searchHistory.filter(s => s.status === 'completed').length / Math.max(1, searchHistory.length)
  }
} 