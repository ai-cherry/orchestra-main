import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Activity, 
  Server, 
  Database, 
  Key, 
  Wifi, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  RefreshCw,
  Clock
} from 'lucide-react';
import { api } from '@/lib/api';

const HealthDashboard = () => {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [error, setError] = useState(null);

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      const data = await api.get('/api/health/');
      setHealthData(data);
      setLastUpdate(new Date());
      setError(null);
    } catch (error) {
      console.error('Failed to fetch health data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchHealthData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-500';
      case 'warning': return 'text-yellow-500';
      case 'critical': return 'text-red-500';
      case 'error': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'warning': return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'critical': return <XCircle className="w-4 h-4 text-red-500" />;
      case 'error': return <XCircle className="w-4 h-4 text-red-500" />;
      default: return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const variant = status === 'healthy' ? 'default' : 
                   status === 'warning' ? 'secondary' : 'destructive';
    return (
      <Badge variant={variant} className="flex items-center gap-1">
        {getStatusIcon(status)}
        {status.toUpperCase()}
      </Badge>
    );
  };

  if (loading && !healthData) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Health Monitor</h1>
          <RefreshCw className="w-6 h-6 animate-spin" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Health Monitor</h1>
          <p className="text-muted-foreground">Real-time system and API health monitoring</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="w-4 h-4" />
            {lastUpdate && `Last updated: ${lastUpdate.toLocaleTimeString()}`}
          </div>
          <button
            onClick={fetchHealthData}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Overall Status Alert */}
      {healthData && (
        <Alert className={`border-l-4 ${
          healthData.overall_status === 'healthy' ? 'border-l-green-500' :
          healthData.overall_status === 'warning' ? 'border-l-yellow-500' : 'border-l-red-500'
        }`}>
          <div className="flex items-center gap-2">
            {getStatusIcon(healthData.overall_status)}
            <AlertDescription className="font-medium">
              System Status: {healthData.overall_status.toUpperCase()}
              {healthData.overall_status !== 'healthy' && ' - Some issues detected'}
            </AlertDescription>
          </div>
        </Alert>
      )}

      {/* System Resources */}
      {healthData?.system && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{healthData.system.cpu?.usage_percent?.toFixed(1)}%</div>
              <div className="flex items-center gap-2 mt-2">
                {getStatusBadge(healthData.system.cpu?.status || 'unknown')}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{healthData.system.memory?.usage_percent?.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">
                {healthData.system.memory?.used_gb}GB / {healthData.system.memory?.total_gb}GB
              </p>
              <div className="flex items-center gap-2 mt-2">
                {getStatusBadge(healthData.system.memory?.status || 'unknown')}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Disk Usage</CardTitle>
              <Server className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{healthData.system.disk?.usage_percent?.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">
                {healthData.system.disk?.used_gb}GB / {healthData.system.disk?.total_gb}GB
              </p>
              <div className="flex items-center gap-2 mt-2">
                {getStatusBadge(healthData.system.disk?.status || 'unknown')}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* API Health */}
      {healthData?.apis && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wifi className="w-5 h-5" />
              API Health Status
            </CardTitle>
            <CardDescription>External API connections and response times</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(healthData.apis).map(([apiName, apiData]) => (
                <div key={apiName} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p className="font-medium capitalize">{apiName.replace('_', ' ')}</p>
                    {apiData.response_time && (
                      <p className="text-xs text-muted-foreground">
                        {(apiData.response_time * 1000).toFixed(0)}ms
                      </p>
                    )}
                  </div>
                  {getStatusBadge(apiData.status || 'unknown')}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Services Status */}
      {healthData?.services && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="w-5 h-5" />
              Services Status
            </CardTitle>
            <CardDescription>Running services and processes</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(healthData.services).map(([serviceName, serviceData]) => (
                <div key={serviceName} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p className="font-medium capitalize">{serviceName.replace('_', ' ')}</p>
                    {serviceData.pid && (
                      <p className="text-xs text-muted-foreground">PID: {serviceData.pid}</p>
                    )}
                  </div>
                  {getStatusBadge(serviceData.status || 'unknown')}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Secrets Status */}
      {healthData?.secrets && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="w-5 h-5" />
              Secrets & API Keys
            </CardTitle>
            <CardDescription>
              API keys and secrets availability ({healthData.secrets.available_count}/{healthData.secrets.total_count} configured)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {healthData.secrets.validation && Object.entries(healthData.secrets.validation).map(([secretName, isAvailable]) => (
                <div key={secretName} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p className="font-medium">{secretName}</p>
                    {healthData.secrets.ai_accessible?.[secretName]?.masked_value && (
                      <p className="text-xs text-muted-foreground font-mono">
                        {healthData.secrets.ai_accessible[secretName].masked_value}
                      </p>
                    )}
                  </div>
                  {getStatusBadge(isAvailable ? 'healthy' : 'error')}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default HealthDashboard;

