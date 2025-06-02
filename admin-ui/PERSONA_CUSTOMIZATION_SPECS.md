# Persona Customization Implementation Specifications

## Overview

This document provides detailed specifications for implementing the persona customization features in the admin UI, including component interfaces, data models, and integration patterns.

## Data Models

### 1. Enhanced Persona Model

```typescript
// Core persona interface
interface Persona {
  id: string
  slug: string
  name: string
  domain: PersonaDomain
  role: string
  description: string
  avatar?: PersonaAvatar
  status: PersonaStatus
  capabilities: PersonaCapability[]
  configuration: PersonaConfiguration
  metadata: PersonaMetadata
  createdAt: Date
  updatedAt: Date
}

// Domain enumeration
enum PersonaDomain {
  PERSONAL = 'personal',
  FINANCIAL = 'financial',
  CLINICAL = 'clinical',
  CUSTOM = 'custom'
}

// Status tracking
interface PersonaStatus {
  active: boolean
  health: 'healthy' | 'degraded' | 'error'
  lastActiveAt?: Date
  errorMessage?: string
}

// Avatar configuration
interface PersonaAvatar {
  type: 'emoji' | 'image' | 'generated'
  value: string // emoji character, image URL, or generation prompt
  color: string // theme color
}

// Capability definition
interface PersonaCapability {
  id: string
  name: string
  description: string
  category: CapabilityCategory
  permissions: string[]
  configuration?: Record<string, any>
  enabled: boolean
}

// Configuration settings
interface PersonaConfiguration {
  llm: LLMConfiguration
  behavior: BehaviorConfiguration
  integrations: IntegrationConfiguration[]
  customPrompts: CustomPromptConfiguration
}

// LLM settings
interface LLMConfiguration {
  model: string
  temperature: number
  maxTokens: number
  topP: number
  frequencyPenalty: number
  presencePenalty: number
  systemPrompt: string
  responseFormat?: 'text' | 'json' | 'markdown'
}

// Behavior settings
interface BehaviorConfiguration {
  personality: PersonalityTraits
  communicationStyle: CommunicationStyle
  responsePatterns: ResponsePattern[]
  contextRetention: number // messages to retain
  memoryStrategy: 'full' | 'summary' | 'selective'
}

// Metadata
interface PersonaMetadata {
  version: string
  author: string
  tags: string[]
  analytics: PersonaAnalytics
  customFields?: Record<string, any>
}
```

### 2. Customization Models

```typescript
// Persona customization request
interface PersonaCustomization {
  id: string
  personaId: string
  userId: string
  name: string
  description: string
  overrides: PersonaOverrides
  schedule?: CustomizationSchedule
  conditions?: CustomizationCondition[]
  createdAt: Date
  updatedAt: Date
}

// Override specifications
interface PersonaOverrides {
  configuration?: Partial<PersonaConfiguration>
  capabilities?: CapabilityOverride[]
  appearance?: Partial<PersonaAvatar>
  behavior?: Partial<BehaviorConfiguration>
}

// Capability override
interface CapabilityOverride {
  capabilityId: string
  enabled?: boolean
  configuration?: Record<string, any>
}

// Scheduling for customizations
interface CustomizationSchedule {
  type: 'always' | 'scheduled' | 'conditional'
  timezone?: string
  activeHours?: TimeRange[]
  activeDays?: DayOfWeek[]
  startDate?: Date
  endDate?: Date
}

// Conditional activation
interface CustomizationCondition {
  type: 'context' | 'metric' | 'event'
  operator: 'equals' | 'contains' | 'greater' | 'less'
  field: string
  value: any
  action: 'activate' | 'deactivate'
}
```

## Component Specifications

### 1. PersonaCustomizationEditor Component

