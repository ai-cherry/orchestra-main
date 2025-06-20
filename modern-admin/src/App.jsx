import './App.css'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState } from 'react'
import ChatInterface from './components/ChatInterface'
import Dashboard from './components/Dashboard'
import AgentFactory from './components/AgentFactory'
import SystemMonitor from './components/SystemMonitor'
import HealthDashboard from './components/HealthDashboard'
import PersonaManagement from './components/PersonaManagement'
import CreativeStudio from './components/CreativeStudio'
import SearchSettings from './components/SearchSettings'
import Sidebar from './components/Sidebar'
import TopNav from './components/TopNav'

function App() {
  const [activePersona, setActivePersona] = useState('sophia')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <Router>
      <div className="flex flex-col h-screen bg-background text-foreground overflow-hidden">
        <TopNav 
          activePersona={activePersona}
          onPersonaChange={setActivePersona}
        />
        
        <div className="flex flex-1 pt-16">
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
              <Route path="/health" element={<HealthDashboard />} />
              <Route path="/agents" element={<AgentFactory />} />
              <Route path="/monitor" element={<SystemMonitor />} />
              <Route path="/personas" element={<PersonaManagement />} />
              <Route path="/creative" element={<CreativeStudio />} />
              <Route path="/settings/search" element={<SearchSettings activePersona={activePersona} />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  )
}

export default App

