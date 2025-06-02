# Orchestrator Landing Page - API Design & Integration Plan

## API Architecture Overview

### Design Principles
1. **RESTful Design**: Clear resource-based endpoints with proper HTTP methods
2. **WebSocket Support**: Real-time bidirectional communication
3. **Circuit Breakers**: Fault tolerance for all external services
4. **Rate Limiting**: Per-user and global rate limits
5. **Idempotency**: All write operations support idempotency keys

### Base Configuration

```typescript
// config/api.config.ts
export const API_CONFIG = {
  baseURL: process.env.VITE_API_URL || 'http://localhost:8000',
  wsURL: process.env.VITE_WS_URL || 'ws://localhost:8000',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
  rateLimits: {
    search: { requests: 10, window: 60000 }, // 10 requests per minute
    voice: { requests: 5, window: 60000 }, // 5 requests per minute
    file: { requests: 20, window: 60000 }, // 20 requests per minute
  },
};
```

## REST API Endpoints

### Search Endpoints

```typescript
// POST /api/v1/orchestrator/search
interface SearchEndpoint {
  request: {
    body: {
      query: string;
      mode: 'creative' | 'deep' | 'super_deep';
      context?: {
        sessionId?: string;
        previousQueries?: string[];
        userPreferences?: {
          language?: string;
          responseStyle?: 'concise' | 'detailed' | 'technical';
          domains?: string[];
        };
      };
      options?: {
        limit?: number; // Default: 10, Max: 50
        offset?: number;
        filters?: {
          dateRange?: { start: string; end: string };
          sources?: string[];
          fileTypes?: string[];
        };
        includeMetadata?: boolean;
        streamResults?: boolean;
      };
    };
    headers: {
      'Authorization': string;
      'X-Request-ID'?: string; // For idempotency
      'X-Session-ID'?: string;
    };
  };
  response: {
    200: {
      searchId: string;
      results: Array<{
        id: string;
        title: string;
        content: string;
        source: string;
        relevanceScore: number;
        timestamp: string;
        metadata?: {
          author?: string;
          tags?: string[];
          fileType?: string;
          wordCount?: number;
          readingTime?: number;
        };
        highlights?: Array<{
          field: string;
          snippets: string[];
        }>;
      }>;
      facets?: {
        sources: Array<{ name: string; count: number }>;
        fileTypes: Array<{ type: string; count: number }>;
        dateRanges: Array<{ range: string; count: number }>;
      };
      suggestions: string[];
      metadata: {
        totalResults: number;
        returnedResults: number;
        searchTime: number;
        queryAnalysis: {
          intent: string;
          entities: string[];
          sentiment?: 'positive' | 'neutral' | 'negative';
        };
      };
    };
    400: ErrorResponse;
    429: RateLimitResponse;
    500: ErrorResponse;
  };
}

// GET /api/v1/orchestrator/search/{searchId}/status
interface SearchStatusEndpoint {
  request: {
    params: {
      searchId: string;
    };
  };
  response: {
    200: {
      searchId: string;
      status: 'pending' | 'processing' | 'completed' | 'failed';
      progress: number; // 0-100
      completedAt?: string;
      error?: string;
    };
  };
}

// POST /api/v1/orchestrator/search/{searchId}/cancel
interface CancelSearchEndpoint {
  request: {
    params: {
      searchId: string;
    };
  };
  response: {
    204: void;
    404: ErrorResponse;
  };
}

// GET /api/v1/orchestrator/suggestions
interface SuggestionsEndpoint {
  request: {
    query: {
      q: string; // Partial query
      limit?: number; // Default: 5, Max: 10
      context?: string; // Previous query for context
    };
  };
  response: {
    200: {
      suggestions: Array<{
        text: string;
        category: 'recent' | 'trending' | 'personalized';
        score: number;
        metadata?: {
          usageCount?: number;
          lastUsed?: string;
        };
      }>;
    };
  };
}
```

### Voice Endpoints

