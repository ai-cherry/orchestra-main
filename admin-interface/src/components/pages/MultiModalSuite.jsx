import { useState } from 'react'
import React from 'react'
import { useParams } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { Progress } from '@/components/ui/progress'
import { 
  Image, 
  Video, 
  Music, 
  FileText, 
  Palette, 
  Wand2, 
  Download, 
  Share, 
  Settings,
  Play,
  Pause,
  Volume2,
  Eye,
  Sparkles,
  Zap,
  Clock,
  DollarSign
} from 'lucide-react'

const generationTypes = {
  image: {
    label: 'Image Generation',
    icon: Image,
    color: 'text-blue-500',
    description: 'Create images from text descriptions',
    models: ['DALL-E 3', 'Midjourney', 'Stable Diffusion XL'],
    aspectRatios: ['1:1', '16:9', '9:16', '4:3', '3:4'],
    styles: ['Photorealistic', 'Artistic', 'Cartoon', 'Abstract', 'Minimalist']
  },
  video: {
    label: 'Video Generation',
    icon: Video,
    color: 'text-purple-500',
    description: 'Generate videos from prompts and images',
    models: ['Runway Gen-2', 'Pika Labs', 'Stable Video'],
    durations: ['2s', '4s', '8s', '16s'],
    styles: ['Cinematic', 'Documentary', 'Animation', 'Time-lapse']
  },
  audio: {
    label: 'Audio Generation',
    icon: Music,
    color: 'text-green-500',
    description: 'Create music and sound effects',
    models: ['MusicGen', 'AudioCraft', 'Jukebox'],
    durations: ['10s', '30s', '60s', '120s'],
    styles: ['Classical', 'Electronic', 'Ambient', 'Rock', 'Jazz']
  },
  text: {
    label: 'Text Generation',
    icon: FileText,
    color: 'text-orange-500',
    description: 'Generate articles, stories, and content',
    models: ['GPT-4', 'Claude-3', 'Gemini Pro'],
    lengths: ['Short (100-300 words)', 'Medium (500-1000 words)', 'Long (1500+ words)'],
    styles: ['Professional', 'Creative', 'Technical', 'Casual', 'Academic']
  }
}

function GenerationTypeSelector({ selectedType, onTypeChange }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {Object.entries(generationTypes).map(([type, config]) => {
        const Icon = config.icon
        return (
          <Button
            key={type}
            variant={selectedType === type ? 'default' : 'outline'}
            onClick={() => onTypeChange(type)}
            className="h-auto p-4 flex flex-col gap-2"
          >
            <Icon className={`h-6 w-6 ${selectedType === type ? 'text-white' : config.color}`} />
            <span className="text-sm font-medium">{config.label}</span>
          </Button>
        )
      })}
    </div>
  )
}

