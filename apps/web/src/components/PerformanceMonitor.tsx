import React, { useEffect, useState } from 'react';
import { useAI } from '../contexts/AIContext';

interface PerformanceData {
  buildTime: number;
  loadTime: number;
  aiResponseTime: number;
  bundleSize: number;
  renderTime: number;
}

const PerformanceMonitor: React.FC = () => {
  const { state, updatePerformanceMetrics } = useAI();
  const [performanceData, setPerformanceData] = useState<PerformanceData>({
    buildTime: 0,
    loadTime: 0,
    aiResponseTime: 0,
    bundleSize: 0,
    renderTime: 0
  });

  useEffect(() => {
    // Track initial load time
    const startTime = performance.now();
    
    const trackPerformance = () => {
      const loadTime = performance.now() - startTime;
      
      // Get performance entries
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const renderTime = navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart;
      
      const newData: PerformanceData = {
        buildTime: state.performanceMetrics.buildTime,
        loadTime: loadTime,
        aiResponseTime: state.performanceMetrics.aiResponseTime,
        bundleSize: Math.round((document.documentElement.innerHTML.length / 1024)), // Rough estimate
        renderTime: renderTime
      };

      setPerformanceData(newData);
      updatePerformanceMetrics({
        responseTime: loadTime,
        buildTime: newData.buildTime
      });
    };

    // Track when the page is fully loaded
    if (document.readyState === 'complete') {
      trackPerformance();
    } else {
      window.addEventListener('load', trackPerformance);
    }

    return () => window.removeEventListener('load', trackPerformance);
  }, [updatePerformanceMetrics, state.performanceMetrics.buildTime, state.performanceMetrics.aiResponseTime]);

  // Track AI response times
  useEffect(() => {
    const startTime = Date.now();
    
    // Simulate AI response tracking (replace with actual AI calls)
    const trackAIResponse = () => {
      const responseTime = Date.now() - startTime;
      updatePerformanceMetrics({ aiResponseTime: responseTime });
      setPerformanceData(prev => ({ ...prev, aiResponseTime: responseTime }));
    };

    // Example: Track after a short delay (replace with actual AI integration)
    const timeout = setTimeout(trackAIResponse, 1000);
    return () => clearTimeout(timeout);
  }, [updatePerformanceMetrics]);

  // Performance targets from the plan
  const targets = {
    buildTime: 15000, // 15s target (current: 38s)
    loadTime: 2000,   // 2s target (current: 6s)
    aiResponseTime: 800, // 800ms target (current: 10s)
    bundleSize: 1000,    // 1MB target
    renderTime: 500      // 500ms target
  };

  const getPerformanceStatus = (value: number, target: number) => {
    if (value <= target * 0.8) return 'excellent';
    if (value <= target) return 'good';
    if (value <= target * 1.5) return 'fair';
    return 'poor';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent': return 'text-green-600';
      case 'good': return 'text-blue-600';
      case 'fair': return 'text-yellow-600';
      case 'poor': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatSize = (kb: number) => {
    if (kb < 1024) return `${kb}KB`;
    return `${(kb / 1024).toFixed(1)}MB`;
  };

  // Only show in development or when AI features are enabled
  if (process.env.NODE_ENV === 'production' && !state.aiAssistantActive) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 min-w-64 z-50 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
          Performance Monitor
        </h3>
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-xs text-gray-500">Live</span>
        </div>
      </div>
      
      <div className="space-y-2">
        {/* Build Time */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600 dark:text-gray-400">Build:</span>
          <span className={`text-xs font-mono ${getStatusColor(getPerformanceStatus(performanceData.buildTime, targets.buildTime))}`}>
            {formatTime(performanceData.buildTime)}
          </span>
        </div>

        {/* Load Time */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600 dark:text-gray-400">Load:</span>
          <span className={`text-xs font-mono ${getStatusColor(getPerformanceStatus(performanceData.loadTime, targets.loadTime))}`}>
            {formatTime(performanceData.loadTime)}
          </span>
        </div>

        {/* AI Response Time */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600 dark:text-gray-400">AI:</span>
          <span className={`text-xs font-mono ${getStatusColor(getPerformanceStatus(performanceData.aiResponseTime, targets.aiResponseTime))}`}>
            {formatTime(performanceData.aiResponseTime)}
          </span>
        </div>

        {/* Bundle Size */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600 dark:text-gray-400">Bundle:</span>
          <span className={`text-xs font-mono ${getStatusColor(getPerformanceStatus(performanceData.bundleSize, targets.bundleSize))}`}>
            {formatSize(performanceData.bundleSize)}
          </span>
        </div>

        {/* Render Time */}
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600 dark:text-gray-400">Render:</span>
          <span className={`text-xs font-mono ${getStatusColor(getPerformanceStatus(performanceData.renderTime, targets.renderTime))}`}>
            {formatTime(performanceData.renderTime)}
          </span>
        </div>
      </div>

      {/* Performance Summary */}
      <div className="mt-3 pt-2 border-t border-gray-200 dark:border-gray-700">
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600 dark:text-gray-400">Overall:</span>
          <div className="flex items-center space-x-1">
            {Object.entries(performanceData).map(([key, value]) => {
              const target = targets[key as keyof typeof targets];
              const status = getPerformanceStatus(value, target);
              return (
                <div
                  key={key}
                  className={`w-2 h-2 rounded-full ${
                    status === 'excellent' ? 'bg-green-500' :
                    status === 'good' ? 'bg-blue-500' :
                    status === 'fair' ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  title={`${key}: ${status}`}
                />
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceMonitor; 