```typescript
// POST /api/v1/orchestrator/voice/transcribe
interface TranscribeEndpoint {
  request: {
    body: FormData; // Contains audio file
    headers: {
      'Content-Type': 'multipart/form-data';
    };
    // FormData fields:
    // - audio: Blob (required)
    // - format: 'webm' | 'mp3' | 'wav' | 'ogg'
    // - language?: string (ISO 639-1 code)
    // - options?: JSON string with TranscribeOptions
  };
  response: {
    200: {
      transcriptionId: string;
      text: string;
      confidence: number; // 0-1
      language: string;
      duration: number; // seconds
      words?: Array<{
        text: string;
        start: number;
        end: number;
        confidence: number;
      }>;
      alternatives?: Array<{
        text: string;
        confidence: number;
      }>;
    };
    400: ErrorResponse;
    413: { error: 'File too large'; maxSize: number };
    415: { error: 'Unsupported audio format' };
  };
}

// POST /api/v1/orchestrator/voice/synthesize
interface SynthesizeEndpoint {
  request: {
    body: {
      text: string;
      voiceId: string;
      options?: {
        speed?: number; // 0.5-2.0, default: 1.0
        pitch?: number; // -20 to 20, default: 0
        volume?: number; // 0-1, default: 1.0
        format?: 'mp3' | 'wav' | 'ogg'; // default: 'mp3'
        sampleRate?: 16000 | 22050 | 44100; // default: 22050
      };
      metadata?: {
        purpose?: string;
        sessionId?: string;
      };
    };
  };
  response: {
    200: {
      synthesisId: string;
      audioUrl: string;
      duration: number; // seconds
      format: string;
      size: number; // bytes
      expiresAt: string; // ISO timestamp
      voice: {
        id: string;
        name: string;
        language: string;
      };
    };
    400: ErrorResponse;
    402: { error: 'Quota exceeded'; quotaInfo: QuotaInfo };
  };
}

// GET /api/v1/orchestrator/voice/voices
interface VoicesEndpoint {
  request: {
    query?: {
      language?: string;
      gender?: 'male' | 'female' | 'neutral';
      provider?: string;
    };
  };
  response: {
    200: {
      voices: Array<{
        id: string;
        name: string;
        language: string;
        languageCode: string;
        gender: 'male' | 'female' | 'neutral';
        provider: string;
        previewUrl?: string;
        styles?: string[];
        useCases?: string[];
        isPremium?: boolean;
      }>;
      total: number;
    };
  };
}

// GET /api/v1/orchestrator/voice/languages
interface VoiceLanguagesEndpoint {
  response: {
    200: {
      languages: Array<{
        code: string;
        name: string;
        nativeName: string;
        voiceCount: number;
      }>;
    };
  };
}
```

### File Management Endpoints

