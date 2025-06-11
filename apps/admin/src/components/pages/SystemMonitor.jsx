import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { useSystemStore } from '../../stores/systemStore'
import { usePersonaStore } from '../../stores/personaStore'
import { 
  Activity, 
  Cpu, 
  HardDrive, 
  Network, 
  Zap, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  LineChart,
  RefreshCw,
  Download,
  Settings,
  Bell,
  Shield,
  Database,
  Globe,
  Brain
} from 'lucide-react'
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, BarChart, Bar, PieChart as RechartsPieChart, Cell } from 'recharts'

function SystemHealthCard({ title, value, unit, status, trend, icon: Icon, description, threshold }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-500'
      case 'warning': return 'text-yellow-500'
      case 'critical': return 'text-red-500'
      default: return 'text-gray-500'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'critical': return <XCircle className="h-4 w-4 text-red-500" />
      default: return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-4 w-4 text-green-500" />
      case 'down': return <TrendingDown className="h-4 w-4 text-red-500" />
      default: return null
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold">
              {typeof value === 'number' ? value.toFixed(1) : value}
              {unit && <span className="text-sm text-muted-foreground ml-1">{unit}</span>}
            </div>
            <div className="flex items-center gap-2">
              {getTrendIcon(trend)}
              {getStatusIcon(status)}
            </div>
          </div>
          
          {threshold && (
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span>Threshold</span>
                <span>{threshold}{unit}</span>
              </div>
              <Progress 
                value={(value / threshold) * 100} 
                className={`h-2 ${status === 'critical' ? 'bg-red-100' : status === 'warning' ? 'bg-yellow-100' : 'bg-green-100'}`}
              />
            </div>
          )}
          
          {description && (
            <p className="text-xs text-muted-foreground">{description}</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function PerformanceChart({ title, data, dataKey, color = '#3b82f6', type = 'line' }) {
  const renderChart = () => {
    switch (type) {
      case 'area':
        return (
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis />
            <Tooltip />
            <Area type="monotone" dataKey={dataKey} stroke={color} fill={color} fillOpacity={0.3} />
          </AreaChart>
        )
      case 'bar':
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis />
            <Tooltip />
            <Bar dataKey={dataKey} fill={color} />
          </BarChart>
        )
      default:
        return (
          <RechartsLineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} />
          </RechartsLineChart>
        )
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            {renderChart()}
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

function PersonaPerformancePanel() {
  const { personas } = usePersonaStore()
  
  const performanceData = personas.map(persona => ({
    name: persona.name,
    health: persona.personalityHealth,
    interactions: persona.interactionCount,
    memory: persona.memoryUsage,
    color: persona.accentColor.replace('bg-', '#')
  }))

  const COLORS = ['#ef4444', '#3b82f6', '#10b981']

  return (
    <Card>
      <CardHeader>
        <CardTitle>Persona Performance</CardTitle>
        <CardDescription>Health and activity metrics for all personas</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 md:grid-cols-2">
          {/* Health Chart */}
          <div>
            <h4 className="text-sm font-medium mb-3">Personality Health</h4>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <RechartsPieChart>
                  <Tooltip />
                  <RechartsPieChart data={performanceData}>
                    {performanceData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </RechartsPieChart>
                </RechartsPieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Activity Metrics */}
          <div className="space-y-4">
            <h4 className="text-sm font-medium">Activity Metrics</h4>
            {personas.map((persona) => (
              <div key={persona.id} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <div className={`h-2 w-2 rounded-full ${persona.accentColor}`} />
                    {persona.name}
                  </span>
                  <span>{persona.personalityHealth.toFixed(1)}%</span>
                </div>
                <Progress value={persona.personalityHealth} className="h-2" />
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function AlertsPanel() {
  const [alerts] = useState([
    {
      id: 1,
      type: 'warning',
      title: 'High Memory Usage',
      description: 'Cherry persona memory usage approaching 80% threshold',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      acknowledged: false
    },
    {
      id: 2,
      type: 'info',
      title: 'Workflow Completed',
      description: 'Sophia market analysis workflow completed successfully',
      timestamp: new Date(Date.now() - 600000).toISOString(),
      acknowledged: true
    },
    {
      id: 3,
      type: 'critical',
      title: 'API Rate Limit',
      description: 'ElevenLabs API approaching rate limit for voice generation',
      timestamp: new Date(Date.now() - 900000).toISOString(),
      acknowledged: false
    }
  ])

  const getAlertIcon = (type) => {
    switch (type) {
      case 'critical': return <XCircle className="h-4 w-4 text-red-500" />
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'info': return <CheckCircle className="h-4 w-4 text-blue-500" />
      default: return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>System Alerts</CardTitle>
          <Button size="sm" variant="outline">
            <Bell className="h-4 w-4 mr-2" />
            Manage
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div 
              key={alert.id} 
              className={`p-3 rounded-lg border ${
                alert.acknowledged ? 'bg-muted/50 opacity-60' : 'bg-background'
              }`}
            >
              <div className="flex items-start gap-3">
                {getAlertIcon(alert.type)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{alert.title}</p>
                  <p className="text-xs text-muted-foreground">{alert.description}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Date(alert.timestamp).toLocaleString()}
                  </p>
                </div>
                {!alert.acknowledged && (
                  <Button size="sm" variant="ghost">
                    Acknowledge
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function ResourceUsagePanel() {
  const { systemHealth, getMetricsForChart } = useSystemStore()
  
  const resourceData = [
    {
      name: 'CPU',
      usage: systemHealth.cpu_usage_percent,
      limit: 100,
      color: '#ef4444'
    },
    {
      name: 'Memory',
      usage: (systemHealth.memory_usage_mb / 1024) * 100,
      limit: 100,
      color: '#3b82f6'
    },
    {
      name: 'Storage',
      usage: 45.2,
      limit: 100,
      color: '#10b981'
    },
    {
      name: 'Network',
      usage: 23.8,
      limit: 100,
      color: '#f59e0b'
    }
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Resource Usage</CardTitle>
        <CardDescription>Real-time system resource consumption</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {resourceData.map((resource) => (
            <div key={resource.name} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">{resource.name}</span>
                <span>{resource.usage.toFixed(1)}%</span>
              </div>
              <Progress 
                value={resource.usage} 
                className="h-2"
                style={{ '--progress-foreground': resource.color }}
              />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export function SystemMonitor() {
  const { systemHealth, getMetricsForChart } = useSystemStore()
  const [refreshing, setRefreshing] = useState(false)

  const handleRefresh = () => {
    setRefreshing(true)
    setTimeout(() => setRefreshing(false), 1000)
  }

  // Generate sample data for charts
  const cpuData = getMetricsForChart('cpu_usage_percent', 20)
  const memoryData = getMetricsForChart('memory_usage_mb', 20).map(item => ({
    ...item,
    value: (item.value / 1024) * 100 // Convert to percentage
  }))
  const responseTimeData = getMetricsForChart('response_time_ms', 20)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Monitor</h1>
          <p className="text-muted-foreground">
            Real-time performance monitoring and system health
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            size="sm" 
            variant="outline" 
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button size="sm" variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button size="sm" variant="outline">
            <Settings className="h-4 w-4 mr-2" />
            Configure
          </Button>
        </div>
      </div>

      {/* System Health Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <SystemHealthCard
          title="CPU Usage"
          value={systemHealth.cpu_usage_percent}
          unit="%"
          status={systemHealth.cpu_usage_percent > 80 ? 'critical' : systemHealth.cpu_usage_percent > 60 ? 'warning' : 'healthy'}
          trend="stable"
          icon={Cpu}
          description="Processor utilization"
          threshold={100}
        />
        <SystemHealthCard
          title="Memory Usage"
          value={systemHealth.memory_usage_mb}
          unit="MB"
          status={systemHealth.memory_usage_mb > 800 ? 'critical' : systemHealth.memory_usage_mb > 600 ? 'warning' : 'healthy'}
          trend="up"
          icon={HardDrive}
          description="RAM consumption"
          threshold={1024}
        />
        <SystemHealthCard
          title="Active Connections"
          value={systemHealth.active_connections}
          status="healthy"
          trend="stable"
          icon={Network}
          description="Real-time connections"
        />
        <SystemHealthCard
          title="Response Time"
          value={systemHealth.response_time_ms}
          unit="ms"
          status={systemHealth.response_time_ms > 200 ? 'warning' : 'healthy'}
          trend="down"
          icon={Zap}
          description="Average latency"
          threshold={500}
        />
      </div>

      {/* Performance Charts */}
      <Tabs defaultValue="performance" className="space-y-4">
        <TabsList>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="personas">Personas</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <PerformanceChart
              title="CPU Usage Over Time"
              data={cpuData}
              dataKey="value"
              color="#ef4444"
              type="area"
            />
            <PerformanceChart
              title="Memory Usage Over Time"
              data={memoryData}
              dataKey="value"
              color="#3b82f6"
              type="line"
            />
          </div>
          <PerformanceChart
            title="Response Time Trends"
            data={responseTimeData}
            dataKey="value"
            color="#10b981"
            type="line"
          />
        </TabsContent>

        <TabsContent value="personas" className="space-y-4">
          <PersonaPerformancePanel />
        </TabsContent>

        <TabsContent value="resources" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <ResourceUsagePanel />
            <AlertsPanel />
          </div>
        </TabsContent>

        <TabsContent value="security" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-green-500" />
                  Security Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm">SSL Certificate</span>
                    <Badge variant="outline" className="text-green-600">Valid</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">API Authentication</span>
                    <Badge variant="outline" className="text-green-600">Active</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Data Encryption</span>
                    <Badge variant="outline" className="text-green-600">AES-256</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Access Control</span>
                    <Badge variant="outline" className="text-green-600">Enabled</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5 text-blue-500" />
                  Data Privacy
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm">Medical Data</span>
                    <Badge variant="outline" className="text-blue-600">Encrypted</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Business Data</span>
                    <Badge variant="outline" className="text-blue-600">Secured</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Personal Data</span>
                    <Badge variant="outline" className="text-blue-600">Protected</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Audit Logs</span>
                    <Badge variant="outline" className="text-blue-600">Active</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="h-5 w-5 text-purple-500" />
                  External Services
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm">ElevenLabs API</span>
                    <Badge variant="outline" className="text-green-600">Connected</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">OpenAI API</span>
                    <Badge variant="outline" className="text-green-600">Connected</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Search APIs</span>
                    <Badge variant="outline" className="text-green-600">Active</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Rate Limits</span>
                    <Badge variant="outline" className="text-yellow-600">Monitored</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

