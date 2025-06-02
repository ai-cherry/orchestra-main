import { io, Socket } from 'socket.io-client';
import useOrchestratorStore from '../store/orchestratorStore';

// WebSocket event types
export interface FileProgressEvent {
  fileId: string;
  progress: number;
  status?: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}

export interface SearchSuggestionEvent {
  suggestion: string;
  category?: string;
  priority?: number;
}

export interface SearchResultEvent {
  results: Array<{
    id: string;
    content: string;
    type: 'text' | 'file' | 'voice';
    timestamp: Date;
    metadata?: Record<string, any>;
  }>;
  query: string;
  isPartial?: boolean;
}

export interface SystemNotificationEvent {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  timestamp: Date;
}

class WebSocketManager {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private maxReconnectDelay = 30000; // Max 30 seconds
  private isIntentionalDisconnect = false;

  constructor() {
    // Bind methods to preserve context
    this.connect = this.connect.bind(this);
    this.disconnect = this.disconnect.bind(this);
    this.setupEventHandlers = this.setupEventHandlers.bind(this);
  }

  connect(url?: string): void {
    if (this.socket?.connected) {
      console.log('WebSocket already connected');
      return;
    }

    const wsUrl = url || process.env.VITE_WS_URL || 'http://localhost:3000';
    
    this.socket = io(wsUrl, {
      transports: ['websocket', 'polling'],
      reconnection: false, // We'll handle reconnection manually
      timeout: 10000,
      auth: {
        // Add authentication token if available
        token: localStorage.getItem('auth_token') || undefined,
      },
    });

    this.setupEventHandlers();
    this.isIntentionalDisconnect = false;
  }

  private setupEventHandlers(): void {
    if (!this.socket) return;

    // Connection events
    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
      
      // Notify store of connection
      const store = useOrchestratorStore.getState();
      store.setWebSocketConnected(true);
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      
      const store = useOrchestratorStore.getState();
      store.setWebSocketConnected(false);

      // Attempt reconnection if not intentional
      if (!this.isIntentionalDisconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.scheduleReconnect();
      }
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
    });

    // File progress events
    this.socket.on('file:progress', (data: FileProgressEvent) => {
      const store = useOrchestratorStore.getState();
      
      if (data.status) {
        store.updateUploadStatus(data.fileId, data.status, data.error);
      } else {
        store.updateUploadProgress(data.fileId, data.progress);
      }
    });

    this.socket.on('file:download:progress', (data: FileProgressEvent) => {
      const store = useOrchestratorStore.getState();
      
      if (data.status) {
        // Map file upload statuses to download statuses
        let downloadStatus: 'pending' | 'downloading' | 'completed' | 'error';
        switch (data.status) {
          case 'uploading':
          case 'processing':
            downloadStatus = 'downloading';
            break;
          case 'completed':
            downloadStatus = 'completed';
            break;
          case 'error':
            downloadStatus = 'error';
            break;
          default:
            downloadStatus = 'pending';
        }
        store.updateDownloadStatus(data.fileId, downloadStatus, data.error);
      } else {
        store.updateDownloadProgress(data.fileId, data.progress);
      }
    });

    // Search events
    this.socket.on('search:suggestion', (data: SearchSuggestionEvent) => {
      const store = useOrchestratorStore.getState();
      const currentSuggestions = store.suggestions;
      
      // Add new suggestion if not already present
      if (!currentSuggestions.includes(data.suggestion)) {
        store.setSuggestions([...currentSuggestions, data.suggestion]);
      }
    });

    this.socket.on('search:results', (data: SearchResultEvent) => {
      const store = useOrchestratorStore.getState();
      
      if (data.isPartial) {
        // Append to existing results for streaming
        const currentResults = store.searchResults;
        const newResults = data.results.map(result => ({
          ...result,
          timestamp: new Date(result.timestamp),
        }));
        store.setSearchResults([...currentResults, ...newResults]);
      } else {
        // Replace results
        const newResults = data.results.map(result => ({
          ...result,
          timestamp: new Date(result.timestamp),
        }));
        store.setSearchResults(newResults);
      }
    });

    // System notifications
    this.socket.on('system:notification', (data: SystemNotificationEvent) => {
      console.log('System notification:', data);
      // You can integrate with a notification system here
      // For example, using a toast library or custom notification store
    });

    // Voice events
    this.socket.on('voice:transcription:update', (data: { text: string; isFinal: boolean }) => {
      const store = useOrchestratorStore.getState();
      
      if (data.isFinal) {
        store.setTranscription(data.text);
        store.setSearchQuery(data.text);
      } else {
        // Update interim transcription
        store.setTranscription(data.text);
      }
    });

    // Custom events
    this.socket.on('orchestrator:update', (data: any) => {
      console.log('Orchestrator update:', data);
      // Handle custom orchestrator updates
    });
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${this.reconnectDelay}ms`);
    
    setTimeout(() => {
      this.connect();
    }, this.reconnectDelay);
    
    // Exponential backoff with jitter
    this.reconnectDelay = Math.min(
      this.maxReconnectDelay,
      this.reconnectDelay * 2 + Math.random() * 1000
    );
  }

  disconnect(): void {
    this.isIntentionalDisconnect = true;
    
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    
    const store = useOrchestratorStore.getState();
    store.setWebSocketConnected(false);
  }

  // Public methods for sending events
  emit(event: string, data: any): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('WebSocket not connected. Cannot emit event:', event);
    }
  }

  // Specific event emitters
  sendFileUploadStart(fileId: string, fileName: string, fileSize: number): void {
    this.emit('file:upload:start', { fileId, fileName, fileSize });
  }

  sendSearchQuery(query: string, mode: string, context?: any): void {
    this.emit('search:query', { query, mode, context });
  }

  sendVoiceRecordingStart(): void {
    this.emit('voice:recording:start', {});
  }

  sendVoiceRecordingStop(): void {
    this.emit('voice:recording:stop', {});
  }

  // Utility methods
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  getSocketId(): string | undefined {
    return this.socket?.id;
  }

  // Subscribe to specific events with callbacks
  on(event: string, callback: (...args: any[]) => void): void {
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  off(event: string, callback?: (...args: any[]) => void): void {
    if (this.socket) {
      this.socket.off(event, callback);
    }
  }
}

// Create singleton instance
const websocketManager = new WebSocketManager();

// Auto-connect in browser environment
if (typeof window !== 'undefined') {
  // Connect when the page loads
  window.addEventListener('load', () => {
    websocketManager.connect();
  });

  // Disconnect when the page unloads
  window.addEventListener('beforeunload', () => {
    websocketManager.disconnect();
  });

  // Handle visibility changes
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      // Page is hidden, you might want to reduce activity
      console.log('Page hidden, WebSocket remains connected');
    } else {
      // Page is visible again, ensure connection
      if (!websocketManager.isConnected()) {
        websocketManager.connect();
      }
    }
  });
}

export default websocketManager;