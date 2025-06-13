import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Sidebar } from './components/layout/Sidebar'
import { ChatInterface } from './pages/ChatInterface'
import { Dashboard } from './pages/Dashboard'
import { AgentFactory } from './pages/AgentFactory'
import { SystemMonitor } from './pages/SystemMonitor'
import { DataIntegrationPage } from './pages/DataIntegrationPage'
import { PersonaProvider } from './contexts/PersonaContext'
import { WebSocketProvider } from './contexts/WebSocketContext'

function App() {
  return (
    <PersonaProvider>
      <WebSocketProvider>
        <Router>
          <div className="flex h-screen bg-background">
            <Sidebar />
            <main className="flex-1 overflow-hidden">
              <Routes>
                <Route path="/" element={<ChatInterface />} />
                <Route path="/chat" element={<ChatInterface />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/agent-factory" element={<AgentFactory />} />
                <Route path="/data-integration" element={<DataIntegrationPage />} />
                <Route path="/system-monitor" element={<SystemMonitor />} />
              </Routes>
            </main>
          </div>
        </Router>
      </WebSocketProvider>
    </PersonaProvider>
  )
}

export default App 