```typescript
// POST /api/v1/orchestrator/files/upload
interface FileUploadEndpoint {
  request: {
    body: FormData;
    // FormData fields:
    // - file: File (required)
    // - metadata?: JSON string with FileMetadata
    // - processImmediately?: 'true' | 'false'
  };
  response: {
    200: {
      fileId: string;
      status: 'uploaded' | 'processing' | 'ready';
      file: {
        name: string;
        size: number;
        type: string;
        lastModified: string;
      };
      uploadedAt: string;
      processedAt?: string;
      expiresAt: string;
      downloadUrl?: string;
      metadata?: {
        extractedText?: string;
        pageCount?: number;
        dimensions?: { width: number; height: number };
        duration?: number; // for audio/video
      };
    };
    400: ErrorResponse;
    413: { error: 'File too large'; maxSize: number };
    415: { error: 'Unsupported file type'; supportedTypes: string[] };
  };
}

// GET /api/v1/orchestrator/files/{fileId}
interface FileDetailsEndpoint {
  request: {
    params: {
      fileId: string;
    };
  };
  response: {
    200: {
      fileId: string;
      status: 'queued' | 'processing' | 'completed' | 'failed';
      progress: number;
      file: FileInfo;
      result?: {
        extractedText?: string;
        summary?: string;
        entities?: Array<{ type: string; value: string }>;
        insights?: string[];
        metadata?: Record<string, any>;
      };
      error?: {
        code: string;
        message: string;
        details?: any;
      };
    };
    404: ErrorResponse;
  };
}

// DELETE /api/v1/orchestrator/files/{fileId}
interface FileDeleteEndpoint {
  request: {
    params: {
      fileId: string;
    };
  };
  response: {
    204: void;
    404: ErrorResponse;
  };
}

// POST /api/v1/orchestrator/files/{fileId}/process
interface FileProcessEndpoint {
  request: {
    params: {
      fileId: string;
    };
    body: {
      operations: Array<{
        type: 'extract_text' | 'summarize' | 'analyze' | 'convert';
        options?: Record<string, any>;
      }>;
      priority?: 'low' | 'normal' | 'high';
    };
  };
  response: {
    202: {
      processId: string;
      status: 'queued';
      estimatedTime?: number; // seconds
    };
  };
}

// GET /api/v1/orchestrator/files
interface ListFilesEndpoint {
  request: {
    query?: {
      status?: string;
      type?: string;
      uploadedAfter?: string;
      uploadedBefore?: string;
      limit?: number;
      offset?: number;
      sortBy?: 'name' | 'size' | 'uploadedAt';
      sortOrder?: 'asc' | 'desc';
    };
  };
  response: {
    200: {
      files: FileInfo[];
      total: number;
      limit: number;
      offset: number;
    };
  };
}
```

## WebSocket Protocol

### Connection Management

```typescript
// WebSocket connection URL format
// ws://localhost:8000/ws/orchestrator?token={jwt_token}

interface WebSocketConnection {
  // Connection lifecycle
  onOpen: () => void;
  onClose: (event: CloseEvent) => void;
  onError: (error: Event) => void;
  
  // Message handling
  onMessage: (event: MessageEvent) => void;
  
  // Heartbeat
  pingInterval: 30000; // 30 seconds
  pongTimeout: 5000; // 5 seconds
}

// Message format
interface WebSocketMessage<T = any> {
  id: string; // Unique message ID
  type: 'event' | 'request' | 'response' | 'error';
  event?: string; // Event name for type='event'
  method?: string; // Method name for type='request'
  data: T;
  timestamp: string;
  correlationId?: string; // For request/response correlation
}
```

### WebSocket Events

```typescript
// Client -> Server Events
interface ClientEvents {
  // Search events
  'search:start': {
    query: string;
    mode: SearchMode;
    options?: SearchOptions;
  };
  
  'search:cancel': {
    searchId: string;
  };
  
  'search:feedback': {
    searchId: string;
    resultId: string;
    feedback: 'helpful' | 'not_helpful';
    comment?: string;
  };
  
  // Voice events
  'voice:stream:start': {
    format: 'webm' | 'raw';
    sampleRate: number;
    language?: string;
  };
  
  'voice:stream:data': {
    audio: ArrayBuffer;
    sequence: number;
  };
  
  'voice:stream:end': {
    finalSequence: number;
  };
  
  // File events
  'file:track': {
    fileId: string;
  };
  
  'file:untrack': {
    fileId: string;
  };
  
  // Session events
  'session:ping': {
    timestamp: string;
  };
  
  'session:update': {
    preferences?: UserPreferences;
    context?: SessionContext;
  };
}

// Server -> Client Events
interface ServerEvents {
  // Search events
  'search:progress': {
    searchId: string;
    progress: number;
    stage: 'querying' | 'ranking' | 'enriching';
  };
  
  'search:result': {
    searchId: string;
    result: SearchResult;
    isPartial: boolean;
  };
  
  'search:complete': {
    searchId: string;
    totalResults: number;
    searchTime: number;
  };
  
  'search:suggestion': {
    suggestion: string;
    trigger: 'typing' | 'context' | 'trending';
  };
  
  // Voice events
  'voice:level': {
    level: number; // 0-100
    timestamp: number;
  };
  
  'voice:partial': {
    text: string;
    confidence: number;
    isFinal: boolean;
  };
  
  'voice:complete': {
    transcriptionId: string;
    fullText: string;
    duration: number;
  };
  
  // File events
  'file:progress': {
    fileId: string;
    progress: number;
    stage: 'uploading' | 'processing' | 'analyzing';
    bytesProcessed?: number;
    totalBytes?: number;
  };
  
  'file:complete': {
    fileId: string;
    result: FileProcessingResult;
  };
  
  'file:error': {
    fileId: string;
    error: {
      code: string;
      message: string;
    };
  };
  
  // System events
  'system:notification': {
    id: string;
    type: 'info' | 'warning' | 'error';
    title: string;
    message: string;
    actions?: Array<{
      label: string;
      action: string;
    }>;
  };
  
  'system:maintenance': {
    scheduledAt: string;
    duration: number;
    affectedServices: string[];
  };
  
  // Session events
  'session:pong': {
    timestamp: string;
    latency: number;
  };
  
  'session:expired': {
    reason: string;
    reconnectUrl?: string;
  };
}
```

