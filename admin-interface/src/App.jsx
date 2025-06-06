import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Sidebar } from './components/layout/Sidebar'
import { Header } from './components/layout/Header'
import { Dashboard } from './components/pages/Dashboard'
import { PersonaHub } from './components/pages/PersonaHub'
import { SearchCenter } from './components/pages/SearchCenter'
import { WorkflowBuilder } from './components/pages/WorkflowBuilder'
import { MultiModalSuite } from './components/pages/MultiModalSuite'
import { SystemMonitor } from './components/pages/SystemMonitor'
import { useWebSocket } from './hooks/useWebSocket'
import { useSystemStore } from './stores/systemStore'
import './App.css'

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const { isConnected, connectionStatus } = useWebSocket('ws://localhost:8000/ws')
  const { systemHealth, updateSystemHealth } = useSystemStore()

  useEffect(() => {
    // Initialize system health monitoring
    const interval = setInterval(() => {
      // This will be replaced with real WebSocket data
      updateSystemHealth({
        timestamp: new Date().toISOString(),
        memory_usage_mb: Math.random() * 1000 + 500,
        cpu_usage_percent: Math.random() * 100,
        active_connections: Math.floor(Math.random() * 50) + 10,
        response_time_ms: Math.random() * 200 + 50,
        error_rate_percent: Math.random() * 5,
        uptime_hours: 24.5
      })
    }, 5000)

    return () => clearInterval(interval)
  }, [updateSystemHealth])

  return (
    <Router>
      <div className="flex h-screen bg-background">
        <Sidebar 
          collapsed={sidebarCollapsed} 
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
        
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header 
            connectionStatus={connectionStatus}
            isConnected={isConnected}
          />
          
          <main className="flex-1 overflow-auto p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/personas" element={<PersonaHub />} />
              <Route path="/personas/:personaId" element={<PersonaHub />} />
              <Route path="/search" element={<SearchCenter />} />
              <Route path="/workflows" element={<WorkflowBuilder />} />
              <Route path="/workflows/:workflowId" element={<WorkflowBuilder />} />
              <Route path="/generate" element={<MultiModalSuite />} />
              <Route path="/generate/:type" element={<MultiModalSuite />} />
              <Route path="/system" element={<SystemMonitor />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  )
}

export default App

