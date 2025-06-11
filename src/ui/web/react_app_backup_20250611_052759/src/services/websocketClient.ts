export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
  source?: string;
}

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

export interface AgentStatus {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'offline' | 'error';
  tasks: number;
  uptime: string;
  lastActivity: string;
  performance: {
    responseTime: number;
    successRate: number;
    errorsToday: number;
  };
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

class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private subscribers: Map<string, Set<(data: any) => void>> = new Map();
  private isConnected = false;
  private heartbeatInterval: NodeJS.Timeout | null = null;

  constructor(private baseUrl: string = 'ws://localhost:8000') {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${this.baseUrl}/ws`);

        this.ws.onopen = () => {
          // console.log('WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.notifySubscribers('connection', { status: 'connected' });
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          // console.log('WebSocket disconnected:', event.code, event.reason);
          this.isConnected = false;
          this.stopHeartbeat();
          this.notifySubscribers('connection', { status: 'disconnected' });
          
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.notifySubscribers('error', { error });
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'User initiated disconnect');
      this.ws = null;
    }
    this.stopHeartbeat();
    this.isConnected = false;
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    // console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      this.connect().catch(console.error);
    }, delay);
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected && this.ws) {
        this.send('ping', {});
      }
    }, 30000); // 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private handleMessage(message: WebSocketMessage): void {
    const { type, payload } = message;
    
    switch (type) {
      case 'system_metrics':
        this.notifySubscribers('metrics', payload as SystemMetrics);
        break;
      
      case 'agent_status':
        this.notifySubscribers('agents', payload as AgentStatus[]);
        break;
      
      case 'service_health':
        this.notifySubscribers('services', payload as ServiceHealth[]);
        break;
      
      case 'chat_response':
        this.notifySubscribers('chat', payload);
        break;
      
      case 'file_upload_progress':
        this.notifySubscribers('fileUpload', payload);
        break;
      
      case 'multimedia_generation':
        this.notifySubscribers('multimedia', payload);
        break;
      
      case 'operator_queue':
        this.notifySubscribers('operator', payload);
        break;
      
      case 'alert':
        this.notifySubscribers('alerts', payload);
        break;
      
      case 'pong':
        // Heartbeat response
        break;
      
      default:
        console.warn('Unknown message type:', type);
        this.notifySubscribers('unknown', { type, payload });
    }
  }

  private notifySubscribers(channel: string, data: any): void {
    const subscribers = this.subscribers.get(channel);
    if (subscribers) {
      subscribers.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in subscriber callback for ${channel}:`, error);
        }
      });
    }
  }

  subscribe(channel: string, callback: (data: any) => void): () => void {
    if (!this.subscribers.has(channel)) {
      this.subscribers.set(channel, new Set());
    }
    
    this.subscribers.get(channel)!.add(callback);
    
    // Return unsubscribe function
    return () => {
      this.subscribers.get(channel)?.delete(callback);
      if (this.subscribers.get(channel)?.size === 0) {
        this.subscribers.delete(channel);
      }
    };
  }

  send(type: string, payload: any): void {
    if (!this.isConnected || !this.ws) {
      console.warn('WebSocket not connected, unable to send message');
      return;
    }

    const message: WebSocketMessage = {
      type,
      payload,
      timestamp: new Date().toISOString(),
      source: 'client'
    };

    this.ws.send(JSON.stringify(message));
  }

  // Convenience methods for specific subscriptions
  subscribeToMetrics(callback: (metrics: SystemMetrics) => void): () => void {
    return this.subscribe('metrics', callback);
  }

  subscribeToAgents(callback: (agents: AgentStatus[]) => void): () => void {
    return this.subscribe('agents', callback);
  }

  subscribeToServices(callback: (services: ServiceHealth[]) => void): () => void {
    return this.subscribe('services', callback);
  }

  subscribeToChat(callback: (chatData: any) => void): () => void {
    return this.subscribe('chat', callback);
  }

  subscribeToAlerts(callback: (alert: any) => void): () => void {
    return this.subscribe('alerts', callback);
  }

  subscribeToConnection(callback: (status: { status: string }) => void): () => void {
    return this.subscribe('connection', callback);
  }

  // Request data methods
  requestSystemMetrics(): void {
    this.send('request_metrics', {});
  }

  requestAgentStatus(): void {
    this.send('request_agents', {});
  }

  requestServiceHealth(): void {
    this.send('request_services', {});
  }

  // Chat methods
  sendChatMessage(message: string, persona: string, searchMode: string): void {
    this.send('chat_message', {
      message,
      persona,
      searchMode,
      timestamp: new Date().toISOString()
    });
  }

  // File upload methods
  notifyFileUploadStart(filename: string, size: number): void {
    this.send('file_upload_start', { filename, size });
  }

  // Agent control methods
  startAgent(agentId: string): void {
    this.send('agent_start', { agentId });
  }

  stopAgent(agentId: string): void {
    this.send('agent_stop', { agentId });
  }

  restartAgent(agentId: string): void {
    this.send('agent_restart', { agentId });
  }

  // Service control methods
  restartService(serviceName: string): void {
    this.send('service_restart', { serviceName });
  }

  testService(serviceName: string): void {
    this.send('service_test', { serviceName });
  }

  getConnectionStatus(): boolean {
    return this.isConnected;
  }

  getReconnectAttempts(): number {
    return this.reconnectAttempts;
  }
}

// Singleton instance
export const wsClient = new WebSocketClient();

// React hook for easier usage
export const useWebSocket = () => {
  return wsClient;
}; 