```typescript
interface PersonaCustomizationEditorProps {
  persona: Persona
  customization?: PersonaCustomization
  onSave: (customization: PersonaCustomization) => Promise<void>
  onCancel: () => void
  mode: 'create' | 'edit'
}

const PersonaCustomizationEditor: React.FC<PersonaCustomizationEditorProps> = ({
  persona,
  customization,
  onSave,
  onCancel,
  mode
}) => {
  // Component implementation
  return (
    <div className="persona-customization-editor">
      <EditorHeader persona={persona} mode={mode} />
      
      <TabPanel defaultTab="basic">
        <Tab id="basic" label="Basic Settings">
          <BasicCustomizationForm />
        </Tab>
        
        <Tab id="behavior" label="Behavior">
          <BehaviorCustomizationForm />
        </Tab>
        
        <Tab id="capabilities" label="Capabilities">
          <CapabilityCustomizationForm />
        </Tab>
        
        <Tab id="integrations" label="Integrations">
          <IntegrationCustomizationForm />
        </Tab>
        
        <Tab id="advanced" label="Advanced">
          <AdvancedCustomizationForm />
        </Tab>
      </TabPanel>
      
      <EditorActions onSave={handleSave} onCancel={onCancel} />
    </div>
  )
}
```

### 2. PersonaPreview Component

```typescript
interface PersonaPreviewProps {
  persona: Persona
  customization?: PersonaCustomization
  previewMode: 'chat' | 'card' | 'full'
  sampleInputs?: string[]
}

const PersonaPreview: React.FC<PersonaPreviewProps> = ({
  persona,
  customization,
  previewMode,
  sampleInputs
}) => {
  const [responses, setResponses] = useState<PreviewResponse[]>([])
  const [loading, setLoading] = useState(false)
  
  const generatePreview = async (input: string) => {
    setLoading(true)
    try {
      const response = await api.generatePersonaPreview({
        personaId: persona.id,
        customization,
        input
      })
      setResponses(prev => [...prev, response])
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="persona-preview">
      {previewMode === 'chat' && <ChatPreview />}
      {previewMode === 'card' && <CardPreview />}
      {previewMode === 'full' && <FullPreview />}
    </div>
  )
}
```

### 3. CapabilityManager Component

```typescript
interface CapabilityManagerProps {
  persona: Persona
  availableCapabilities: PersonaCapability[]
  onChange: (capabilities: PersonaCapability[]) => void
}

const CapabilityManager: React.FC<CapabilityManagerProps> = ({
  persona,
  availableCapabilities,
  onChange
}) => {
  const [selectedCapabilities, setSelectedCapabilities] = useState(persona.capabilities)
  const [searchTerm, setSearchTerm] = useState('')
  
  const categorizedCapabilities = useMemo(() => {
    return groupBy(availableCapabilities, 'category')
  }, [availableCapabilities])
  
  return (
    <div className="capability-manager">
      <SearchInput
        value={searchTerm}
        onChange={setSearchTerm}
        placeholder="Search capabilities..."
      />
      
      <div className="capability-categories">
        {Object.entries(categorizedCapabilities).map(([category, capabilities]) => (
          <CapabilityCategory
            key={category}
            category={category}
            capabilities={capabilities}
            selected={selectedCapabilities}
            onToggle={handleCapabilityToggle}
          />
        ))}
      </div>
      
      <CapabilityConfigPanel
        capabilities={selectedCapabilities}
        onConfigChange={handleConfigChange}
      />
    </div>
  )
}
```

## API Integration Specifications

### 1. Persona Customization API

```typescript
// API client interface
interface PersonaCustomizationAPI {
  // CRUD operations
  createCustomization(data: CreateCustomizationRequest): Promise<PersonaCustomization>
  updateCustomization(id: string, data: UpdateCustomizationRequest): Promise<PersonaCustomization>
  deleteCustomization(id: string): Promise<void>
  getCustomization(id: string): Promise<PersonaCustomization>
  listCustomizations(filters?: CustomizationFilters): Promise<PersonaCustomization[]>
  
  // Validation and preview
  validateCustomization(data: PersonaCustomization): Promise<ValidationResult>
  previewCustomization(personaId: string, customization: PersonaCustomization): Promise<PreviewResult>
  
  // Import/Export
  exportCustomization(id: string): Promise<CustomizationExport>
  importCustomization(data: CustomizationExport): Promise<PersonaCustomization>
  
  // Batch operations
  applyCustomizationBatch(personaIds: string[], customization: PersonaCustomization): Promise<BatchResult>
}

// Request/Response types
interface CreateCustomizationRequest {
  personaId: string
  name: string
  description?: string
  overrides: PersonaOverrides
  schedule?: CustomizationSchedule
  conditions?: CustomizationCondition[]
}

interface ValidationResult {
  valid: boolean
  errors?: ValidationError[]
  warnings?: ValidationWarning[]
  suggestions?: ValidationSuggestion[]
}

interface PreviewResult {
  personaId: string
  customizationId?: string
  samples: {
    input: string
    baseResponse: string
    customizedResponse: string
    differences: ResponseDifference[]
  }[]
}
```

