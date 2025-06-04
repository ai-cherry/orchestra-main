# conductor Landing Page - Component Architecture

## Executive Summary
This document outlines the comprehensive component architecture for the conductor Landing Page, designed to integrate seamlessly with the existing admin-ui infrastructure while providing advanced search, voice, and file management capabilities.

## Architecture Overview

### Design Principles
1. **Modular Architecture**: Hot-swappable components with clear interfaces
2. **Performance First**: Sub-100ms response times with optimized rendering
3. **Event-Driven**: WebSocket-based real-time updates
4. **Accessibility**: WCAG 2.1 AA compliant with full keyboard navigation
5. **Scalability**: Designed for 10x growth without refactoring

### Technology Stack
- **Frontend**: React 18.3.1, TypeScript, TanStack Router
- **State Management**: Zustand with persist middleware
- **Styling**: Tailwind CSS with custom theme
- **Components**: Radix UI primitives with custom styling
- **Real-time**: WebSocket connections with reconnection logic
- **Performance**: React.lazy, Suspense, and virtual scrolling

## Component Hierarchy

```typescript
// Root Component Structure
conductorLandingPage/
├── Header/
│   ├── Logo
│   ├── Navigation
│   ├── GlobalSearch
│   ├── NotificationBell
│   └── UserProfile
├── MainContent/
│   ├── SearchSection/
│   │   ├── SearchInput
│   │   ├── InputModeSelector
│   │   └── SearchModeSelector
│   ├── MessageComposer/
│   │   ├── TextArea
│   │   └── ActionButtons
│   ├── SuggestionsPanel/
│   │   └── SuggestionChips
│   ├── VoiceSection/
│   │   ├── VoiceRecorder
│   │   └── VoiceSynthesizer
│   └── FileManager/
│       ├── FileUploader
│       └── DownloadTable
└── Footer/
```

## Component Specifications

### 1. Core Layout Components

```typescript
// conductorLandingPage.tsx
interface conductorLandingPageProps {
  className?: string;
  initialMode?: SearchMode;
  onSearchComplete?: (results: SearchResult[]) => void;
}

// Header.tsx
interface HeaderProps {
  user?: User;
  notifications?: Notification[];
  onNavigate?: (route: string) => void;
}

// MainContent.tsx
interface MainContentProps {
  activePanel: PanelType;
  onPanelChange: (panel: PanelType) => void;
}
```

### 2. Search Components

```typescript
// SearchInput.tsx
interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder?: string;
  maxLength?: number;
  isLoading?: boolean;
  error?: string;
}

// InputModeSelector.tsx
interface InputModeSelectorProps {
  mode: InputMode;
  onChange: (mode: InputMode) => void;
  disabled?: boolean;
}

// SearchModeSelector.tsx
interface SearchModeSelectorProps {
  mode: SearchMode;
  onChange: (mode: SearchMode) => void;
  availableModes?: SearchMode[];
}

type InputMode = 'text' | 'voice' | 'file';
type SearchMode = 'creative' | 'deep' | 'super_deep';
```

### 3. Voice Components

```typescript
// VoiceRecorder.tsx
interface VoiceRecorderProps {
  onTranscription: (text: string) => void;
  onError: (error: Error) => void;
  language?: string;
  maxDuration?: number;
}

// VoiceSynthesizer.tsx
interface VoiceSynthesizerProps {
  text: string;
  voice: VoiceOption;
  onComplete?: () => void;
  onError?: (error: Error) => void;
}

interface VoiceOption {
  id: string;
  name: string;
  language: string;
  gender: 'male' | 'female' | 'neutral';
}
```

### 4. File Management Components

```typescript
// FileUploader.tsx
interface FileUploaderProps {
  onUpload: (files: File[]) => void;
  acceptedTypes?: string[];
  maxSize?: number;
  maxFiles?: number;
  onError?: (error: FileError) => void;
}

// DownloadTable.tsx
interface DownloadTableProps {
  downloads: FileDownload[];
  onCancel: (id: string) => void;
  onRetry: (id: string) => void;
  onOpen: (id: string) => void;
}

interface FileDownload {
  id: string;
  name: string;
  size: number;
  progress: number;
  status: 'queued' | 'downloading' | 'completed' | 'failed';
  error?: string;
  url?: string;
}
```

