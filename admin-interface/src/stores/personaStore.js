import { create } from 'zustand'

export const usePersonaStore = create((set, get) => ({
  // Persona configurations
  personas: [
    {
      id: 'cherry',
      name: 'Cherry',
      title: 'Personal Life Companion',
      icon: 'Heart',
      accentColor: 'bg-pink-500',
      borderColor: 'border-pink-500',
      status: 'active',
      interactionCount: 0,
      lastInteraction: null,
      personalityHealth: 95.0,
      memoryUsage: 0,
      voiceStatus: 'ready',
      coordinationStatus: 'active',
      personalityTraits: [
        { id: 'playfulness', label: 'Playfulness', value: 95, description: 'How playful and fun-loving' },
        { id: 'warmth', label: 'Warmth', value: 90, description: 'Emotional warmth and caring' },
        { id: 'intelligence', label: 'Intelligence', value: 85, description: 'Analytical and problem-solving ability' },
        { id: 'creativity', label: 'Creativity', value: 88, description: 'Creative and imaginative thinking' },
        { id: 'empathy', label: 'Empathy', value: 92, description: 'Understanding and sharing emotions' },
        { id: 'confidence', label: 'Confidence', value: 80, description: 'Self-assurance and boldness' },
        { id: 'curiosity', label: 'Curiosity', value: 87, description: 'Interest in learning and exploring' },
        { id: 'humor', label: 'Humor', value: 93, description: 'Wit and comedic timing' },
        { id: 'loyalty', label: 'Loyalty', value: 96, description: 'Dedication and faithfulness' },
        { id: 'spontaneity', label: 'Spontaneity', value: 89, description: 'Willingness to be spontaneous' }
      ],
      voiceSettings: {
        profileId: 'cherry_voice_001',
        provider: 'elevenlabs',
        stability: 75,
        similarityBoost: 80,
        styleExaggeration: 65,
        speakerBoost: true
      },
      adaptiveSettings: {
        learningRate: 0.7,
        optimizationStrategy: 'quality_maximization',
        performanceHistoryRetentionDays: 30,
        isEnabled: true
      }
    },
    {
      id: 'sophia',
      name: 'Sophia',
      title: 'Business Intelligence Specialist',
      icon: 'Briefcase',
      accentColor: 'bg-blue-500',
      borderColor: 'border-blue-500',
      status: 'active',
      interactionCount: 0,
      lastInteraction: null,
      personalityHealth: 92.0,
      memoryUsage: 0,
      voiceStatus: 'ready',
      coordinationStatus: 'active',
      personalityTraits: [
        { id: 'analytical', label: 'Analytical', value: 95, description: 'Data analysis and logical reasoning' },
        { id: 'professional', label: 'Professional', value: 90, description: 'Business-appropriate demeanor' },
        { id: 'efficiency', label: 'Efficiency', value: 88, description: 'Focus on productivity and results' },
        { id: 'strategic', label: 'Strategic', value: 92, description: 'Long-term planning and vision' },
        { id: 'detail_oriented', label: 'Detail-Oriented', value: 87, description: 'Attention to specifics' },
        { id: 'leadership', label: 'Leadership', value: 85, description: 'Ability to guide and direct' },
        { id: 'innovation', label: 'Innovation', value: 80, description: 'Creative problem-solving in business' },
        { id: 'communication', label: 'Communication', value: 88, description: 'Clear and effective communication' },
        { id: 'adaptability', label: 'Adaptability', value: 83, description: 'Flexibility in changing situations' },
        { id: 'reliability', label: 'Reliability', value: 94, description: 'Consistent and dependable performance' }
      ],
      voiceSettings: {
        profileId: 'sophia_voice_001',
        provider: 'elevenlabs',
        stability: 85,
        similarityBoost: 75,
        styleExaggeration: 45,
        speakerBoost: false
      },
      adaptiveSettings: {
        learningRate: 0.5,
        optimizationStrategy: 'pareto_frontier',
        performanceHistoryRetentionDays: 60,
        isEnabled: true
      }
    },
    {
      id: 'karen',
      name: 'Karen',
      title: 'Healthcare & Clinical Specialist',
      icon: 'Stethoscope',
      accentColor: 'bg-green-500',
      borderColor: 'border-green-500',
      status: 'active',
      interactionCount: 0,
      lastInteraction: null,
      personalityHealth: 94.0,
      memoryUsage: 0,
      voiceStatus: 'ready',
      coordinationStatus: 'active',
      personalityTraits: [
        { id: 'compassion', label: 'Compassion', value: 96, description: 'Deep caring for patient wellbeing' },
        { id: 'precision', label: 'Precision', value: 94, description: 'Accuracy in medical information' },
        { id: 'knowledge', label: 'Knowledge', value: 92, description: 'Medical and clinical expertise' },
        { id: 'patience', label: 'Patience', value: 90, description: 'Calm and understanding demeanor' },
        { id: 'ethics', label: 'Ethics', value: 98, description: 'Strong moral and professional standards' },
        { id: 'communication', label: 'Communication', value: 88, description: 'Clear medical communication' },
        { id: 'empathy', label: 'Empathy', value: 95, description: 'Understanding patient perspectives' },
        { id: 'thoroughness', label: 'Thoroughness', value: 91, description: 'Comprehensive approach to care' },
        { id: 'calm', label: 'Calm', value: 89, description: 'Maintaining composure under pressure' },
        { id: 'advocacy', label: 'Advocacy', value: 93, description: 'Standing up for patient needs' }
      ],
      voiceSettings: {
        profileId: 'karen_voice_001',
        provider: 'elevenlabs',
        stability: 90,
        similarityBoost: 70,
        styleExaggeration: 35,
        speakerBoost: false
      },
      adaptiveSettings: {
        learningRate: 0.4,
        optimizationStrategy: 'quality_maximization',
        performanceHistoryRetentionDays: 90,
        isEnabled: true
      }
    }
  ],
  
  // Current selected persona
  selectedPersona: null,
  
  // Persona metrics
  personaMetrics: {},
  
  // Actions
  setSelectedPersona: (personaId) => set({ selectedPersona: personaId }),
  
  updatePersonalityTrait: (personaId, traitId, value) => set((state) => ({
    personas: state.personas.map(persona => 
      persona.id === personaId 
        ? {
            ...persona,
            personalityTraits: persona.personalityTraits.map(trait =>
              trait.id === traitId ? { ...trait, value } : trait
            )
          }
        : persona
    )
  })),
  
  updateVoiceSettings: (personaId, settings) => set((state) => ({
    personas: state.personas.map(persona =>
      persona.id === personaId
        ? { ...persona, voiceSettings: { ...persona.voiceSettings, ...settings } }
        : persona
    )
  })),
  
  updateAdaptiveSettings: (personaId, settings) => set((state) => ({
    personas: state.personas.map(persona =>
      persona.id === personaId
        ? { ...persona, adaptiveSettings: { ...persona.adaptiveSettings, ...settings } }
        : persona
    )
  })),
  
  updatePersonaMetrics: (personaId, metrics) => set((state) => ({
    personaMetrics: {
      ...state.personaMetrics,
      [personaId]: metrics
    }
  })),
  
  getPersonaById: (personaId) => {
    const { personas } = get()
    return personas.find(p => p.id === personaId)
  }
}))

