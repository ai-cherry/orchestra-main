import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

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
  settings?: PersonaSettings;
  metadata?: Record<string, any>;
  createdAt?: string;
  updatedAt?: string;
}

// Persona-specific settings
export interface PersonaSettings {
  theme?: {
    primaryColor?: string;
    secondaryColor?: string;
    fontFamily?: string;
  };
  preferences?: {
    language?: string;
    timezone?: string;
    dateFormat?: string;
  };
  features?: {
    [key: string]: boolean;
  };
}

// API sync status
export interface SyncStatus {
  isSyncing: boolean;
  lastSyncedAt?: string;
  error?: string;
}

// Define the store state interface
interface PersonaState {
  // State
  personas: Persona[];
  activePersonaId: string | null;
  isLoading: boolean;
  error: string | null;
  syncStatus: SyncStatus;
  
  // Computed getters
  activePersona: Persona | null;
  
  // Actions
  setPersonas: (personas: Persona[]) => void;
  setActivePersona: (personaId: string) => void;
  getActivePersona: () => Persona | null;
  getCurrentPersona: () => Persona | null; // Alias for consistency
  getPersonaById: (personaId: string) => Persona | undefined;
  getAllPersonas: () => Persona[];
  addPersona: (persona: Persona) => void;
  updatePersona: (personaId: string, updates: Partial<Persona>) => void;
  removePersona: (personaId: string) => void;
  
  // Batch operations
  addMultiplePersonas: (personas: Persona[]) => void;
  updateMultiplePersonas: (updates: Array<{ id: string; updates: Partial<Persona> }>) => void;
  removeMultiplePersonas: (personaIds: string[]) => void;
  
  // Settings management
  updatePersonaSettings: (personaId: string, settings: Partial<PersonaSettings>) => void;
  
  // Loading and error states
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  
  // Sync management
  setSyncStatus: (status: Partial<SyncStatus>) => void;
  markAsSynced: () => void;
  
  // Reset
  reset: () => void;
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
    permissions: ['personal', 'health', 'lifestyle'],
    settings: {
      theme: {
        primaryColor: '#FF1744',
        secondaryColor: '#F50057',
      },
      features: {
        healthTracking: true,
        habitCoaching: true,
        mediaGeneration: true,
      }
    },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: 'sophia',
    name: 'Sophia',
    domain: 'PayReady',
    role: 'Financial Operations',
    description: 'Financial technology and payment processing specialist',
    color: '#2196F3', // Blue
    icon: '💰',
    permissions: ['financial', 'transactions', 'compliance'],
    settings: {
      theme: {
        primaryColor: '#2196F3',
        secondaryColor: '#1976D2',
      },
      features: {
        financialDashboard: true,
        transactionMonitoring: true,
        complianceReporting: true,
      }
    },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: 'karen',
    name: 'Karen',
    domain: 'ParagonRX',
    role: 'Healthcare Specialist',
    description: 'Medical compliance and pharmaceutical operations expert',
    color: '#4CAF50', // Green
    icon: '🏥',
    permissions: ['healthcare', 'medical', 'pharma', 'compliance'],
    settings: {
      theme: {
        primaryColor: '#4CAF50',
        secondaryColor: '#388E3C',
      },
      features: {
        clinicalWorkspace: true,
        patientManagement: true,
        prescriptionTracking: true,
      }
    },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }
];

