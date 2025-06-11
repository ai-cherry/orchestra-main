import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Search, 
  Music, 
  Image, 
  Video, 
  FileText, 
  Edit3,
  Sparkles,
  Brain,
  Zap,
  Download,
  Share,
  RefreshCw,
  Play,
  Pause,
  Volume2,
  Eye,
  Clock,
  DollarSign
} from 'lucide-react'
import { useSystemStore } from '@/stores/systemStore'

const CREATION_TOOLS = {
  song: {
    icon: Music,
    label: 'Create Song',
    description: 'Generate music with lyrics and vocals',
    color: 'bg-purple-500',
    provider: 'Mureka'
  },
  image: {
    icon: Image,
    label: 'Generate Image',
    description: 'Create images from text descriptions',
    color: 'bg-blue-500',
    provider: 'Stability AI / Venice AI'
  },
  video: {
    icon: Video,
    label: 'Create Video',
    description: 'Generate video content',
    color: 'bg-red-500',
    provider: 'Runway ML'
  },
  story: {
    icon: FileText,
    label: 'Write Story',
    description: 'AI-powered creative writing',
    color: 'bg-green-500',
    provider: 'Together AI'
  },
  edit: {
    icon: Edit3,
    label: 'Edit Image',
    description: 'Modify and enhance images',
    color: 'bg-orange-500',
    provider: 'Stability AI'
  }
}

const SEARCH_MODES = [
  { id: 'normal', label: 'Normal', icon: Search, description: 'Standard search' },
  { id: 'deep', label: 'Deep', icon: Brain, description: 'Comprehensive analysis' },
  { id: 'creative', label: 'Creative', icon: Sparkles, description: 'Imaginative exploration' },
  { id: 'research', label: 'Research', icon: FileText, description: 'Academic & factual' },
  { id: 'private', label: 'Private', icon: Eye, description: 'Confidential search' }
]

