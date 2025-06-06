import { create } from 'zustand'

export const useSystemStore = create((set, get) => ({
  // System health metrics
  systemHealth: {
    timestamp: new Date().toISOString(),
    memory_usage_mb: 0,
    cpu_usage_percent: 0,
    active_connections: 0,
    response_time_ms: 0,
    error_rate_percent: 0,
    uptime_hours: 0
  },
  
  // Connection status
  isConnected: false,
  connectionStatus: 'disconnected',
  
  // System metrics history
  metricsHistory: [],
  
  // Actions
  updateSystemHealth: (metrics) => set((state) => ({
    systemHealth: metrics,
    metricsHistory: [...state.metricsHistory.slice(-100), metrics] // Keep last 100 entries
  })),
  
  setConnectionStatus: (status, connected) => set({
    connectionStatus: status,
    isConnected: connected
  }),
  
  // Get latest metrics for charts
  getMetricsForChart: (metricName, limit = 20) => {
    const { metricsHistory } = get()
    return metricsHistory
      .slice(-limit)
      .map(metric => ({
        timestamp: new Date(metric.timestamp).toLocaleTimeString(),
        value: metric[metricName] || 0
      }))
  }
}))

