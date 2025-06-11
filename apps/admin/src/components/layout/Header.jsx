import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Wifi, 
  WifiOff, 
  AlertCircle, 
  CheckCircle,
  Clock,
  Settings
} from 'lucide-react'
import { cn } from '@/lib/utils'

const connectionStatusConfig = {
  connected: {
    icon: CheckCircle,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    label: 'Connected',
    description: 'Real-time updates active'
  },
  connecting: {
    icon: Clock,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
    label: 'Connecting',
    description: 'Establishing connection...'
  },
  disconnected: {
    icon: WifiOff,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    label: 'Disconnected',
    description: 'No real-time updates'
  },
  error: {
    icon: AlertCircle,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    label: 'Error',
    description: 'Connection failed'
  }
}

export function Header({ connectionStatus, isConnected }) {
  const statusConfig = connectionStatusConfig[connectionStatus] || connectionStatusConfig.disconnected
  const StatusIcon = statusConfig.icon

  return (
    <header className="bg-card border-b border-border px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Page Title */}
        <div>
          <h1 className="text-2xl font-semibold text-foreground">
            AI Assistant Admin Interface
          </h1>
          <p className="text-sm text-muted-foreground">
            Mission Control for Cherry, Sophia & Karen
          </p>
        </div>

        {/* Status and Actions */}
        <div className="flex items-center gap-4">
          {/* Connection Status */}
          <div className="flex items-center gap-2">
            <div className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-full",
              statusConfig.bgColor
            )}>
              <StatusIcon className={cn("h-4 w-4", statusConfig.color)} />
              <span className={cn("text-sm font-medium", statusConfig.color)}>
                {statusConfig.label}
              </span>
            </div>
          </div>

          {/* Real-time Indicator */}
          {isConnected && (
            <div className="flex items-center gap-2">
              <div className="relative">
                <Wifi className="h-4 w-4 text-green-500" />
                <div className="absolute -top-1 -right-1 h-2 w-2 bg-green-500 rounded-full animate-pulse" />
              </div>
              <span className="text-sm text-muted-foreground">Live</span>
            </div>
          )}

          {/* Settings Button */}
          <Button variant="ghost" size="sm">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Connection Details */}
      {connectionStatus !== 'connected' && (
        <div className="mt-2">
          <Badge variant="outline" className={statusConfig.color}>
            {statusConfig.description}
          </Badge>
        </div>
      )}
    </header>
  )
}