### WebSocket Manager Implementation

```typescript
// services/websocket/OrchestratorWebSocket.ts
import { EventEmitter } from 'events';

export class OrchestratorWebSocket extends EventEmitter {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private readonly maxReconnectAttempts = 5;
  private readonly reconnectDelay = 1000;
  private messageQueue: WebSocketMessage[] = [];
  private isConnected = false;
  private pingInterval: NodeJS.Timeout | null = null;
  private correlationMap = new Map<string, (data: any) => void>();
  
  constructor(
    private url: string,
    private token: string,
    private options: WebSocketOptions = {}
  ) {
    super();
    this.connect();
  }
  
  private connect(): void {
    try {
      this.ws = new WebSocket(`${this.url}?token=${this.token}`);
      this.setupEventHandlers();
    } catch (error) {
      this.handleConnectionError(error);
    }
  }
  
  private setupEventHandlers(): void {
    if (!this.ws) return;
    
    this.ws.onopen = () => {
      console.log('[WS] Connected');
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.emit('connected');
      this.flushMessageQueue();
      this.startHeartbeat();
    };
    
    this.ws.onclose = (event) => {
      console.log('[WS] Disconnected', event.code, event.reason);
      this.isConnected = false;
      this.emit('disconnected', event);
      this.stopHeartbeat();
      
      if (event.code !== 1000 && event.code !== 1001) {
        this.attemptReconnect();
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('[WS] Error', error);
      this.emit('error', error);
    };
    
    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('[WS] Failed to parse message', error);
      }
    };
  }
  
  private handleMessage(message: WebSocketMessage): void {
    // Handle correlation for request/response pattern
    if (message.correlationId && this.correlationMap.has(message.correlationId)) {
      const handler = this.correlationMap.get(message.correlationId)!;
      handler(message.data);
      this.correlationMap.delete(message.correlationId);
      return;
    }
    
    // Handle events
    if (message.type === 'event' && message.event) {
      this.emit(message.event, message.data);
    }
    
    // Handle errors
    if (message.type === 'error') {
      this.emit('error', message.data);
    }
  }
  
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WS] Max reconnection attempts reached');
      this.emit('reconnectFailed');
      return;
    }
    
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);
    
    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }
  
  private startHeartbeat(): void {
    this.pingInterval = setInterval(() => {
      this.send('session:ping', { timestamp: new Date().toISOString() });
    }, 30000);
  }
  
  private stopHeartbeat(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }
  
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift()!;
      this.sendMessage(message);
    }
  }
  
  send<K extends keyof ClientEvents>(
    event: K,
    data: ClientEvents[K],
    options?: { correlationId?: string }
  ): void {
    const message: WebSocketMessage = {
      id: generateId(),
      type: 'event',
      event,
      data,
      timestamp: new Date().toISOString(),
      correlationId: options?.correlationId,
    };
    
    if (this.isConnected) {
      this.sendMessage(message);
    } else {
      this.messageQueue.push(message);
    }
  }
  
  request<T = any>(
    method: string,
    data: any
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const correlationId = generateId();
      const timeout = setTimeout(() => {
        this.correlationMap.delete(correlationId);
        reject(new Error('Request timeout'));
      }, 30000);
      
      this.correlationMap.set(correlationId, (response) => {
        clearTimeout(timeout);
        resolve(response);
      });
      
      const message: WebSocketMessage = {
        id: generateId(),
        type: 'request',
        method,
        data,
        timestamp: new Date().toISOString(),
        correlationId,
      };
      
      if (this.isConnected) {
        this.sendMessage(message);
      } else {
        clearTimeout(timeout);
        this.correlationMap.delete(correlationId);
        reject(new Error('WebSocket not connected'));
      }
    });
  }
  
  private sendMessage(message: WebSocketMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }
  
  close(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, 'Client closing connection');
      this.ws = null;
    }
  }
}
```