## State Management Architecture

### Zustand Store Design

```typescript
// stores/conductorStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { subscribeWithSelector } from 'zustand/middleware';

interface conductorState {
  // Search State
  search: {
    query: string;
    mode: SearchMode;
    inputMode: InputMode;
    suggestions: Suggestion[];
    results: SearchResult[];
    isSearching: boolean;
    error: string | null;
  };
  
  // Voice State
  voice: {
    isRecording: boolean;
    recordingDuration: number;
    transcription: string;
    selectedVoice: VoiceOption;
    isSynthesizing: boolean;
    audioUrl: string | null;
  };
  
  // File State
  files: {
    uploads: FileUpload[];
    downloads: FileDownload[];
    dragActive: boolean;
  };
  
  // UI State
  ui: {
    activePanel: PanelType;
    isLoading: boolean;
    errors: AppError[];
    theme: 'dark' | 'light';
  };
  
  // Actions
  actions: {
    // Search Actions
    setQuery: (query: string) => void;
    setSearchMode: (mode: SearchMode) => void;
    setInputMode: (mode: InputMode) => void;
    performSearch: () => Promise<void>;
    clearSearch: () => void;
    
    // Voice Actions
    startRecording: () => void;
    stopRecording: () => void;
    setTranscription: (text: string) => void;
    synthesizeSpeech: (text: string) => Promise<void>;
    
    // File Actions
    uploadFiles: (files: File[]) => Promise<void>;
    cancelUpload: (id: string) => void;
    retryDownload: (id: string) => void;
    
    // UI Actions
    setActivePanel: (panel: PanelType) => void;
    addError: (error: AppError) => void;
    clearErrors: () => void;
  };
}

export const useconductorStore = create<conductorState>()(
  subscribeWithSelector(
    persist(
      (set, get) => ({
        // Initial state
        search: {
          query: '',
          mode: 'creative',
          inputMode: 'text',
          suggestions: [],
          results: [],
          isSearching: false,
          error: null,
        },
        voice: {
          isRecording: false,
          recordingDuration: 0,
          transcription: '',
          selectedVoice: defaultVoice,
          isSynthesizing: false,
          audioUrl: null,
        },
        files: {
          uploads: [],
          downloads: [],
          dragActive: false,
        },
        ui: {
          activePanel: 'search',
          isLoading: false,
          errors: [],
          theme: 'dark',
        },
        actions: {
          // Implementation details...
        },
      }),
      {
        name: 'conductor-storage',
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          search: { mode: state.search.mode },
          voice: { selectedVoice: state.voice.selectedVoice },
          ui: { theme: state.ui.theme },
        }),
      }
    )
  )
);
```

### Store Subscriptions and Effects

```typescript
// Subscription for WebSocket updates
useconductorStore.subscribe(
  (state) => state.search.query,
  (query) => {
    if (query.length > 2) {
      debouncedFetchSuggestions(query);
    }
  }
);

// Subscription for voice recording duration
useconductorStore.subscribe(
  (state) => state.voice.isRecording,
  (isRecording) => {
    if (isRecording) {
      startRecordingTimer();
    } else {
      stopRecordingTimer();
    }
  }
);
```

## API Contract Design

### REST API Endpoints