### 2. Real-time Synchronization

```typescript
// WebSocket events for real-time updates
interface CustomizationWebSocketEvents {
  'customization.created': {
    customization: PersonaCustomization
    userId: string
  }
  
  'customization.updated': {
    customizationId: string
    changes: Partial<PersonaCustomization>
    userId: string
  }
  
  'customization.deleted': {
    customizationId: string
    userId: string
  }
  
  'customization.applied': {
    personaId: string
    customizationId: string
    timestamp: Date
  }
}

// Real-time sync hook
const useCustomizationSync = (personaId: string) => {
  const queryClient = useQueryClient()
  const [syncStatus, setSyncStatus] = useState<'connected' | 'disconnected'>('disconnected')
  
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/customizations/${personaId}`)
    
    ws.onopen = () => setSyncStatus('connected')
    ws.onclose = () => setSyncStatus('disconnected')
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      switch (data.type) {
        case 'customization.updated':
          queryClient.setQueryData(
            ['customization', data.customizationId],
            (old) => ({ ...old, ...data.changes })
          )
          break
        // Handle other events...
      }
    }
    
    return () => ws.close()
  }, [personaId, queryClient])
  
  return { syncStatus }
}
```

## State Management Implementation

### 1. Customization Store

```typescript
interface CustomizationStore {
  // State
  customizations: Map<string, PersonaCustomization>
  activeCustomizations: Map<string, string> // personaId -> customizationId
  draftCustomizations: Map<string, Partial<PersonaCustomization>>
  
  // Actions
  loadCustomizations: (personaId?: string) => Promise<void>
  createCustomization: (data: CreateCustomizationRequest) => Promise<PersonaCustomization>
  updateCustomization: (id: string, updates: Partial<PersonaCustomization>) => Promise<void>
  deleteCustomization: (id: string) => Promise<void>
  
  // Draft management
  saveDraft: (personaId: string, draft: Partial<PersonaCustomization>) => void
  loadDraft: (personaId: string) => Partial<PersonaCustomization> | undefined
  clearDraft: (personaId: string) => void
  
  // Activation
  activateCustomization: (personaId: string, customizationId: string) => Promise<void>
  deactivateCustomization: (personaId: string) => Promise<void>
  
  // Validation
  validateCustomization: (customization: PersonaCustomization) => Promise<ValidationResult>
}

const useCustomizationStore = create<CustomizationStore>()(
  devtools(
    persist(
      (set, get) => ({
        customizations: new Map(),
        activeCustomizations: new Map(),
        draftCustomizations: new Map(),
        
        loadCustomizations: async (personaId?: string) => {
          const filters = personaId ? { personaId } : undefined
          const customizations = await api.listCustomizations(filters)
          
          set((state) => {
            const newMap = new Map(state.customizations)
            customizations.forEach(c => newMap.set(c.id, c))
            return { customizations: newMap }
          })
        },
        
        // ... other actions
      }),
      {
        name: 'customization-store',
        partialize: (state) => ({
          draftCustomizations: Array.from(state.draftCustomizations.entries()),
          activeCustomizations: Array.from(state.activeCustomizations.entries()),
        })
      }
    )
  )
)
```

### 2. Query Hooks

```typescript
// Custom hooks for data fetching
const usePersonaCustomizations = (personaId: string) => {
  return useQuery({
    queryKey: ['customizations', personaId],
    queryFn: () => api.listCustomizations({ personaId }),
    staleTime: 5 * 60 * 1000,
  })
}

