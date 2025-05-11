import { useState, useEffect } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import { ThemeProvider } from './components/theme-provider'
import { Toaster } from './components/ui/toaster'
import Layout from './components/layout/Layout'
import Dashboard from './modules/dashboard/Dashboard'
import MemoryManagement from './modules/memory/MemoryManagement'
import AgentRegistry from './modules/agents/AgentRegistry'
import ConversationExplorer from './modules/conversations/ConversationExplorer'
import McpMonitoring from './modules/mcp/McpMonitoring'
import NotFound from './modules/NotFound'

/**
 * Main application component
 */
function App() {
  const location = useLocation()
  const [mounted, setMounted] = useState(false)

  // Ensure theme is applied after hydration to avoid FOUC
  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  return (
    <ThemeProvider defaultTheme="system" storageKey="ai-orchestra-ui-theme">
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="memory" element={<MemoryManagement />} />
          <Route path="agents" element={<AgentRegistry />} />
          <Route path="conversations" element={<ConversationExplorer />} />
          <Route path="mcp" element={<McpMonitoring />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
      <Toaster />
    </ThemeProvider>
  )
}

export default App