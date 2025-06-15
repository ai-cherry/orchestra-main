import React, { useState, useEffect } from 'react';
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
import { api } from '../lib/api';

const HealthDashboard = () => {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [error, setError] = useState(null);

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      
      // Try multiple health endpoints
      let data = null;
      const endpoints = ['/health', '/api/health/', '/api/health'];
      
      for (const endpoint of endpoints) {
        try {
          data = await api.get(endpoint);
          break;
        } catch (err) {
          console.warn(`Health endpoint ${endpoint} failed:`, err.message);
        }
      }
      
      if (!data) {
        throw new Error('All health endpoints failed');
      }
      
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
    const bgColor = status === 'healthy' ? 'bg-green-500/10 text-green-500 border-green-500/20' : 
                   status === 'warning' ? 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20' : 
                   'bg-red-500/10 text-red-500 border-red-500/20';
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md border text-xs font-medium ${bgColor}`}>
        {getStatusIcon(status)}
        {status.toUpperCase()}
      </span>
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
            <div key={i} className="bg-card border border-border rounded-xl p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
              <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            </div>
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
            className="flex items-center gap-2 px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <XCircle className="w-5 h-5 text-red-500" />
            <div>
              <p className="font-medium text-red-500">Health Check Failed</p>
              <p className="text-sm text-red-400">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Basic Health Status */}
      {healthData && (
        <div className="bg-card border border-border rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4">API Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="flex items-center justify-between p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
              <div>
                <p className="font-medium">Service</p>
                <p className="text-sm text-muted-foreground">{healthData.service || 'Orchestra API'}</p>
              </div>
              {getStatusBadge(healthData.status === 'healthy' ? 'healthy' : 'error')}
            </div>
            
            {healthData.version && (
              <div className="flex items-center justify-between p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <div>
                  <p className="font-medium">Version</p>
                  <p className="text-sm text-muted-foreground">{healthData.version}</p>
                </div>
                <span className="text-blue-500 font-medium">✓ Active</span>
              </div>
            )}
            
            {healthData.timestamp && (
              <div className="flex items-center justify-between p-4 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                <div>
                  <p className="font-medium">Last Check</p>
                  <p className="text-sm text-muted-foreground">
                    {new Date(healthData.timestamp).toLocaleTimeString()}
                  </p>
                </div>
                <span className="text-purple-500 font-medium">✓ Recent</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* System Resources */}
      {healthData?.system && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium">CPU Usage</h3>
              <Activity className="h-5 w-5 text-muted-foreground" />
            </div>
            <div className="text-2xl font-bold">{healthData.system.cpu?.usage_percent?.toFixed(1)}%</div>
            <div className="flex items-center gap-2 mt-2">
              {getStatusBadge(healthData.system.cpu?.status || 'healthy')}
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium">Memory Usage</h3>
              <Database className="h-5 w-5 text-muted-foreground" />
            </div>
            <div className="text-2xl font-bold">{healthData.system.memory?.usage_percent?.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              {healthData.system.memory?.used_gb}GB / {healthData.system.memory?.total_gb}GB
            </p>
            <div className="flex items-center gap-2 mt-2">
              {getStatusBadge(healthData.system.memory?.status || 'healthy')}
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium">Disk Usage</h3>
              <Server className="h-5 w-5 text-muted-foreground" />
            </div>
            <div className="text-2xl font-bold">{healthData.system.disk?.usage_percent?.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              {healthData.system.disk?.used_gb}GB / {healthData.system.disk?.total_gb}GB
            </p>
            <div className="flex items-center gap-2 mt-2">
              {getStatusBadge(healthData.system.disk?.status || 'healthy')}
            </div>
          </div>
        </div>
      )}

      {/* API Health */}
      {healthData?.apis && (
        <div className="bg-card border border-border rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Wifi className="w-5 h-5" />
            API Health Status
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(healthData.apis).map(([apiName, apiData]) => (
              <div key={apiName} className="flex items-center justify-between p-3 border border-border rounded-lg">
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
        </div>
      )}

      {/* Services Status */}
      {healthData?.services && (
        <div className="bg-card border border-border rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Server className="w-5 h-5" />
            Services Status
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(healthData.services).map(([serviceName, serviceData]) => (
              <div key={serviceName} className="flex items-center justify-between p-3 border border-border rounded-lg">
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
        </div>
      )}

      {/* Secrets Status */}
      {healthData?.secrets && (
        <div className="bg-card border border-border rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Key className="w-5 h-5" />
            Secrets & API Keys
          </h2>
          <p className="text-sm text-muted-foreground mb-4">
            API keys and secrets availability ({healthData.secrets.available_count}/{healthData.secrets.total_count} configured)
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {healthData.secrets.validation && Object.entries(healthData.secrets.validation).map(([secretName, isAvailable]) => (
              <div key={secretName} className="flex items-center justify-between p-3 border border-border rounded-lg">
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
        </div>
      )}
    </div>
  );
};

export default HealthDashboard;

