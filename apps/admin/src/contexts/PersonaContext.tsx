import React, { createContext, useContext, useState, ReactNode } from 'react';

interface PersonaTheme {
  primary: string;
  secondary: string;
  background: string;
  border: string;
  text: string;
}

interface Persona {
  id: 'sophia' | 'karen' | 'cherry';
  name: string;
  role: string;
  icon: string;
  description: string;
  theme: PersonaTheme;
  model: string;
  searchBias: string[];
  capabilities: string[];
}

interface PersonaContextType {
  currentPersona: Persona;
  personas: Record<string, Persona>;
  switchPersona: (personaId: 'sophia' | 'karen' | 'cherry') => void;
  chatHistory: Record<string, any[]>;
}

const personas: Record<string, Persona> = {
  sophia: {
    id: 'sophia',
    name: 'Sophia',
    role: 'Business Intelligence',
    icon: '💼',
    description: 'Expert in apartment technology, fintech, and business analysis',
    theme: {
      primary: '#3B82F6',
      secondary: '#60A5FA',
      background: 'rgba(59, 130, 246, 0.1)',
      border: 'rgba(59, 130, 246, 0.3)',
      text: '#60A5FA'
    },
    model: 'claude-3-5-sonnet-20241022',
    searchBias: ['market analysis', 'business metrics', 'apartment technology', 'fintech', 'proptech'],
    capabilities: ['presentations', 'market reports', 'competitive analysis', 'business proposals']
  },
  karen: {
    id: 'karen',
    name: 'Karen',
    role: 'Clinical Research',
    icon: '🔬',
    description: 'Specialist in pharmaceutical research and clinical studies',
    theme: {
      primary: '#10B981',
      secondary: '#34D399',
      background: 'rgba(16, 185, 129, 0.1)',
      border: 'rgba(16, 185, 129, 0.3)',
      text: '#34D399'
    },
    model: 'claude-3-opus-20240229',
    searchBias: ['clinical trials', 'pharmaceutical research', 'medical literature', 'FDA compliance'],
    capabilities: ['research reports', 'study protocols', 'literature reviews', 'data analysis']
  },
  cherry: {
    id: 'cherry',
    name: 'Cherry',
    role: 'Creative Assistant',
    icon: '🌟',
    description: 'Creative powerhouse for content generation and artistic projects',
    theme: {
      primary: '#F59E0B',
      secondary: '#FBBF24',
      background: 'rgba(245, 158, 11, 0.1)',
      border: 'rgba(245, 158, 11, 0.3)',
      text: '#FBBF24'
    },
    model: 'gpt-4-turbo',
    searchBias: ['creative inspiration', 'design trends', 'innovation', 'artistic techniques'],
    capabilities: ['songs', 'images', 'videos', 'stories', 'creative writing']
  }
};

const PersonaContext = createContext<PersonaContextType | undefined>(undefined);

export const PersonaProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentPersonaId, setCurrentPersonaId] = useState<'sophia' | 'karen' | 'cherry'>('sophia');
  const [chatHistory, setChatHistory] = useState<Record<string, any[]>>({
    sophia: [],
    karen: [],
    cherry: []
  });

  const switchPersona = (personaId: 'sophia' | 'karen' | 'cherry') => {
    setCurrentPersonaId(personaId);
  };

  const currentPersona = personas[currentPersonaId];

  return (
    <PersonaContext.Provider value={{
      currentPersona,
      personas,
      switchPersona,
      chatHistory
    }}>
      {children}
    </PersonaContext.Provider>
  );
};

export const usePersona = () => {
  const context = useContext(PersonaContext);
  if (context === undefined) {
    throw new Error('usePersona must be used within a PersonaProvider');
  }
  return context;
};

