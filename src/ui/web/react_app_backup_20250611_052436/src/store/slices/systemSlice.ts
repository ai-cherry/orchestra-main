import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface SystemMetrics {
  cpu: number;
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  apiRequests: number;
  responseTime: number;
  activeSessions: number;
  uptime: number;
}

export interface ServiceHealth {
  name: string;
  status: 'online' | 'warning' | 'offline';
  responseTime: number;
  lastCheck: string;
  details?: {
    version?: string;
    connections?: number;
    errors?: number;
  };
}

export interface SystemAlert {
  id: string;
  type: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
}

interface SystemState {
  metrics: SystemMetrics;
  services: ServiceHealth[];
  alerts: SystemAlert[];
  isConnected: boolean;
  lastUpdate: string | null;
  performance: {
    pageLoadTime: number;
    apiLatency: number;
    errorRate: number;
  };
}

const initialState: SystemState = {
  metrics: {
    cpu: 0,
    memory: {
      used: 0,
      total: 0,
      percentage: 0,
    },
    apiRequests: 0,
    responseTime: 0,
    activeSessions: 0,
    uptime: 0,
  },
  services: [
    {
      name: 'Cherry AI API',
      status: 'online',
      responseTime: 150,
      lastCheck: new Date().toISOString(),
      details: { connections: 8, errors: 0 }
    },
    {
      name: 'Memory MCP Server',
      status: 'warning',
      responseTime: 234,
      lastCheck: new Date().toISOString(),
      details: { connections: 12, errors: 3 }
    },
    {
      name: 'PostgreSQL',
      status: 'online',
      responseTime: 45,
      lastCheck: new Date().toISOString(),
      details: { connections: 8, errors: 0 }
    },
    {
      name: 'Redis Cache',
      status: 'online',
      responseTime: 12,
      lastCheck: new Date().toISOString(),
      details: { connections: 5, errors: 0 }
    },
    {
      name: 'Weaviate Vector DB',
      status: 'online',
      responseTime: 89,
      lastCheck: new Date().toISOString(),
      details: { connections: 3, errors: 0 }
    }
  ],
  alerts: [],
  isConnected: false,
  lastUpdate: null,
  performance: {
    pageLoadTime: 0,
    apiLatency: 0,
    errorRate: 0,
  }
};

const systemSlice = createSlice({
  name: 'system',
  initialState,
  reducers: {
    updateMetrics: (state, action: PayloadAction<SystemMetrics>) => {
      state.metrics = action.payload;
      state.lastUpdate = new Date().toISOString();
    },
    
    updateServiceHealth: (state, action: PayloadAction<ServiceHealth[]>) => {
      state.services = action.payload;
      state.lastUpdate = new Date().toISOString();
    },
    
    updateSingleService: (state, action: PayloadAction<ServiceHealth>) => {
      const index = state.services.findIndex(s => s.name === action.payload.name);
      if (index !== -1) {
        state.services[index] = action.payload;
      } else {
        state.services.push(action.payload);
      }
      state.lastUpdate = new Date().toISOString();
    },
    
    addAlert: (state, action: PayloadAction<Omit<SystemAlert, 'id' | 'timestamp' | 'acknowledged'>>) => {
      const alert: SystemAlert = {
        ...action.payload,
        id: `alert-${Date.now()}`,
        timestamp: new Date().toISOString(),
        acknowledged: false,
      };
      state.alerts.unshift(alert);
      
      // Keep only last 50 alerts
      if (state.alerts.length > 50) {
        state.alerts = state.alerts.slice(0, 50);
      }
    },
    
    acknowledgeAlert: (state, action: PayloadAction<string>) => {
      const alert = state.alerts.find(a => a.id === action.payload);
      if (alert) {
        alert.acknowledged = true;
      }
    },
    
    clearAlerts: (state) => {
      state.alerts = [];
    },
    
    setConnectionStatus: (state, action: PayloadAction<boolean>) => {
      state.isConnected = action.payload;
    },
    
    updatePerformance: (state, action: PayloadAction<Partial<SystemState['performance']>>) => {
      state.performance = { ...state.performance, ...action.payload };
    },
    
    resetMetrics: (state) => {
      state.metrics = initialState.metrics;
      state.alerts = [];
      state.lastUpdate = null;
    }
  }
});

export const {
  updateMetrics,
  updateServiceHealth,
  updateSingleService,
  addAlert,
  acknowledgeAlert,
  clearAlerts,
  setConnectionStatus,
  updatePerformance,
  resetMetrics
} = systemSlice.actions;

export default systemSlice.reducer; 