```typescript
// Search API
interface SearchAPI {
  // POST /api/conductor/search
  search(request: SearchRequest): Promise<SearchResponse>;
  
  // GET /api/conductor/suggestions
  getSuggestions(query: string): Promise<SuggestionResponse>;
  
  // POST /api/conductor/search/cancel
  cancelSearch(searchId: string): Promise<void>;
}

interface SearchRequest {
  query: string;
  mode: SearchMode;
  context?: {
    previousResults?: string[];
    userPreferences?: UserPreferences;
    sessionId?: string;
  };
  options?: {
    limit?: number;
    offset?: number;
    filters?: SearchFilter[];
  };
}

interface SearchResponse {
  searchId: string;
  results: SearchResult[];
  suggestions: string[];
  metadata: {
    totalResults: number;
    searchTime: number;
    relevanceScore: number;
  };
  facets?: SearchFacet[];
}

// Voice API
interface VoiceAPI {
  // POST /api/conductor/voice/transcribe
  transcribe(request: TranscribeRequest): Promise<TranscribeResponse>;
  
  // POST /api/conductor/voice/synthesize
  synthesize(request: SynthesizeRequest): Promise<SynthesizeResponse>;
  
  // GET /api/conductor/voice/voices
  getAvailableVoices(): Promise<VoiceOption[]>;
}

interface TranscribeRequest {
  audio: Blob;
  format: 'webm' | 'mp3' | 'wav';
  language?: string;
  options?: {
    punctuation?: boolean;
    profanityFilter?: boolean;
    wordTimestamps?: boolean;
  };
}

interface TranscribeResponse {
  transcription: string;
  confidence: number;
  language: string;
  words?: WordTimestamp[];
}

interface SynthesizeRequest {
  text: string;
  voiceId: string;
  options?: {
    speed?: number; // 0.5 - 2.0
    pitch?: number; // -20 - 20
    volume?: number; // 0 - 1
    format?: 'mp3' | 'wav';
  };
}

interface SynthesizeResponse {
  audioUrl: string;
  duration: number;
  format: string;
}

// File API
interface FileAPI {
  // POST /api/conductor/files/upload
  uploadFile(request: FileUploadRequest): Promise<FileUploadResponse>;
  
  // GET /api/conductor/files/{fileId}/status
  getFileStatus(fileId: string): Promise<FileStatusResponse>;
  
  // DELETE /api/conductor/files/{fileId}
  deleteFile(fileId: string): Promise<void>;
  
  // POST /api/conductor/files/{fileId}/process
  processFile(fileId: string, options: ProcessOptions): Promise<ProcessResponse>;
}

interface FileUploadRequest {
  file: File;
  metadata?: {
    description?: string;
    tags?: string[];
    processImmediately?: boolean;
  };
}

interface FileUploadResponse {
  fileId: string;
  status: 'uploaded' | 'processing' | 'ready';
  metadata: {
    name: string;
    size: number;
    type: string;
    uploadedAt: string;
  };
}

interface FileStatusResponse {
  fileId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  result?: {
    extractedText?: string;
    metadata?: Record<string, any>;
    insights?: string[];
  };
  error?: {
    code: string;
    message: string;
  };
}
```

### WebSocket Events

```typescript
// WebSocket Connection
interface WebSocketEvents {
  // Client -> Server
  'search:start': { query: string; mode: SearchMode };
  'search:cancel': { searchId: string };
  'voice:start': { language?: string };
  'voice:stop': void;
  'file:track': { fileId: string };
  
  // Server -> Client
  'search:progress': { searchId: string; progress: number };
  'search:result': { searchId: string; result: SearchResult };
  'search:complete': { searchId: string; metadata: SearchMetadata };
  'voice:level': { level: number }; // 0-100
  'voice:partial': { text: string };
  'file:progress': { fileId: string; progress: number };
  'file:complete': { fileId: string; result: FileResult };
  'error': { type: string; message: string; details?: any };
}

// WebSocket Manager
class conductorWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  
  connect(url: string, token: string): void {
    this.ws = new WebSocket(`${url}?token=${token}`);
    this.setupEventHandlers();
  }
  
  private setupEventHandlers(): void {
    if (!this.ws) return;
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.attemptReconnect();
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onmessage = (event) => {
      this.handleMessage(JSON.parse(event.data));
    };
  }
  
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }
    
    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect(this.url, this.token);
    }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
  }
  
  emit<K extends keyof WebSocketEvents>(
    event: K,
    data: WebSocketEvents[K]
  ): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ event, data }));
    }
  }
}
```

## Performance Optimization Strategies

### 1. Code Splitting and Lazy Loading

```typescript
// Lazy load heavy components
const VoiceSection = lazy(() => import('./components/VoiceSection'));
const FileManager = lazy(() => import('./components/FileManager'));

// Route-based code splitting
const routes = [
  {
    path: '/conductor',
    component: lazy(() => import('./pages/conductorLanding')),
  },
];
```

### 2. Memoization and Performance Hooks

```typescript
// Memoize expensive computations
const SearchResults = memo(({ results }: { results: SearchResult[] }) => {
  const processedResults = useMemo(
    () => processResults(results),
    [results]
  );
  
  return (
    <VirtualList
      items={processedResults}
      itemHeight={80}
      renderItem={renderSearchResult}
    />
  );
});

// Debounce search input
const debouncedSearch = useMemo(
  () => debounce(performSearch, 300),
  [performSearch]
);
```

