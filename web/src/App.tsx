import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Sidebar } from './components/layout/Sidebar'
import { ChatInterface } from './pages/ChatInterface'
import { Dashboard } from './pages/Dashboard'
import { AgentFactory } from './pages/AgentFactory'
import { SystemMonitor } from './pages/SystemMonitor'
import { DataIntegrationPage } from './pages/DataIntegrationPage'
import { DesignSystemDemo } from './pages/DesignSystemDemo'

function App() {
  return (
    <Router>
      <div className="flex h-screen bg-background">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          <Routes>
            <Route path="/" element={<ChatInterface />} />
            <Route path="/chat" element={<ChatInterface />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/agent-factory" element={<AgentFactory />} />
            <Route path="/data-integration" element={<DataIntegrationPage />} />
            <Route path="/system-monitor" element={<SystemMonitor />} />
            <Route path="/design-system" element={<DesignSystemDemo />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App