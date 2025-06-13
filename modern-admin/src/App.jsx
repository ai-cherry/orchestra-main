import './App.css'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState } from 'react'
import ChatInterface from './components/ChatInterface'
import Dashboard from './components/Dashboard'
import AgentFactory from './components/AgentFactory'
import SystemMonitor from './components/SystemMonitor'
import Sidebar from './components/Sidebar'

function App() {
  const [activePersona, setActivePersona] = useState('sophia')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <Router>
      <div className="flex h-screen bg-background text-foreground overflow-hidden">
        <Sidebar 
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          activePersona={activePersona}
          onPersonaChange={setActivePersona}
        />
        
        <main className={`flex-1 transition-all duration-300 ${sidebarCollapsed ? 'ml-16' : 'ml-80'}`}>
          <Routes>
            <Route path="/" element={
              <ChatInterface 
                activePersona={activePersona}
                onPersonaChange={setActivePersona}
              />
            } />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/agent-factory" element={<AgentFactory />} />
            <Route path="/system-monitor" element={<SystemMonitor />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App

