import React, { useState, useEffect } from 'react'
import { Search, Settings, Zap, Shield, Database, Globe, Clock, DollarSign } from 'lucide-react'
import apiClient from '../lib/api'

const SearchModes = {
  normal: {
    name: 'Normal',
    icon: Search,
    description: 'Quick search using basic sources',
    color: 'blue',
    sources: ['Database', 'DuckDuckGo'],
    estimatedTime: '2-5s',
    cost: 'Free'
  },
  deep: {
    name: 'Deep',
    icon: Zap,
    description: 'Comprehensive search with multiple APIs',
    color: 'purple',
    sources: ['Database', 'DuckDuckGo', 'Exa AI', 'SERP'],
    estimatedTime: '10-20s',
    cost: '$0.02-0.05'
  },
  super_deep: {
    name: 'Super Deep',
    icon: Settings,
    description: 'Exhaustive search with web scraping',
    color: 'orange',
    sources: ['Database', 'DuckDuckGo', 'Exa AI', 'SERP', 'Apify', 'PhantomBuster'],
    estimatedTime: '20-30s',
    cost: '$0.05-0.10'
  },
  uncensored: {
    name: 'Uncensored',
    icon: Shield,
    description: 'Unrestricted search with alternative sources',
    color: 'red',
    sources: ['Venice AI', 'ZenRows', 'Exa AI', 'Database'],
    estimatedTime: '15-25s',
    cost: '$0.03-0.08'
  }
}

