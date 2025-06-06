import { useState, useEffect } from 'react'

const SupervisorFactory = ({ persona, systemStatus }) => {
  const [supervisors, setSupervisors] = useState([])
  const [teams, setTeams] = useState([])
  const [selectedSupervisor, setSelectedSupervisor] = useState(null)
  const [viewMode, setViewMode] = useState('supervisors') // 'supervisors' or 'teams'

  const personas = {
    cherry: {
      name: 'Cherry',
      icon: '🍒',
      color: '#ff4757',
      supervisorTypes: [
        { id: 'health', name: 'Health Supervisor', icon: '🧘', description: 'Oversees wellness and health agents' },
        { id: 'creative', name: 'Creative Supervisor', icon: '🎨', description: 'Manages creative and artistic agents' },
        { id: 'personal', name: 'Personal Supervisor', icon: '💕', description: 'Coordinates personal life agents' }
      ]
    },
    sophia: {
      name: 'Sophia',
      icon: '💼',
      color: '#8b4513',
      supervisorTypes: [
        { id: 'business', name: 'Business Supervisor', icon: '📊', description: 'Oversees business analysis agents' },
        { id: 'financial', name: 'Financial Supervisor', icon: '💰', description: 'Manages financial planning agents' },
        { id: 'strategy', name: 'Strategy Supervisor', icon: '🎯', description: 'Coordinates strategic planning agents' }
      ]
    },
    karen: {
      name: 'Karen',
      icon: '🏥',
      color: '#dc143c',
      supervisorTypes: [
        { id: 'clinical', name: 'Clinical Supervisor', icon: '🔬', description: 'Oversees clinical research agents' },
        { id: 'compliance', name: 'Compliance Supervisor', icon: '📋', description: 'Manages compliance monitoring agents' },
        { id: 'operations', name: 'Operations Supervisor', icon: '⚙️', description: 'Coordinates operational agents' }
      ]
    }
  }

  const currentPersona = personas[persona] || personas.cherry

  // Mock supervisor data
  useEffect(() => {
    const mockSupervisors = [
      {
        id: 1,
        name: 'Health Supervisor Alpha',
        type: 'health',
        status: 'active',
        agentsManaged: 8,
        performance: 96,
        efficiency: 94,
        lastActive: new Date().toISOString(),
        responsibilities: ['Agent Coordination', 'Performance Monitoring', 'Task Distribution'],
        managedAgents: ['Wellness Coach Alpha', 'Nutrition Advisor Beta', 'Fitness Tracker Gamma']
      },
      {
        id: 2,
        name: 'Creative Supervisor Beta',
        type: 'creative',
        status: 'active',
        agentsManaged: 6,
        performance: 91,
        efficiency: 88,
        lastActive: new Date(Date.now() - 180000).toISOString(),
        responsibilities: ['Creative Direction', 'Quality Control', 'Innovation Management'],
        managedAgents: ['Creative Assistant Beta', 'Design Reviewer Delta', 'Content Creator Epsilon']
      },
      {
        id: 3,
        name: 'Personal Supervisor Gamma',
        type: 'personal',
        status: 'monitoring',
        agentsManaged: 4,
        performance: 89,
        efficiency: 92,
        lastActive: new Date(Date.now() - 300000).toISOString(),
        responsibilities: ['Relationship Management', 'Personal Growth', 'Life Optimization'],
        managedAgents: ['Relationship Manager Gamma', 'Lifestyle Optimizer Zeta']
      }
    ]
    setSupervisors(mockSupervisors)

    const mockTeams = [
      {
        id: 1,
        name: 'Wellness Team',
        supervisor: 'Health Supervisor Alpha',
        agents: 8,
        performance: 94,
        activeTasks: 23,
        completedToday: 15,
        focus: 'Health & Wellness Optimization'
      },
      {
        id: 2,
        name: 'Creative Team',
        supervisor: 'Creative Supervisor Beta',
        agents: 6,
        performance: 89,
        activeTasks: 18,
        completedToday: 12,
        focus: 'Creative Content & Design'
      }
    ]
    setTeams(mockTeams)
  }, [])

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return '#2ed573'
      case 'monitoring': return '#ffa502'
      case 'offline': return '#ff4757'
      default: return '#888888'
    }
  }

  const getPerformanceColor = (performance) => {
    if (performance >= 90) return '#2ed573'
    if (performance >= 70) return '#ffa502'
    return '#ff4757'
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <div 
            className="w-12 h-12 rounded-full flex items-center justify-center text-xl"
            style={{ 
              backgroundColor: `${currentPersona.color}20`,
              border: `2px solid ${currentPersona.color}`
            }}
          >
            👑
          </div>
          <div>
            <h1 className="text-3xl font-bold" style={{ color: currentPersona.color }}>
              {currentPersona.name} Supervisor Factory
            </h1>
            <p className="text-secondary">
              Manage supervisors and agent teams for {currentPersona.name}
            </p>
          </div>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={() => setViewMode(viewMode === 'supervisors' ? 'teams' : 'supervisors')}
            className="btn btn-secondary"
          >
            {viewMode === 'supervisors' ? '👥 View Teams' : '👑 View Supervisors'}
          </button>
          <button
            className="btn btn-primary"
            style={{ backgroundColor: currentPersona.color }}
          >
            👑 Create Supervisor
          </button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold" style={{ color: currentPersona.color }}>
                {supervisors.length}
              </div>
              <div className="text-sm text-secondary">Active Supervisors</div>
            </div>
            <div className="text-2xl">👑</div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold" style={{ color: currentPersona.color }}>
                {supervisors.reduce((sum, s) => sum + s.agentsManaged, 0)}
              </div>
              <div className="text-sm text-secondary">Managed Agents</div>
            </div>
            <div className="text-2xl">🤖</div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-success">
                {Math.round(supervisors.reduce((sum, s) => sum + s.performance, 0) / supervisors.length)}%
              </div>
              <div className="text-sm text-secondary">Avg Performance</div>
            </div>
            <div className="text-2xl">📈</div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-success">
                {Math.round(supervisors.reduce((sum, s) => sum + s.efficiency, 0) / supervisors.length)}%
              </div>
              <div className="text-sm text-secondary">Efficiency</div>
            </div>
            <div className="text-2xl">⚡</div>
          </div>
        </div>
      </div>

      {viewMode === 'supervisors' ? (
        /* Supervisors View */
        <div className="space-y-6">
          <h2 className="text-xl font-semibold">Active Supervisors</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {supervisors.map((supervisor) => {
              const supervisorType = currentPersona.supervisorTypes.find(t => t.id === supervisor.type)
              return (
                <div
                  key={supervisor.id}
                  className="card cursor-pointer hover:bg-tertiary transition-all"
                  onClick={() => setSelectedSupervisor(supervisor)}
                >
                  {/* Supervisor Header */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="text-2xl">{supervisorType?.icon || '👑'}</div>
                      <div>
                        <h3 className="font-semibold text-primary">{supervisor.name}</h3>
                        <p className="text-sm text-secondary">{supervisorType?.name}</p>
                      </div>
                    </div>
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: getStatusColor(supervisor.status) }}
                    ></div>
                  </div>

                  {/* Performance Metrics */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <div className="text-lg font-bold" style={{ color: currentPersona.color }}>
                        {supervisor.agentsManaged}
                      </div>
                      <div className="text-xs text-secondary">Agents Managed</div>
                    </div>
                    <div>
                      <div 
                        className="text-lg font-bold"
                        style={{ color: getPerformanceColor(supervisor.performance) }}
                      >
                        {supervisor.performance}%
                      </div>
                      <div className="text-xs text-secondary">Performance</div>
                    </div>
                  </div>

                  {/* Efficiency Bar */}
                  <div className="mb-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-secondary">Efficiency</span>
                      <span className="text-sm font-semibold text-success">
                        {supervisor.efficiency}%
                      </span>
                    </div>
                    <div className="w-full bg-tertiary rounded-full h-2">
                      <div 
                        className="h-2 rounded-full transition-all bg-success"
                        style={{ width: `${supervisor.efficiency}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Responsibilities */}
                  <div className="space-y-1">
                    {supervisor.responsibilities.slice(0, 2).map((responsibility, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <div 
                          className="w-1.5 h-1.5 rounded-full"
                          style={{ backgroundColor: currentPersona.color }}
                        ></div>
                        <span className="text-xs text-secondary">{responsibility}</span>
                      </div>
                    ))}
                    {supervisor.responsibilities.length > 2 && (
                      <div className="text-xs text-muted">
                        +{supervisor.responsibilities.length - 2} more responsibilities
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ) : (
        /* Teams View */
        <div className="space-y-6">
          <h2 className="text-xl font-semibold">Agent Teams</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {teams.map((team) => (
              <div key={team.id} className="card">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-semibold" style={{ color: currentPersona.color }}>
                      {team.name}
                    </h3>
                    <p className="text-sm text-secondary">Supervised by {team.supervisor}</p>
                  </div>
                  <div className="text-2xl">👥</div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold" style={{ color: currentPersona.color }}>
                      {team.agents}
                    </div>
                    <div className="text-xs text-secondary">Team Members</div>
                  </div>
                  <div className="text-center">
                    <div 
                      className="text-2xl font-bold"
                      style={{ color: getPerformanceColor(team.performance) }}
                    >
                      {team.performance}%
                    </div>
                    <div className="text-xs text-secondary">Team Performance</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-lg font-bold text-warning">
                      {team.activeTasks}
                    </div>
                    <div className="text-xs text-secondary">Active Tasks</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-success">
                      {team.completedToday}
                    </div>
                    <div className="text-xs text-secondary">Completed Today</div>
                  </div>
                </div>

                <div className="border-t border-color pt-4">
                  <div className="text-sm text-secondary mb-2">Team Focus:</div>
                  <div className="text-sm font-medium text-primary">{team.focus}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Supervisor Types */}
      <div className="card mt-8">
        <div className="card-header">
          <h3 className="card-title">Available Supervisor Types for {currentPersona.name}</h3>
          <p className="card-description">Specialized supervisors designed for {currentPersona.name}'s domain</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {currentPersona.supervisorTypes.map((type) => (
            <div key={type.id} className="p-4 border border-color rounded-lg hover:bg-tertiary transition-all">
              <div className="flex items-center gap-3 mb-2">
                <div className="text-xl">{type.icon}</div>
                <div>
                  <h4 className="font-semibold text-sm">{type.name}</h4>
                </div>
              </div>
              <p className="text-xs text-secondary mb-3">{type.description}</p>
              <button 
                className="text-xs px-3 py-1 rounded"
                style={{ 
                  backgroundColor: `${currentPersona.color}20`,
                  color: currentPersona.color
                }}
              >
                Create Supervisor
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default SupervisorFactory

