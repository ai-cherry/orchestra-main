import React from 'react'
import { NavLink } from 'react-router-dom'
import { 
  MessageSquare, 
  BarChart3, 
  Bot, 
  Activity, 
  Database,
  Home,
  Settings,
  HelpCircle
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { usePersona } from '@/contexts/PersonaContext'

interface NavItemProps {
  to: string
  icon: React.ElementType
  label: string
  badge?: string
}

function NavItem({ to, icon: Icon, label, badge }: NavItemProps) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200',
          'hover:bg-accent hover:text-accent-foreground',
          isActive 
            ? 'bg-primary text-primary-foreground' 
            : 'text-muted-foreground'
        )
      }
    >
      <Icon className="w-4 h-4" />
      <span>{label}</span>
      {badge && (
        <span className="ml-auto px-2 py-0.5 bg-primary text-primary-foreground text-xs rounded-full">
          {badge}
        </span>
      )}
    </NavLink>
  )
}

function PersonaSelector() {
  const { currentPersona, setCurrentPersona, personaConfig } = usePersona()

  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
        AI Personas
      </h3>
      <div className="space-y-1">
        {Object.entries(personaConfig).map(([key, config]) => (
          <button
            key={key}
            onClick={() => setCurrentPersona(key as any)}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200',
              'hover:bg-accent hover:text-accent-foreground',
              currentPersona === key
                ? `bg-${config.color}-600 text-white` 
                : 'text-muted-foreground'
            )}
          >
            <div className={cn(
              'w-2 h-2 rounded-full',
              `bg-${config.color}-500`
            )} />
            <span>{config.name}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

export function Sidebar() {
  return (
    <div className="w-64 bg-card border-r border-border flex flex-col">
      <div className="p-6">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-sm">🎼</span>
          </div>
          <div>
            <h1 className="font-bold text-lg">Orchestra AI</h1>
            <p className="text-xs text-muted-foreground">Admin Interface</p>
          </div>
        </div>

        <nav className="space-y-1">
          <NavItem to="/" icon={Home} label="Home" />
          <NavItem to="/chat" icon={MessageSquare} label="Chat" />
          <NavItem to="/dashboard" icon={BarChart3} label="Dashboard" />
          <NavItem to="/agent-factory" icon={Bot} label="Agent Factory" />
          <NavItem to="/data-integration" icon={Database} label="Data Integration" badge="New" />
          <NavItem to="/system-monitor" icon={Activity} label="System Monitor" />
        </nav>
      </div>

      <div className="p-6 border-t border-border">
        <PersonaSelector />
      </div>

      <div className="mt-auto p-6 border-t border-border">
        <nav className="space-y-1">
          <NavItem to="/settings" icon={Settings} label="Settings" />
          <NavItem to="/help" icon={HelpCircle} label="Help" />
        </nav>
      </div>
    </div>
  )
} 