// Create the Zustand store with immer for immutable updates
const usePersonaStore = create<PersonaState>()(
  subscribeWithSelector(
    devtools(
      persist(
        immer((set, get) => ({
          // Initial state
          personas: initialPersonas,
          activePersonaId: 'cherry',
          isLoading: false,
          error: null,
          syncStatus: {
            isSyncing: false,
          },
          
          // Computed getter
          get activePersona() {
            const state = get();
            if (!state.activePersonaId) return null;
            return state.personas.find(p => p.id === state.activePersonaId) || null;
          },
          
          // Actions
          setPersonas: (personas: Persona[]) => set((state) => {
            state.personas = personas;
          }),
          
          setActivePersona: (personaId: string) => set((state) => {
            const persona = state.personas.find((p: Persona) => p.id === personaId);
            if (persona) {
              state.activePersonaId = personaId;
            }
          }),
          
          getActivePersona: () => {
            const state = get();
            if (!state.activePersonaId) return null;
            return state.personas.find(p => p.id === state.activePersonaId) || null;
          },
          
          getCurrentPersona: () => {
            return get().getActivePersona();
          },
          
          getPersonaById: (personaId: string) => {
            return get().personas.find(p => p.id === personaId);
          },
          
          getAllPersonas: () => {
            return get().personas;
          },
          
          addPersona: (persona: Persona) => set((state) => {
            const now = new Date().toISOString();
            state.personas.push({
              ...persona,
              createdAt: persona.createdAt || now,
              updatedAt: persona.updatedAt || now,
            });
          }),
          
          updatePersona: (personaId: string, updates: Partial<Persona>) => set((state) => {
            const index = state.personas.findIndex((p: Persona) => p.id === personaId);
            if (index !== -1) {
              state.personas[index] = {
                ...state.personas[index],
                ...updates,
                updatedAt: new Date().toISOString(),
              };
            }
          }),
          
          removePersona: (personaId: string) => set((state) => {
            state.personas = state.personas.filter((p: Persona) => p.id !== personaId);
            if (state.activePersonaId === personaId) {
              state.activePersonaId = state.personas[0]?.id || null;
            }
          }),
          
          // Batch operations
          addMultiplePersonas: (personas: Persona[]) => set((state) => {
            const now = new Date().toISOString();
            const personasWithTimestamps = personas.map(p => ({
              ...p,
              createdAt: p.createdAt || now,
              updatedAt: p.updatedAt || now,
            }));
            state.personas.push(...personasWithTimestamps);
          }),
          
          updateMultiplePersonas: (updates: Array<{ id: string; updates: Partial<Persona> }>) => set((state) => {
            const now = new Date().toISOString();
            updates.forEach(({ id, updates }) => {
              const index = state.personas.findIndex((p: Persona) => p.id === id);
              if (index !== -1) {
                state.personas[index] = {
                  ...state.personas[index],
                  ...updates,
                  updatedAt: now,
                };
              }
            });
          }),
          
          removeMultiplePersonas: (personaIds: string[]) => set((state) => {
            state.personas = state.personas.filter((p: Persona) => !personaIds.includes(p.id));
            if (personaIds.includes(state.activePersonaId || '')) {
              state.activePersonaId = state.personas[0]?.id || null;
            }
          }),
          
          // Settings management
          updatePersonaSettings: (personaId: string, settings: Partial<PersonaSettings>) => set((state) => {
            const index = state.personas.findIndex((p: Persona) => p.id === personaId);
            if (index !== -1) {
              state.personas[index].settings = {
                ...state.personas[index].settings,
                ...settings,
              };
              state.personas[index].updatedAt = new Date().toISOString();
            }
          }),
          
          // Loading and error states
          setLoading: (isLoading: boolean) => set((state) => {
            state.isLoading = isLoading;
          }),
          
          setError: (error: string | null) => set((state) => {
            state.error = error;
          }),
          
          clearError: () => set((state) => {
            state.error = null;
          }),
          
          // Sync management
          setSyncStatus: (status: Partial<SyncStatus>) => set((state) => {
            state.syncStatus = {
              ...state.syncStatus,
              ...status,
            };
          }),
          
          markAsSynced: () => set((state) => {
            state.syncStatus = {
              isSyncing: false,
              lastSyncedAt: new Date().toISOString(),
              error: undefined,
            };
          }),
          
          // Reset
          reset: () => set((state) => {
            state.personas = initialPersonas;
            state.activePersonaId = 'cherry';
            state.isLoading = false;
            state.error = null;
            state.syncStatus = {
              isSyncing: false,
            };
          }),
        })),
        {
          name: 'persona-storage',
          partialize: (state) => ({
            activePersonaId: state.activePersonaId,
            // Store custom personas (non-initial ones)
            personas: state.personas.filter(p => !initialPersonas.find(ip => ip.id === p.id)),
            // Store modifications to initial personas
            personaModifications: initialPersonas.reduce((acc, initialPersona) => {
              const currentPersona = state.personas.find(p => p.id === initialPersona.id);
              if (currentPersona && JSON.stringify(currentPersona) !== JSON.stringify(initialPersona)) {
                acc[initialPersona.id] = currentPersona;
              }
              return acc;
            }, {} as Record<string, Persona>),
          }),
          merge: (persistedState: any, currentState) => {
            // Merge persisted state with current state
            const mergedPersonas = [...initialPersonas];
            
            // Apply modifications to initial personas
            if (persistedState.personaModifications) {
              Object.entries(persistedState.personaModifications).forEach(([id, persona]) => {
                const index = mergedPersonas.findIndex(p => p.id === id);
                if (index !== -1) {
                  mergedPersonas[index] = persona as Persona;
                }
              });
            }
            
            // Add custom personas
            if (persistedState.personas) {
              mergedPersonas.push(...persistedState.personas);
            }
            
            return {
              ...currentState,
              personas: mergedPersonas,
              activePersonaId: persistedState.activePersonaId || currentState.activePersonaId,
            };
          },
        }
      ),
      {
        name: 'PersonaStore',
      }
    )
  )
);

// Selectors for common use cases
export const useActivePersona = () => usePersonaStore((state) => state.activePersona);
export const usePersonaById = (id: string) => usePersonaStore((state) => state.getPersonaById(id));
export const useAllPersonas = () => usePersonaStore((state) => state.personas);
export const usePersonaActions = () => usePersonaStore((state) => ({
  setActivePersona: state.setActivePersona,
  addPersona: state.addPersona,
  updatePersona: state.updatePersona,
  removePersona: state.removePersona,
  updatePersonaSettings: state.updatePersonaSettings,
}));

export default usePersonaStore;