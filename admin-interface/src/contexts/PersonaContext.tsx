import React, { createContext, useState, useContext, useMemo } from 'react';

// 1. Define Persona and Theme Structures
const personas = {
  cherry: {
    id: 'cherry',
    name: 'Cherry',
    icon: '🍒',
    theme: {
      primary: '#D92626', // A real red
      secondary: '#F15A5A',
      background: 'rgba(217, 38, 38, 0.1)',
      border: 'rgba(217, 38, 38, 0.3)',
      text: '#F15A5A'
    }
  },
  sophia: {
    id: 'sophia',
    name: 'Sophia',
    icon: '💼',
    theme: {
      primary: '#3B82F6',
      secondary: '#60A5FA',
      background: 'rgba(59, 130, 246, 0.1)',
      border: 'rgba(59, 130, 246, 0.3)',
      text: '#60A5FA'
    }
  },
  karen: {
    id: 'karen',
    name: 'Karen',
    icon: '🔬',
    theme: {
      primary: '#10B981',
      secondary: '#34D399',
      background: 'rgba(16, 185, 129, 0.1)',
      border: 'rgba(16, 185, 129, 0.3)',
      text: '#34D399'
    }
  },
  master: {
    id: 'master',
    name: 'Master',
    icon: '⚡',
    theme: {
      primary: '#F59E0B',
      secondary: '#FBBF24',
      background: 'rgba(245, 158, 11, 0.1)',
      border: 'rgba(245, 158, 11, 0.3)',
      text: '#FBBF24'
    }
  }
};

// 2. Create the Context
const PersonaContext = createContext({
  personas: {},
  activePersona: 'cherry',
  currentPersona: personas.cherry,
  setActivePersona: (personaId: string) => {},
});

// 3. Create the Provider Component
export const PersonaProvider = ({ children }) => {
  const [activePersona, setActivePersona] = useState('cherry');

  const currentPersona = useMemo(() => personas[activePersona], [activePersona]);

  const value = {
    personas,
    activePersona,
    currentPersona,
    setActivePersona,
  };

  return (
    <PersonaContext.Provider value={value}>
      {children}
    </PersonaContext.Provider>
  );
};

// 4. Create a custom hook for easy consumption
export const usePersona = () => {
  const context = useContext(PersonaContext);
  if (context === undefined) {
    throw new Error('usePersona must be used within a PersonaProvider');
  }
  return context;
}; 