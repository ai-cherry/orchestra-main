import React from 'react';
import { Persona } from './HomePage';

interface PersonaSelectorProps {
  personas: Persona[];
  activePersona: string;
  onPersonaChange: (personaId: string) => void;
}

export const PersonaSelector: React.FC<PersonaSelectorProps> = ({
  personas,
  activePersona,
  onPersonaChange,
}) => {
  const getPersonaCardClasses = (persona: Persona, isActive: boolean) => {
    const baseClasses = "relative group cursor-pointer rounded-2xl p-6 transition-all duration-300 backdrop-blur-lg border-2 transform hover:scale-105 hover:shadow-card-hover";
    
    if (isActive) {
      switch (persona.color) {
        case 'cherry':
          return `${baseClasses} bg-cherry-500/20 border-cherry-500 shadow-glow-cherry`;
        case 'sophia':
          return `${baseClasses} bg-sophia-500/20 border-sophia-500 shadow-glow-sophia`;
        case 'karen':
          return `${baseClasses} bg-karen-500/20 border-karen-500 shadow-glow-karen`;
        default:
          return `${baseClasses} bg-white/20 border-white/40`;
      }
    }
    
    return `${baseClasses} bg-white/10 border-white/20 hover:border-white/40`;
  };

  const getPersonaGradient = (persona: Persona) => {
    switch (persona.color) {
      case 'cherry':
        return 'from-cherry-400 to-cherry-600';
      case 'sophia':
        return 'from-sophia-400 to-sophia-600';
      case 'karen':
        return 'from-karen-400 to-karen-600';
      default:
        return 'from-blue-400 to-blue-600';
    }
  };

  const getPersonaIconClasses = (persona: Persona, isActive: boolean) => {
    const baseClasses = "text-6xl mb-4 transition-transform duration-300 group-hover:scale-110";
    
    if (isActive) {
      return `${baseClasses} animate-bounce-slow`;
    }
    
    return baseClasses;
  };

  return (
    <div className="w-full">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Choose Your AI Orchestrator</h2>
        <p className="text-white/70 text-lg">Each persona brings unique capabilities and personality</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
        {personas.map((persona) => {
          const isActive = activePersona === persona.id;
          
          return (
            <div
              key={persona.id}
              onClick={() => onPersonaChange(persona.id)}
              className={getPersonaCardClasses(persona, isActive)}
              role="button"
              tabIndex={0}
              aria-pressed={isActive}
              aria-label={`Select ${persona.name} persona`}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onPersonaChange(persona.id);
                }
              }}
            >
              {/* Active indicator */}
              {isActive && (
                <div className="absolute -top-2 -right-2 w-6 h-6 bg-white rounded-full flex items-center justify-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                </div>
              )}
              
              {/* Persona Icon */}
              <div className="text-center">
                <div className={getPersonaIconClasses(persona, isActive)}>
                  {persona.icon}
                </div>
                
                {/* Persona Name */}
                <h3 className={`text-2xl font-bold mb-3 bg-gradient-to-r ${getPersonaGradient(persona)} bg-clip-text text-transparent`}>
                  {persona.name}
                </h3>
                
                {/* Persona Description */}
                <p className="text-white/80 text-sm leading-relaxed mb-4">
                  {persona.description}
                </p>
                
                {/* Persona Features */}
                <div className="space-y-2 text-xs">
                  {persona.id === 'cherry' && (
                    <>
                      <div className="flex items-center justify-center gap-2 text-white/60">
                        <span>🎨</span>
                        <span>Creative & Artistic</span>
                      </div>
                      <div className="flex items-center justify-center gap-2 text-white/60">
                        <span>💭</span>
                        <span>Personal Assistant</span>
                      </div>
                      <div className="flex items-center justify-center gap-2 text-white/60">
                        <span>🌟</span>
                        <span>Playful & Engaging</span>
                      </div>
                    </>
                  )}
                  
                  {persona.id === 'sophia' && (
                    <>
                      <div className="flex items-center justify-center gap-2 text-white/60">
                        <span>📊</span>
                        <span>Business Analytics</span>
                      </div>
                      <div className="flex items-center justify-center gap-2 text-white/60">
                        <span>💰</span>
                        <span>Payment Solutions</span>
                      </div>
                      <div className="flex items-center justify-center gap-2 text-white/60">
                        <span>🎯</span>
                        <span>Strategic Planning</span>
                      </div>
                    </>
                  )}
                  
                  {persona.id === 'karen' && (
                    <>
                      <div className="flex items-center justify-center gap-2 text-white/60">
                        <span>🔬</span>
                        <span>Clinical Research</span>
                      </div>
                      <div className="flex items-center justify-center gap-2 text-white/60">
                        <span>📋</span>
                        <span>HIPAA Compliant</span>
                      </div>
                      <div className="flex items-center justify-center gap-2 text-white/60">
                        <span>🏥</span>
                        <span>Healthcare Focus</span>
                      </div>
                    </>
                  )}
                </div>
                
                {/* Active State Button */}
                {isActive ? (
                  <div className={`mt-4 px-4 py-2 rounded-lg bg-gradient-to-r ${getPersonaGradient(persona)} text-white font-semibold text-sm`}>
                    ✓ Active
                  </div>
                ) : (
                  <div className="mt-4 px-4 py-2 rounded-lg bg-white/10 text-white/80 font-semibold text-sm group-hover:bg-white/20 transition-colors">
                    Select
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Current Selection Info */}
      <div className="mt-6 text-center">
        <div className="inline-flex items-center gap-3 px-6 py-3 bg-white/10 backdrop-blur-lg rounded-full border border-white/20">
          <span className="text-white/70">Currently active:</span>
          <span className="font-semibold text-white">
            {personas.find(p => p.id === activePersona)?.icon} {personas.find(p => p.id === activePersona)?.name}
          </span>
        </div>
      </div>
    </div>
  );
}; 