const useCustomizationMutation = () => {
  const queryClient = useQueryClient()
  
  return {
    create: useMutation({
      mutationFn: api.createCustomization,
      onSuccess: (data) => {
        queryClient.invalidateQueries(['customizations', data.personaId])
        toast.success('Customization created successfully')
      },
    }),
    
    update: useMutation({
      mutationFn: ({ id, data }: { id: string; data: UpdateCustomizationRequest }) =>
        api.updateCustomization(id, data),
      onSuccess: (data) => {
        queryClient.invalidateQueries(['customizations', data.personaId])
        toast.success('Customization updated successfully')
      },
    }),
    
    delete: useMutation({
      mutationFn: api.deleteCustomization,
      onSuccess: (_, id) => {
        queryClient.invalidateQueries(['customizations'])
        toast.success('Customization deleted successfully')
      },
    }),
  }
}
```

## Performance Optimization

### 1. Lazy Loading Strategy

```typescript
// Lazy load heavy components
const PersonaCustomizationEditor = lazy(() => 
  import('./components/PersonaCustomizationEditor')
)

const CapabilityConfigPanel = lazy(() =>
  import('./components/CapabilityConfigPanel')
)

// Suspense wrapper
const LazyPersonaEditor = () => (
  <Suspense fallback={<EditorSkeleton />}>
    <PersonaCustomizationEditor />
  </Suspense>
)
```

### 2. Memoization Strategy

```typescript
// Memoize expensive computations
const useProcessedCapabilities = (capabilities: PersonaCapability[]) => {
  return useMemo(() => {
    // Group by category
    const grouped = groupBy(capabilities, 'category')
    
    // Sort by priority
    const sorted = mapValues(grouped, cats => 
      sortBy(cats, ['priority', 'name'])
    )
    
    // Calculate statistics
    const stats = {
      total: capabilities.length,
      enabled: capabilities.filter(c => c.enabled).length,
      byCategory: mapValues(grouped, cats => cats.length)
    }
    
    return { grouped: sorted, stats }
  }, [capabilities])
}

