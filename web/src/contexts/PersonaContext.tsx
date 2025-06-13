import { createContext, useContext, useState, ReactNode } from 'react'

export type Persona = 'cherry' | 'sophia' | 'karen'

interface PersonaContextType {
  currentPersona: Persona
  setCurrentPersona: (persona: Persona) => void
  personaConfig: {
    [key in Persona]: {
      name: string
      color: string
      description: string
      specialties: string[]
    }
  }
}

const PersonaContext = createContext<PersonaContextType | undefined>(undefined)

export function PersonaProvider({ children }: { children: ReactNode }) {
  const [currentPersona, setCurrentPersona] = useState<Persona>('sophia')

  const personaConfig = {
    cherry: {
      name: 'Cherry',
      color: 'cherry',
      description: 'Creative AI focused on design, content creation, and artistic workflows',
      specialties: ['Design', 'Content Creation', 'Branding', 'Visual Arts', 'Marketing Materials']
    },
    sophia: {
      name: 'Sophia',
      color: 'sophia',
      description: 'Strategic AI specialized in analysis, planning, and business intelligence',
      specialties: ['Strategic Analysis', 'Business Intelligence', 'Market Research', 'Planning', 'Decision Support']
    },
    karen: {
      name: 'Karen',
      color: 'karen',
      description: 'Operational AI expert in processes, workflows, and system optimization',
      specialties: ['Process Optimization', 'Workflow Management', 'Quality Assurance', 'Operations', 'Automation']
    }
  }

  return (
    <PersonaContext.Provider value={{
      currentPersona,
      setCurrentPersona,
      personaConfig
    }}>
      {children}
    </PersonaContext.Provider>
  )
}

export function usePersona() {
  const context = useContext(PersonaContext)
  if (!context) {
    throw new Error('usePersona must be used within a PersonaProvider')
  }
  return context
} 