export default function EnhancedSearchCenter() {
  const [query, setQuery] = useState('')
  const [searchMode, setSearchMode] = useState('normal')
  const [showCreationPanel, setShowCreationPanel] = useState(false)
  const [selectedCreationTool, setSelectedCreationTool] = useState(null)
  const [results, setResults] = useState([])
  const [creations, setCreations] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [activeTab, setActiveTab] = useState('search')

  const { systemMetrics } = useSystemStore()

  // Smart query detection
  useEffect(() => {
    const lowerQuery = query.toLowerCase()
    if (lowerQuery.includes('create song') || lowerQuery.includes('generate music')) {
      setSelectedCreationTool('song')
      setShowCreationPanel(true)
    } else if (lowerQuery.includes('generate image') || lowerQuery.includes('create picture')) {
      setSelectedCreationTool('image')
      setShowCreationPanel(true)
    } else if (lowerQuery.includes('write story') || lowerQuery.includes('create story')) {
      setSelectedCreationTool('story')
      setShowCreationPanel(true)
    }
  }, [query])

  const handleSearch = async () => {
    if (!query.trim()) return
    
    setIsSearching(true)
    try {
      // Enhanced search with Together AI ranking
      const response = await fetch('/api/search/enhanced', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          mode: searchMode,
          use_ranking: true,
          persona_context: 'cherry' // Could be dynamic based on current persona
        })
      })
      
      const data = await response.json()
      setResults(data.results || [])
      setActiveTab('results')
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setIsSearching(false)
    }
  }

  const handleCreateContent = async (type, params) => {
    setIsCreating(true)
    try {
      const response = await fetch('/api/create/content', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type,
          ...params,
          persona_context: 'cherry'
        })
      })
      
      const data = await response.json()
      
      // Add to creations list
      setCreations(prev => [{
        id: data.creation_id,
        type,
        status: 'processing',
        created_at: new Date().toISOString(),
        ...params
      }, ...prev])
      
      setActiveTab('creations')
      
      // Poll for completion
      pollCreationStatus(data.creation_id)
    } catch (error) {
      console.error('Creation failed:', error)
    } finally {
      setIsCreating(false)
    }
  }

  const pollCreationStatus = async (creationId) => {
    const poll = async () => {
      try {
        const response = await fetch(`/api/create/status/${creationId}`)
        const data = await response.json()
        
        setCreations(prev => prev.map(creation => 
          creation.id === creationId 
            ? { ...creation, ...data }
            : creation
        ))
        
        if (data.status === 'processing') {
          setTimeout(poll, 2000) // Poll every 2 seconds
        }
      } catch (error) {
        console.error('Status poll failed:', error)
      }
    }
    
    poll()
  }

  const CreationPanel = ({ tool }) => {
    const [creationParams, setCreationParams] = useState({})
    
    const toolConfig = CREATION_TOOLS[tool]
    if (!toolConfig) return null

    return (
      <Card className="mt-4 border-l-4" style={{ borderLeftColor: toolConfig.color.replace('bg-', '') }}>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <toolConfig.icon className="h-5 w-5" />
            {toolConfig.label}
            <Badge variant="outline" className="ml-auto">
              {toolConfig.provider}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {tool === 'song' && (
            <SongCreationForm 
              onSubmit={(params) => handleCreateContent('song', params)}
              isLoading={isCreating}
            />
          )}
          {tool === 'image' && (
            <ImageCreationForm 
              onSubmit={(params) => handleCreateContent('image', params)}
              isLoading={isCreating}
            />
          )}
          {tool === 'story' && (
            <StoryCreationForm 
              onSubmit={(params) => handleCreateContent('story', params)}
              isLoading={isCreating}
            />
          )}
          {tool === 'video' && (
            <VideoCreationForm 
              onSubmit={(params) => handleCreateContent('video', params)}
              isLoading={isCreating}
            />
          )}
          {tool === 'edit' && (
            <ImageEditForm 
              onSubmit={(params) => handleCreateContent('edit', params)}
              isLoading={isCreating}
            />
          )}
        </CardContent>
      </Card>
    )
  }

  const ResultCard = ({ item, type = 'search' }) => {
    const isCreation = type === 'creation'
    
    return (
      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              {isCreation && (
                <div className={`p-1 rounded ${CREATION_TOOLS[item.type]?.color || 'bg-gray-500'}`}>
                  {CREATION_TOOLS[item.type]?.icon && 
                    <CREATION_TOOLS[item.type].icon className="h-4 w-4 text-white" />
                  }
                </div>
              )}
              <div>
                <h3 className="font-medium text-sm">
                  {isCreation ? item.title || `${CREATION_TOOLS[item.type]?.label}` : item.title}
                </h3>
                <p className="text-xs text-muted-foreground">
                  {isCreation ? CREATION_TOOLS[item.type]?.provider : item.source}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-1">
              {isCreation && (
                <Badge 
                  variant={item.status === 'completed' ? 'default' : 'secondary'}
                  className="text-xs"
                >
                  {item.status}
                </Badge>
              )}
              {item.cost && (
                <Badge variant="outline" className="text-xs">
                  ${item.cost}
                </Badge>
              )}
            </div>
          </div>
          
          <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
            {item.description || item.content}
          </p>
          
          {/* Media Preview */}
          {item.output_url && (
            <div className="mb-3">
              {item.type === 'song' && (
                <div className="flex items-center gap-2 p-2 bg-muted rounded">
                  <Button size="sm" variant="ghost">
                    <Play className="h-4 w-4" />
                  </Button>
                  <div className="flex-1 h-1 bg-gray-200 rounded">
                    <div className="h-1 bg-purple-500 rounded w-1/3"></div>
                  </div>
                  <Volume2 className="h-4 w-4 text-muted-foreground" />
                </div>
              )}
              {(item.type === 'image' || item.type === 'edit') && (
                <img 
                  src={item.output_url} 
                  alt="Generated content"
                  className="w-full h-32 object-cover rounded"
                />
              )}
              {item.type === 'video' && (
                <video 
                  src={item.output_url}
                  className="w-full h-32 object-cover rounded"
                  controls
                />
              )}
            </div>
          )}
          
          {/* Action Buttons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              {new Date(item.created_at || item.timestamp).toLocaleDateString()}
            </div>
            
            <div className="flex items-center gap-1">
              {item.output_url && (
                <>
                  <Button size="sm" variant="ghost">
                    <Download className="h-4 w-4" />
                  </Button>
                  <Button size="sm" variant="ghost">
                    <Share className="h-4 w-4" />
                  </Button>
                </>
              )}
              {isCreation && item.status === 'completed' && (
                <Button size="sm" variant="ghost">
                  <RefreshCw className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Search & Creation Center</h1>
          <p className="text-muted-foreground">
            Search knowledge or create content with AI
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Zap className="h-4 w-4" />
          Enhanced with Together AI ranking
        </div>
      </div>

      {/* Search Interface */}
      <Card>
        <CardContent className="p-6">
          <div className="flex gap-4 mb-4">
            <div className="flex-1">
              <Input
                placeholder="Search knowledge or describe what you want to create..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="text-base"
              />
            </div>
            <Button 
              onClick={handleSearch}
              disabled={isSearching || !query.trim()}
              className="px-6"
            >
              {isSearching ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
              Search
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowCreationPanel(!showCreationPanel)}
              className="px-6"
            >
              <Sparkles className="h-4 w-4 mr-2" />
              Create
            </Button>
          </div>

          {/* Search Modes */}
          <div className="flex gap-2 mb-4">
            {SEARCH_MODES.map((mode) => (
              <Button
                key={mode.id}
                variant={searchMode === mode.id ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSearchMode(mode.id)}
                className="flex items-center gap-1"
              >
                <mode.icon className="h-3 w-3" />
                {mode.label}
              </Button>
            ))}
          </div>

          {/* Creation Tools */}
          {showCreationPanel && (
            <div className="border-t pt-4">
              <h3 className="font-medium mb-3">Creation Tools</h3>
              <div className="grid grid-cols-5 gap-3 mb-4">
                {Object.entries(CREATION_TOOLS).map(([key, tool]) => (
                  <Button
                    key={key}
                    variant={selectedCreationTool === key ? 'default' : 'outline'}
                    onClick={() => setSelectedCreationTool(selectedCreationTool === key ? null : key)}
                    className="flex flex-col items-center gap-2 h-auto py-3"
                  >
                    <tool.icon className="h-5 w-5" />
                    <span className="text-xs">{tool.label}</span>
                  </Button>
                ))}
              </div>
              
              {selectedCreationTool && (
                <CreationPanel tool={selectedCreationTool} />
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="search" className="flex items-center gap-2">
            <Search className="h-4 w-4" />
            Search Results ({results.length})
          </TabsTrigger>
          <TabsTrigger value="creations" className="flex items-center gap-2">
            <Sparkles className="h-4 w-4" />
            My Creations ({creations.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="search" className="space-y-4">
          {results.length > 0 ? (
            <div className="grid gap-4">
              {results.map((result, index) => (
                <ResultCard key={index} item={result} type="search" />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="font-medium mb-2">No search results yet</h3>
                <p className="text-muted-foreground">
                  Enter a search query to find information across all your data sources
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="creations" className="space-y-4">
          {creations.length > 0 ? (
            <div className="grid gap-4">
              {creations.map((creation) => (
                <ResultCard key={creation.id} item={creation} type="creation" />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <Sparkles className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="font-medium mb-2">No creations yet</h3>
                <p className="text-muted-foreground">
                  Use the creation tools to generate songs, images, stories, and more
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

// Creation Form Components
const SongCreationForm = ({ onSubmit, isLoading }) => {
  const [lyrics, setLyrics] = useState('')
  const [style, setStyle] = useState('')
  const [model, setModel] = useState('auto')

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({
      lyrics,
      style,
      model,
      title: `Song: ${style || 'Custom'}`
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="text-sm font-medium">Lyrics</label>
        <textarea
          value={lyrics}
          onChange={(e) => setLyrics(e.target.value)}
          placeholder="Enter song lyrics or let AI generate them..."
          className="w-full mt-1 p-2 border rounded-md h-24 resize-none"
          required
        />
      </div>
      <div>
        <label className="text-sm font-medium">Style & Mood</label>
        <Input
          value={style}
          onChange={(e) => setStyle(e.target.value)}
          placeholder="e.g., r&b, slow, passionate, male vocal"
          className="mt-1"
          required
        />
      </div>
      <div className="flex gap-2">
        <Button type="submit" disabled={isLoading} className="flex-1">
          {isLoading ? 'Creating...' : 'Create Song'}
        </Button>
      </div>
    </form>
  )
}

const ImageCreationForm = ({ onSubmit, isLoading }) => {
  const [prompt, setPrompt] = useState('')
  const [style, setStyle] = useState('photorealistic')
  const [provider, setProvider] = useState('stability')

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({
      prompt,
      style,
      provider,
      title: `Image: ${prompt.slice(0, 30)}...`
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="text-sm font-medium">Description</label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the image you want to create..."
          className="w-full mt-1 p-2 border rounded-md h-20 resize-none"
          required
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">Style</label>
          <select
            value={style}
            onChange={(e) => setStyle(e.target.value)}
            className="w-full mt-1 p-2 border rounded-md"
          >
            <option value="photorealistic">Photorealistic</option>
            <option value="artistic">Artistic</option>
            <option value="cartoon">Cartoon</option>
            <option value="abstract">Abstract</option>
          </select>
        </div>
        <div>
          <label className="text-sm font-medium">Provider</label>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="w-full mt-1 p-2 border rounded-md"
          >
            <option value="stability">Stability AI (Professional)</option>
            <option value="venice">Venice AI (Uncensored)</option>
          </select>
        </div>
      </div>
      <Button type="submit" disabled={isLoading} className="w-full">
        {isLoading ? 'Generating...' : 'Generate Image'}
      </Button>
    </form>
  )
}

const StoryCreationForm = ({ onSubmit, isLoading }) => {
  const [theme, setTheme] = useState('')
  const [length, setLength] = useState('short')
  const [voice, setVoice] = useState('cherry')

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({
      theme,
      length,
      voice,
      title: `Story: ${theme.slice(0, 30)}...`
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="text-sm font-medium">Theme/Topic</label>
        <Input
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
          placeholder="What should the story be about?"
          className="mt-1"
          required
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium">Length</label>
          <select
            value={length}
            onChange={(e) => setLength(e.target.value)}
            className="w-full mt-1 p-2 border rounded-md"
          >
            <option value="short">Short (500 words)</option>
            <option value="medium">Medium (1500 words)</option>
            <option value="long">Long (3000+ words)</option>
          </select>
        </div>
        <div>
          <label className="text-sm font-medium">Persona Voice</label>
          <select
            value={voice}
            onChange={(e) => setVoice(e.target.value)}
            className="w-full mt-1 p-2 border rounded-md"
          >
            <option value="cherry">Cherry (Playful)</option>
            <option value="sophia">Sophia (Professional)</option>
            <option value="karen">Karen (Clinical)</option>
          </select>
        </div>
      </div>
      <Button type="submit" disabled={isLoading} className="w-full">
        {isLoading ? 'Writing...' : 'Write Story'}
      </Button>
    </form>
  )
}

const VideoCreationForm = ({ onSubmit, isLoading }) => {
  const [prompt, setPrompt] = useState('')
  const [duration, setDuration] = useState('short')

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({
      prompt,
      duration,
      title: `Video: ${prompt.slice(0, 30)}...`
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="text-sm font-medium">Video Description</label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the video you want to create..."
          className="w-full mt-1 p-2 border rounded-md h-20 resize-none"
          required
        />
      </div>
      <div>
        <label className="text-sm font-medium">Duration</label>
        <select
          value={duration}
          onChange={(e) => setDuration(e.target.value)}
          className="w-full mt-1 p-2 border rounded-md"
        >
          <option value="short">Short (3-5 seconds)</option>
          <option value="medium">Medium (10-15 seconds)</option>
        </select>
      </div>
      <Button type="submit" disabled={isLoading} className="w-full">
        {isLoading ? 'Creating...' : 'Create Video'}
      </Button>
    </form>
  )
}

const ImageEditForm = ({ onSubmit, isLoading }) => {
  const [instructions, setInstructions] = useState('')
  const [file, setFile] = useState(null)

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit({
      instructions,
      file,
      title: `Edit: ${instructions.slice(0, 30)}...`
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="text-sm font-medium">Upload Image</label>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files[0])}
          className="w-full mt-1 p-2 border rounded-md"
          required
        />
      </div>
      <div>
        <label className="text-sm font-medium">Edit Instructions</label>
        <textarea
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          placeholder="Describe how you want to edit the image..."
          className="w-full mt-1 p-2 border rounded-md h-20 resize-none"
          required
        />
      </div>
      <Button type="submit" disabled={isLoading} className="w-full">
        {isLoading ? 'Processing...' : 'Edit Image'}
      </Button>
    </form>
  )
}

