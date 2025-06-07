import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type Persona = 'cherry' | 'sophia' | 'karen' | 'master'

export interface PersonaState {
  id: Persona
  name: string
  preferences: Record<string, any>
  metrics: {
    activeAgents: number
    dataFiles: number
    businessTools: number
    searches: number
    lastActivity: Date
  }
  settings: {
    theme: string
    notifications: boolean
    autoSearch: boolean
    defaultSearchMode: string
  }
}

export interface GlobalMetrics {
  totalAgents: number
  totalFiles: number
  totalRecords: number
  systemLoad: number
  uptime: number
}

interface PersonaStore {
  // Current state
  activePersona: Persona
  personaStates: Record<Persona, PersonaState>
  globalMetrics: GlobalMetrics
  isConnected: boolean
  
  // Actions
  setActivePersona: (persona: Persona) => void
  updatePersonaMetrics: (persona: Persona, metrics: Partial<PersonaState['metrics']>) => void
  updatePersonaSettings: (persona: Persona, settings: Partial<PersonaState['settings']>) => void
  updateGlobalMetrics: (metrics: Partial<GlobalMetrics>) => void
  setConnectionStatus: (connected: boolean) => void
}

// Default persona states
const defaultPersonaStates: Record<Persona, PersonaState> = {
  cherry: {
    id: 'cherry',
    name: 'Cherry',
    preferences: {
      primaryColor: 'red',
      focusAreas: ['creative', 'finance', 'ranch'],
      defaultTools: ['quickbooks', 'spotify']
    },
    metrics: {
      activeAgents: 3,
      dataFiles: 5,
      businessTools: 2,
      searches: 12,
      lastActivity: new Date()
    },
    settings: {
      theme: 'dark',
      notifications: true,
      autoSearch: true,
      defaultSearchMode: 'creative'
    }
  },
  sophia: {
    id: 'sophia',
    name: 'Sophia',
    preferences: {
      primaryColor: 'blue',
      focusAreas: ['business', 'analytics', 'strategy'],
      defaultTools: ['hubspot', 'gong', 'apollo', 'linkedin', 'netsuite']
    },
    metrics: {
      activeAgents: 8,
      dataFiles: 15,
      businessTools: 5,
      searches: 34,
      lastActivity: new Date()
    },
    settings: {
      theme: 'dark',
      notifications: true,
      autoSearch: true,
      defaultSearchMode: 'analytical'
    }
  },
  karen: {
    id: 'karen',
    name: 'Karen',
    preferences: {
      primaryColor: 'emerald',
      focusAreas: ['healthcare', 'research', 'compliance'],
      defaultTools: ['paragon_crm']
    },
    metrics: {
      activeAgents: 6,
      dataFiles: 8,
      businessTools: 1,
      searches: 18,
      lastActivity: new Date()
    },
    settings: {
      theme: 'dark',
      notifications: true,
      autoSearch: false,
      defaultSearchMode: 'research'
    }
  },
  master: {
    id: 'master',
    name: 'Master',
    preferences: {
      primaryColor: 'yellow',
      focusAreas: ['orchestration', 'cross-domain', 'optimization'],
      defaultTools: ['all_tools']
    },
    metrics: {
      activeAgents: 25,
      dataFiles: 28,
      businessTools: 8,
      searches: 64,
      lastActivity: new Date()
    },
    settings: {
      theme: 'dark',
      notifications: true,
      autoSearch: true,
      defaultSearchMode: 'super_deep'
    }
  }
}

const defaultGlobalMetrics: GlobalMetrics = {
  totalAgents: 42,
  totalFiles: 56,
  totalRecords: 125847,
  systemLoad: 0.68,
  uptime: 99.7
}

export const usePersona = create<PersonaStore>()(
  persist(
    (set, get) => ({
      // Initial state
      activePersona: 'cherry',
      personaStates: defaultPersonaStates,
      globalMetrics: defaultGlobalMetrics,
      isConnected: true,

      // Actions
      setActivePersona: (persona: Persona) => {
        set((state) => ({
          activePersona: persona,
          personaStates: {
            ...state.personaStates,
            [persona]: {
              ...state.personaStates[persona],
              metrics: {
                ...state.personaStates[persona].metrics,
                lastActivity: new Date()
              }
            }
          }
        }))
      },

      updatePersonaMetrics: (persona: Persona, metrics: Partial<PersonaState['metrics']>) => {
        set((state) => ({
          personaStates: {
            ...state.personaStates,
            [persona]: {
              ...state.personaStates[persona],
              metrics: {
                ...state.personaStates[persona].metrics,
                ...metrics,
                lastActivity: new Date()
              }
            }
          }
        }))
      },

      updatePersonaSettings: (persona: Persona, settings: Partial<PersonaState['settings']>) => {
        set((state) => ({
          personaStates: {
            ...state.personaStates,
            [persona]: {
              ...state.personaStates[persona],
              settings: {
                ...state.personaStates[persona].settings,
                ...settings
              }
            }
          }
        }))
      },

      updateGlobalMetrics: (metrics: Partial<GlobalMetrics>) => {
        set((state) => ({
          globalMetrics: {
            ...state.globalMetrics,
            ...metrics
          }
        }))
      },

      setConnectionStatus: (connected: boolean) => {
        set({ isConnected: connected })
      }
    }),
    {
      name: 'persona-storage',
      partialize: (state) => ({
        activePersona: state.activePersona,
        personaStates: state.personaStates
      })
    }
  )
)

// Hook for getting current persona data
export const useCurrentPersona = () => {
  const { activePersona, personaStates } = usePersona()
  return personaStates[activePersona]
}

// Hook for persona-specific data filtering
export const usePersonaData = <T extends { persona?: string }>(data: T[]): T[] => {
  const { activePersona } = usePersona()
  
  if (activePersona === 'master') {
    return data
  }
  
  return data.filter(item => 
    !item.persona || item.persona === activePersona
  )
}

// Utility functions
export const getPersonaColor = (persona: Persona): string => {
  switch (persona) {
    case 'cherry': return 'red'
    case 'sophia': return 'blue'
    case 'karen': return 'emerald'
    case 'master': return 'yellow'
    default: return 'gray'
  }
}

export const getPersonaIcon = (persona: Persona): string => {
  switch (persona) {
    case 'cherry': return '🍒'
    case 'sophia': return '💼'
    case 'karen': return '🔬'
    case 'master': return '⚡'
    default: return '👤'
  }
} 