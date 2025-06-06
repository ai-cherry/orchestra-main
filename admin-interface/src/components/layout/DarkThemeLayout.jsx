import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const DarkThemeLayout = ({ children, selectedPersona, systemStatus, onPersonaChange }) => {
  const navigate = useNavigate()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const navigationItems = [
    { 
      id: 'search', 
      label: 'Search', 
      icon: '🔍', 
      path: '/search',
      description: 'Multi-modal search & creation'
    },
    { 
      id: 'agents', 
      label: 'Agent Factory', 
      icon: '🏭', 
      path: '/agents',
      description: 'Manage AI agents'
    },
    { 
      id: 'supervisors', 
      label: 'Supervisor Factory', 
      icon: '👑', 
      path: '/supervisors',
      description: 'Agent supervisors & teams'
    },
    { 
      id: 'projects', 
      label: 'Projects', 
      icon: '📋', 
      path: '/projects',
      description: 'Project management & todos'
    },
    { 
      id: 'health', 
      label: 'System Health', 
      icon: '⚡', 
      path: '/health',
      description: 'API & integration status'
    }
  ]

  const personas = {
    cherry: {
      name: 'Cherry',
      icon: '🍒',
      color: '#ff4757',
      description: 'Personal life assistant focused on health, wellness, and creative exploration'
    },
    sophia: {
      name: 'Sophia',
      icon: '💼',
      color: '#8b4513',
      description: 'Business & professional assistant for real estate, finance, and career development'
    },
    karen: {
      name: 'Karen',
      icon: '🏥',
      color: '#dc143c',
      description: 'Healthcare operations supervisor for medical data and clinical operations'
    }
  }

  const handleNavigation = (path) => {
    navigate(path)
  }

  const handlePersonaSelect = (personaId) => {
    onPersonaChange(personaId)
    navigate('/search') // Always go to search when selecting persona
  }

  return (
    <div className="min-h-screen bg-primary flex">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-secondary border-b border-color h-16 flex items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🍒</span>
            <h1 className="text-xl font-bold text-primary">Cherry AI Orchestrator</h1>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {/* System Status */}
          <div className="flex items-center gap-3">
            <div className={`status-indicator ${systemStatus.apiConnected ? 'status-connected' : 'status-disconnected'}`}>
              <div className="w-2 h-2 rounded-full bg-current"></div>
              {systemStatus.apiConnected ? 'API Connected' : 'Disconnected'}
            </div>
            
            {selectedPersona && (
              <div className="flex items-center gap-2 px-3 py-1 bg-tertiary rounded-lg">
                <span>{personas[selectedPersona]?.icon}</span>
                <span className="font-medium">{personas[selectedPersona]?.name}</span>
              </div>
            )}
            
            <div className="text-sm text-secondary">
              {systemStatus.activeSessions} Active Sessions
            </div>
          </div>
          
          {/* Persona Selector */}
          <button 
            onClick={() => navigate('/personas')}
            className="btn btn-ghost"
          >
            Switch Persona
          </button>
        </div>
      </header>

      {/* Sidebar Navigation */}
      <aside className={`fixed left-0 top-16 bottom-0 bg-secondary border-r border-color transition-all duration-300 z-40 ${
        sidebarCollapsed ? 'w-16' : 'w-64'
      }`}>
        <div className="p-4">
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="w-full btn btn-ghost mb-4"
          >
            {sidebarCollapsed ? '→' : '←'}
          </button>
          
          <nav className="space-y-2">
            {navigationItems.map((item) => (
              <button
                key={item.id}
                onClick={() => handleNavigation(item.path)}
                className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all hover:bg-tertiary ${
                  window.location.pathname === item.path ? 'bg-tertiary border-l-4 border-cherry-red' : ''
                }`}
              >
                <span className="text-lg">{item.icon}</span>
                {!sidebarCollapsed && (
                  <div className="flex-1 text-left">
                    <div className="font-medium text-primary">{item.label}</div>
                    <div className="text-xs text-secondary">{item.description}</div>
                  </div>
                )}
              </button>
            ))}
          </nav>
        </div>
        
        {/* System Overview */}
        {!sidebarCollapsed && (
          <div className="absolute bottom-4 left-4 right-4">
            <div className="card p-4">
              <h3 className="text-sm font-semibold mb-3">System Overview</h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-secondary">Active Agents</span>
                  <span className="text-sm font-bold text-cherry-red">{systemStatus.activeAgents}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-secondary">API Requests</span>
                  <span className="text-sm font-bold text-cherry-red">{systemStatus.apiRequests.toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-secondary">System Health</span>
                  <span className="text-sm font-bold text-success">{systemStatus.systemHealth}%</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </aside>

      {/* Main Content */}
      <main className={`flex-1 transition-all duration-300 ${
        sidebarCollapsed ? 'ml-16' : 'ml-64'
      } mt-16 p-6`}>
        <div className="max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}

export default DarkThemeLayout

