import { useState, useEffect } from 'react'

const AgentFactory = ({ persona, systemStatus }) => {
  const [agents, setAgents] = useState([])
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [showCreateAgent, setShowCreateAgent] = useState(false)
  const [agentFilter, setAgentFilter] = useState('all')

  const personas = {
    cherry: {
      name: 'Cherry',
      icon: '🍒',
      color: '#ff4757',
      agentTypes: [
        { id: 'wellness', name: 'Wellness Coach', icon: '🧘', description: 'Health and wellness guidance' },
        { id: 'creative', name: 'Creative Assistant', icon: '🎨', description: 'Creative project support' },
        { id: 'relationship', name: 'Relationship Manager', icon: '💕', description: 'Personal relationship insights' },
        { id: 'lifestyle', name: 'Lifestyle Optimizer', icon: '✨', description: 'Daily life optimization' }
      ]
    },
    sophia: {
      name: 'Sophia',
      icon: '💼',
      color: '#8b4513',
      agentTypes: [
        { id: 'analyst', name: 'Business Analyst', icon: '📊', description: 'Market and business analysis' },
        { id: 'finance', name: 'Financial Advisor', icon: '💰', description: 'Financial planning and analysis' },
        { id: 'realestate', name: 'Real Estate Expert', icon: '🏠', description: 'Property market insights' },
        { id: 'strategy', name: 'Strategy Consultant', icon: '🎯', description: 'Business strategy development' }
      ]
    },
    karen: {
      name: 'Karen',
      icon: '🏥',
      color: '#dc143c',
      agentTypes: [
        { id: 'clinical', name: 'Clinical Researcher', icon: '🔬', description: 'Medical research and analysis' },
        { id: 'compliance', name: 'Compliance Monitor', icon: '📋', description: 'Healthcare compliance tracking' },
        { id: 'data', name: 'Medical Data Analyst', icon: '📈', description: 'Healthcare data analysis' },
        { id: 'operations', name: 'Operations Manager', icon: '⚙️', description: 'Clinical operations oversight' }
      ]
    }
  }

  const currentPersona = personas[persona] || personas.cherry

  // Mock agent data
  useEffect(() => {
    const mockAgents = [
      {
        id: 1,
        name: 'Wellness Coach Alpha',
        type: 'wellness',
        status: 'active',
        performance: 95,
        tasks: 12,
        supervisor: 'Health Supervisor',
        lastActive: new Date().toISOString(),
        capabilities: ['Health Analysis', 'Workout Planning', 'Nutrition Guidance']
      },
      {
        id: 2,
        name: 'Creative Assistant Beta',
        type: 'creative',
        status: 'active',
        performance: 88,
        tasks: 8,
        supervisor: 'Creative Supervisor',
        lastActive: new Date(Date.now() - 300000).toISOString(),
        capabilities: ['Content Creation', 'Design Feedback', 'Brainstorming']
      },
      {
        id: 3,
        name: 'Relationship Manager Gamma',
        type: 'relationship',
        status: 'idle',
        performance: 92,
        tasks: 3,
        supervisor: 'Personal Supervisor',
        lastActive: new Date(Date.now() - 600000).toISOString(),
        capabilities: ['Communication Analysis', 'Conflict Resolution', 'Social Insights']
      }
    ]
    setAgents(mockAgents)
  }, [])

  const filteredAgents = agents.filter(agent => 
    agentFilter === 'all' || agent.status === agentFilter
  )

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return '#2ed573'
      case 'idle': return '#ffa502'
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
            {currentPersona.icon}
          </div>
          <div>
            <h1 className="text-3xl font-bold" style={{ color: currentPersona.color }}>
              {currentPersona.name} Agent Factory
            </h1>
            <p className="text-secondary">
              Manage AI agents and supervisors for {currentPersona.name}
            </p>
          </div>
        </div>
        
        <button
          onClick={() => setShowCreateAgent(true)}
          className="btn btn-primary"
          style={{ backgroundColor: currentPersona.color }}
        >
          🤖 Create Agent
        </button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold" style={{ color: currentPersona.color }}>
                {agents.length}
              </div>
              <div className="text-sm text-secondary">Total Agents</div>
            </div>
            <div className="text-2xl">🤖</div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-success">
                {agents.filter(a => a.status === 'active').length}
              </div>
              <div className="text-sm text-secondary">Active Agents</div>
            </div>
            <div className="text-2xl">⚡</div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold" style={{ color: currentPersona.color }}>
                {agents.reduce((sum, a) => sum + a.tasks, 0)}
              </div>
              <div className="text-sm text-secondary">Active Tasks</div>
            </div>
            <div className="text-2xl">📋</div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-success">
                {Math.round(agents.reduce((sum, a) => sum + a.performance, 0) / agents.length)}%
              </div>
              <div className="text-sm text-secondary">Avg Performance</div>
            </div>
            <div className="text-2xl">📈</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <span className="text-sm font-medium">Filter by status:</span>
        {['all', 'active', 'idle', 'offline'].map((filter) => (
          <button
            key={filter}
            onClick={() => setAgentFilter(filter)}
            className={`px-3 py-1 rounded-lg text-sm transition-all ${
              agentFilter === filter 
                ? 'bg-current text-white' 
                : 'bg-tertiary text-secondary hover:bg-hover'
            }`}
            style={{ 
              backgroundColor: agentFilter === filter ? currentPersona.color : 'var(--bg-tertiary)'
            }}
          >
            {filter.charAt(0).toUpperCase() + filter.slice(1)}
          </button>
        ))}
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {filteredAgents.map((agent) => {
          const agentType = currentPersona.agentTypes.find(t => t.id === agent.type)
          return (
            <div
              key={agent.id}
              className="card cursor-pointer hover:bg-tertiary transition-all"
              onClick={() => setSelectedAgent(agent)}
            >
              {/* Agent Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="text-2xl">{agentType?.icon || '🤖'}</div>
                  <div>
                    <h3 className="font-semibold text-primary">{agent.name}</h3>
                    <p className="text-sm text-secondary">{agentType?.name}</p>
                  </div>
                </div>
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: getStatusColor(agent.status) }}
                ></div>
              </div>

              {/* Performance */}
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-secondary">Performance</span>
                  <span 
                    className="text-sm font-semibold"
                    style={{ color: getPerformanceColor(agent.performance) }}
                  >
                    {agent.performance}%
                  </span>
                </div>
                <div className="w-full bg-tertiary rounded-full h-2">
                  <div 
                    className="h-2 rounded-full transition-all"
                    style={{ 
                      width: `${agent.performance}%`,
                      backgroundColor: getPerformanceColor(agent.performance)
                    }}
                  ></div>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <div className="text-lg font-bold" style={{ color: currentPersona.color }}>
                    {agent.tasks}
                  </div>
                  <div className="text-xs text-secondary">Active Tasks</div>
                </div>
                <div>
                  <div className="text-lg font-bold text-secondary">
                    {agent.supervisor.split(' ')[0]}
                  </div>
                  <div className="text-xs text-secondary">Supervisor</div>
                </div>
              </div>

              {/* Capabilities */}
              <div className="space-y-1">
                {agent.capabilities.slice(0, 2).map((capability, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <div 
                      className="w-1.5 h-1.5 rounded-full"
                      style={{ backgroundColor: currentPersona.color }}
                    ></div>
                    <span className="text-xs text-secondary">{capability}</span>
                  </div>
                ))}
                {agent.capabilities.length > 2 && (
                  <div className="text-xs text-muted">
                    +{agent.capabilities.length - 2} more capabilities
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Agent Types */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Available Agent Types for {currentPersona.name}</h3>
          <p className="card-description">Specialized agents designed for {currentPersona.name}'s domain</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {currentPersona.agentTypes.map((type) => (
            <div key={type.id} className="p-4 border border-color rounded-lg hover:bg-tertiary transition-all">
              <div className="flex items-center gap-3 mb-2">
                <div className="text-xl">{type.icon}</div>
                <div>
                  <h4 className="font-semibold text-sm">{type.name}</h4>
                </div>
              </div>
              <p className="text-xs text-secondary">{type.description}</p>
              <div className="mt-3">
                <button 
                  className="text-xs px-2 py-1 rounded"
                  style={{ 
                    backgroundColor: `${currentPersona.color}20`,
                    color: currentPersona.color
                  }}
                >
                  Create Agent
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default AgentFactory

