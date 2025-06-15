import { useState } from 'react'
import { Settings, Search, Bell, User, ChevronDown } from 'lucide-react'
import { Link } from 'react-router-dom'

const personas = [
  { id: 'cherry', name: 'Cherry', emoji: '🍒', subtitle: 'Personal Assistant' },
  { id: 'sophia', name: 'Sophia', emoji: '💼', subtitle: 'Pay Ready' },
  { id: 'karen', name: 'Karen', emoji: '🏥', subtitle: 'ParagonRX' }
]

export default function TopNav({ activePersona, onPersonaChange }) {
  const [showPersonaMenu, setShowPersonaMenu] = useState(false)
  const currentPersona = personas.find(p => p.id === activePersona) || personas[0]

  return (
    <div className="fixed top-0 left-0 right-0 h-16 bg-gray-900 border-b border-gray-800 z-50">
      <div className="flex items-center justify-between h-full px-6">
        {/* Left Section - Logo and Title */}
        <div className="flex items-center space-x-4">
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">OA</span>
            </div>
            <h1 className="text-xl font-bold text-white">Orchestra AI</h1>
          </Link>
        </div>

        {/* Center Section - Search Bar */}
        <div className="flex-1 max-w-2xl mx-8">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Quick search..."
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Right Section - Persona Selector and Actions */}
        <div className="flex items-center space-x-4">
          {/* Persona Selector */}
          <div className="relative">
            <button
              onClick={() => setShowPersonaMenu(!showPersonaMenu)}
              className="flex items-center space-x-2 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 hover:bg-gray-700 transition-colors"
            >
              <span className="text-2xl">{currentPersona.emoji}</span>
              <div className="text-left">
                <div className="text-sm font-medium text-white">{currentPersona.name}</div>
                <div className="text-xs text-gray-400">{currentPersona.subtitle}</div>
              </div>
              <ChevronDown className="w-4 h-4 text-gray-400" />
            </button>

            {/* Persona Dropdown Menu */}
            {showPersonaMenu && (
              <div className="absolute right-0 mt-2 w-56 bg-gray-800 border border-gray-700 rounded-lg shadow-lg overflow-hidden">
                {personas.map((persona) => (
                  <button
                    key={persona.id}
                    onClick={() => {
                      onPersonaChange(persona.id)
                      setShowPersonaMenu(false)
                    }}
                    className={`w-full flex items-center space-x-3 px-4 py-3 hover:bg-gray-700 transition-colors ${
                      activePersona === persona.id ? 'bg-gray-700' : ''
                    }`}
                  >
                    <span className="text-2xl">{persona.emoji}</span>
                    <div className="text-left flex-1">
                      <div className="text-sm font-medium text-white">{persona.name}</div>
                      <div className="text-xs text-gray-400">{persona.subtitle}</div>
                    </div>
                    {activePersona === persona.id && (
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Notifications */}
          <button className="p-2 hover:bg-gray-800 rounded-lg transition-colors relative">
            <Bell className="w-5 h-5 text-gray-400" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          {/* Settings */}
          <Link 
            to="/settings/search" 
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            title="Search Settings"
          >
            <Settings className="w-5 h-5 text-gray-400" />
          </Link>

          {/* User Menu */}
          <button className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
            <User className="w-5 h-5 text-gray-400" />
          </button>
        </div>
      </div>
    </div>
  )
} 