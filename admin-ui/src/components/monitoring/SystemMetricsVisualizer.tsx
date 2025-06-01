import React, { useState, useEffect } from 'react';
import { Cpu, HardDrive, Activity, Zap, TrendingUp, TrendingDown } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface MetricData {
  timestamp: string;
  cpu: number;
  memory: number;
  disk: number;
  network: number;
}

const SystemMetricsVisualizer: React.FC = () => {
  const [metricsHistory, setMetricsHistory] = useState<MetricData[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<'cpu' | 'memory' | 'disk' | 'network'>('cpu');

  // Simulate real-time metrics
  useEffect(() => {
    const generateMetric = (base: number, variance: number) => {
      return Math.max(0, Math.min(100, base + (Math.random() - 0.5) * variance));
    };

    const interval = setInterval(() => {
      const newMetric: MetricData = {
        timestamp: new Date().toLocaleTimeString(),
        cpu: generateMetric(45, 30),
        memory: generateMetric(60, 20),
        disk: generateMetric(75, 10),
        network: generateMetric(30, 40),
      };

      setMetricsHistory((prev) => {
        const updated = [...prev, newMetric];
        // Keep only last 20 data points
        return updated.slice(-20);
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const currentMetrics = metricsHistory[metricsHistory.length - 1] || {
    cpu: 0,
    memory: 0,
    disk: 0,
    network: 0,
  };

  const getMetricColor = (value: number) => {
    if (value > 80) return 'text-red-600 dark:text-red-400';
    if (value > 60) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-green-600 dark:text-green-400';
  };

  const getChartColor = (metric: string) => {
    switch (metric) {
      case 'cpu': return '#3b82f6';
      case 'memory': return '#8b5cf6';
      case 'disk': return '#f59e0b';
      case 'network': return '#10b981';
      default: return '#6b7280';
    }
  };

  const metricCards = [
    {
      key: 'cpu' as const,
      label: 'CPU Usage',
      icon: Cpu,
      value: currentMetrics.cpu,
      unit: '%',
      color: 'bg-blue-100 dark:bg-blue-900/30',
      iconColor: 'text-blue-600 dark:text-blue-400',
    },
    {
      key: 'memory' as const,
      label: 'Memory',
      icon: Activity,
      value: currentMetrics.memory,
      unit: '%',
      color: 'bg-purple-100 dark:bg-purple-900/30',
      iconColor: 'text-purple-600 dark:text-purple-400',
    },
    {
      key: 'disk' as const,
      label: 'Disk I/O',
      icon: HardDrive,
      value: currentMetrics.disk,
      unit: '%',
      color: 'bg-yellow-100 dark:bg-yellow-900/30',
      iconColor: 'text-yellow-600 dark:text-yellow-400',
    },
    {
      key: 'network' as const,
      label: 'Network',
      icon: Zap,
      value: currentMetrics.network,
      unit: 'Mbps',
      color: 'bg-green-100 dark:bg-green-900/30',
      iconColor: 'text-green-600 dark:text-green-400',
    },
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        System Metrics
      </h3>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {metricCards.map((metric) => (
          <button
            key={metric.key}
            onClick={() => setSelectedMetric(metric.key)}
            className={`p-4 rounded-lg border-2 transition-all ${
              selectedMetric === metric.key
                ? 'border-blue-500 shadow-lg'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className={`p-2 rounded-lg ${metric.color}`}>
                <metric.icon className={`h-5 w-5 ${metric.iconColor}`} />
              </div>
              {metric.value > 60 ? (
                <TrendingUp className="h-4 w-4 text-red-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-green-500" />
              )}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 text-left">{metric.label}</p>
            <p className={`text-2xl font-bold text-left ${getMetricColor(metric.value)}`}>
              {metric.value.toFixed(1)}{metric.unit}
            </p>
          </button>
        ))}
      </div>

      {/* Chart */}
      <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-4">
          {metricCards.find((m) => m.key === selectedMetric)?.label} - Last 40 seconds
        </h4>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={metricsHistory}>
              <defs>
                <linearGradient id={`gradient-${selectedMetric}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={getChartColor(selectedMetric)} stopOpacity={0.8} />
                  <stop offset="95%" stopColor={getChartColor(selectedMetric)} stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis 
                dataKey="timestamp" 
                stroke="#9ca3af"
                fontSize={12}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis 
                stroke="#9ca3af"
                fontSize={12}
                domain={[0, 100]}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '0.375rem',
                }}
                labelStyle={{ color: '#d1d5db' }}
                itemStyle={{ color: getChartColor(selectedMetric) }}
              />
              <Area
                type="monotone"
                dataKey={selectedMetric}
                stroke={getChartColor(selectedMetric)}
                strokeWidth={2}
                fill={`url(#gradient-${selectedMetric})`}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* System Info */}
      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
          <p className="text-gray-500 dark:text-gray-400">System Load</p>
          <p className="font-medium text-gray-900 dark:text-gray-100">
            {(currentMetrics.cpu / 100 * 4).toFixed(2)} / 4.00
          </p>
        </div>
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
          <p className="text-gray-500 dark:text-gray-400">Uptime</p>
          <p className="font-medium text-gray-900 dark:text-gray-100">14d 7h 23m</p>
        </div>
      </div>
    </div>
  );
};

export default SystemMetricsVisualizer; 