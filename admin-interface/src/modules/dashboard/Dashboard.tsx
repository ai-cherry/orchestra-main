import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { AreaChart, BarChart, LineChart } from '../../components/ui/charts'
import { formatBytes, formatNumber } from '../../lib/utils'
import { apiService, SystemStats, ActivityEvent, TimeSeriesDataPoint } from '../../lib/api'
import { useMultiFetch } from '../../lib/hooks'

/**
 * Dashboard component that displays system overview and key metrics
 */
const Dashboard = () => {
  // Use the custom hook to fetch all dashboard data in parallel
  const { 
    data, 
    loading, 
    error, 
    refetch 
  } = useMultiFetch({
    stats: apiService.getSystemStats,
    activities: apiService.getRecentActivity,
    performanceData: apiService.getSystemPerformance,
    memoryData: apiService.getMemoryUsage,
    agentData: apiService.getAgentActivity
  })
  
  // Extract data from the hook result
  const stats = data.stats as SystemStats | undefined
  const activities = data.activities as ActivityEvent[] | undefined
  const performanceData = data.performanceData as TimeSeriesDataPoint[] | undefined
  const memoryData = data.memoryData as TimeSeriesDataPoint[] | undefined
  const agentData = data.agentData as TimeSeriesDataPoint[] | undefined
  
  // Show loading state
  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading dashboard data...</p>
        </div>
      </div>
    )
  }
  
  // Show error state
  if (error) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="text-center">
          <div className="rounded-full bg-destructive/10 p-3 text-destructive mx-auto w-fit">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
          <h3 className="mt-4 text-lg font-medium">Error Loading Dashboard</h3>
          <p className="mt-2 text-sm text-muted-foreground">{error}</p>
          <button 
            className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
            onClick={() => refetch()}
          >
            Retry
          </button>
        </div>
      </div>
    )
  }
  
  // If no data is available after loading
  if (!stats || !activities || !performanceData || !memoryData || !agentData) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground">No dashboard data available.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
      </div>

      {/* System Health Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              className="h-4 w-4 text-muted-foreground"
            >
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.memorySystem.usagePercentage}%</div>
            <div className="text-xs text-muted-foreground">
              {formatBytes(stats.memorySystem.totalUsed)} / {formatBytes(stats.memorySystem.totalCapacity)}
            </div>
            <div className="mt-4 h-1 w-full rounded-full bg-secondary">
              <div 
                className="h-1 rounded-full bg-primary" 
                style={{ width: `${stats.memorySystem.usagePercentage}%` }}
              ></div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              className="h-4 w-4 text-muted-foreground"
            >
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.activeAgents}</div>
            <p className="text-xs text-muted-foreground">
              +12% from last week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">API Requests</CardTitle>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              className="h-4 w-4 text-muted-foreground"
            >
              <rect width="20" height="14" x="2" y="5" rx="2" />
              <path d="M2 10h20" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(stats.apiRequests)}</div>
            <p className="text-xs text-muted-foreground">
              +19% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              className="h-4 w-4 text-muted-foreground"
            >
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold text-status-${stats.systemHealth === 'healthy' ? 'healthy' : stats.systemHealth === 'degraded' ? 'warning' : 'error'}`}>
              {stats.systemHealth === 'healthy' ? 'Healthy' : stats.systemHealth === 'degraded' ? 'Degraded' : 'Unhealthy'}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats.systemHealth === 'healthy' ? 'All systems operational' : stats.systemHealth === 'degraded' ? 'Some systems degraded' : 'System issues detected'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Memory Tier Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Memory Tier Overview</CardTitle>
          <CardDescription>
            Usage across hot, warm, and cold memory tiers
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-memory-hot"></div>
                  <span className="text-sm font-medium">Hot Tier (Redis)</span>
                </div>
                <span className="text-sm text-muted-foreground">{stats.memorySystem.hot.percentage}% used</span>
              </div>
              <div className="h-2 w-full rounded-full bg-secondary">
                <div 
                  className="h-2 rounded-full bg-memory-hot"
                  style={{ width: `${stats.memorySystem.hot.percentage}%` }}
                ></div>
              </div>
              <div className="text-xs text-muted-foreground">
                {formatBytes(stats.memorySystem.hot.used)} / {formatBytes(stats.memorySystem.hot.total)}
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-memory-warm"></div>
                  <span className="text-sm font-medium">Warm Tier (Firestore)</span>
                </div>
                <span className="text-sm text-muted-foreground">{stats.memorySystem.warm.percentage}% used</span>
              </div>
              <div className="h-2 w-full rounded-full bg-secondary">
                <div 
                  className="h-2 rounded-full bg-memory-warm"
                  style={{ width: `${stats.memorySystem.warm.percentage}%` }}
                ></div>
              </div>
              <div className="text-xs text-muted-foreground">
                {formatBytes(stats.memorySystem.warm.used)} / {formatBytes(stats.memorySystem.warm.total)}
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-memory-cold"></div>
                  <span className="text-sm font-medium">Cold Tier (Compressed)</span>
                </div>
                <span className="text-sm text-muted-foreground">{stats.memorySystem.cold.percentage}% used</span>
              </div>
              <div className="h-2 w-full rounded-full bg-secondary">
                <div 
                  className="h-2 rounded-full bg-memory-cold"
                  style={{ width: `${stats.memorySystem.cold.percentage}%` }}
                ></div>
              </div>
              <div className="text-xs text-muted-foreground">
                {formatBytes(stats.memorySystem.cold.used)} / {formatBytes(stats.memorySystem.cold.total)}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Charts */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="memory">Memory</TabsTrigger>
          <TabsTrigger value="agents">Agents</TabsTrigger>
        </TabsList>
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Performance</CardTitle>
              <CardDescription>
                System performance metrics over the past 30 days
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              <LineChart
                data={performanceData}
                xAxisKey="name"
                yAxisKey="value"
                className="h-[300px]"
              />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="memory" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Memory Usage</CardTitle>
              <CardDescription>
                Memory usage by tier over the past 30 days
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              <AreaChart
                data={memoryData}
                categories={["hot", "warm", "cold"]}
                colors={["#ef4444", "#f59e0b", "#3b82f6"]}
                xAxisKey="name"
                className="h-[300px]"
              />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="agents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agent Activity</CardTitle>
              <CardDescription>
                Agent activity by type over the past 30 days
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              <BarChart
                data={agentData}
                xAxisKey="name"
                yAxisKey="value"
                className="h-[300px]"
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>
            Latest system events and notifications
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {activities.map((activity) => (
              <div key={activity.id} className="flex items-start space-x-4">
                <div className={`mt-0.5 h-2 w-2 rounded-full bg-status-${
                  activity.type === "warning" 
                    ? "warning" 
                    : activity.type === "success" 
                      ? "healthy" 
                      : activity.type === "error"
                        ? "error"
                        : "info"
                }`} />
                <div className="space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {activity.title}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {activity.description}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {activity.time}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Dashboard
