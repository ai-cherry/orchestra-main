import { useState, useEffect } from 'react'

const ProjectManagement = ({ persona }) => {
  const [projects, setProjects] = useState([])
  const [todos, setTodos] = useState([])
  const [viewMode, setViewMode] = useState('projects') // 'projects' or 'todos'
  const [selectedProject, setSelectedProject] = useState(null)
  const [newTodo, setNewTodo] = useState('')
  const [todoFilter, setTodoFilter] = useState('all')

  const personas = {
    cherry: {
      name: 'Cherry',
      icon: '🍒',
      color: '#ff4757',
      projectTypes: ['Health & Wellness', 'Creative Projects', 'Personal Growth', 'Lifestyle']
    },
    sophia: {
      name: 'Sophia',
      icon: '💼',
      color: '#8b4513',
      projectTypes: ['Business Analysis', 'Financial Planning', 'Real Estate', 'Strategy']
    },
    karen: {
      name: 'Karen',
      icon: '🏥',
      color: '#dc143c',
      projectTypes: ['Clinical Research', 'Compliance', 'Medical Data', 'Operations']
    }
  }

  const currentPersona = personas[persona] || personas.cherry

  // Mock project data
  useEffect(() => {
    const mockProjects = [
      {
        id: 1,
        name: 'Wellness Optimization Program',
        type: 'Health & Wellness',
        status: 'active',
        priority: 'high',
        progress: 75,
        dueDate: '2025-06-15',
        assignedAgents: ['Wellness Coach Alpha', 'Nutrition Advisor Beta'],
        tasks: 12,
        completedTasks: 9,
        description: 'Comprehensive wellness program focusing on nutrition, exercise, and mental health'
      },
      {
        id: 2,
        name: 'Creative Content Strategy',
        type: 'Creative Projects',
        status: 'active',
        priority: 'medium',
        progress: 45,
        dueDate: '2025-06-20',
        assignedAgents: ['Creative Assistant Beta'],
        tasks: 8,
        completedTasks: 4,
        description: 'Develop creative content strategy for personal branding and expression'
      },
      {
        id: 3,
        name: 'Personal Growth Tracking',
        type: 'Personal Growth',
        status: 'planning',
        priority: 'medium',
        progress: 15,
        dueDate: '2025-07-01',
        assignedAgents: ['Lifestyle Optimizer Zeta'],
        tasks: 6,
        completedTasks: 1,
        description: 'Track and optimize personal development goals and milestones'
      }
    ]
    setProjects(mockProjects)

    const mockTodos = [
      {
        id: 1,
        text: 'Review wellness program metrics',
        priority: 'high',
        status: 'pending',
        projectId: 1,
        assignedAgent: 'Wellness Coach Alpha',
        dueDate: '2025-06-07',
        createdAt: new Date().toISOString()
      },
      {
        id: 2,
        text: 'Create content calendar for next month',
        priority: 'medium',
        status: 'in-progress',
        projectId: 2,
        assignedAgent: 'Creative Assistant Beta',
        dueDate: '2025-06-08',
        createdAt: new Date(Date.now() - 86400000).toISOString()
      },
      {
        id: 3,
        text: 'Set up personal growth tracking dashboard',
        priority: 'low',
        status: 'pending',
        projectId: 3,
        assignedAgent: 'Lifestyle Optimizer Zeta',
        dueDate: '2025-06-10',
        createdAt: new Date(Date.now() - 172800000).toISOString()
      },
      {
        id: 4,
        text: 'Research new meditation techniques',
        priority: 'medium',
        status: 'completed',
        projectId: 1,
        assignedAgent: 'Wellness Coach Alpha',
        dueDate: '2025-06-05',
        createdAt: new Date(Date.now() - 259200000).toISOString()
      }
    ]
    setTodos(mockTodos)
  }, [])

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return '#2ed573'
      case 'planning': return '#ffa502'
      case 'completed': return '#2ed573'
      case 'on-hold': return '#ff4757'
      case 'in-progress': return '#3742fa'
      case 'pending': return '#ffa502'
      default: return '#888888'
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return '#ff4757'
      case 'medium': return '#ffa502'
      case 'low': return '#2ed573'
      default: return '#888888'
    }
  }

  const filteredTodos = todos.filter(todo => {
    if (todoFilter === 'all') return true
    if (todoFilter === 'priority') return todo.priority === 'high'
    return todo.status === todoFilter
  })

  const addTodo = () => {
    if (!newTodo.trim()) return
    
    const todo = {
      id: Date.now(),
      text: newTodo,
      priority: 'medium',
      status: 'pending',
      projectId: selectedProject?.id || null,
      assignedAgent: null,
      dueDate: new Date(Date.now() + 86400000 * 3).toISOString().split('T')[0],
      createdAt: new Date().toISOString()
    }
    
    setTodos([todo, ...todos])
    setNewTodo('')
  }

  const toggleTodoStatus = (todoId) => {
    setTodos(todos.map(todo => 
      todo.id === todoId 
        ? { ...todo, status: todo.status === 'completed' ? 'pending' : 'completed' }
        : todo
    ))
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
            📋
          </div>
          <div>
            <h1 className="text-3xl font-bold" style={{ color: currentPersona.color }}>
              {currentPersona.name} Project Management
            </h1>
            <p className="text-secondary">
              Manage projects and prioritized to-do lists for {currentPersona.name}
            </p>
          </div>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={() => setViewMode(viewMode === 'projects' ? 'todos' : 'projects')}
            className="btn btn-secondary"
          >
            {viewMode === 'projects' ? '✅ View Todos' : '📋 View Projects'}
          </button>
          <button
            className="btn btn-primary"
            style={{ backgroundColor: currentPersona.color }}
          >
            ➕ New {viewMode === 'projects' ? 'Project' : 'Todo'}
          </button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold" style={{ color: currentPersona.color }}>
                {projects.filter(p => p.status === 'active').length}
              </div>
              <div className="text-sm text-secondary">Active Projects</div>
            </div>
            <div className="text-2xl">📋</div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-warning">
                {todos.filter(t => t.status === 'pending').length}
              </div>
              <div className="text-sm text-secondary">Pending Todos</div>
            </div>
            <div className="text-2xl">⏳</div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-error">
                {todos.filter(t => t.priority === 'high').length}
              </div>
              <div className="text-sm text-secondary">High Priority</div>
            </div>
            <div className="text-2xl">🔥</div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-success">
                {Math.round(projects.reduce((sum, p) => sum + p.progress, 0) / projects.length)}%
              </div>
              <div className="text-sm text-secondary">Avg Progress</div>
            </div>
            <div className="text-2xl">📈</div>
          </div>
        </div>
      </div>

      {viewMode === 'projects' ? (
        /* Projects View */
        <div className="space-y-6">
          <h2 className="text-xl font-semibold">Active Projects</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <div
                key={project.id}
                className="card cursor-pointer hover:bg-tertiary transition-all"
                onClick={() => setSelectedProject(project)}
              >
                {/* Project Header */}
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-primary">{project.name}</h3>
                    <p className="text-sm text-secondary">{project.type}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: getPriorityColor(project.priority) }}
                    ></div>
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: getStatusColor(project.status) }}
                    ></div>
                  </div>
                </div>

                {/* Progress */}
                <div className="mb-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-secondary">Progress</span>
                    <span className="text-sm font-semibold" style={{ color: currentPersona.color }}>
                      {project.progress}%
                    </span>
                  </div>
                  <div className="w-full bg-tertiary rounded-full h-2">
                    <div 
                      className="h-2 rounded-full transition-all"
                      style={{ 
                        width: `${project.progress}%`,
                        backgroundColor: currentPersona.color
                      }}
                    ></div>
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <div className="text-lg font-bold" style={{ color: currentPersona.color }}>
                      {project.completedTasks}/{project.tasks}
                    </div>
                    <div className="text-xs text-secondary">Tasks</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-secondary">
                      {new Date(project.dueDate).toLocaleDateString()}
                    </div>
                    <div className="text-xs text-secondary">Due Date</div>
                  </div>
                </div>

                {/* Assigned Agents */}
                <div className="space-y-1">
                  <div className="text-xs text-secondary">Assigned Agents:</div>
                  {project.assignedAgents.slice(0, 2).map((agent, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <div 
                        className="w-1.5 h-1.5 rounded-full"
                        style={{ backgroundColor: currentPersona.color }}
                      ></div>
                      <span className="text-xs text-secondary">{agent}</span>
                    </div>
                  ))}
                  {project.assignedAgents.length > 2 && (
                    <div className="text-xs text-muted">
                      +{project.assignedAgents.length - 2} more agents
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        /* Todos View */
        <div className="space-y-6">
          {/* Add Todo */}
          <div className="card">
            <div className="flex gap-3">
              <input
                type="text"
                value={newTodo}
                onChange={(e) => setNewTodo(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addTodo()}
                placeholder="Add a new todo..."
                className="input flex-1"
              />
              <button
                onClick={addTodo}
                className="btn btn-primary"
                style={{ backgroundColor: currentPersona.color }}
              >
                Add Todo
              </button>
            </div>
          </div>

          {/* Todo Filters */}
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium">Filter:</span>
            {['all', 'pending', 'in-progress', 'completed', 'priority'].map((filter) => (
              <button
                key={filter}
                onClick={() => setTodoFilter(filter)}
                className={`px-3 py-1 rounded-lg text-sm transition-all ${
                  todoFilter === filter 
                    ? 'bg-current text-white' 
                    : 'bg-tertiary text-secondary hover:bg-hover'
                }`}
                style={{ 
                  backgroundColor: todoFilter === filter ? currentPersona.color : 'var(--bg-tertiary)'
                }}
              >
                {filter === 'priority' ? 'High Priority' : filter.charAt(0).toUpperCase() + filter.slice(1)}
              </button>
            ))}
          </div>

          {/* Todo List */}
          <div className="space-y-3">
            {filteredTodos.map((todo) => {
              const project = projects.find(p => p.id === todo.projectId)
              return (
                <div
                  key={todo.id}
                  className={`card transition-all ${
                    todo.status === 'completed' ? 'opacity-60' : ''
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <button
                      onClick={() => toggleTodoStatus(todo.id)}
                      className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                        todo.status === 'completed' 
                          ? 'bg-success border-success text-white' 
                          : 'border-color hover:border-current'
                      }`}
                      style={{ 
                        borderColor: todo.status !== 'completed' ? currentPersona.color : undefined
                      }}
                    >
                      {todo.status === 'completed' && '✓'}
                    </button>
                    
                    <div className="flex-1">
                      <div className={`font-medium ${
                        todo.status === 'completed' ? 'line-through text-secondary' : 'text-primary'
                      }`}>
                        {todo.text}
                      </div>
                      <div className="flex items-center gap-4 text-xs text-secondary mt-1">
                        {project && (
                          <span>📋 {project.name}</span>
                        )}
                        {todo.assignedAgent && (
                          <span>🤖 {todo.assignedAgent}</span>
                        )}
                        <span>📅 {new Date(todo.dueDate).toLocaleDateString()}</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: getPriorityColor(todo.priority) }}
                      ></div>
                      <div 
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: getStatusColor(todo.status) }}
                      ></div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

export default ProjectManagement

