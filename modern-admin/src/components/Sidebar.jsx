import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Music, 
  MessageSquare, 
  LayoutDashboard, 
  Bot, 
  Activity,
  ChevronLeft,
  ChevronRight,
  Circle
} from 'lucide-react'

const personas = [
  {
    id: 'cherry',
    name: 'Cherry',
    description: 'Creative AI specialized in content creation, design, and innovation',
    color: 'cherry',
    gradient: 'cherry-gradient',
    status: 'available'
  },
  {
    id: 'sophia',
    name: 'Sophia',
    description: 'Strategic AI focused on analysis, planning, and complex problem-solving',
    color: 'sophia',
    gradient: 'sophia-gradient',
    status: 'active'
  },
  {
    id: 'karen',
    name: 'Karen',
    description: 'Operational AI focused on execution, automation, and workflow management',
    color: 'karen',
    gradient: 'karen-gradient',
    status: 'available'
  }
]

const navigation = [
  { name: 'Chat', href: '/', icon: MessageSquare },
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Agent Factory', href: '/agent-factory', icon: Bot },
  { name: 'System Monitor', href: '/system-monitor', icon: Activity },
]

export default function Sidebar({ collapsed, onToggle, activePersona, onPersonaChange }) {
  const location = useLocation()

  return (
    <div className={`fixed left-0 top-0 h-full bg-sidebar border-r border-sidebar-border transition-all duration-300 z-50 ${
      collapsed ? 'w-16' : 'w-80'
    }`}>
      {/* Header */}
      <div className="p-6 border-b border-sidebar-border">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <Music className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-sidebar-foreground">Orchestra AI</h1>
                <p className="text-sm text-sidebar-foreground/60">Admin Interface</p>
              </div>
            </div>
          )}
          
          <button
            onClick={onToggle}
            className="p-2 rounded-lg hover:bg-sidebar-accent transition-colors"
          >
            {collapsed ? (
              <ChevronRight className="w-4 h-4 text-sidebar-foreground" />
            ) : (
              <ChevronLeft className="w-4 h-4 text-sidebar-foreground" />
            )}
          </button>
        </div>
        
        {!collapsed && (
          <div className="mt-4 flex items-center gap-2 text-sm text-sidebar-foreground/60">
            <Circle className="w-2 h-2 fill-green-500 text-green-500 animate-pulse-slow" />
            4 agents active
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="p-4">
        <div className="space-y-2">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 group ${
                  isActive
                    ? 'bg-sidebar-primary text-sidebar-primary-foreground shadow-lg'
                    : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
                }`}
              >
                <item.icon className={`w-5 h-5 ${isActive ? 'text-sidebar-primary-foreground' : 'text-sidebar-foreground/60 group-hover:text-sidebar-accent-foreground'}`} />
                {!collapsed && (
                  <span className="font-medium">{item.name}</span>
                )}
              </Link>
            )
          })}
        </div>
      </nav>

      {/* Personas */}
      {!collapsed && (
        <div className="p-4 border-t border-sidebar-border">
          <h3 className="text-sm font-semibold text-sidebar-foreground/60 uppercase tracking-wider mb-4">
            AI Personas
          </h3>
          
          <div className="space-y-3">
            {personas.map((persona) => (
              <button
                key={persona.id}
                onClick={() => onPersonaChange(persona.id)}
                className={`w-full p-4 rounded-xl border transition-all duration-200 text-left group ${
                  activePersona === persona.id
                    ? 'border-sidebar-primary bg-sidebar-primary/10 shadow-lg'
                    : 'border-sidebar-border hover:border-sidebar-primary/50 hover:bg-sidebar-accent/50'
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold ${persona.gradient}`}>
                    {persona.name[0]}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-sidebar-foreground">{persona.name}</h4>
                      <div className={`w-2 h-2 rounded-full ${
                        persona.status === 'active' ? 'bg-green-500' : 'bg-gray-400'
                      }`} />
                    </div>
                    <p className="text-xs text-sidebar-foreground/60 capitalize">{persona.status}</p>
                  </div>
                </div>
                
                <p className="text-sm text-sidebar-foreground/70 leading-relaxed">
                  {persona.description}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

