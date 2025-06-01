import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

// Define the Persona type
export interface Persona {
  id: string;
  name: string;
  domain: string;
  role: string;
  description: string;
  color: string; // For theming
  icon?: string; // Optional icon/emoji
  permissions?: string[]; // For future RBAC
}

// Define the store state interface
interface PersonaState {
  personas: Persona[];
  activePersonaId: string | null;
  
  // Actions
  setActivePersona: (personaId: string) => void;
  getActivePersona: () => Persona | null;
  getCurrentPersona: () => Persona | null; // Alias for consistency
  getPersonaById: (personaId: string) => Persona | undefined;
  getAllPersonas: () => Persona[];
  addPersona: (persona: Persona) => void;
  updatePersona: (personaId: string, updates: Partial<Persona>) => void;
  removePersona: (personaId: string) => void;
}

// Initial personas data
const initialPersonas: Persona[] = [
  {
    id: 'cherry',
    name: 'Cherry',
    domain: 'Personal',
    role: 'Personal Assistant',
    description: 'Your personal life assistant for health, habits, and lifestyle',
    color: '#FF1744', // Red/Pink
    icon: '🍒',
    permissions: ['personal', 'health', 'lifestyle']
  },
  {
    id: 'sophia',
    name: 'Sophia',
    domain: 'PayReady',
    role: 'Financial Operations',
    description: 'Financial technology and payment processing specialist',
    color: '#2196F3', // Blue
    icon: '💰',
    permissions: ['financial', 'transactions', 'compliance']
  },
  {
    id: 'karen',
    name: 'Karen',
    domain: 'ParagonRX',
    role: 'Healthcare Specialist',
    description: 'Medical compliance and pharmaceutical operations expert',
    color: '#4CAF50', // Green
    icon: '🏥',
    permissions: ['healthcare', 'medical', 'pharma', 'compliance']
  }
];

// Create the Zustand store
const usePersonaStore = create<PersonaState>()(
  devtools(
    persist(
      (set, get) => ({
        personas: initialPersonas,
        activePersonaId: 'cherry',
        
        setActivePersona: (personaId: string) => {
          const persona = get().getPersonaById(personaId);
          if (persona) {
            set({ activePersonaId: personaId });
          }
        },
        
        getActivePersona: () => {
          const state = get();
          if (!state.activePersonaId) return null;
          return state.personas.find(p => p.id === state.activePersonaId) || null;
        },
        
        getCurrentPersona: () => {
          // Alias for getActivePersona for consistency with the usage in components
          return get().getActivePersona();
        },
        
        getPersonaById: (personaId: string) => {
          return get().personas.find(p => p.id === personaId);
        },
        
        getAllPersonas: () => {
          return get().personas;
        },
        
        addPersona: (persona: Persona) => {
          set((state) => ({
            personas: [...state.personas, persona]
          }));
        },
        
        updatePersona: (personaId: string, updates: Partial<Persona>) => {
          set((state) => ({
            personas: state.personas.map(p => 
              p.id === personaId ? { ...p, ...updates } : p
            )
          }));
        },
        
        removePersona: (personaId: string) => {
          set((state) => ({
            personas: state.personas.filter(p => p.id !== personaId),
            // Clear active persona if it's the one being removed
            activePersonaId: state.activePersonaId === personaId ? null : state.activePersonaId
          }));
        }
      }),
      {
        name: 'persona-storage', // Key in localStorage
        partialize: (state) => ({ 
          activePersonaId: state.activePersonaId,
          // Optionally persist custom personas added by user
          personas: state.personas.filter(p => !initialPersonas.find(ip => ip.id === p.id))
        })
      }
    ),
    {
      name: 'PersonaStore'
    }
  )
);

export default usePersonaStore; 