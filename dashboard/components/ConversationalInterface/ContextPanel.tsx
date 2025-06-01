"use client";

import React, { useState, useEffect, useRef } from 'react';
import { 
  CpuChipIcon, 
  ClockIcon, 
  ChartBarIcon,
  UserGroupIcon,
  BoltIcon,
  ServerIcon
} from '@heroicons/react/24/outline';
import type { ConversationContext, SystemMetrics, Agent } from '@/types/conversation';

interface ContextPanelProps {
  context: ConversationContext;
}

/**
 * ContextPanel Component
 * 
 * Displays contextual information about the system, active agents,
 * and recent activities. Updates in real-time for monitoring.
 */
export const ContextPanel: React.FC<ContextPanelProps> = ({ context }) => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isVisible, setIsVisible] = useState(true);
  
  // Refs for visibility detection
  const containerRef = useRef<HTMLDivElement>(null);
  
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

  /**
   * Fetch system metrics
   */
  const fetchMetrics = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/metrics`, {
        headers: {
          'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || ''
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      }
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    }
  };

  /**
   * Fetch active agents
   */
  const fetchAgents = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/agents`, {
        headers: {
          'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || ''
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAgents(data);
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Setup visibility observer
   */
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => setIsVisible(entry.isIntersecting),
      { threshold: 0.1 }
    );
    
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }
    
    return () => observer.disconnect();
  }, []);

  /**
   * Initial data fetch and polling setup (only when visible)
   */
  useEffect(() => {
    if (!isVisible) return;
    
    fetchMetrics();
    fetchAgents();
    
    // Poll for updates every 5 seconds when visible
    const interval = setInterval(() => {
      fetchMetrics();
      fetchAgents();
    }, 5000);
    
    return () => clearInterval(interval);
  }, [isVisible]);

  /**
   * Format uptime for display
   */
  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  /**
   * Get status color
   */
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'ready':
        return 'text-green-500';
      case 'idle':
        return 'text-yellow-500';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  return (
    <div ref={containerRef} className="h-full p-6 space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white mb-2">System Context</h2>
        <p className="text-sm text-gray-400">Real-time system information</p>
      </div>
      
      {/* System Status */}
      <div className="bg-gray-900 rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-medium text-gray-300 uppercase tracking-wider">
          System Status
        </h3>
        
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Status</span>
          <span className={`font-medium capitalize ${getStatusColor(context.systemStatus)}`}>
            {context.systemStatus}
          </span>
        </div>
        
        {metrics && (
          <>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 flex items-center">
                <CpuChipIcon className="h-4 w-4 mr-1" />
                CPU
              </span>
              <span className="text-white">{metrics.cpuUsage.toFixed(1)}%</span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-400 flex items-center">
                <ServerIcon className="h-4 w-4 mr-1" />
                Memory
              </span>
              <span className="text-white">{metrics.memoryUsage.toFixed(1)}%</span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-gray-400 flex items-center">
                <ClockIcon className="h-4 w-4 mr-1" />
                Uptime
              </span>
              <span className="text-white">{formatUptime(metrics.uptime)}</span>
            </div>
          </>
        )}
      </div>
      
      {/* Active Agents */}
      <div className="bg-gray-900 rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-medium text-gray-300 uppercase tracking-wider">
          Active Agents ({agents.length})
        </h3>
        
        {isLoading ? (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-sky-500 mx-auto"></div>
          </div>
        ) : agents.length > 0 ? (
          <div className="space-y-2">
            {agents.slice(0, 5).map((agent) => (
              <div key={agent.id} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${
                    agent.status === 'active' ? 'bg-green-500' : 'bg-gray-500'
                  }`} />
                  <span className="text-sm text-gray-300">{agent.name}</span>
                </div>
                <span className="text-xs text-gray-500">{agent.type}</span>
              </div>
            ))}
            {agents.length > 5 && (
              <p className="text-xs text-gray-500 text-center">
                +{agents.length - 5} more
              </p>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-500 text-center">No active agents</p>
        )}
      </div>
      
      {/* Recent Actions */}
      <div className="bg-gray-900 rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-medium text-gray-300 uppercase tracking-wider">
          Recent Actions
        </h3>
        
        {context.recentActions.length > 0 ? (
          <div className="space-y-2">
            {context.recentActions.slice(0, 5).map((action, index) => (
              <div key={index} className="flex items-center space-x-2">
                <BoltIcon className="h-4 w-4 text-yellow-500" />
                <span className="text-sm text-gray-300 truncate">{action}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500 text-center">No recent actions</p>
        )}
      </div>
      
      {/* Quick Stats */}
      {metrics && (
        <div className="bg-gray-900 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-300 uppercase tracking-wider mb-3">
            Quick Stats
          </h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-white">{metrics.activeAgents}</p>
              <p className="text-xs text-gray-400">Active Agents</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-white">{metrics.tasksCompleted}</p>
              <p className="text-xs text-gray-400">Tasks Done</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};