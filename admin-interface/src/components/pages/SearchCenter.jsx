import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { 
  Search, 
  Filter, 
  Globe, 
  Database, 
  Brain, 
  Sparkles, 
  Lock, 
  Zap,
  ExternalLink,
  Clock,
  Star,
  TrendingUp
} from 'lucide-react'

const searchModes = [
  {
    id: 'normal',
    name: 'Normal',
    icon: Search,
    description: 'Standard search across available data',
    color: 'text-blue-500'
  },
  {
    id: 'deep',
    name: 'Deep',
    icon: Brain,
    description: 'Comprehensive analysis with multiple sources',
    color: 'text-purple-500'
  },
  {
    id: 'super_deep',
    name: 'Super Deep',
    icon: Zap,
    description: 'Exhaustive research with advanced reasoning',
    color: 'text-orange-500'
  },
  {
    id: 'creative',
    name: 'Creative',
    icon: Sparkles,
    description: 'Innovative and imaginative search approach',
    color: 'text-pink-500'
  },
  {
    id: 'private',
    name: 'Private',
    icon: Lock,
    description: 'Secure search within private data only',
    color: 'text-red-500'
  },
  {
    id: 'domain',
    name: 'Domain',
    icon: Database,
    description: 'Search within specific persona domains',
    color: 'text-green-500'
  },
  {
    id: 'web',
    name: 'Web',
    icon: Globe,
    description: 'External web search and discovery',
    color: 'text-cyan-500'
  }
]

const domainFilters = {
  cherry: [
    'Personal Conversations',
    'Relationship Advice',
    'Life Coaching',
    'Entertainment',
    'Travel Plans',
    'Health & Wellness'
  ],
  sophia: [
    'Market Reports',
    'Client Communications',
    'Financial Statements',
    'Business Analytics',
    'Strategic Plans',
    'Competitive Intelligence'
  ],
  karen: [
    'Medical Records',
    'Clinical Research',
    'Patient Communications',
    'Treatment Protocols',
    'Drug Information',
    'Healthcare Guidelines'
  ]
}

function SearchModeSelector({ selectedMode, onModeChange }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
      {searchModes.map((mode) => {
        const Icon = mode.icon
        return (
          <Button
            key={mode.id}
            variant={selectedMode === mode.id ? 'default' : 'outline'}
            size="sm"
            onClick={() => onModeChange(mode.id)}
            className="flex flex-col h-auto p-3 gap-1"
          >
            <Icon className={`h-4 w-4 ${selectedMode === mode.id ? 'text-white' : mode.color}`} />
            <span className="text-xs">{mode.name}</span>
          </Button>
        )
      })}
    </div>
  )
}

