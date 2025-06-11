import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { usePersonaStore } from '../../stores/personaStore'
import { 
  Heart, 
  Briefcase, 
  Stethoscope, 
  Settings, 
  Mic, 
  Brain, 
  TrendingUp,
  Play,
  Pause,
  Volume2,
  ArrowLeft
} from 'lucide-react'

function PersonalitySlider({ trait, onValueChange, accentColor }) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <label className="text-sm font-medium">{trait.label}</label>
        <span className="text-sm text-muted-foreground">{trait.value}%</span>
      </div>
      <Slider
        value={[trait.value]}
        onValueChange={(value) => onValueChange(trait.id, value[0])}
        max={100}
        step={1}
        className="w-full"
      />
      {trait.description && (
        <p className="text-xs text-muted-foreground">{trait.description}</p>
      )}
    </div>
  )
}

function VoiceSettingsPanel({ persona, onVoiceSettingsChange }) {
  const [isPlaying, setIsPlaying] = useState(false)

  const handleTestVoice = () => {
    setIsPlaying(!isPlaying)
    // Simulate voice testing
    setTimeout(() => setIsPlaying(false), 3000)
  }

  return (
    <div className="space-y-6">
      {/* Voice Profile */}
      <div>
        <h3 className="text-lg font-medium mb-4">Voice Profile</h3>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Provider</label>
            <p className="text-sm text-muted-foreground capitalize">
              {persona.voiceSettings.provider}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium">Profile ID</label>
            <p className="text-sm text-muted-foreground">
              {persona.voiceSettings.profileId}
            </p>
          </div>
        </div>
      </div>

      {/* Voice Parameters */}
      <div className="space-y-4">
        <h4 className="font-medium">Voice Parameters</h4>
        
        <div className="space-y-2">
          <div className="flex justify-between">
            <label className="text-sm">Stability</label>
            <span className="text-sm text-muted-foreground">
              {persona.voiceSettings.stability}%
            </span>
          </div>
          <Slider
            value={[persona.voiceSettings.stability]}
            onValueChange={(value) => 
              onVoiceSettingsChange({ stability: value[0] })
            }
            max={100}
            step={1}
          />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between">
            <label className="text-sm">Similarity Boost</label>
            <span className="text-sm text-muted-foreground">
              {persona.voiceSettings.similarityBoost}%
            </span>
          </div>
          <Slider
            value={[persona.voiceSettings.similarityBoost]}
            onValueChange={(value) => 
              onVoiceSettingsChange({ similarityBoost: value[0] })
            }
            max={100}
            step={1}
          />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between">
            <label className="text-sm">Style Exaggeration</label>
            <span className="text-sm text-muted-foreground">
              {persona.voiceSettings.styleExaggeration}%
            </span>
          </div>
          <Slider
            value={[persona.voiceSettings.styleExaggeration]}
            onValueChange={(value) => 
              onVoiceSettingsChange({ styleExaggeration: value[0] })
            }
            max={100}
            step={1}
          />
        </div>

        <div className="flex items-center justify-between">
          <label className="text-sm">Speaker Boost</label>
          <Switch
            checked={persona.voiceSettings.speakerBoost}
            onCheckedChange={(checked) => 
              onVoiceSettingsChange({ speakerBoost: checked })
            }
          />
        </div>
      </div>

      {/* Voice Testing */}
      <div className="space-y-4">
        <h4 className="font-medium">Voice Testing</h4>
        <div className="flex gap-2">
          <Button 
            onClick={handleTestVoice}
            disabled={isPlaying}
            className="flex-1"
          >
            {isPlaying ? (
              <>
                <Pause className="h-4 w-4 mr-2" />
                Playing...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Test Voice
              </>
            )}
          </Button>
          <Button variant="outline" size="icon">
            <Volume2 className="h-4 w-4" />
          </Button>
        </div>
        {isPlaying && (
          <div className="space-y-2">
            <Progress value={60} className="h-2" />
            <p className="text-xs text-muted-foreground">
              "Hello! This is {persona.name} speaking with the current voice settings."
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

function AdaptiveAgentPanel({ persona, onAdaptiveSettingsChange }) {
  return (
    <div className="space-y-6">
      {/* Learning Configuration */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Learning Configuration</h3>
        
        <div className="space-y-2">
          <div className="flex justify-between">
            <label className="text-sm">Learning Rate</label>
            <span className="text-sm text-muted-foreground">
              {persona.adaptiveSettings.learningRate}
            </span>
          </div>
          <Slider
            value={[persona.adaptiveSettings.learningRate]}
            onValueChange={(value) => 
              onAdaptiveSettingsChange({ learningRate: value[0] })
            }
            max={1}
            step={0.1}
            min={0.1}
          />
          <p className="text-xs text-muted-foreground">
            How quickly the AI adapts to new patterns and feedback
          </p>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Optimization Strategy</label>
          <div className="grid grid-cols-1 gap-2">
            {['quality_maximization', 'cost_minimization', 'pareto_frontier'].map((strategy) => (
              <Button
                key={strategy}
                variant={persona.adaptiveSettings.optimizationStrategy === strategy ? 'default' : 'outline'}
                size="sm"
                onClick={() => onAdaptiveSettingsChange({ optimizationStrategy: strategy })}
                className="justify-start"
              >
                {strategy.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </Button>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <label className="text-sm font-medium">Adaptive Learning</label>
            <p className="text-xs text-muted-foreground">
              Enable continuous learning and optimization
            </p>
          </div>
          <Switch
            checked={persona.adaptiveSettings.isEnabled}
            onCheckedChange={(checked) => 
              onAdaptiveSettingsChange({ isEnabled: checked })
            }
          />
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="space-y-4">
        <h4 className="font-medium">Performance Metrics</h4>
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">94.2%</div>
              <p className="text-xs text-muted-foreground">Satisfaction Score</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">1.2s</div>
              <p className="text-xs text-muted-foreground">Avg Response Time</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">2.1%</div>
              <p className="text-xs text-muted-foreground">Error Rate</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">847</div>
              <p className="text-xs text-muted-foreground">Total Interactions</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

function PersonaOverview() {
  const { personas } = usePersonaStore()

  const getPersonaIcon = (id) => {
    switch (id) {
      case 'cherry': return Heart
      case 'sophia': return Briefcase
      case 'karen': return Stethoscope
      default: return Brain
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AI Personas</h1>
        <p className="text-muted-foreground">
          Manage and configure Cherry, Sophia, and Karen
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {personas.map((persona) => {
          const PersonaIcon = getPersonaIcon(persona.id)
          
          return (
            <Card key={persona.id} className={`border-l-4 ${persona.borderColor}`}>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-lg ${persona.accentColor}/10`}>
                    <PersonaIcon className={`h-6 w-6 ${persona.accentColor.replace('bg-', 'text-')}`} />
                  </div>
                  <div>
                    <CardTitle className="text-xl">{persona.name}</CardTitle>
                    <CardDescription>{persona.title}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Status */}
                <div className="flex items-center justify-between">
                  <span className="text-sm">Status</span>
                  <Badge variant="outline" className="capitalize">
                    {persona.status}
                  </Badge>
                </div>

                {/* Personality Health */}
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>Personality Health</span>
                    <span>{persona.personalityHealth.toFixed(1)}%</span>
                  </div>
                  <Progress value={persona.personalityHealth} className="h-2" />
                </div>

                {/* Key Stats */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Interactions</p>
                    <p className="font-medium">{persona.interactionCount}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Memory</p>
                    <p className="font-medium">{persona.memoryUsage.toFixed(1)} MB</p>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <Button asChild size="sm" className="flex-1">
                    <Link to={`/personas/${persona.id}`}>
                      <Settings className="h-4 w-4 mr-2" />
                      Configure
                    </Link>
                  </Button>
                  <Button size="sm" variant="outline" className="flex-1">
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Analytics
                  </Button>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}

function PersonaDetail() {
  const { personaId } = useParams()
  const { 
    getPersonaById, 
    updatePersonalityTrait, 
    updateVoiceSettings, 
    updateAdaptiveSettings 
  } = usePersonaStore()
  
  const persona = getPersonaById(personaId)

  if (!persona) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-semibold">Persona not found</h2>
        <p className="text-muted-foreground mt-2">
          The requested persona could not be found.
        </p>
        <Button asChild className="mt-4">
          <Link to="/personas">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Personas
          </Link>
        </Button>
      </div>
    )
  }

  const getPersonaIcon = (id) => {
    switch (id) {
      case 'cherry': return Heart
      case 'sophia': return Briefcase
      case 'karen': return Stethoscope
      default: return Brain
    }
  }

  const PersonaIcon = getPersonaIcon(persona.id)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/personas">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Link>
        </Button>
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-lg ${persona.accentColor}/10`}>
            <PersonaIcon className={`h-6 w-6 ${persona.accentColor.replace('bg-', 'text-')}`} />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{persona.name}</h1>
            <p className="text-muted-foreground">{persona.title}</p>
          </div>
        </div>
      </div>

      {/* Configuration Tabs */}
      <Tabs defaultValue="personality" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="personality">
            <Brain className="h-4 w-4 mr-2" />
            Personality
          </TabsTrigger>
          <TabsTrigger value="voice">
            <Mic className="h-4 w-4 mr-2" />
            Voice
          </TabsTrigger>
          <TabsTrigger value="adaptive">
            <TrendingUp className="h-4 w-4 mr-2" />
            Adaptive AI
          </TabsTrigger>
        </TabsList>

        <TabsContent value="personality" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Personality Configuration</CardTitle>
              <CardDescription>
                Adjust {persona.name}'s personality traits and characteristics
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {persona.personalityTraits.map((trait) => (
                <PersonalitySlider
                  key={trait.id}
                  trait={trait}
                  onValueChange={(traitId, value) => 
                    updatePersonalityTrait(persona.id, traitId, value)
                  }
                  accentColor={persona.accentColor}
                />
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="voice" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Voice Configuration</CardTitle>
              <CardDescription>
                Configure {persona.name}'s voice settings and parameters
              </CardDescription>
            </CardHeader>
            <CardContent>
              <VoiceSettingsPanel
                persona={persona}
                onVoiceSettingsChange={(settings) => 
                  updateVoiceSettings(persona.id, settings)
                }
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="adaptive" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Adaptive AI Configuration</CardTitle>
              <CardDescription>
                Configure {persona.name}'s learning and optimization settings
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AdaptiveAgentPanel
                persona={persona}
                onAdaptiveSettingsChange={(settings) => 
                  updateAdaptiveSettings(persona.id, settings)
                }
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export function PersonaHub() {
  const { personaId } = useParams()
  
  return personaId ? <PersonaDetail /> : <PersonaOverview />
}