export default function AdvancedSearchInterface({ onSearch, isSearching = false, currentMode = 'normal' }) {
  const [selectedMode, setSelectedMode] = useState(currentMode)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState(null)
  const [searchSources, setSearchSources] = useState({})
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [includeDatabase, setIncludeDatabase] = useState(true)
  const [includeInternet, setIncludeInternet] = useState(true)
  const [maxResults, setMaxResults] = useState(10)

  // Load available search sources on component mount
  useEffect(() => {
    loadSearchSources()
  }, [])

  const loadSearchSources = async () => {
    try {
      const response = await apiClient.request('/api/search/sources')
      setSearchSources(response.sources || {})
    } catch (error) {
      console.error('Failed to load search sources:', error)
    }
  }

  const executeAdvancedSearch = async () => {
    if (!searchQuery.trim()) return

    try {
      const searchRequest = {
        query: searchQuery,
        persona: 'sophia', // This should come from parent component
        search_mode: selectedMode,
        include_database: includeDatabase,
        include_internet: includeInternet,
        max_results: maxResults
      }

      const response = await apiClient.request('/api/search/advanced', {
        method: 'POST',
        body: JSON.stringify(searchRequest)
      })

      setSearchResults(response)
      
      // Call parent callback if provided
      if (onSearch) {
        onSearch(response)
      }
    } catch (error) {
      console.error('Advanced search failed:', error)
      setSearchResults({
        error: 'Search failed. Please try again.',
        query: searchQuery
      })
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      executeAdvancedSearch()
    }
  }

  return (
    <div className="space-y-6">
      {/* Search Mode Selection */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Object.entries(SearchModes).map(([mode, config]) => {
          const IconComponent = config.icon
          const isSelected = selectedMode === mode
          
          return (
            <button
              key={mode}
              onClick={() => setSelectedMode(mode)}
              className={`p-4 rounded-xl border-2 transition-all duration-200 text-left ${
                isSelected
                  ? `border-${config.color}-500 bg-${config.color}-500/10 shadow-lg`
                  : 'border-gray-600 bg-gray-700/50 hover:border-gray-500 hover:bg-gray-700'
              }`}
            >
              <div className="flex items-center space-x-3 mb-3">
                <div className={`p-2 rounded-lg ${
                  isSelected 
                    ? `bg-${config.color}-500/20 text-${config.color}-400` 
                    : 'bg-gray-600/50 text-gray-400'
                }`}>
                  <IconComponent className="w-5 h-5" />
                </div>
                <div>
                  <h3 className={`font-semibold ${
                    isSelected ? `text-${config.color}-400` : 'text-white'
                  }`}>
                    {config.name}
                  </h3>
                  <p className="text-xs text-gray-400">{config.cost}</p>
                </div>
              </div>
              
              <p className="text-sm text-gray-300 mb-3">
                {config.description}
              </p>
              
              <div className="flex items-center justify-between text-xs text-gray-400">
                <div className="flex items-center space-x-1">
                  <Clock className="w-3 h-3" />
                  <span>{config.estimatedTime}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Database className="w-3 h-3" />
                  <span>{config.sources.length} sources</span>
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {/* Search Input */}
      <div className="space-y-4">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={`Enter your search query (${SearchModes[selectedMode].name} mode)...`}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            disabled={isSearching}
          />
          
          <button
            onClick={executeAdvancedSearch}
            disabled={isSearching || !searchQuery.trim()}
            className={`absolute right-2 top-1/2 transform -translate-y-1/2 px-4 py-1.5 rounded-md transition-colors ${
              isSearching || !searchQuery.trim()
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : `bg-${SearchModes[selectedMode].color}-600 hover:bg-${SearchModes[selectedMode].color}-700 text-white`
            }`}
          >
            {isSearching ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* Advanced Options Toggle */}
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center space-x-2 text-sm text-gray-400 hover:text-white transition-colors"
        >
          <Settings className="w-4 h-4" />
          <span>Advanced Options</span>
        </button>

        {/* Advanced Options Panel */}
        {showAdvanced && (
          <div className="bg-gray-800/50 rounded-lg p-4 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={includeDatabase}
                    onChange={(e) => setIncludeDatabase(e.target.checked)}
                    className="rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-300">Include Database</span>
                </label>
                
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={includeInternet}
                    onChange={(e) => setIncludeInternet(e.target.checked)}
                    className="rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-300">Include Internet</span>
                </label>
              </div>
              
              <div className="space-y-2">
                <label className="block text-sm text-gray-300">Max Results</label>
                <select
                  value={maxResults}
                  onChange={(e) => setMaxResults(parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value={5}>5 results</option>
                  <option value={10}>10 results</option>
                  <option value={20}>20 results</option>
                  <option value={50}>50 results</option>
                </select>
              </div>
              
              <div className="space-y-2">
                <label className="block text-sm text-gray-300">Available Sources</label>
                <div className="text-xs space-y-1">
                  {Object.entries(searchSources).map(([source, config]) => (
                    <div key={source} className="flex items-center justify-between">
                      <span className={config.available ? 'text-green-400' : 'text-red-400'}>
                        {source}
                      </span>
                      <span className="text-gray-500">{config.cost}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Search Results */}
      {searchResults && (
        <div className="space-y-4">
          {searchResults.error ? (
            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
              <p className="text-red-400">{searchResults.error}</p>
            </div>
          ) : (
            <>
              {/* Search Summary */}
              <div className="bg-gray-800/50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold text-white">
                    Search Results for "{searchResults.query}"
                  </h3>
                  <div className="flex items-center space-x-4 text-sm text-gray-400">
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>{searchResults.processing_time_ms}ms</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <DollarSign className="w-4 h-4" />
                      <span>${searchResults.cost_estimate}</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4 text-sm">
                  <span className="text-gray-300">
                    {searchResults.total_results} results from {searchResults.sources_used.length} sources
                  </span>
                  <div className="flex items-center space-x-2">
                    {searchResults.sources_used.map((source, index) => (
                      <span key={index} className="px-2 py-1 bg-gray-700 rounded text-xs">
                        {source}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Results List */}
              <div className="space-y-3">
                {searchResults.blended_results.map((result, index) => (
                  <div key={index} className="bg-gray-800/50 rounded-lg p-4 hover:bg-gray-800/70 transition-colors">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-white line-clamp-2">
                        {result.url ? (
                          <a 
                            href={result.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="hover:text-blue-400 transition-colors"
                          >
                            {result.title}
                          </a>
                        ) : (
                          result.title
                        )}
                      </h4>
                      <div className="flex items-center space-x-2 text-xs">
                        <span className="px-2 py-1 bg-gray-700 rounded">
                          {result.source}
                        </span>
                        <span className="text-gray-400">
                          {(result.relevance_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    
                    <p className="text-gray-300 text-sm line-clamp-3 mb-2">
                      {result.content}
                    </p>
                    
                    {result.url && (
                      <a 
                        href={result.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                      >
                        {result.url}
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}

