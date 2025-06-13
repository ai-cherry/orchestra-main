import { Activity, Cpu, HardDrive, Wifi, AlertTriangle, CheckCircle } from 'lucide-react'

export default function SystemMonitor() {
  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">System Monitor</h1>
          <p className="text-muted-foreground">Real-time system performance and health monitoring</p>
        </div>
      </div>

      {/* API Tests */}
      <div className="bg-card border border-border rounded-xl p-6">
        <h2 className="text-xl font-semibold text-foreground mb-4">API Tests</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="p-4 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors">
            Test System Status
          </button>
          <button className="p-4 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors">
            Test Agents
          </button>
          <button className="p-4 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors">
            Test Deploy Agent
          </button>
        </div>
      </div>

      {/* Frontend Tests */}
      <div className="bg-card border border-border rounded-xl p-6">
        <h2 className="text-xl font-semibold text-foreground mb-4">Frontend Tests</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button className="p-4 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors">
            Test Navigation
          </button>
          <button className="p-4 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors">
            Test Chat Interface
          </button>
        </div>
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-500" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">System Status</h3>
              <p className="text-sm text-muted-foreground">4 agents, 10.5% CPU</p>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Uptime</span>
              <span className="text-foreground">2d 14h 32m</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Memory</span>
              <span className="text-foreground">2.1GB / 8GB</span>
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-500" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Navigation</h3>
              <p className="text-sm text-muted-foreground">Admin interface accessible</p>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Response Time</span>
              <span className="text-foreground">45ms</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Availability</span>
              <span className="text-foreground">99.9%</span>
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-500" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground">Agents List</h3>
              <p className="text-sm text-muted-foreground">Found 6 agents</p>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Active</span>
              <span className="text-foreground">4</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Idle</span>
              <span className="text-foreground">2</span>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center">
              <Cpu className="w-5 h-5 text-blue-500" />
            </div>
            <span className="text-2xl font-bold text-foreground">10.5%</span>
          </div>
          <h3 className="font-medium text-foreground">CPU Usage</h3>
          <div className="w-full bg-muted rounded-full h-2 mt-2">
            <div className="bg-blue-500 h-2 rounded-full" style={{ width: '10.5%' }}></div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
              <Activity className="w-5 h-5 text-green-500" />
            </div>
            <span className="text-2xl font-bold text-foreground">26%</span>
          </div>
          <h3 className="font-medium text-foreground">Memory</h3>
          <div className="w-full bg-muted rounded-full h-2 mt-2">
            <div className="bg-green-500 h-2 rounded-full" style={{ width: '26%' }}></div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 bg-purple-500/10 rounded-lg flex items-center justify-center">
              <HardDrive className="w-5 h-5 text-purple-500" />
            </div>
            <span className="text-2xl font-bold text-foreground">45%</span>
          </div>
          <h3 className="font-medium text-foreground">Disk Usage</h3>
          <div className="w-full bg-muted rounded-full h-2 mt-2">
            <div className="bg-purple-500 h-2 rounded-full" style={{ width: '45%' }}></div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 bg-orange-500/10 rounded-lg flex items-center justify-center">
              <Wifi className="w-5 h-5 text-orange-500" />
            </div>
            <span className="text-2xl font-bold text-foreground">1.2MB/s</span>
          </div>
          <h3 className="font-medium text-foreground">Network</h3>
          <div className="w-full bg-muted rounded-full h-2 mt-2">
            <div className="bg-orange-500 h-2 rounded-full" style={{ width: '60%' }}></div>
          </div>
        </div>
      </div>
    </div>
  )
}

