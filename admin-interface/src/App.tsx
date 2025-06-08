import React, { Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'
import ErrorBoundary from './components/ErrorBoundary'

// Import all the pages
import SearchPage from './app/page'
import IntelligenceHubPage from './app/intelligence-hub/page'
import AgentSwarmPage from './app/agent-swarm/page'
import AgentFactoryPage from './app/agent-factory/page' // Assuming this will be created
import BusinessToolsPage from './app/business-tools/page'

// Loading component
const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen bg-gray-900">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
      <p className="mt-4 text-gray-400">Loading...</p>
    </div>
  </div>
)

function App() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingFallback />}>
        <MainLayout>
          <Routes>
            <Route path="/" element={
              <ErrorBoundary>
                <SearchPage />
              </ErrorBoundary>
            } />
            <Route path="/intelligence-hub" element={
              <ErrorBoundary>
                <IntelligenceHubPage />
              </ErrorBoundary>
            } />
            <Route path="/agent-swarm" element={
              <ErrorBoundary>
                <AgentSwarmPage />
              </ErrorBoundary>
            } />
            <Route path="/agent-factory" element={
              <ErrorBoundary>
                <AgentFactoryPage />
              </ErrorBoundary>
            } />
            <Route path="/business-tools" element={
              <ErrorBoundary>
                <BusinessToolsPage />
              </ErrorBoundary>
            } />
            {/* The Search Orchestrator and Data Pipeline are detailed views, not main pages now. */}
          </Routes>
        </MainLayout>
      </Suspense>
    </ErrorBoundary>
  )
}

export default App 