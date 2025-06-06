import { useState } from 'react'

const PersonaSelection = ({ onPersonaSelect, currentPersona }) => {
  const [hoveredPersona, setHoveredPersona] = useState(null)

  const personas = [
    {
      id: 'cherry',
      name: 'Cherry',
      icon: '🍒',
      color: '#ff4757',
      description: 'Personal life assistant focused on health, wellness, and creative exploration',
      features: ['Health & Wellness', 'Creative Projects', 'Personal Growth', 'Relationship Management'],
      stats: { agents: 8, projects: 12, health: 'Optimal' }
    },
    {
      id: 'sophia',
      name: 'Sophia',
      icon: '💼',
      color: '#8b4513',
      description: 'Business & professional assistant for real estate, finance, and career development',
      features: ['Real Estate Analysis', 'Financial Planning', 'Market Research', 'Career Development'],
      stats: { agents: 10, projects: 8, health: 'Optimal' }
    },
    {
      id: 'karen',
      name: 'Karen',
      icon: '🏥',
      color: '#dc143c',
      description: 'Healthcare operations supervisor for medical data and clinical operations',
      features: ['Medical Data Analysis', 'Clinical Operations', 'Compliance Monitoring', 'Research Support'],
      stats: { agents: 6, projects: 5, health: 'Optimal' }
    }
  ]

  const handlePersonaSelect = (personaId) => {
    onPersonaSelect(personaId)
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6">
      <div className="text-center mb-12 fade-in">
        <h1 className="text-4xl font-bold mb-4">
          Welcome to <span style={{ color: '#ff4757' }}>Cherry AI Orchestrator</span>
        </h1>
        <p className="text-xl text-secondary max-w-2xl mx-auto">
          Choose your AI persona to access personalized tools, agents, and workflows tailored to your specific needs.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl w-full">
        {personas.map((persona, index) => (
          <div
            key={persona.id}
            className={`card cursor-pointer transition-all duration-300 ${
              currentPersona === persona.id ? 'ring-2 ring-cherry-red' : ''
            } ${hoveredPersona === persona.id ? 'scale-105' : ''}`}
            style={{
              borderColor: hoveredPersona === persona.id ? persona.color : 'var(--border-color)',
              animationDelay: `${index * 0.1}s`
            }}
            onMouseEnter={() => setHoveredPersona(persona.id)}
            onMouseLeave={() => setHoveredPersona(null)}
            onClick={() => handlePersonaSelect(persona.id)}
          >
            {/* Persona Header */}
            <div className="text-center mb-6">
              <div 
                className="w-20 h-20 mx-auto mb-4 rounded-full flex items-center justify-center text-4xl"
                style={{ 
                  backgroundColor: `${persona.color}20`,
                  border: `2px solid ${persona.color}`
                }}
              >
                {persona.icon}
              </div>
              <h2 className="text-2xl font-bold mb-2" style={{ color: persona.color }}>
                {persona.name}
              </h2>
              <p className="text-secondary text-sm leading-relaxed">
                {persona.description}
              </p>
            </div>

            {/* Features */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold mb-3 text-primary">Key Features</h3>
              <div className="space-y-2">
                {persona.features.map((feature, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <div 
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: persona.color }}
                    ></div>
                    <span className="text-sm text-secondary">{feature}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Stats */}
            <div className="border-t border-color pt-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-lg font-bold" style={{ color: persona.color }}>
                    {persona.stats.agents}
                  </div>
                  <div className="text-xs text-secondary">Agents</div>
                </div>
                <div>
                  <div className="text-lg font-bold" style={{ color: persona.color }}>
                    {persona.stats.projects}
                  </div>
                  <div className="text-xs text-secondary">Projects</div>
                </div>
                <div>
                  <div className="text-lg font-bold text-success">
                    {persona.stats.health}
                  </div>
                  <div className="text-xs text-secondary">Health</div>
                </div>
              </div>
            </div>

            {/* Selection Indicator */}
            {currentPersona === persona.id && (
              <div className="absolute top-4 right-4">
                <div 
                  className="w-6 h-6 rounded-full flex items-center justify-center text-white text-sm"
                  style={{ backgroundColor: persona.color }}
                >
                  ✓
                </div>
              </div>
            )}

            {/* Hover Effect */}
            {hoveredPersona === persona.id && (
              <div className="absolute inset-0 rounded-lg pointer-events-none">
                <div 
                  className="absolute inset-0 rounded-lg opacity-10"
                  style={{ backgroundColor: persona.color }}
                ></div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="mt-12 flex gap-4">
        {currentPersona && (
          <button
            onClick={() => handlePersonaSelect(currentPersona)}
            className="btn btn-primary px-8 py-3 text-lg"
          >
            Continue with {personas.find(p => p.id === currentPersona)?.name}
          </button>
        )}
        
        <button
          onClick={() => window.location.href = '/health'}
          className="btn btn-secondary px-6 py-3"
        >
          System Overview
        </button>
      </div>

      {/* Quick Stats */}
      <div className="mt-8 grid grid-cols-3 gap-8 text-center">
        <div>
          <div className="text-2xl font-bold text-cherry-red">24</div>
          <div className="text-sm text-secondary">Total Active Agents</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-cherry-red">1,247</div>
          <div className="text-sm text-secondary">API Requests Today</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-success">98.5%</div>
          <div className="text-sm text-secondary">System Health</div>
        </div>
      </div>
    </div>
  )
}

export default PersonaSelection

