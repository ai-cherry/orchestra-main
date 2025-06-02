import React, { useState } from 'react';
import { useParams } from '@tanstack/react-router';
import { useNavigate } from '@tanstack/react-router';
import PageWrapper from '@/components/layout/PageWrapper';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { PersonaTraitSliders, defaultPersonaTraits, PersonaTrait } from '@/components/personas/PersonaTraitSliders';
import { usePersonaById, usePersonaActions } from '@/store/personaStore';
import { useUpdatePersona } from '@/hooks/usePersonaApi';
import { 
  ArrowLeft, 
  Save, 
  Settings, 
  Brain, 
  Zap, 
  Thermometer, 
  Users,
  Code,
  FileText,
  Shield,
  Activity
} from 'lucide-react';

export function PersonaCustomizationPage() {
  const params = useParams({ from: '/personas/$personaId' });
  const personaId = params.personaId;
  const navigate = useNavigate();
  const persona = usePersonaById(personaId);
  const { updatePersona: updateLocalPersona } = usePersonaActions();
  const { mutate: updateRemotePersona, isPending } = useUpdatePersona(personaId);
  
  const [traits, setTraits] = useState<PersonaTrait[]>(
    defaultPersonaTraits[personaId] || defaultPersonaTraits.cherry
  );
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2048);
  const [topP, setTopP] = useState(0.9);
  const [frequencyPenalty, setFrequencyPenalty] = useState(0.0);
  const [presencePenalty, setPresencePenalty] = useState(0.0);

  if (!persona) {
    return (
      <PageWrapper title="Persona Not Found">
        <div className="text-center py-12">
          <p className="text-muted-foreground">The requested persona could not be found.</p>
          <Button onClick={() => navigate({ to: '/personas' })} className="mt-4">
            Back to Personas
          </Button>
        </div>
      </PageWrapper>
    );
  }

  const handleTraitChange = (traitId: string, value: number) => {
    setTraits(prev => prev.map(trait => 
      trait.id === traitId ? { ...trait, value } : trait
    ));
  };

  const handleSave = () => {
    const updates = {
      settings: {
        ...persona.settings,
        traits: traits.reduce((acc, trait) => {
          acc[trait.id] = trait.value;
          return acc;
        }, {} as Record<string, number>),
        llm: {
          temperature,
          maxTokens,
          topP,
          frequencyPenalty,
          presencePenalty,
        },
      },
    };

    // Update local state
    updateLocalPersona(personaId, updates);
    
    // Update remote
    updateRemotePersona(updates);
  };

  return (
    <PageWrapper title={`Customize ${persona.name}`}>
      <div className="flex flex-col space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate({ to: '/personas' })}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <div className="flex items-center gap-2">
              <span className="text-2xl">{persona.icon}</span>
              <div>
                <h1 className="text-2xl font-bold">{persona.name}</h1>
                <p className="text-sm text-muted-foreground">{persona.role}</p>
              </div>
            </div>
          </div>
          <Button onClick={handleSave} disabled={isPending}>
            <Save className="mr-2 h-4 w-4" />
            {isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="rules" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="rules">
              <Code className="mr-2 h-4 w-4" />
              Rules Engine
            </TabsTrigger>
            <TabsTrigger value="matrix">
              <Brain className="mr-2 h-4 w-4" />
              Persona Matrix
            </TabsTrigger>
            <TabsTrigger value="llm">
              <Zap className="mr-2 h-4 w-4" />
              LLM Hub
            </TabsTrigger>
            <TabsTrigger value="temperature">
              <Thermometer className="mr-2 h-4 w-4" />
              Temperature
            </TabsTrigger>
            <TabsTrigger value="team">
              <Users className="mr-2 h-4 w-4" />
              Team Settings
            </TabsTrigger>
          </TabsList>

          {/* Rules Engine Tab */}
          <TabsContent value="rules" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Behavioral Rules</CardTitle>
                <CardDescription>
                  Define rules and constraints for {persona.name}'s behavior
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Response Guidelines</Label>
                  <textarea
                    className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm"
                    placeholder="Enter behavioral guidelines..."
                    defaultValue={`Always maintain a ${persona.role.toLowerCase()} perspective. Be helpful and ${persona.domain.toLowerCase()}-focused.`}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label>Forbidden Topics</Label>
                  <Input placeholder="Enter comma-separated topics to avoid..." />
                </div>

                <div className="space-y-2">
                  <Label>Required Disclaimers</Label>
                  <Input placeholder="Enter required disclaimers..." />
                </div>

                <div className="flex items-center space-x-2">
                  <Switch id="safety-mode" />
                  <Label htmlFor="safety-mode">Enable enhanced safety mode</Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Switch id="fact-checking" defaultChecked />
                  <Label htmlFor="fact-checking">Enable fact-checking</Label>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Context Rules</CardTitle>
                <CardDescription>
                  Configure how {persona.name} handles context and memory
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Context Window</Label>
                  <Select defaultValue="4096">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="2048">2,048 tokens</SelectItem>
                      <SelectItem value="4096">4,096 tokens</SelectItem>
                      <SelectItem value="8192">8,192 tokens</SelectItem>
                      <SelectItem value="16384">16,384 tokens</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Memory Retention</Label>
                  <Select defaultValue="session">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">No memory</SelectItem>
                      <SelectItem value="session">Session-based</SelectItem>
                      <SelectItem value="persistent">Persistent</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Persona Matrix Tab */}
          <TabsContent value="matrix" className="space-y-4">
            <PersonaTraitSliders
              traits={traits}
              onChange={handleTraitChange}
            />
          </TabsContent>

          {/* LLM Hub Tab */}
          <TabsContent value="llm" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Model Selection</CardTitle>
                <CardDescription>
                  Choose and configure the language model for {persona.name}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Primary Model</Label>
                  <Select defaultValue="gpt-4">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gpt-4">GPT-4</SelectItem>
                      <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                      <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                      <SelectItem value="claude-3">Claude 3</SelectItem>
                      <SelectItem value="claude-2">Claude 2</SelectItem>
                      <SelectItem value="llama-2">Llama 2</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Fallback Model</Label>
                  <Select defaultValue="gpt-3.5-turbo">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                      <SelectItem value="claude-instant">Claude Instant</SelectItem>
                      <SelectItem value="llama-2-7b">Llama 2 7B</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Response Format</Label>
                  <Select defaultValue="text">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="text">Plain Text</SelectItem>
                      <SelectItem value="markdown">Markdown</SelectItem>
                      <SelectItem value="json">JSON</SelectItem>
                      <SelectItem value="structured">Structured Output</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Model Parameters</CardTitle>
                <CardDescription>
                  Fine-tune model behavior
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Max Tokens</Label>
                    <span className="text-sm text-muted-foreground">{maxTokens}</span>
                  </div>
                  <Slider
                    value={[maxTokens]}
                    onValueChange={(v) => setMaxTokens(v[0])}
                    min={256}
                    max={4096}
                    step={256}
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Top P</Label>
                    <span className="text-sm text-muted-foreground">{topP}</span>
                  </div>
                  <Slider
                    value={[topP]}
                    onValueChange={(v) => setTopP(v[0])}
                    min={0}
                    max={1}
                    step={0.1}
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Frequency Penalty</Label>
                    <span className="text-sm text-muted-foreground">{frequencyPenalty}</span>
                  </div>
                  <Slider
                    value={[frequencyPenalty]}
                    onValueChange={(v) => setFrequencyPenalty(v[0])}
                    min={-2}
                    max={2}
                    step={0.1}
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Presence Penalty</Label>
                    <span className="text-sm text-muted-foreground">{presencePenalty}</span>
                  </div>
                  <Slider
                    value={[presencePenalty]}
                    onValueChange={(v) => setPresencePenalty(v[0])}
                    min={-2}
                    max={2}
                    step={0.1}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Temperature Control Tab */}
          <TabsContent value="temperature" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Temperature Settings</CardTitle>
                <CardDescription>
                  Control the creativity and randomness of {persona.name}'s responses
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Temperature</Label>
                      <p className="text-sm text-muted-foreground">
                        Higher values make output more random, lower values more deterministic
                      </p>
                    </div>
                    <span className="text-2xl font-mono">{temperature.toFixed(1)}</span>
                  </div>
                  <Slider
                    value={[temperature]}
                    onValueChange={(v) => setTemperature(v[0])}
                    min={0}
                    max={2}
                    step={0.1}
                    className="w-full"
                  />
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div 
                      className="p-4 rounded-lg border cursor-pointer hover:bg-accent"
                      onClick={() => setTemperature(0.3)}
                    >
                      <Shield className="h-8 w-8 mx-auto mb-2 text-blue-500" />
                      <h4 className="font-semibold">Conservative</h4>
                      <p className="text-xs text-muted-foreground">0.3 - Focused & Consistent</p>
                    </div>
                    <div 
                      className="p-4 rounded-lg border cursor-pointer hover:bg-accent"
                      onClick={() => setTemperature(0.7)}
                    >
                      <Activity className="h-8 w-8 mx-auto mb-2 text-green-500" />
                      <h4 className="font-semibold">Balanced</h4>
                      <p className="text-xs text-muted-foreground">0.7 - Natural & Versatile</p>
                    </div>
                    <div 
                      className="p-4 rounded-lg border cursor-pointer hover:bg-accent"
                      onClick={() => setTemperature(1.2)}
                    >
                      <Zap className="h-8 w-8 mx-auto mb-2 text-orange-500" />
                      <h4 className="font-semibold">Creative</h4>
                      <p className="text-xs text-muted-foreground">1.2 - Imaginative & Diverse</p>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="font-semibold">Temperature Presets by Use Case</h4>
                  <div className="space-y-2">
                    {[
                      { name: 'Code Generation', value: 0.2, icon: Code },
                      { name: 'Technical Documentation', value: 0.3, icon: FileText },
                      { name: 'Customer Support', value: 0.5, icon: Users },
                      { name: 'Creative Writing', value: 1.0, icon: Brain },
                    ].map((preset) => (
                      <div
                        key={preset.name}
                        className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent cursor-pointer"
                        onClick={() => setTemperature(preset.value)}
                      >
                        <div className="flex items-center gap-3">
                          <preset.icon className="h-4 w-4" />
                          <span>{preset.name}</span>
                        </div>
                        <Badge variant="secondary">{preset.value}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Team Settings Tab */}
          <TabsContent value="team" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Team Configuration</CardTitle>
                <CardDescription>
                  Configure how {persona.name} works with other personas and agents
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Collaboration Mode</Label>
                  <Select defaultValue="cooperative">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="independent">Independent</SelectItem>
                      <SelectItem value="cooperative">Cooperative</SelectItem>
                      <SelectItem value="leader">Team Leader</SelectItem>
                      <SelectItem value="follower">Team Follower</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Communication Style</Label>
                  <Select defaultValue="direct">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="direct">Direct</SelectItem>
                      <SelectItem value="diplomatic">Diplomatic</SelectItem>
                      <SelectItem value="supportive">Supportive</SelectItem>
                      <SelectItem value="analytical">Analytical</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Allowed Collaborators</Label>
                  <div className="space-y-2">
                    {['cherry', 'sophia', 'karen'].filter(id => id !== personaId).map((id) => (
                      <div key={id} className="flex items-center space-x-2">
                        <Switch id={`collab-${id}`} defaultChecked />
                        <Label htmlFor={`collab-${id}`} className="capitalize">{id}</Label>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Delegation Settings</CardTitle>
                <CardDescription>
                  Configure task delegation preferences
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Switch id="auto-delegate" />
                  <Label htmlFor="auto-delegate">Enable automatic task delegation</Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Switch id="request-help" defaultChecked />
                  <Label htmlFor="request-help">Can request help from other personas</Label>
                </div>

                <div className="space-y-2">
                  <Label>Delegation Threshold</Label>
                  <Select defaultValue="medium">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low - Delegate frequently</SelectItem>
                      <SelectItem value="medium">Medium - Balanced approach</SelectItem>
                      <SelectItem value="high">High - Rarely delegate</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </PageWrapper>
  );
}