### 3. Virtual Scrolling for Large Lists

```typescript
// VirtualList component for file downloads
interface VirtualListProps<T> {
  items: T[];
  itemHeight: number;
  renderItem: (item: T, index: number) => ReactNode;
  overscan?: number;
}

const VirtualList = <T,>({
  items,
  itemHeight,
  renderItem,
  overscan = 3,
}: VirtualListProps<T>) => {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const visibleRange = useMemo(() => {
    const container = containerRef.current;
    if (!container) return { start: 0, end: 0 };
    
    const start = Math.floor(scrollTop / itemHeight);
    const end = Math.ceil(
      (scrollTop + container.clientHeight) / itemHeight
    );
    
    return {
      start: Math.max(0, start - overscan),
      end: Math.min(items.length, end + overscan),
    };
  }, [scrollTop, itemHeight, items.length, overscan]);
  
  // Render only visible items
  const visibleItems = items.slice(visibleRange.start, visibleRange.end);
  
  return (
    <div
      ref={containerRef}
      onScroll={(e) => setScrollTop(e.currentTarget.scrollTop)}
      style={{ height: '100%', overflow: 'auto' }}
    >
      <div style={{ height: items.length * itemHeight }}>
        <div
          style={{
            transform: `translateY(${visibleRange.start * itemHeight}px)`,
          }}
        >
          {visibleItems.map((item, index) =>
            renderItem(item, visibleRange.start + index)
          )}
        </div>
      </div>
    </div>
  );
};
```

### 4. Resource Preloading and Caching

```typescript
// Preload critical resources
const preloadResources = () => {
  // Preload fonts
  const fontLink = document.createElement('link');
  fontLink.rel = 'preload';
  fontLink.as = 'font';
  fontLink.href = '/fonts/Inter-var.woff2';
  fontLink.crossOrigin = 'anonymous';
  document.head.appendChild(fontLink);
  
  // Preload critical images
  const criticalImages = ['/logo.svg', '/icons/search.svg'];
  criticalImages.forEach((src) => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'image';
    link.href = src;
    document.head.appendChild(link);
  });
};

// Service Worker for caching
const cachingStrategy = {
  static: {
    name: 'static-v1',
    urls: ['/fonts/', '/icons/', '/images/'],
    strategy: 'CacheFirst',
  },
  api: {
    name: 'api-v1',
    urls: ['/api/conductor/suggestions'],
    strategy: 'NetworkFirst',
    ttl: 300, // 5 minutes
  },
};
```

### 5. Performance Budget

```typescript
interface PerformanceBudget {
  metrics: {
    firstContentfulPaint: 1500; // ms
    timeToInteractive: 3000; // ms
    totalBlockingTime: 300; // ms
    cumulativeLayoutShift: 0.1;
    largestContentfulPaint: 2500; // ms
  };
  resources: {
    totalJavaScript: 300; // KB
    totalCSS: 50; // KB
    totalImages: 500; // KB
    totalFonts: 100; // KB
  };
  thirdParty: {
    totalSize: 200; // KB
    maxRequests: 10;
  };
}

// Performance monitoring
const performanceObserver = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (entry.entryType === 'largest-contentful-paint') {
      console.log('LCP:', entry.startTime);
      // Send to analytics
    }
  }
});

performanceObserver.observe({ entryTypes: ['largest-contentful-paint'] });
```

## Accessibility Implementation

### 1. Keyboard Navigation

```typescript
// Keyboard navigation hook
const useKeyboardNavigation = () => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Global shortcuts
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'k':
            e.preventDefault();
            focusSearchInput();
            break;
          case '/':
            e.preventDefault();
            toggleCommandPalette();
            break;
        }
      }
      
      // Tab navigation
      if (e.key === 'Tab') {
        const focusableElements = getFocusableElements();
        handleTabNavigation(e, focusableElements);
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);
};
```

### 2. ARIA Labels and Roles

