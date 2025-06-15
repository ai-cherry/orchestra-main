import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Music, 
  MessageSquare, 
  LayoutDashboard, 
  Bot, 
  Activity,
  Brain,
  Palette,
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
  { name: 'Personas', href: '/personas', icon: Brain },
  { name: 'Creative Studio', href: '/creative', icon: Palette },
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

      {/* Quick Actions */}
      {!collapsed && (
        <div className="p-4 border-t border-sidebar-border">
          <h3 className="text-sm font-semibold text-sidebar-foreground/60 uppercase tracking-wider mb-4">
            Quick Actions
          </h3>
          
          <div className="space-y-2">
            <button className="w-full text-left px-3 py-2 rounded-lg text-sm text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors">
              New Chat Session
            </button>
            <button className="w-full text-left px-3 py-2 rounded-lg text-sm text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors">
              View Search History
            </button>
            <button className="w-full text-left px-3 py-2 rounded-lg text-sm text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors">
              Export Conversations
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

