import React from 'react';
import { DollarSign, TrendingUp, AlertCircle, Shield, Activity, GitBranch } from 'lucide-react';

interface FinancialDashboardWidgetProps {
  apis?: string[];
  complianceRules?: string[];
}

const FinancialDashboardWidget: React.FC<FinancialDashboardWidgetProps> = ({ 
  apis = ['Stripe', 'PayPal'], 
  complianceRules = ['PCI-DSS', 'SOC2'] 
}) => {
  // Mock data for financial metrics
  const metrics = {
    dailyVolume: 145789.32,
    transactions: 1847,
    successRate: 99.2,
    fraudAlerts: 3,
    avgProcessingTime: '1.2s',
    activeDevOps: 12
  };

  const recentAlerts = [
    { id: 1, type: 'fraud', message: 'Suspicious pattern detected', severity: 'high' },
    { id: 2, type: 'compliance', message: 'PCI audit scheduled', severity: 'medium' },
    { id: 3, type: 'system', message: 'API rate limit warning', severity: 'low' },
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Financial Dashboard</h3>
        <div className="flex items-center space-x-2">
          {apis.map((api, idx) => (
            <span key={idx} className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">
              {api}
            </span>
          ))}
        </div>
      </div>

      {/* Transaction Monitor */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <DollarSign className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400">Volume</span>
          </div>
          <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
            ${metrics.dailyVolume.toLocaleString()}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Today</p>
        </div>

        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <Activity className="h-5 w-5 text-green-600 dark:text-green-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400">Success</span>
          </div>
          <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{metrics.successRate}%</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">{metrics.transactions} txns</p>
        </div>

        <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400">Alerts</span>
          </div>
          <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{metrics.fraudAlerts}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Active</p>
        </div>
      </div>

      {/* DevOps Integration */}
      <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <GitBranch className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">DevOps Status</span>
          </div>
          <span className="text-xs text-green-600 dark:text-green-400">● Active</span>
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-gray-500 dark:text-gray-400">Deployments:</span>
            <span className="ml-2 text-gray-900 dark:text-gray-100 font-medium">{metrics.activeDevOps}</span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Avg Response:</span>
            <span className="ml-2 text-gray-900 dark:text-gray-100 font-medium">{metrics.avgProcessingTime}</span>
          </div>
        </div>
      </div>

      {/* Audit Trail */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">Recent Activity</h4>
          <div className="flex items-center space-x-1 text-xs text-gray-500 dark:text-gray-400">
            <Shield className="h-3 w-3" />
            <span>{complianceRules.join(', ')}</span>
          </div>
        </div>
        <div className="space-y-2">
          {recentAlerts.map((alert) => (
            <div key={alert.id} className={`p-3 rounded-md border ${
              alert.severity === 'high' 
                ? 'border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/20' 
                : alert.severity === 'medium'
                ? 'border-yellow-300 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/20'
                : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/30'
            }`}>
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-900 dark:text-gray-100">{alert.message}</p>
                <span className={`text-xs px-2 py-1 rounded ${
                  alert.severity === 'high' 
                    ? 'bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200' 
                    : alert.severity === 'medium'
                    ? 'bg-yellow-200 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-200'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                }`}>
                  {alert.type}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <button className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition-colors">
          Open Financial Control Center
        </button>
      </div>
    </div>
  );
};

export default FinancialDashboardWidget; 