```typescript
// Accessible search component
const SearchInput: FC<SearchInputProps> = ({ value, onChange, onSubmit }) => {
  const inputId = useId();
  const [announcement, setAnnouncement] = useState('');
  
  return (
    <div role="search" aria-label="conductor search">
      <label htmlFor={inputId} className="sr-only">
        Search query
      </label>
      <input
        id={inputId}
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            onSubmit();
            setAnnouncement('Search submitted');
          }
        }}
        aria-describedby="search-instructions"
        aria-live="polite"
        aria-atomic="true"
      />
      <span id="search-instructions" className="sr-only">
        Press Enter to search, use arrow keys to navigate suggestions
      </span>
      <div role="status" aria-live="polite" className="sr-only">
        {announcement}
      </div>
    </div>
  );
};
```

### 3. Focus Management

```typescript
// Focus trap for modals
const useFocusTrap = (ref: RefObject<HTMLElement>) => {
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    
    const focusableElements = element.querySelectorAll(
      'a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[
      focusableElements.length - 1
    ] as HTMLElement;
    
    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      
      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    };
    
    element.addEventListener('keydown', handleTabKey);
    firstElement?.focus();
    
    return () => element.removeEventListener('keydown', handleTabKey);
  }, [ref]);
};
```

## Integration Plan

### Phase 1: Foundation (Week 1)
1. Set up new route `/conductor` in TanStack Router
2. Create base Zustand store with TypeScript interfaces
3. Implement core layout components
4. Set up WebSocket infrastructure

### Phase 2: Core Features (Week 2)
1. Implement search functionality with all modes
2. Add voice recording and synthesis
3. Create file upload/download system
4. Integrate with existing API patterns

### Phase 3: Enhancement (Week 3)
1. Add real-time updates via WebSocket
2. Implement virtual scrolling for performance
3. Add comprehensive error handling
4. Create loading states and skeletons

### Phase 4: Polish (Week 4)
1. Accessibility audit and fixes
2. Performance optimization
3. Cross-browser testing
4. Documentation and handoff

## Testing Strategy

### Unit Tests
```typescript
// Component testing with React Testing Library
describe('SearchInput', () => {
  it('should handle search submission', async () => {
    const onSubmit = jest.fn();
    const { getByRole } = render(
      <SearchInput value="test" onChange={() => {}} onSubmit={onSubmit} />
    );
    
    const input = getByRole('searchbox');
    fireEvent.keyDown(input, { key: 'Enter' });
    
    expect(onSubmit).toHaveBeenCalled();
  });
});
```

### Integration Tests
```typescript
// API integration tests
describe('Search API', () => {
  it('should return search results', async () => {
    const response = await searchAPI.search({
      query: 'test query',
      mode: 'deep',
    });
    
    expect(response.results).toHaveLength(10);
    expect(response.metadata.searchTime).toBeLessThan(500);
  });
});
```

### E2E Tests
```typescript
// Playwright E2E tests
test('complete search flow', async ({ page }) => {
  await page.goto('/conductor');
  
  // Type search query
  await page.fill('[role="searchbox"]', 'AI coordination');
  await page.press('[role="searchbox"]', 'Enter');
  
  // Wait for results
  await page.waitForSelector('[data-testid="search-results"]');
  
  // Verify results displayed
  const results = await page.$$('[data-testid="search-result"]');
  expect(results.length).toBeGreaterThan(0);
});
```

## Security Considerations

1. **Input Validation**: All user inputs sanitized before processing
2. **File Upload Security**: Type validation, size limits, virus scanning
3. **API Rate Limiting**: Implement per-user rate limits
4. **WebSocket Security**: Token-based authentication, message validation
5. **Content Security Policy**: Strict CSP headers for XSS protection

## Monitoring and Analytics

```typescript
// Performance monitoring
interface PerformanceMetrics {
  searchLatency: number;
  voiceProcessingTime: number;
  fileUploadSpeed: number;
  webSocketLatency: number;
  renderTime: number;
}

// User analytics
interface UserAnalytics {
  searchQueries: number;
  searchModes: Record<SearchMode, number>;
  voiceUsage: number;
  fileUploads: number;
  errors: ErrorMetric[];
}
```

## Conclusion

This architecture provides a solid foundation for implementing the conductor Landing Page with:
- Modular, maintainable component structure
- Comprehensive state management
- Robust API contracts
- Performance optimizations
- Full accessibility support
- Clear integration path

The design ensures scalability, performance, and user experience while maintaining consistency with the existing admin-ui infrastructure.