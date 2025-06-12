import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import './App.css'

// Import components
import DarkThemeLayout from './components/layout/DarkThemeLayout'
import PersonaSelection from './components/pages/PersonaSelection'
import SearchInterface from './components/pages/SearchInterface'
import AgentFactory from './components/pages/AgentFactory'
import SupervisorFactory from './components/pages/SupervisorFactory'
import ProjectManagement from './components/pages/ProjectManagement'
import SystemHealth from './components/pages/SystemHealth'
import { FeatureDemo } from './components/pages/FeatureDemo'

function App() {
  const [selectedPersona, setSelectedPersona] = useState(null)
  const [systemStatus, setSystemStatus] = useState({
    apiConnected: true,
    activeSessions: 3,
    activeAgents: 24,
    apiRequests: 1247,
    systemHealth: 98.5
  })

  // Load persona from localStorage on mount
  useEffect(() => {
    const savedPersona = localStorage.getItem('selectedPersona')
    if (savedPersona) {
      setSelectedPersona(savedPersona)
    }
  }, [])

  // Save persona to localStorage when changed
  useEffect(() => {
    if (selectedPersona) {
      localStorage.setItem('selectedPersona', selectedPersona)
    }
  }, [selectedPersona])

  return (
    <Router>
      <div className="app dark-theme">
        <DarkThemeLayout 
          selectedPersona={selectedPersona}
          systemStatus={systemStatus}
          onPersonaChange={setSelectedPersona}
        >
          <Routes>
            {/* Default route - if no persona selected, show selection */}
            <Route 
              path="/" 
              element={
                selectedPersona ? 
                <Navigate to="/search" replace /> : 
                <PersonaSelection onPersonaSelect={setSelectedPersona} />
              } 
            />
            
            {/* Search-first interface */}
            <Route 
              path="/search" 
              element={
                <SearchInterface 
                  persona={selectedPersona}
                  onPersonaChange={setSelectedPersona}
                />
              } 
            />
            
            {/* Agent management */}
            <Route 
              path="/agents" 
              element={
                <AgentFactory 
                  persona={selectedPersona}
                  systemStatus={systemStatus}
                />
              } 
            />
            
            {/* Supervisor management */}
            <Route 
              path="/supervisors" 
              element={
                <SupervisorFactory 
                  persona={selectedPersona}
                  systemStatus={systemStatus}
                />
              } 
            />
            
            {/* Project management */}
            <Route 
              path="/projects" 
              element={
                <ProjectManagement 
                  persona={selectedPersona}
                />
              } 
            />
            
            {/* System health */}
            <Route 
              path="/health" 
              element={
                <SystemHealth 
                  systemStatus={systemStatus}
                  onStatusUpdate={setSystemStatus}
                />
              } 
            />
            
            {/* Feature demonstration */}
            <Route 
              path="/features" 
              element={
                <FeatureDemo 
                  persona={selectedPersona || 'cherry'}
                />
              } 
            />
            
            {/* Persona selection (accessible anytime) */}
            <Route 
              path="/personas" 
              element={
                <PersonaSelection 
                  onPersonaSelect={setSelectedPersona}
                  currentPersona={selectedPersona}
                />
              } 
            />
          </Routes>
        </DarkThemeLayout>
      </div>
    </Router>
  )
}

export default App