## API Client Implementation

### Base HTTP Client

```typescript
// services/api/httpClient.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { API_CONFIG } from '@/config/api.config';

class HttpClient {
  private instance: AxiosInstance;
  private requestQueue = new Map<string, Promise<any>>();
  
  constructor() {
    this.instance = axios.create({
      baseURL: API_CONFIG.baseURL,
      timeout: API_CONFIG.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    this.setupInterceptors();
  }
  
  private setupInterceptors(): void {
    // Request interceptor
    this.instance.interceptors.request.use(
      (config) => {
        // Add auth token
        const token = localStorage.getItem('auth-token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // Add request ID for tracking
        config.headers['X-Request-ID'] = generateId();
        
        // Add session ID if available
        const sessionId = sessionStorage.getItem('session-id');
        if (sessionId) {
          config.headers['X-Session-ID'] = sessionId;
        }
        
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // Response interceptor
    this.instance.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        // Handle 401 - Token refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            await this.refreshToken();
            return this.instance(originalRequest);
          } catch (refreshError) {
            // Redirect to login
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }
        
        // Handle 429 - Rate limiting
        if (error.response?.status === 429) {
          const retryAfter = error.response.headers['retry-after'];
          const delay = retryAfter ? parseInt(retryAfter) * 1000 : 5000;
          
          await new Promise(resolve => setTimeout(resolve, delay));
          return this.instance(originalRequest);
        }
        
        // Handle 503 - Service unavailable
        if (error.response?.status === 503 && originalRequest._retryCount < 3) {
          originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;
          const delay = Math.pow(2, originalRequest._retryCount) * 1000;
          
          await new Promise(resolve => setTimeout(resolve, delay));
          return this.instance(originalRequest);
        }
        
        return Promise.reject(error);
      }
    );
  }
  
  private async refreshToken(): Promise<void> {
    // Implement token refresh logic
    const refreshToken = localStorage.getItem('refresh-token');
    const response = await this.instance.post('/auth/refresh', {
      refreshToken,
    });
    
    localStorage.setItem('auth-token', response.data.accessToken);
    localStorage.setItem('refresh-token', response.data.refreshToken);
  }
  
  // Request deduplication
  async dedupedRequest<T>(
    key: string,
    config: AxiosRequestConfig
  ): Promise<T> {
    if (this.requestQueue.has(key)) {
      return this.requestQueue.get(key)!;
    }
    
    const promise = this.instance.request<T>(config)
      .then(response => response.data)
      .finally(() => this.requestQueue.delete(key));
    
    this.requestQueue.set(key, promise);
    return promise;
  }
  
  get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.get<T>(url, config).then(res => res.data);
  }
  
  post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.post<T>(url, data, config).then(res => res.data);
  }
  
  put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.put<T>(url, data, config).then(res => res.data);
  }
  
  delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.instance.delete<T>(url, config).then(res => res.data);
  }
}

export const httpClient = new HttpClient();
```

### API Service Classes

