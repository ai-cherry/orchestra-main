'use client';

import React from 'react';
import { 
  Server, 
  Database, 
  Activity, 
  Users, 
  Cherry, 
  Brain, 
  Stethoscope,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3
} from 'lucide-react';

export function DashboardOverview() {
  const infrastructureMetrics = {
    totalServers: 7,
    activeServers: 7,
    uptime: '99.9%',
    monthlyCost: '$455',
    databases: {
      postgresql: 'Running',
      redis: 'Running',
      weaviate: 'Running',
      pinecone: 'Connected'
    },
    monitoring: {
      prometheus: 'Collecting Metrics',
      grafana: '5 Active Dashboards',
      elk: 'Logging Active',
      alerts: 0
    }
  };

  const domainMetrics = {
    cherry: {
      status: 'Active',
      lastInteraction: '2 minutes ago',
      tasksCompleted: 23,
      satisfaction: 98
    },
    sophia: {
      status: 'Ready',
      lastInteraction: '15 minutes ago',
      reportsGenerated: 5,
      insights: 12
    },
    karen: {
      status: 'Standby',
      lastInteraction: '1 hour ago',
      patientsProcessed: 0,
      compliance: 100
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>
          <p className="text-gray-600">Real-time status of your AI orchestrator system</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-600">System Operational</span>
          </div>
        </div>
      </div>

      {/* Infrastructure Status */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center">
            <Server className="h-5 w-5 mr-2 text-indigo-600" />
            Infrastructure Status
          </h2>
          <span className="text-sm text-gray-500">Tier 2 Enterprise Setup</span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="metric-card">
            <div className="flex items-center justify-between">
              <div>
                <p className="metric-label">Total Servers</p>
                <p className="metric-value">{infrastructureMetrics.totalServers} Active</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </div>
          
          <div className="metric-card">
            <div className="flex items-center justify-between">
              <div>
                <p className="metric-label">Monthly Cost</p>
                <p className="metric-value">{infrastructureMetrics.monthlyCost}</p>
              </div>
              <BarChart3 className="h-8 w-8 text-blue-500" />
            </div>
          </div>
          
          <div className="metric-card">
            <div className="flex items-center justify-between">
              <div>
                <p className="metric-label">Uptime</p>
                <p className="metric-value">{infrastructureMetrics.uptime}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-500" />
            </div>
          </div>
          
          <div className="metric-card">
            <div className="flex items-center justify-between">
              <div>
                <p className="metric-label">Active Alerts</p>
                <p className="metric-value">{infrastructureMetrics.monitoring.alerts}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-gray-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Domain Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cherry Domain */}
        <div className="domain-card cherry">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Cherry className="h-6 w-6 text-cherry-500 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Cherry</h3>
            </div>
            <span className="status-indicator online">Active</span>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Last Interaction</span>
              <span className="text-sm font-medium">{domainMetrics.cherry.lastInteraction}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Tasks Completed</span>
              <span className="text-sm font-medium">{domainMetrics.cherry.tasksCompleted}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Satisfaction</span>
              <span className="text-sm font-medium text-green-600">{domainMetrics.cherry.satisfaction}%</span>
            </div>
          </div>
          
          <div className="mt-4 pt-4 border-t border-cherry-200">
            <p className="text-xs text-gray-500">Personal assistant for lifestyle, entertainment, and ranch management</p>
          </div>
        </div>

        {/* Sophia Domain */}
        <div className="domain-card sophia">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Brain className="h-6 w-6 text-sophia-500 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Sophia</h3>
            </div>
            <span className="status-indicator warning">Ready</span>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Last Interaction</span>
              <span className="text-sm font-medium">{domainMetrics.sophia.lastInteraction}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Reports Generated</span>
              <span className="text-sm font-medium">{domainMetrics.sophia.reportsGenerated}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Insights</span>
              <span className="text-sm font-medium text-blue-600">{domainMetrics.sophia.insights}</span>
            </div>
          </div>
          
          <div className="mt-4 pt-4 border-t border-sophia-200">
            <p className="text-xs text-gray-500">Business intelligence for Pay Ready operations and analytics</p>
          </div>
        </div>

        {/* Karen Domain */}
        <div className="domain-card karen">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Stethoscope className="h-6 w-6 text-karen-500 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Karen</h3>
            </div>
            <span className="status-indicator warning">Standby</span>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Last Interaction</span>
              <span className="text-sm font-medium">{domainMetrics.karen.lastInteraction}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Patients Processed</span>
              <span className="text-sm font-medium">{domainMetrics.karen.patientsProcessed}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Compliance</span>
              <span className="text-sm font-medium text-green-600">{domainMetrics.karen.compliance}%</span>
            </div>
          </div>
          
          <div className="mt-4 pt-4 border-t border-karen-200">
            <p className="text-xs text-gray-500">Healthcare operations for ParagonRX management</p>
          </div>
        </div>
      </div>

      {/* Database & Monitoring Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Database Stack */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Database className="h-5 w-5 mr-2 text-green-600" />
            Database Stack
          </h3>
          
          <div className="space-y-3">
            {Object.entries(infrastructureMetrics.databases).map(([db, status]) => (
              <div key={db} className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 capitalize">{db}</span>
                <span className="status-indicator online">{status}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Monitoring & Logging */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Activity className="h-5 w-5 mr-2 text-blue-600" />
            Monitoring & Logging
          </h3>
          
          <div className="space-y-3">
            {Object.entries(infrastructureMetrics.monitoring).map(([service, status]) => (
              <div key={service} className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 capitalize">{service}</span>
                <span className="status-indicator online">{status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="btn-secondary flex items-center justify-center space-x-2">
            <Activity className="h-4 w-4" />
            <span>Health Check</span>
          </button>
          
          <button className="btn-secondary flex items-center justify-center space-x-2">
            <BarChart3 className="h-4 w-4" />
            <span>View Metrics</span>
          </button>
          
          <button className="btn-secondary flex items-center justify-center space-x-2">
            <Database className="h-4 w-4" />
            <span>Backup Data</span>
          </button>
          
          <button className="btn-primary flex items-center justify-center space-x-2">
            <Users className="h-4 w-4" />
            <span>Deploy App</span>
          </button>
        </div>
      </div>
    </div>
  );
}