function DomainFilterPanel({ selectedPersona, selectedFilters, onFilterChange, isVisible }) {
  if (!isVisible) return null

  const filters = domainFilters[selectedPersona] || []

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Domain Filters</CardTitle>
        <CardDescription>
          Filter search within {selectedPersona}'s domain
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2">
          {filters.map((filter) => (
            <div key={filter} className="flex items-center space-x-2">
              <Checkbox
                id={filter}
                checked={selectedFilters.includes(filter)}
                onCheckedChange={(checked) => {
                  if (checked) {
                    onFilterChange([...selectedFilters, filter])
                  } else {
                    onFilterChange(selectedFilters.filter(f => f !== filter))
                  }
                }}
              />
              <label
                htmlFor={filter}
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                {filter}
              </label>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function SearchResultCard({ result }) {
  const getSourceIcon = (sourceType) => {
    switch (sourceType) {
      case 'web': return Globe
      case 'database': return Database
      case 'document': return Database
      case 'internal_knowledge': return Brain
      default: return Database
    }
  }

  const SourceIcon = getSourceIcon(result.sourceType)

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="space-y-3">
          {/* Header */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1">
              <h3 className="font-medium text-sm leading-tight">{result.title}</h3>
              <p className="text-xs text-muted-foreground mt-1">{result.snippet}</p>
            </div>
            <div className="flex items-center gap-2">
              <SourceIcon className="h-4 w-4 text-muted-foreground" />
              {result.url && (
                <Button size="sm" variant="ghost" className="h-6 w-6 p-0">
                  <ExternalLink className="h-3 w-3" />
                </Button>
              )}
            </div>
          </div>

          {/* Metadata */}
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                {result.sourceName}
              </Badge>
              {result.relevanceScore && (
                <div className="flex items-center gap-1">
                  <Star className="h-3 w-3 text-yellow-500" />
                  <span>{(result.relevanceScore * 100).toFixed(0)}%</span>
                </div>
              )}
            </div>
            {result.timestamp && (
              <div className="flex items-center gap-1 text-muted-foreground">
                <Clock className="h-3 w-3" />
                <span>{new Date(result.timestamp).toLocaleDateString()}</span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function SearchHistory({ searches, onSearchSelect }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Recent Searches</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {searches.map((search, index) => (
            <Button
              key={index}
              variant="ghost"
              size="sm"
              onClick={() => onSearchSelect(search)}
              className="w-full justify-start text-left h-auto p-2"
            >
              <div className="flex-1">
                <p className="text-sm font-medium truncate">{search.query}</p>
                <p className="text-xs text-muted-foreground">
                  {search.mode} • {search.resultsCount} results
                </p>
              </div>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export function SearchCenter() {
  const [query, setQuery] = useState('')
  const [selectedMode, setSelectedMode] = useState('normal')
  const [selectedPersona, setSelectedPersona] = useState('cherry')
  const [selectedFilters, setSelectedFilters] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState([])
  const [searchHistory, setSearchHistory] = useState([
    {
      query: 'Cherry personality optimization strategies',
      mode: 'deep',
      resultsCount: 12,
      timestamp: new Date()
    },
    {
      query: 'Sophia business intelligence workflows',
      mode: 'domain',
      resultsCount: 8,
      timestamp: new Date()
    },
    {
      query: 'Karen medical consultation protocols',
      mode: 'private',
      resultsCount: 15,
      timestamp: new Date()
    }
  ])

  const handleSearch = async () => {
    if (!query.trim()) return

    setIsSearching(true)
    
    // Simulate search API call
    setTimeout(() => {
      const mockResults = [
        {
          id: '1',
          title: 'Advanced Personality Modeling for AI Assistants',
          snippet: 'Comprehensive guide to implementing dynamic personality traits in conversational AI systems...',
          sourceType: 'document',
          sourceName: 'AI Research Papers',
          relevanceScore: 0.95,
          timestamp: new Date().toISOString()
        },
        {
          id: '2',
          title: 'ElevenLabs Voice Optimization Best Practices',
          snippet: 'Learn how to fine-tune voice parameters for natural-sounding AI speech synthesis...',
          sourceType: 'web',
          sourceName: 'ElevenLabs Documentation',
          relevanceScore: 0.88,
          url: 'https://elevenlabs.io/docs',
          timestamp: new Date().toISOString()
        },
        {
          id: '3',
          title: 'Multi-Agent Coordination Frameworks',
          snippet: 'Exploring efficient coordination mechanisms between specialized AI agents...',
          sourceType: 'internal_knowledge',
          sourceName: 'Internal Knowledge Base',
          relevanceScore: 0.82,
          timestamp: new Date().toISOString()
        }
      ]

      setSearchResults(mockResults)
      setSearchHistory(prev => [{
        query,
        mode: selectedMode,
        resultsCount: mockResults.length,
        timestamp: new Date()
      }, ...prev.slice(0, 4)])
      setIsSearching(false)
    }, 1500)
  }

  const handleSearchSelect = (search) => {
    setQuery(search.query)
    setSelectedMode(search.mode)
  }

  const selectedModeConfig = searchModes.find(mode => mode.id === selectedMode)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Search Center</h1>
        <p className="text-muted-foreground">
          Multi-modal search across all your AI assistant data and external sources
        </p>
      </div>

      {/* Search Interface */}
      <Card>
        <CardHeader>
          <CardTitle>Unified Search</CardTitle>
          <CardDescription>
            Search across internal knowledge, persona data, and external sources
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Search Input */}
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Enter your search query..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="pl-10"
              />
            </div>
            <Select value={selectedPersona} onValueChange={setSelectedPersona}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="cherry">Cherry</SelectItem>
                <SelectItem value="sophia">Sophia</SelectItem>
                <SelectItem value="karen">Karen</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={handleSearch} disabled={isSearching || !query.trim()}>
              {isSearching ? 'Searching...' : 'Search'}
            </Button>
          </div>

          {/* Search Mode Selector */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Search Mode</span>
              {selectedModeConfig && (
                <Badge variant="outline" className="text-xs">
                  {selectedModeConfig.description}
                </Badge>
              )}
            </div>
            <SearchModeSelector
              selectedMode={selectedMode}
              onModeChange={setSelectedMode}
            />
          </div>

          {/* Domain Filters */}
          <DomainFilterPanel
            selectedPersona={selectedPersona}
            selectedFilters={selectedFilters}
            onFilterChange={setSelectedFilters}
            isVisible={selectedMode === 'domain'}
          />
        </CardContent>
      </Card>

      {/* Search Results and History */}
      <div className="grid gap-6 lg:grid-cols-4">
        {/* Search Results */}
        <div className="lg:col-span-3 space-y-4">
          {searchResults.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">
                  Search Results ({searchResults.length})
                </h2>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <TrendingUp className="h-4 w-4" />
                  <span>Sorted by relevance</span>
                </div>
              </div>
              <div className="space-y-3">
                {searchResults.map((result) => (
                  <SearchResultCard key={result.id} result={result} />
                ))}
              </div>
            </div>
          )}

          {isSearching && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">
                Searching across {selectedMode} mode...
              </p>
            </div>
          )}

          {!isSearching && searchResults.length === 0 && query && (
            <div className="text-center py-12">
              <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No results found</h3>
              <p className="text-muted-foreground">
                Try adjusting your search query or changing the search mode
              </p>
            </div>
          )}

          {!query && (
            <div className="text-center py-12">
              <Brain className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">Start your search</h3>
              <p className="text-muted-foreground">
                Enter a query above to search across all your AI assistant data
              </p>
            </div>
          )}
        </div>

        {/* Search History */}
        <div className="space-y-4">
          <SearchHistory
            searches={searchHistory}
            onSearchSelect={handleSearchSelect}
          />

          {/* Search Tips */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Search Tips</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              <div className="flex items-start gap-2">
                <Brain className="h-3 w-3 mt-0.5 text-purple-500" />
                <span><strong>Deep mode:</strong> Combines multiple sources for comprehensive results</span>
              </div>
              <div className="flex items-start gap-2">
                <Database className="h-3 w-3 mt-0.5 text-green-500" />
                <span><strong>Domain mode:</strong> Search within specific persona knowledge</span>
              </div>
              <div className="flex items-start gap-2">
                <Globe className="h-3 w-3 mt-0.5 text-cyan-500" />
                <span><strong>Web mode:</strong> External search with smart result blending</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