// Memoize components
const PersonaCard = memo(({ persona, onEdit, onDelete }) => {
  // Component implementation
}, (prevProps, nextProps) => {
  // Custom comparison
  return prevProps.persona.updatedAt === nextProps.persona.updatedAt
})
```

### 3. Virtual Scrolling

```typescript
// Virtual list for large datasets
const PersonaList = ({ personas }: { personas: Persona[] }) => {
  const rowVirtualizer = useVirtualizer({
    count: personas.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 120, // Estimated row height
    overscan: 5,
  })
  
  return (
    <div ref={parentRef} className="persona-list">
      <div style={{ height: `${rowVirtualizer.getTotalSize()}px` }}>
        {rowVirtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            <PersonaCard persona={personas[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  )
}
```

## Testing Strategy

### 1. Component Testing

```typescript
// Component test example
describe('PersonaCustomizationEditor', () => {
  it('should render all customization tabs', () => {
    const { getByRole } = render(
      <PersonaCustomizationEditor
        persona={mockPersona}
        mode="create"
        onSave={jest.fn()}
        onCancel={jest.fn()}
      />
    )
    
    expect(getByRole('tab', { name: 'Basic Settings' })).toBeInTheDocument()
    expect(getByRole('tab', { name: 'Behavior' })).toBeInTheDocument()
    expect(getByRole('tab', { name: 'Capabilities' })).toBeInTheDocument()
  })
  
  it('should validate required fields before saving', async () => {
    const onSave = jest.fn()
    const { getByRole } = render(
      <PersonaCustomizationEditor
        persona={mockPersona}
        mode="create"
        onSave={onSave}
        onCancel={jest.fn()}
      />
    )
    
    fireEvent.click(getByRole('button', { name: 'Save' }))
    
    await waitFor(() => {
      expect(onSave).not.toHaveBeenCalled()
      expect(getByRole('alert')).toHaveTextContent('Name is required')
    })
  })
})
```

### 2. Integration Testing

```typescript
// API integration test
describe('Persona Customization API', () => {
  it('should create and retrieve customization', async () => {
    const customization = await api.createCustomization({
      personaId: 'test-persona',
      name: 'Test Customization',
      overrides: {
        configuration: {
          llm: { temperature: 0.5 }
        }
      }
    })
    
    expect(customization.id).toBeDefined()
    
    const retrieved = await api.getCustomization(customization.id)
    expect(retrieved).toEqual(customization)
  })
})
```

## Migration Strategy

### 1. Data Migration

```typescript
// Migration script for existing personas
const migratePersonasToNewSchema = async () => {
  const oldPersonas = await db.query('SELECT * FROM personas')
  
  for (const oldPersona of oldPersonas) {
    const newPersona: Persona = {
      ...oldPersona,
      configuration: {
        llm: {
          model: oldPersona.model || 'gpt-4',
          temperature: oldPersona.temperature || 0.7,
          maxTokens: oldPersona.max_tokens || 2000,
          // ... map other fields
        },
        behavior: {
          // ... map behavior fields
        },
        integrations: [],
        customPrompts: {}
      },
      capabilities: mapOldCapabilities(oldPersona.capabilities),
      metadata: {
        version: '2.0',
        author: 'system',
        tags: oldPersona.tags || [],
        analytics: {}
      }
    }
    
    await db.query('INSERT INTO personas_v2 ...', newPersona)
  }
}
```

## Security Considerations

### 1. Permission Model

```typescript
// Permission checking
const canCustomizePersona = (user: User, persona: Persona): boolean => {
  // Check user permissions
  if (user.role === 'admin') return true
  if (user.role === 'user' && persona.domain === 'personal') return true
  
  // Check persona-specific permissions
  return persona.metadata.customFields?.allowedUsers?.includes(user.id) || false
}

// Permission enforcement in API
app.put('/api/personas/:id/customize', authenticate, async (req, res) => {
  const persona = await getPersona(req.params.id)
  
  if (!canCustomizePersona(req.user, persona)) {
    return res.status(403).json({ error: 'Insufficient permissions' })
  }
  
  // Process customization...
})
```

### 2. Input Validation

```typescript
// Validation schema
const customizationSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
  overrides: z.object({
    configuration: z.object({
      llm: z.object({
        temperature: z.number().min(0).max(2),
        maxTokens: z.number().min(1).max(32000),
        // ... other validations
      }).partial()
    }).optional()
  })
})

// Validate input
const validateCustomization = (data: unknown): ValidationResult => {
  try {
    const validated = customizationSchema.parse(data)
    return { valid: true, data: validated }
  } catch (error) {
    return { 
      valid: false, 
      errors: error.errors.map(e => ({
        field: e.path.join('.'),
        message: e.message
      }))
    }
  }
}
```

## Deployment Considerations

### 1. Feature Flags

```typescript
// Feature flag configuration
const featureFlags = {
  personaCustomization: {
    enabled: process.env.FEATURE_PERSONA_CUSTOMIZATION === 'true',
    rolloutPercentage: 100,
    allowedUsers: [],
    allowedDomains: ['personal', 'financial', 'clinical']
  }
}

// Feature flag check
const PersonaPage = () => {
  const { isEnabled } = useFeatureFlag('personaCustomization')
  
  return (
    <div>
      {isEnabled ? <PersonaCustomizationEditor /> : <LegacyPersonaEditor />}
    </div>
  )
}
```

### 2. Monitoring and Analytics

```typescript
// Track customization usage
const trackCustomizationEvent = (event: string, data: any) => {
  analytics.track({
    event: `persona_customization_${event}`,
    properties: {
      personaId: data.personaId,
      customizationId: data.customizationId,
      userId: data.userId,
      timestamp: new Date().toISOString(),
      ...data
    }
  })
}

// Performance monitoring
const measureCustomizationPerformance = () => {
  performance.mark('customization-start')
  
  // ... perform customization
  
  performance.mark('customization-end')
  performance.measure('customization', 'customization-start', 'customization-end')
  
  const measure = performance.getEntriesByName('customization')[0]
  analytics.track('performance_customization', {
    duration: measure.duration,
    timestamp: new Date().toISOString()
  })
}
```

## Conclusion

This specification provides a comprehensive blueprint for implementing persona customization features in the admin UI. The modular architecture, robust state management, and performance optimizations ensure a scalable and maintainable solution that can grow with the platform's needs.