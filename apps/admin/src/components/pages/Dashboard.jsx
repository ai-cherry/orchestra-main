import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { useSystemStore } from '../../stores/systemStore'
import { usePersonaStore } from '../../stores/personaStore'
import { 
  Activity, 
  Cpu, 
  HardDrive, 
  Users, 
  Zap, 
  TrendingUp,
  Heart,
  Briefcase,
  Stethoscope,
  ArrowUpRight,
  ArrowDownRight,
  Minus
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

function SystemMetricCard({ title, value, unit, trend, icon: Icon, description }) {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up': return <ArrowUpRight className="h-4 w-4 text-green-500" />
      case 'down': return <ArrowDownRight className="h-4 w-4 text-red-500" />
      default: return <Minus className="h-4 w-4 text-gray-500" />
    }
  }

  const formatValue = (val) => {
    if (typeof val === 'number') {
      return val.toFixed(1)
    }
    return val
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold">
              {formatValue(value)}{unit && <span className="text-sm text-muted-foreground ml-1">{unit}</span>}
            </div>
            {description && (
              <p className="text-xs text-muted-foreground mt-1">{description}</p>
            )}
          </div>
          {trend && getTrendIcon()}
        </div>
      </CardContent>
    </Card>
  )
}

function PersonaStatusCard({ persona }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-500'
      case 'idle': return 'bg-yellow-500'
      case 'error': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getPersonaIcon = (id) => {
    switch (id) {
      case 'cherry': return Heart
      case 'sophia': return Briefcase
      case 'karen': return Stethoscope
      default: return Users
    }
  }

  const PersonaIcon = getPersonaIcon(persona.id)

  return (
    <Card className={`border-l-4 ${persona.borderColor}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${persona.accentColor}/10`}>
              <PersonaIcon className={`h-5 w-5 ${persona.accentColor.replace('bg-', 'text-')}`} />
            </div>
            <div>
              <CardTitle className="text-lg">{persona.name}</CardTitle>
              <CardDescription>{persona.title}</CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className={`h-2 w-2 rounded-full ${getStatusColor(persona.status)}`} />
            <Badge variant="outline" className="capitalize">
              {persona.status}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Personality Health */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span>Personality Health</span>
            <span>{persona.personalityHealth.toFixed(1)}%</span>
          </div>
          <Progress value={persona.personalityHealth} className="h-2" />
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">Interactions</p>
            <p className="font-medium">{persona.interactionCount}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Memory Usage</p>
            <p className="font-medium">{persona.memoryUsage.toFixed(1)} MB</p>
          </div>
          <div>
            <p className="text-muted-foreground">Voice Status</p>
            <p className="font-medium capitalize">{persona.voiceStatus}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Coordination</p>
            <p className="font-medium capitalize">{persona.coordinationStatus}</p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Button size="sm" variant="outline" className="flex-1">
            Configure
          </Button>
          <Button size="sm" variant="outline" className="flex-1">
            Monitor
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function SystemMetricsChart() {
  const { getMetricsForChart } = useSystemStore()
  const cpuData = getMetricsForChart('cpu_usage_percent', 20)
  const memoryData = getMetricsForChart('memory_usage_mb', 20)

  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle>System Performance</CardTitle>
        <CardDescription>Real-time CPU and memory usage</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={cpuData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#3b82f6" 
                strokeWidth={2}
                name="CPU Usage (%)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

export function Dashboard() {
  const { systemHealth, updateSystemHealth } = useSystemStore()
  const { personas } = usePersonaStore()

  // Simulate real-time updates (will be replaced with actual WebSocket data)
  useEffect(() => {
    const interval = setInterval(() => {
      updateSystemHealth({
        timestamp: new Date().toISOString(),
        memory_usage_mb: Math.random() * 500 + 300,
        cpu_usage_percent: Math.random() * 80 + 10,
        active_connections: Math.floor(Math.random() * 30) + 15,
        response_time_ms: Math.random() * 150 + 25,
        error_rate_percent: Math.random() * 3,
        uptime_hours: 24.5 + Math.random() * 0.1
      })
    }, 2000)

    return () => clearInterval(interval)
  }, [updateSystemHealth])

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Real-time overview of your AI assistant ecosystem
        </p>
      </div>

      {/* System Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <SystemMetricCard
          title="Memory Usage"
          value={systemHealth.memory_usage_mb}
          unit="MB"
          trend="stable"
          icon={HardDrive}
          description="System memory consumption"
        />
        <SystemMetricCard
          title="CPU Usage"
          value={systemHealth.cpu_usage_percent}
          unit="%"
          trend="down"
          icon={Cpu}
          description="Processor utilization"
        />
        <SystemMetricCard
          title="Active Connections"
          value={systemHealth.active_connections}
          trend="up"
          icon={Activity}
          description="Real-time connections"
        />
        <SystemMetricCard
          title="Response Time"
          value={systemHealth.response_time_ms}
          unit="ms"
          trend="stable"
          icon={Zap}
          description="Average response latency"
        />
      </div>

      {/* Performance Chart */}
      <div className="grid gap-4 md:grid-cols-3">
        <SystemMetricsChart />
        
        {/* Quick Stats */}
        <Card>
          <CardHeader>
            <CardTitle>System Health</CardTitle>
            <CardDescription>Overall system status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm">Uptime</span>
              <span className="font-medium">{systemHealth.uptime_hours.toFixed(1)}h</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Error Rate</span>
              <span className="font-medium">{systemHealth.error_rate_percent.toFixed(2)}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Status</span>
              <Badge variant="outline" className="text-green-600">
                Healthy
              </Badge>
            </div>
            <div className="pt-2">
              <Button className="w-full" variant="outline">
                <TrendingUp className="h-4 w-4 mr-2" />
                View Detailed Metrics
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Persona Status Cards */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">AI Personas</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {personas.map((persona) => (
            <PersonaStatusCard key={persona.id} persona={persona} />
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest system events and interactions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
              <div className="h-2 w-2 bg-green-500 rounded-full" />
              <div className="flex-1">
                <p className="text-sm font-medium">Cherry personality updated</p>
                <p className="text-xs text-muted-foreground">Playfulness increased to 95%</p>
              </div>
              <span className="text-xs text-muted-foreground">2 min ago</span>
            </div>
            <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
              <div className="h-2 w-2 bg-blue-500 rounded-full" />
              <div className="flex-1">
                <p className="text-sm font-medium">Sophia workflow executed</p>
                <p className="text-xs text-muted-foreground">Market analysis completed successfully</p>
              </div>
              <span className="text-xs text-muted-foreground">5 min ago</span>
            </div>
            <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
              <div className="h-2 w-2 bg-green-500 rounded-full" />
              <div className="flex-1">
                <p className="text-sm font-medium">Karen voice settings updated</p>
                <p className="text-xs text-muted-foreground">Stability adjusted for medical consultations</p>
              </div>
              <span className="text-xs text-muted-foreground">8 min ago</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

