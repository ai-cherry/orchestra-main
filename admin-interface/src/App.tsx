import React from 'react'
import { Routes, Route } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'

// Import all the pages
import SearchPage from './app/page'
import IntelligenceHubPage from './app/intelligence-hub/page'
import AgentSwarmPage from './app/agent-swarm/page'
import AgentFactoryPage from './app/agent-factory/page' // Assuming this will be created
import BusinessToolsPage from './app/business-tools/page'

function App() {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/intelligence-hub" element={<IntelligenceHubPage />} />
        <Route path="/agent-swarm" element={<AgentSwarmPage />} />
        <Route path="/agent-factory" element={<AgentFactoryPage />} />
        <Route path="/business-tools" element={<BusinessToolsPage />} />
        {/* The Search Orchestrator and Data Pipeline are detailed views, not main pages now. */}
      </Routes>
    </MainLayout>
  )
}

export default App 