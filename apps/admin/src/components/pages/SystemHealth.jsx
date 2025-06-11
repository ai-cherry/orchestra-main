import { useState, useEffect } from 'react'

const SystemHealth = ({ persona }) => {
  const [systemMetrics, setSystemMetrics] = useState({
    apiHealth: 98.5,
    agentStatus: 'optimal',
    activeConnections: 24,
    responseTime: 145,
    memoryUsage: 67,
    cpuUsage: 23
  })

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">System Health</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-success">
                {systemMetrics.apiHealth}%
              </div>
              <div className="text-sm text-secondary">API Health</div>
            </div>
            <div className="text-2xl">🟢</div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-primary">
                {systemMetrics.activeConnections}
              </div>
              <div className="text-sm text-secondary">Active Connections</div>
            </div>
            <div className="text-2xl">🔗</div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-warning">
                {systemMetrics.responseTime}ms
              </div>
              <div className="text-sm text-secondary">Response Time</div>
            </div>
            <div className="text-2xl">⚡</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SystemHealth