function GenerationForm({ type, onGenerate, isGenerating }) {
  const [prompt, setPrompt] = useState('')
  const [selectedModel, setSelectedModel] = useState('')
  const [selectedStyle, setSelectedStyle] = useState('')
  const [selectedAspectRatio, setSelectedAspectRatio] = useState('')
  const [selectedDuration, setSelectedDuration] = useState('')
  const [selectedLength, setSelectedLength] = useState('')
  const [quality, setQuality] = useState([80])
  const [creativity, setCreativity] = useState([70])

  const config = generationTypes[type]

  const handleGenerate = () => {
    const params = {
      prompt,
      model: selectedModel,
      style: selectedStyle,
      aspectRatio: selectedAspectRatio,
      duration: selectedDuration,
      length: selectedLength,
      quality: quality[0],
      creativity: creativity[0]
    }
    onGenerate(type, params)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <config.icon className={`h-5 w-5 ${config.color}`} />
          {config.label}
        </CardTitle>
        <CardDescription>{config.description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Prompt Input */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Prompt</label>
          <Textarea
            placeholder={`Describe what you want to generate...`}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={3}
          />
        </div>

        {/* Model Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Model</label>
          <Select value={selectedModel} onValueChange={setSelectedModel}>
            <SelectTrigger>
              <SelectValue placeholder="Select a model" />
            </SelectTrigger>
            <SelectContent>
              {config.models.map((model) => (
                <SelectItem key={model} value={model}>
                  {model}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Style Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Style</label>
          <Select value={selectedStyle} onValueChange={setSelectedStyle}>
            <SelectTrigger>
              <SelectValue placeholder="Select a style" />
            </SelectTrigger>
            <SelectContent>
              {config.styles.map((style) => (
                <SelectItem key={style} value={style}>
                  {style}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Type-specific options */}
        {type === 'image' && config.aspectRatios && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Aspect Ratio</label>
            <Select value={selectedAspectRatio} onValueChange={setSelectedAspectRatio}>
              <SelectTrigger>
                <SelectValue placeholder="Select aspect ratio" />
              </SelectTrigger>
              <SelectContent>
                {config.aspectRatios.map((ratio) => (
                  <SelectItem key={ratio} value={ratio}>
                    {ratio}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {(type === 'video' || type === 'audio') && config.durations && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Duration</label>
            <Select value={selectedDuration} onValueChange={setSelectedDuration}>
              <SelectTrigger>
                <SelectValue placeholder="Select duration" />
              </SelectTrigger>
              <SelectContent>
                {config.durations.map((duration) => (
                  <SelectItem key={duration} value={duration}>
                    {duration}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {type === 'text' && config.lengths && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Length</label>
            <Select value={selectedLength} onValueChange={setSelectedLength}>
              <SelectTrigger>
                <SelectValue placeholder="Select length" />
              </SelectTrigger>
              <SelectContent>
                {config.lengths.map((length) => (
                  <SelectItem key={length} value={length}>
                    {length}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* Quality and Creativity Sliders */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex justify-between">
              <label className="text-sm font-medium">Quality</label>
              <span className="text-sm text-muted-foreground">{quality[0]}%</span>
            </div>
            <Slider
              value={quality}
              onValueChange={setQuality}
              max={100}
              step={5}
            />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <label className="text-sm font-medium">Creativity</label>
              <span className="text-sm text-muted-foreground">{creativity[0]}%</span>
            </div>
            <Slider
              value={creativity}
              onValueChange={setCreativity}
              max={100}
              step={5}
            />
          </div>
        </div>

        {/* Generate Button */}
        <Button 
          onClick={handleGenerate}
          disabled={!prompt.trim() || isGenerating}
          className="w-full"
          size="lg"
        >
          {isGenerating ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
              Generating...
            </>
          ) : (
            <>
              <Wand2 className="h-4 w-4 mr-2" />
              Generate {config.label.split(' ')[0]}
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  )
}

function GenerationResult({ result, type }) {
  const [isPlaying, setIsPlaying] = useState(false)

  const renderPreview = () => {
    switch (type) {
      case 'image':
        return (
          <div className="aspect-square bg-gray-100 rounded-lg flex items-center justify-center">
            {result.url ? (
              <img 
                src={result.url} 
                alt={result.prompt} 
                className="w-full h-full object-cover rounded-lg"
              />
            ) : (
              <Image className="h-12 w-12 text-gray-400" />
            )}
          </div>
        )
      case 'video':
        return (
          <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center relative">
            {result.url ? (
              <>
                <video 
                  src={result.url} 
                  className="w-full h-full object-cover rounded-lg"
                  controls={false}
                />
                <Button
                  size="sm"
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="absolute inset-0 m-auto w-12 h-12 rounded-full"
                >
                  {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                </Button>
              </>
            ) : (
              <Video className="h-12 w-12 text-gray-400" />
            )}
          </div>
        )
      case 'audio':
        return (
          <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center">
            <div className="text-center space-y-4">
              <Music className="h-12 w-12 text-gray-400 mx-auto" />
              {result.url && (
                <div className="flex items-center gap-2">
                  <Button size="sm" onClick={() => setIsPlaying(!isPlaying)}>
                    {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  </Button>
                  <Volume2 className="h-4 w-4" />
                  <Progress value={isPlaying ? 45 : 0} className="w-24" />
                </div>
              )}
            </div>
          </div>
        )
      case 'text':
        return (
          <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
            {result.content ? (
              <p className="text-sm leading-relaxed">{result.content}</p>
            ) : (
              <div className="flex items-center justify-center h-32">
                <FileText className="h-12 w-12 text-gray-400" />
              </div>
            )}
          </div>
        )
      default:
        return null
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">Generated {generationTypes[type].label.split(' ')[0]}</CardTitle>
          <div className="flex gap-2">
            <Button size="sm" variant="outline">
              <Eye className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="outline">
              <Download className="h-4 w-4" />
            </Button>
            <Button size="sm" variant="outline">
              <Share className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Preview */}
        {renderPreview()}

        {/* Metadata */}
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground">
            <strong>Prompt:</strong> {result.prompt}
          </div>
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Model: {result.model}</span>
            <span>Style: {result.style}</span>
          </div>
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>{result.generationTime}s</span>
            </div>
            <div className="flex items-center gap-1">
              <DollarSign className="h-3 w-3" />
              <span>${result.cost}</span>
            </div>
          </div>
        </div>

        {/* Status */}
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-green-600">
            {result.status}
          </Badge>
          {result.quality && (
            <Badge variant="outline">
              Quality: {result.quality}%
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function GenerationHistory({ history, onResultSelect }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Recent Generations</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {history.map((item, index) => (
            <Button
              key={index}
              variant="ghost"
              size="sm"
              onClick={() => onResultSelect(item)}
              className="w-full justify-start text-left h-auto p-2"
            >
              <div className="flex items-center gap-3">
                {React.createElement(generationTypes[item.type].icon, { 
                  className: `h-4 w-4 ${generationTypes[item.type].color}` 
                })}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{item.prompt}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.type} • {new Date(item.timestamp).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export function MultiModalSuite() {
  const { type: urlType } = useParams()
  const [selectedType, setSelectedType] = useState(urlType || 'image')
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentResult, setCurrentResult] = useState(null)
  const [generationHistory, setGenerationHistory] = useState([
    {
      type: 'image',
      prompt: 'A futuristic AI assistant interface with holographic displays',
      model: 'DALL-E 3',
      style: 'Photorealistic',
      status: 'completed',
      generationTime: 8.5,
      cost: 0.04,
      quality: 95,
      timestamp: new Date().toISOString()
    },
    {
      type: 'text',
      prompt: 'Write a technical blog post about AI assistant architectures',
      model: 'GPT-4',
      style: 'Technical',
      status: 'completed',
      generationTime: 12.3,
      cost: 0.08,
      quality: 92,
      timestamp: new Date().toISOString()
    }
  ])

  const handleGenerate = async (type, params) => {
    setIsGenerating(true)
    
    // Simulate generation process
    setTimeout(() => {
      const result = {
        type,
        prompt: params.prompt,
        model: params.model,
        style: params.style,
        status: 'completed',
        generationTime: Math.random() * 15 + 5,
        cost: Math.random() * 0.1 + 0.02,
        quality: params.quality,
        timestamp: new Date().toISOString(),
        url: type === 'image' ? '/api/placeholder/400/400' : null,
        content: type === 'text' ? 'This is a sample generated text content that would be much longer in a real scenario...' : null
      }
      
      setCurrentResult(result)
      setGenerationHistory(prev => [result, ...prev.slice(0, 9)])
      setIsGenerating(false)
    }, 3000)
  }

  const handleResultSelect = (result) => {
    setCurrentResult(result)
    setSelectedType(result.type)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Multi-Modal Generation Suite</h1>
        <p className="text-muted-foreground">
          Create images, videos, audio, and text content with AI
        </p>
      </div>

      {/* Generation Type Selector */}
      <GenerationTypeSelector
        selectedType={selectedType}
        onTypeChange={setSelectedType}
      />

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Generation Form */}
        <div className="lg:col-span-2">
          <GenerationForm
            type={selectedType}
            onGenerate={handleGenerate}
            isGenerating={isGenerating}
          />

          {/* Current Result */}
          {currentResult && (
            <div className="mt-6">
              <GenerationResult
                result={currentResult}
                type={currentResult.type}
              />
            </div>
          )}

          {/* Generation Progress */}
          {isGenerating && (
            <Card className="mt-6">
              <CardContent className="p-6">
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary" />
                    <span className="text-sm font-medium">Generating {generationTypes[selectedType].label.split(' ')[0]}...</span>
                  </div>
                  <Progress value={65} className="w-full" />
                  <div className="text-xs text-muted-foreground">
                    Processing with {generationTypes[selectedType].models[0]} • Estimated time: 15-30 seconds
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <GenerationHistory
            history={generationHistory}
            onResultSelect={handleResultSelect}
          />

          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Usage Statistics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span>Generations Today</span>
                <span className="font-medium">12</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Total Cost</span>
                <span className="font-medium">$2.34</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Success Rate</span>
                <span className="font-medium">98.5%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Avg Quality</span>
                <span className="font-medium">94.2%</span>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button size="sm" variant="outline" className="w-full justify-start">
                <Sparkles className="h-4 w-4 mr-2" />
                Enhance Last Result
              </Button>
              <Button size="sm" variant="outline" className="w-full justify-start">
                <Zap className="h-4 w-4 mr-2" />
                Batch Generate
              </Button>
              <Button size="sm" variant="outline" className="w-full justify-start">
                <Settings className="h-4 w-4 mr-2" />
                Model Settings
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

