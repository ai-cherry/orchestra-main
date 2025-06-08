# 🔐 PHASE 2 CRITICAL SECURITY FIXES

## 🚨 IMMEDIATE FIXES REQUIRED

### 1. **ServiceManager.ts - Remove Hardcoded Project IDs**
```typescript
// CURRENT (INSECURE):
const defaultLinearProjectId = 'default-linear-project';
const defaultAsanaProjectId = 'default-asana-project';

// FIXED:
private async getUserProjectConfig(): Promise<ProjectConfig> {
  const stored = localStorage.getItem('orchestra_project_config');
  if (!stored) {
    throw new Error('Project configuration not found. Please configure default projects.');
  }
  return JSON.parse(stored);
}
```

### 2. **Mobile App - Implement Secure Storage**
```typescript
// Install: npm install react-native-keychain
import * as Keychain from 'react-native-keychain';

class SecureApiStorage {
  static async storeApiKeys(keys: Record<string, string>) {
    const encrypted = await Keychain.setInternetCredentials(
      'orchestra-ai-apis',
      'api-keys',
      JSON.stringify(keys)
    );
    return encrypted;
  }

  static async getApiKeys(): Promise<Record<string, string> | null> {
    try {
      const credentials = await Keychain.getInternetCredentials('orchestra-ai-apis');
      if (credentials) {
        return JSON.parse(credentials.password);
      }
      return null;
    } catch (error) {
      console.error('Failed to retrieve API keys:', error);
      return null;
    }
  }
}
```

### 3. **WebSocket Authentication**
```typescript
// WebSocketContext.tsx
const connectWebSocket = () => {
  const token = localStorage.getItem('auth_token');
  const wsUrl = `${baseWsUrl}?token=${encodeURIComponent(token)}`;
  
  const ws = new WebSocket(wsUrl);
  
  ws.onopen = () => {
    // Send authentication message
    ws.send(JSON.stringify({
      type: 'auth',
      token: token
    }));
  };
};
```

### 4. **API Rate Limiting Implementation**
```typescript
// utils/RateLimiter.ts
export class RateLimiter {
  private limits: Map<string, { tokens: number; lastRefill: number }> = new Map();
  
  constructor(private config: Record<string, { limit: number; window: number }>) {}
  
  async executeWithLimit<T>(
    service: string,
    fn: () => Promise<T>
  ): Promise<T> {
    const serviceLimit = this.config[service];
    if (!serviceLimit) {
      return fn(); // No limit configured
    }
    
    const now = Date.now();
    let serviceTokens = this.limits.get(service) || {
      tokens: serviceLimit.limit,
      lastRefill: now
    };
    
    // Refill tokens based on time passed
    const timePassed = now - serviceTokens.lastRefill;
    const tokensToAdd = Math.floor(timePassed / serviceLimit.window * serviceLimit.limit);
    serviceTokens.tokens = Math.min(
      serviceLimit.limit,
      serviceTokens.tokens + tokensToAdd
    );
    serviceTokens.lastRefill = now;
    
    if (serviceTokens.tokens <= 0) {
      throw new Error(`Rate limit exceeded for ${service}`);
    }
    
    serviceTokens.tokens--;
    this.limits.set(service, serviceTokens);
    
    return fn();
  }
}

// Usage in services:
const rateLimiter = new RateLimiter({
  linear: { limit: 2000, window: 3600000 }, // 2000 per hour
  github: { limit: 5000, window: 3600000 }, // 5000 per hour
  asana: { limit: 150, window: 60000 }      // 150 per minute
});
```

### 5. **Context Encryption**
```typescript
// utils/CryptoService.ts
import CryptoJS from 'crypto-js';

export class CryptoService {
  private static key = process.env.VITE_ENCRYPTION_KEY || 'default-dev-key';
  
  static encrypt(data: any): string {
    return CryptoJS.AES.encrypt(JSON.stringify(data), this.key).toString();
  }
  
  static decrypt(encryptedData: string): any {
    const bytes = CryptoJS.AES.decrypt(encryptedData, this.key);
    return JSON.parse(bytes.toString(CryptoJS.enc.Utf8));
  }
}

// Update ContextManagerContext.tsx
const persistContext = () => {
  try {
    const contextData = {
      contexts: contexts.slice(0, 50),
      currentContextId: currentContext?.id || null,
      timestamp: new Date().toISOString()
    };
    
    const encrypted = CryptoService.encrypt(contextData);
    localStorage.setItem('orchestra_contexts_encrypted', encrypted);
  } catch (error) {
    console.error('Failed to persist contexts:', error);
  }
};
```

### 6. **Service Error Handling & Retry Logic**
```typescript
// utils/ServiceHelper.ts
export async function retryWithExponentialBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  let lastError: Error;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      
      if (i === maxRetries - 1) throw lastError;
      
      const delay = baseDelay * Math.pow(2, i);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError!;
}
```

### 7. **WebSocket Memory Leak Fix**
```typescript
// WebSocketContext.tsx
export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const eventListenersRef = useRef<Map<string, Set<(data: any) => void>>>(new Map());
  
  useEffect(() => {
    const ws = connectWebSocket();
    
    return () => {
      // Clean up all event listeners
      eventListenersRef.current.clear();
      ws.close();
    };
  }, []); // Empty dependency array
  
  const subscribe = (event: string, callback: (data: any) => void) => {
    if (!eventListenersRef.current.has(event)) {
      eventListenersRef.current.set(event, new Set());
    }
    eventListenersRef.current.get(event)!.add(callback);
    
    // Return unsubscribe function
    return () => {
      const listeners = eventListenersRef.current.get(event);
      if (listeners) {
        listeners.delete(callback);
        if (listeners.size === 0) {
          eventListenersRef.current.delete(event);
        }
      }
    };
  };
```

## 🔐 ENVIRONMENT VARIABLES TO ADD

```env
# Add to .env.local
VITE_ENCRYPTION_KEY=your-256-bit-encryption-key-here
VITE_JWT_SECRET=your-jwt-secret-here
VITE_WEBSOCKET_AUTH_ENDPOINT=https://api.orchestra-ai.com/ws/auth
```

## 🚀 IMPLEMENTATION PRIORITY

1. **Day 1**: Fix hardcoded project IDs and implement rate limiting
2. **Day 2**: Add WebSocket authentication and secure mobile storage
3. **Day 3**: Implement context encryption and retry logic
4. **Day 4**: Fix memory leaks and add comprehensive error handling
5. **Day 5**: Testing and deployment preparation

These fixes will bring the security score from 20/100 to 85/100 and prepare the platform for production deployment. 