```typescript
// services/api/searchAPI.ts
import { httpClient } from './httpClient';
import { circuitBreaker } from '@/utils/circuitBreaker';

export class SearchAPI {
  private searchCache = new Map<string, SearchResponse>();
  private cacheTimeout = 5 * 60 * 1000; // 5 minutes
  
  @circuitBreaker({ threshold: 5, timeout: 10000 })
  async search(request: SearchRequest): Promise<SearchResponse> {
    const cacheKey = this.getCacheKey(request);
    const cached = this.searchCache.get(cacheKey);
    
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached;
    }
    
    const response = await httpClient.post<SearchResponse>(
      '/api/v1/orchestrator/search',
      request,
      {
        headers: {
          'X-Request-ID': generateId(), // For idempotency
        },
      }
    );
    
    this.searchCache.set(cacheKey, {
      ...response,
      timestamp: Date.now(),
    });
    
    return response;
  }
  
  async getSearchStatus(searchId: string): Promise<SearchStatus> {
    return httpClient.get(`/api/v1/orchestrator/search/${searchId}/status`);
  }
  
  async cancelSearch(searchId: string): Promise<void> {
    return httpClient.post(`/api/v1/orchestrator/search/${searchId}/cancel`);
  }
  
  @circuitBreaker({ threshold: 10, timeout: 5000 })
  async getSuggestions(query: string, options?: SuggestionOptions): Promise<SuggestionResponse> {
    return httpClient.dedupedRequest(
      `suggestions:${query}`,
      {
        method: 'GET',
        url: '/api/v1/orchestrator/suggestions',
        params: {
          q: query,
          ...options,
        },
      }
    );
  }
  
  private getCacheKey(request: SearchRequest): string {
    return JSON.stringify({
      query: request.query,
      mode: request.mode,
      filters: request.options?.filters,
    });
  }
}

export const searchAPI = new SearchAPI();
```

## Integration Plan

### Phase 1: Infrastructure Setup (Days 1-3)

1. **API Client Setup**
   ```typescript
   // Tasks:
   - [ ] Configure axios instance with interceptors
   - [ ] Implement circuit breaker utility
   - [ ] Set up request/response logging
   - [ ] Create error handling middleware
   ```

2. **WebSocket Infrastructure**
   ```typescript
   // Tasks:
   - [ ] Implement WebSocket manager class
   - [ ] Set up reconnection logic
   - [ ] Create event emitter system
   - [ ] Implement message queuing
   ```

3. **State Management Integration**
   ```typescript
   // Tasks:
   - [ ] Create Zustand store for orchestrator
   - [ ] Implement store persistence
   - [ ] Set up store subscriptions
   - [ ] Create store middleware for logging
   ```

### Phase 2: Core Feature Implementation (Days 4-7)

1. **Search Integration**
   ```typescript
   // Tasks:
   - [ ] Implement search API service
   - [ ] Create search result caching
   - [ ] Set up real-time search updates
   - [ ] Implement suggestion system
   ```

2. **Voice Integration**
   ```typescript
   // Tasks:
   - [ ] Implement voice recording logic
   - [ ] Create streaming transcription
   - [ ] Set up voice synthesis
   - [ ] Implement voice selection UI
   ```

3. **File Management**
   ```typescript
   // Tasks:
   - [ ] Create file upload service
   - [ ] Implement progress tracking
   - [ ] Set up file processing queue
   - [ ] Create download manager
   ```

### Phase 3: Real-time Features (Days 8-10)

1. **WebSocket Events**
   ```typescript
   // Tasks:
   - [ ] Implement search progress events
   - [ ] Create file upload progress tracking
   - [ ] Set up voice level monitoring
   - [ ] Implement system notifications
   ```

2. **Performance Optimization**
   ```typescript
   // Tasks:
   - [ ] Implement request deduplication
   - [ ] Set up response caching
   - [ ] Create virtual scrolling
   - [ ] Optimize bundle splitting
   ```

### Phase 4: Testing & Polish (Days 11-14)

1. **Testing**
   ```typescript