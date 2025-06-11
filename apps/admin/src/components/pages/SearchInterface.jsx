import { useState, useEffect } from 'react'

const SearchInterface = ({ persona, onPersonaChange }) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchMode, setSearchMode] = useState('normal')
  const [searchResults, setSearchResults] = useState([])
  const [recentSearches, setRecentSearches] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [showCreateTools, setShowCreateTools] = useState(false)

  const personas = {
    cherry: {
      name: 'Cherry',
      icon: '🍒',
      color: '#ff4757',
      placeholder: 'Search for wellness tips, creative ideas, or personal insights...',
      recentSearches: [
        'Cherry personality optimization strategies',
        'Creative writing prompts for personal growth',
        'Wellness routines for busy professionals'
      ]
    },
    sophia: {
      name: 'Sophia',
      icon: '💼',
      color: '#8b4513',
      placeholder: 'Search for business intelligence, market data, or financial insights...',
      recentSearches: [
        'Sophia business intelligence workflows',
        'Real estate market analysis tools',
        'Financial planning strategies'
      ]
    },
    karen: {
      name: 'Karen',
      icon: '🏥',
      color: '#dc143c',
      placeholder: 'Search for medical data, clinical research, or healthcare insights...',
      recentSearches: [
        'Karen clinical data management',
        'Healthcare compliance requirements',
        'Medical research methodologies'
      ]
    }
  }

  const searchModes = [
    { id: 'normal', label: 'Normal', icon: '🔍', description: 'Standard search across available data' },
    { id: 'deep', label: 'Deep', icon: '🧠', description: 'Comprehensive analysis with context' },
    { id: 'super-deep', label: 'Super Deep', icon: '⚡', description: 'Maximum depth with all sources' },
    { id: 'creative', label: 'Creative', icon: '🎨', description: 'Creative and innovative perspectives' },
    { id: 'private', label: 'Private', icon: '🔒', description: 'Personal data only, secure search' },
    { id: 'domain', label: 'Domain', icon: '📚', description: 'Domain-specific knowledge base' },
    { id: 'web', label: 'Web', icon: '🌐', description: 'External web search integration' }
  ]

  const createTools = [
    { id: 'song', label: 'Create Song', icon: '🎵', description: 'Generate music with Mureka AI' },
    { id: 'image', label: 'Generate Image', icon: '🖼️', description: 'Create images with AI' },
    { id: 'story', label: 'Write Story', icon: '✍️', description: 'AI-powered creative writing' },
    { id: 'video', label: 'Create Video', icon: '🎬', description: 'Generate video content' },
    { id: 'edit', label: 'Edit Image', icon: '🎨', description: 'Advanced image editing' }
  ]

  const currentPersona = personas[persona] || personas.cherry

  useEffect(() => {
    // Load recent searches for current persona
    const saved = localStorage.getItem(`recentSearches_${persona}`)
    if (saved) {
      setRecentSearches(JSON.parse(saved))
    } else {
      setRecentSearches(currentPersona.recentSearches)
    }
  }, [persona])

  const handleSearch = async () => {
    if (!searchQuery.trim()) return

    setIsSearching(true)
    
    // Save to recent searches
    const newRecentSearches = [
      searchQuery,
      ...recentSearches.filter(s => s !== searchQuery)
    ].slice(0, 10)
    setRecentSearches(newRecentSearches)
    localStorage.setItem(`recentSearches_${persona}`, JSON.stringify(newRecentSearches))

    // Simulate search (replace with actual API call)
    setTimeout(() => {
      setSearchResults([
        {
          id: 1,
          title: `${currentPersona.name}-specific result for: ${searchQuery}`,
          content: `This is a personalized search result for ${currentPersona.name} based on your query "${searchQuery}" using ${searchMode} mode.`,
          source: 'Knowledge Base',
          timestamp: new Date().toISOString(),
          relevance: 0.95,
          type: 'text'
        },
        {
          id: 2,
          title: `Related ${currentPersona.name} insights`,
          content: `Additional context and information related to "${searchQuery}" specifically curated for ${currentPersona.name}'s domain.`,
          source: 'Domain Knowledge',
          timestamp: new Date().toISOString(),
          relevance: 0.87,
          type: 'text'
        }
      ])
      setIsSearching(false)
    }, 1000)
  }

  const handleCreateTool = (toolId) => {
    // Handle creation tool selection
    console.log(`Opening ${toolId} creation tool for ${persona}`)
    setShowCreateTools(false)
  }

  const detectCreateIntent = (query) => {
    const createKeywords = ['create', 'generate', 'make', 'write', 'compose', 'design']
    return createKeywords.some(keyword => query.toLowerCase().includes(keyword))
  }

  useEffect(() => {
    setShowCreateTools(detectCreateIntent(searchQuery))
  }, [searchQuery])

  return (
    <div className="max-w-6xl mx-auto">
      {/* Persona Header */}
      <div className="text-center mb-8 fade-in">
        <div className="flex items-center justify-center gap-4 mb-4">
          <div 
            className="w-16 h-16 rounded-full flex items-center justify-center text-2xl"
            style={{ 
              backgroundColor: `${currentPersona.color}20`,
              border: `2px solid ${currentPersona.color}`
            }}
          >
            {currentPersona.icon}
          </div>
          <div>
            <h1 className="text-3xl font-bold" style={{ color: currentPersona.color }}>
              {currentPersona.name} Search Center
            </h1>
            <p className="text-secondary">
              Multi-modal search and creation tailored for {currentPersona.name}
            </p>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="search-bar mb-8">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder={currentPersona.placeholder}
            className="search-input"
            style={{ borderColor: searchQuery ? currentPersona.color : 'var(--border-color)' }}
          />
          <button
            onClick={handleSearch}
            disabled={!searchQuery.trim() || isSearching}
            className="absolute right-4 top-1/2 transform -translate-y-1/2 btn btn-primary px-6"
            style={{ backgroundColor: currentPersona.color }}
          >
            {isSearching ? '⏳' : '🔍'} Search
          </button>
        </div>
      </div>

      {/* Search Modes & Create Tools */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Search Modes */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Search Modes</h3>
            <p className="card-description">Choose your search depth and approach</p>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {searchModes.map((mode) => (
              <button
                key={mode.id}
                onClick={() => setSearchMode(mode.id)}
                className={`p-3 rounded-lg border transition-all text-left ${
                  searchMode === mode.id 
                    ? 'border-current bg-current bg-opacity-10' 
                    : 'border-color hover:bg-tertiary'
                }`}
                style={{ 
                  borderColor: searchMode === mode.id ? currentPersona.color : 'var(--border-color)',
                  color: searchMode === mode.id ? currentPersona.color : 'var(--text-primary)'
                }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span>{mode.icon}</span>
                  <span className="font-medium text-sm">{mode.label}</span>
                </div>
                <div className="text-xs text-secondary">{mode.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Create Tools */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Quick Create</h3>
            <p className="card-description">Generate content with AI tools</p>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {createTools.map((tool) => (
              <button
                key={tool.id}
                onClick={() => handleCreateTool(tool.id)}
                className={`p-3 rounded-lg border border-color hover:bg-tertiary transition-all text-left ${
                  showCreateTools ? 'ring-2 ring-current ring-opacity-50' : ''
                }`}
                style={{ 
                  ringColor: showCreateTools ? currentPersona.color : 'transparent'
                }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span>{tool.icon}</span>
                  <span className="font-medium text-sm">{tool.label}</span>
                </div>
                <div className="text-xs text-secondary">{tool.description}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results & Recent Searches */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Search Results */}
        <div className="lg:col-span-2">
          {searchResults.length > 0 ? (
            <div className="space-y-4">
              <h3 className="text-xl font-semibold mb-4">Search Results</h3>
              {searchResults.map((result) => (
                <div key={result.id} className="card hover:bg-tertiary transition-all">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-semibold text-primary">{result.title}</h4>
                    <div className="flex items-center gap-2">
                      <span 
                        className="text-xs px-2 py-1 rounded"
                        style={{ 
                          backgroundColor: `${currentPersona.color}20`,
                          color: currentPersona.color
                        }}
                      >
                        {Math.round(result.relevance * 100)}% match
                      </span>
                    </div>
                  </div>
                  <p className="text-secondary mb-3">{result.content}</p>
                  <div className="flex items-center justify-between text-sm text-muted">
                    <span>{result.source}</span>
                    <span>{new Date(result.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🧠</div>
              <h3 className="text-xl font-semibold mb-2">Start Your Search</h3>
              <p className="text-secondary">
                Enter a query above to search across all your {currentPersona.name} data and external sources
              </p>
            </div>
          )}
        </div>

        {/* Recent Searches */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Recent Searches</h3>
            <p className="card-description">{currentPersona.name}-specific history</p>
          </div>
          <div className="space-y-2">
            {recentSearches.map((search, index) => (
              <button
                key={index}
                onClick={() => setSearchQuery(search)}
                className="w-full text-left p-2 rounded hover:bg-tertiary transition-all"
              >
                <div className="font-medium text-sm text-primary">{search}</div>
                <div className="text-xs text-secondary">
                  {searchMode} • {recentSearches.length - index} searches ago
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default SearchInterface

