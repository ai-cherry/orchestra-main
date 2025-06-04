'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

interface Server {
  id: string;
  name: string;
  ip: string;
  status: 'running' | 'stopped' | 'starting' | 'stopping';
  cpu: string;
  memory: string;
  type: 'production' | 'database' | 'staging' | 'worker' | 'loadbalancer';
}

interface DatabaseStatus {
  postgresql: 'running' | 'stopped' | 'error';
  redis: 'running' | 'stopped' | 'error';
  weaviate: 'running' | 'stopped' | 'error';
  pinecone: 'connected' | 'disconnected' | 'error';
}

interface MonitoringStatus {
  prometheus: 'active' | 'inactive' | 'error';
  grafana: 'active' | 'inactive' | 'error';
  elk: 'active' | 'inactive' | 'error';
  alerts: number;
}

interface InfrastructureState {
  servers: Server[];
  databases: DatabaseStatus;
  monitoring: MonitoringStatus;
  uptime: string;
  monthlyCost: number;
  lastUpdated: Date;
}

interface InfrastructureContextType {
  infrastructure: InfrastructureState;
  refreshInfrastructure: () => Promise<void>;
  startServer: (serverId: string) => Promise<boolean>;
  stopServer: (serverId: string) => Promise<boolean>;
  restartServer: (serverId: string) => Promise<boolean>;
  isLoading: boolean;
}

const InfrastructureContext = createContext<InfrastructureContextType | undefined>(undefined);

// Mock data - in production this would come from your infrastructure APIs
const mockServers: Server[] = [
  {
    id: '1',
    name: 'Production Server',
    ip: '45.32.69.157',
    status: 'running',
    cpu: '4 CPU',
    memory: '8GB RAM',
    type: 'production',
  },
  {
    id: '2',
    name: 'Database Server',
    ip: '45.77.87.106',
    status: 'running',
    cpu: '8 CPU',
    memory: '32GB RAM',
    type: 'database',
  },
  {
    id: '3',
    name: 'Staging Server',
    ip: '207.246.108.201',
    status: 'running',
    cpu: '4 CPU',
    memory: '8GB RAM',
    type: 'staging',
  },
  {
    id: '4',
    name: 'Load Balancer',
    ip: '45.63.58.63',
    status: 'running',
    cpu: 'Managed',
    memory: 'Service',
    type: 'loadbalancer',
  },
  {
    id: '5',
    name: 'K8s Worker 1',
    ip: '207.246.104.92',
    status: 'running',
    cpu: '2 CPU',
    memory: '4GB RAM',
    type: 'worker',
  },
  {
    id: '6',
    name: 'K8s Worker 2',
    ip: '66.42.107.3',
    status: 'running',
    cpu: '2 CPU',
    memory: '4GB RAM',
    type: 'worker',
  },
  {
    id: '7',
    name: 'K8s Worker 3',
    ip: '45.32.68.4',
    status: 'running',
    cpu: '2 CPU',
    memory: '4GB RAM',
    type: 'worker',
  },
];

export function InfrastructureProvider({ children }: { children: React.ReactNode }) {
  const [infrastructure, setInfrastructure] = useState<InfrastructureState>({
    servers: mockServers,
    databases: {
      postgresql: 'running',
      redis: 'running',
      weaviate: 'running',
      pinecone: 'connected',
    },
    monitoring: {
      prometheus: 'active',
      grafana: 'active',
      elk: 'active',
      alerts: 0,
    },
    uptime: '99.9%',
    monthlyCost: 455,
    lastUpdated: new Date(),
  });
  const [isLoading, setIsLoading] = useState(false);

  const refreshInfrastructure = async () => {
    setIsLoading(true);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // In production, this would fetch real data from your infrastructure APIs
    setInfrastructure(prev => ({
      ...prev,
      lastUpdated: new Date(),
    }));
    
    setIsLoading(false);
  };

  const startServer = async (serverId: string): Promise<boolean> => {
    setIsLoading(true);
    
    // Update server status to starting
    setInfrastructure(prev => ({
      ...prev,
      servers: prev.servers.map(server =>
        server.id === serverId ? { ...server, status: 'starting' } : server
      ),
    }));
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Update server status to running
    setInfrastructure(prev => ({
      ...prev,
      servers: prev.servers.map(server =>
        server.id === serverId ? { ...server, status: 'running' } : server
      ),
      lastUpdated: new Date(),
    }));
    
    setIsLoading(false);
    return true;
  };

  const stopServer = async (serverId: string): Promise<boolean> => {
    setIsLoading(true);
    
    // Update server status to stopping
    setInfrastructure(prev => ({
      ...prev,
      servers: prev.servers.map(server =>
        server.id === serverId ? { ...server, status: 'stopping' } : server
      ),
    }));
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Update server status to stopped
    setInfrastructure(prev => ({
      ...prev,
      servers: prev.servers.map(server =>
        server.id === serverId ? { ...server, status: 'stopped' } : server
      ),
      lastUpdated: new Date(),
    }));
    
    setIsLoading(false);
    return true;
  };

  const restartServer = async (serverId: string): Promise<boolean> => {
    await stopServer(serverId);
    await new Promise(resolve => setTimeout(resolve, 1000));
    return await startServer(serverId);
  };

  // Auto-refresh infrastructure status every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      refreshInfrastructure();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const value = {
    infrastructure,
    refreshInfrastructure,
    startServer,
    stopServer,
    restartServer,
    isLoading,
  };

  return (
    <InfrastructureContext.Provider value={value}>
      {children}
    </InfrastructureContext.Provider>
  );
}

export function useInfrastructure() {
  const context = useContext(InfrastructureContext);
  if (context === undefined) {
    throw new Error('useInfrastructure must be used within an InfrastructureProvider');
  }
  return context;
}

