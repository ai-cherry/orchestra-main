"use client"

import { useState } from "react"
import { ChevronDown, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { usePersona, getPersonaIcon, getPersonaColor, type Persona } from "@/hooks/usePersona"

export function PersonaSelector() {
  const { activePersona, personaStates, setActivePersona } = usePersona()
  const [isOpen, setIsOpen] = useState(false)

  const personas: { id: Persona; name: string; description: string }[] = [
    {
      id: 'cherry',
      name: 'Cherry',
      description: 'Creative & Finance Focus'
    },
    {
      id: 'sophia',
      name: 'Sophia',
      description: 'Business Intelligence'
    },
    {
      id: 'karen',
      name: 'Karen',
      description: 'Healthcare & Research'
    },
    {
      id: 'master',
      name: 'Master',
      description: 'All-Domain Orchestrator'
    }
  ]

  const currentPersona = personas.find(p => p.id === activePersona)
  const currentPersonaState = personaStates[activePersona]

  const getPersonaButtonClasses = (persona: Persona) => {
    const color = getPersonaColor(persona)
    switch (color) {
      case 'red':
        return 'bg-red-600 hover:bg-red-700 text-white'
      case 'blue':
        return 'bg-blue-600 hover:bg-blue-700 text-white'
      case 'emerald':
        return 'bg-emerald-600 hover:bg-emerald-700 text-white'
      case 'yellow':
        return 'bg-yellow-600 hover:bg-yellow-700 text-white'
      default:
        return 'bg-gray-600 hover:bg-gray-700 text-white'
    }
  }

  const getPersonaBadgeClasses = (persona: Persona) => {
    const color = getPersonaColor(persona)
    switch (color) {
      case 'red':
        return 'bg-red-500/20 text-red-400 border-red-500/50'
      case 'blue':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/50'
      case 'emerald':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50'
      case 'yellow':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/50'
    }
  }

  const handlePersonaSelect = (persona: Persona) => {
    setActivePersona(persona)
    setIsOpen(false)
  }

  return (
    <div className="relative">
      <Button
        onClick={() => setIsOpen(!isOpen)}
        className={`${getPersonaButtonClasses(activePersona)} px-4 py-2 rounded-lg font-medium focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 transition-all duration-200 min-w-[200px] justify-between`}
      >
        <div className="flex items-center space-x-3">
          <span className="text-lg">{getPersonaIcon(activePersona)}</span>
          <div className="text-left">
            <div className="font-semibold">{currentPersona?.name}</div>
            <div className="text-xs opacity-90">{currentPersona?.description}</div>
          </div>
        </div>
        <ChevronDown 
          size={16} 
          className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} 
        />
      </Button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown */}
          <div className="absolute top-full right-0 mt-2 w-80 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl z-50 overflow-hidden">
            <div className="p-4 border-b border-gray-700">
              <h3 className="text-white font-semibold text-sm">Select Persona</h3>
              <p className="text-gray-400 text-xs mt-1">Switch between different AI personalities</p>
            </div>
            
            <div className="max-h-80 overflow-y-auto">
              {personas.map((persona) => {
                const personaState = personaStates[persona.id]
                const isActive = persona.id === activePersona
                
                return (
                  <button
                    key={persona.id}
                    onClick={() => handlePersonaSelect(persona.id)}
                    className={`w-full p-4 text-left hover:bg-gray-800/50 transition-all duration-200 group ${
                      isActive ? 'bg-gray-800/70' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="text-2xl group-hover:scale-110 transition-transform duration-200">
                          {getPersonaIcon(persona.id)}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-white font-medium">{persona.name}</span>
                            {isActive && <Check size={14} className="text-green-400" />}
                          </div>
                          <div className="text-gray-400 text-sm">{persona.description}</div>
                          <div className="flex items-center space-x-2 mt-2">
                            <Badge className={`${getPersonaBadgeClasses(persona.id)} text-xs px-2 py-1`}>
                              {personaState.metrics.activeAgents} agents
                            </Badge>
                            <Badge className="bg-gray-700/50 text-gray-300 text-xs px-2 py-1">
                              {personaState.metrics.searches} searches
                            </Badge>
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="text-xs text-gray-400">
                          {personaState.metrics.dataFiles} files
                        </div>
                        <div className="text-xs text-gray-400">
                          {personaState.metrics.businessTools} tools
                        </div>
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
            
            <div className="p-4 border-t border-gray-700 bg-gray-800/50">
              <div className="text-xs text-gray-400">
                Current: <span className="text-white font-medium">{currentPersona?.name}</span>
                {' • '}
                Last Activity: {currentPersonaState.metrics.lastActivity.toLocaleTimeString()}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
} 