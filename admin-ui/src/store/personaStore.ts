import { create } from 'zustand';

// Define the Persona interface based on v1 appData structure
export interface Persona {
  id: string;
  name: string;
  domain: string;
  color: string; // Original color from appData
  personality: string;
  status: string;
  activeAgents: number;
  tasksCompleted: number;
  preferredModels: string[];
}

// Define the state structure for the persona store
export interface PersonaStoreState {
  personas: Persona[];
  currentPersonaId: string;
  accentColors: Record<string, string>; // Maps persona ID to its primary accent color
  setPersona: (personaId: string) => void;
  getPersonaById: (id: string) => Persona | undefined;
  getCurrentPersona: () => Persona | undefined;
  getCurrentDomain: () => string | undefined;
  getCurrentAccentColor: () => string | undefined;
}

const initialPersonas: Persona[] = [
  {
    id: "cherry",
    name: "Cherry",
    domain: "Personal",
    color: "#ff69b4",
    personality: "Casual, Supportive, Creative",
    status: "active",
    activeAgents: 3,
    tasksCompleted: 127,
    preferredModels: ["Claude 3 Haiku", "GPT-4 Turbo"]
  },
  {
    id: "sophia",
    name: "Sophia",
    domain: "PayReady",
    color: "#0066cc", // Original color from appData
    personality: "Professional, Precise, Analytical",
    status: "active",
    activeAgents: 5,
    tasksCompleted: 89,
    preferredModels: ["GPT-4 Turbo", "CodeLlama"]
  },
  {
    id: "karen",
    name: "Karen",
    domain: "Paragon RX",
    color: "#00cc66", // Original color from appData
    personality: "Formal, Compliant, Research-focused",
    status: "active",
    activeAgents: 2,
    tasksCompleted: 34,
    preferredModels: ["Claude 2.1", "GPT-4"]
  }
];

const initialAccentColors: Record<string, string> = {
  cherry: '#ff69b4',
  sophia: '#2196f3', // User-specified accent color
  karen: '#4caf50',   // User-specified accent color
};

// Create the Zustand store
export const usePersonaStore = create<PersonaStoreState>((set, get) => ({
  personas: initialPersonas,
  currentPersonaId: 'cherry',
  accentColors: initialAccentColors,

  setPersona: (personaId: string) => set({ currentPersonaId: personaId }),

  getPersonaById: (id: string) => {
    return get().personas.find(p => p.id === id);
  },

  getCurrentPersona: () => {
    const currentId = get().currentPersonaId;
    return get().personas.find(p => p.id === currentId);
  },

  getCurrentDomain: () => {
    const currentPersona = get().getCurrentPersona();
    return currentPersona?.domain;
  },

  getCurrentAccentColor: () => {
    const currentId = get().currentPersonaId;
    return get().accentColors[currentId];
  },
}));

export default usePersonaStore;
