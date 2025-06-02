# Orchestrator Landing Page - Implementation Guide & Code Handoff

## Overview
This document provides a complete implementation guide for the Orchestrator Landing Page, consolidating all architectural decisions, component specifications, and integration requirements for immediate development.

## Project Structure

```
admin-ui/src/
├── components/
│   └── orchestrator/
│       ├── OrchestratorLandingPage.tsx
│       ├── layout/
│       │   ├── Header.tsx
│       │   ├── Footer.tsx
│       │   └── MainContent.tsx
│       ├── search/
│       │   ├── SearchSection.tsx
│       │   ├── SearchInput.tsx
│       │   ├── InputModeSelector.tsx
│       │   ├── SearchModeSelector.tsx
│       │   ├── SearchResults.tsx
│       │   └── SearchResultItem.tsx
│       ├── voice/
│       │   ├── VoiceSection.tsx
│       │   ├── VoiceRecorder.tsx
│       │   ├── VoiceSynthesizer.tsx
│       │   ├── VoiceSelector.tsx
│       │   └── VoiceVisualizer.tsx
│       ├── files/
│       │   ├── FileManager.tsx
│       │   ├── FileUploader.tsx
│       │   ├── DownloadTable.tsx
│       │   ├── DownloadTableRow.tsx
│       │   └── FileIcon.tsx
│       ├── suggestions/
│       │   ├── SuggestionsPanel.tsx
│       │   └── SuggestionChip.tsx
│       └── common/
│           ├── LoadingSpinner.tsx
│           ├── ErrorBoundary.tsx
│           └── VirtualList.tsx
├── store/
│   └── orchestratorStore.ts
├── services/
│   ├── api/
│   │   ├── httpClient.ts
│   │   ├── searchAPI.ts
│   │   ├── voiceAPI.ts
│   │   └── fileAPI.ts
│   └── websocket/
│       ├── OrchestratorWebSocket.ts
│       └── websocketEvents.ts
├── hooks/
│   ├── useOrchestratorSearch.ts
│   ├── useVoiceRecording.ts
│   ├── useFileUpload.ts
│   └── useWebSocket.ts
├── types/
│   └── orchestrator.types.ts
├── utils/
│   ├── circuitBreaker.ts
│   ├── debounce.ts
│   ├── formatters.ts
│   └── validators.ts
└── routes/
    └── orchestrator.tsx
```

## Implementation Steps

### Step 1: Type Definitions
Create the base type definitions that will be used throughout the application.

```typescript
// types/orchestrator.types.ts
export type InputMode = 'text' | 'voice' | 'file';
export type SearchMode = 'creative' | 'deep' | 'super_deep';
export type FileStatus = 'queued' | 'downloading' | 'completed' | 'failed' | 'cancelled';

export interface SearchResult {
  id: string;
  title: string;
  content: string;
  relevance: number;
  source: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

// ... (include all types from orchestrator_component_specifications.md)
```

### Step 2: Zustand Store Setup
Implement the orchestrator store with all required state and actions.

```typescript
// store/orchestratorStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { subscribeWithSelector } from 'zustand/middleware';
import { searchAPI, voiceAPI, fileAPI } from '@/services/api';

interface OrchestratorState {
  // State definitions from architecture document
  search: SearchState;
  voice: VoiceState;
  files: FilesState;
  ui: UIState;
  
  // Actions
  actions: OrchestratorActions;
}

export const useOrchestratorStore = create<OrchestratorState>()(
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
        // ... rest of initial state
        
        actions: {
          // Search actions
          setQuery: (query: string) => 
            set((state) => ({ 
              search: { ...state.search, query } 
            })),
            
          performSearch: async () => {
            const { search } = get();
            if (!search.query.trim()) return;
            
            set((state) => ({
              search: { ...state.search, isSearching: true, error: null }
            }));
            
            try {
              const response = await searchAPI.search({
                query: search.query,
                mode: search.mode,
              });
              
              set((state) => ({
                search: {
                  ...state.search,
                  results: response.results,
                  suggestions: response.suggestions,
                  isSearching: false,
                }
              }));
            } catch (error) {
              set((state) => ({
                search: {
                  ...state.search,
                  error: error.message,
                  isSearching: false,
                }
              }));
            }
          },
          // ... implement all other actions
        },
      }),
      {
        name: 'orchestrator-storage',
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

### Step 3: API Services Implementation
Create the API service classes with proper error handling and caching.

```typescript
// services/api/httpClient.ts
import axios from 'axios';
import { API_CONFIG } from '@/config/api.config';

// Implement base HTTP client with interceptors
// (Use code from orchestrator_api_integration.md)

// services/api/searchAPI.ts
export class SearchAPI {
  // Implement search methods with circuit breaker
  // (Use code from orchestrator_api_integration.md)
}

// services/api/voiceAPI.ts
export class VoiceAPI {
  // Implement voice methods
}

// services/api/fileAPI.ts
export class FileAPI {
  // Implement file management methods
}
```

### Step 4: WebSocket Implementation
Set up the WebSocket connection for real-time updates.

```typescript
// services/websocket/OrchestratorWebSocket.ts
// (Use the complete implementation from orchestrator_api_integration.md)

// hooks/useWebSocket.ts
import { useEffect, useRef } from 'react';
import { OrchestratorWebSocket } from '@/services/websocket';
import { useOrchestratorStore } from '@/store/orchestratorStore';

export const useWebSocket = () => {
  const wsRef = useRef<OrchestratorWebSocket | null>(null);
  const { actions } = useOrchestratorStore();
  
  useEffect(() => {
    const token = localStorage.getItem('auth-token');
    if (!token) return;
    
    wsRef.current = new OrchestratorWebSocket(
      API_CONFIG.wsURL,
      token
    );
    
    // Set up event listeners
    wsRef.current.on('search:result', (data) => {
      actions.addSearchResult(data);
    });
    
    wsRef.current.on('file:progress', (data) => {
      actions.updateFileProgress(data.fileId, data.progress);
    });
    
    // ... other event listeners
    
    return () => {
      wsRef.current?.close();
    };
  }, []);
  
  return wsRef.current;
};
```

### Step 5: Core Components Implementation

#### Main Landing Page Component
```typescript
// components/orchestrator/OrchestratorLandingPage.tsx
import { FC, Suspense, lazy } from 'react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { useOrchestratorStore } from '@/store/orchestratorStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Header } from './layout/Header';
import { SearchSection } from './search/SearchSection';
import { MessageComposer } from './MessageComposer';
import { SuggestionsPanel } from './suggestions/SuggestionsPanel';
import { LoadingSection } from './common/LoadingSection';

const VoiceSection = lazy(() => import('./voice/VoiceSection'));
const FileManager = lazy(() => import('./files/FileManager'));

export const OrchestratorLandingPage: FC = () => {
  const { ui } = useOrchestratorStore();
  const ws = useWebSocket();
  
  return (
    <PageWrapper className="orchestrator-landing bg-[#181111] min-h-screen">
      <Header />
      <main className="flex-1 overflow-hidden">
        <div className="container mx-auto px-4 py-6 max-w-6xl">
          <SearchSection />
          <MessageComposer />
          <SuggestionsPanel />
          
          <Suspense fallback={<LoadingSection />}>
            {ui.activePanel === 'voice' && <VoiceSection />}
            {ui.activePanel === 'file' && <FileManager />}
          </Suspense>
        </div>
      </main>
    </PageWrapper>
  );
};
```

#### Search Components
```typescript
// components/orchestrator/search/SearchInput.tsx
// (Use the complete implementation from orchestrator_component_specifications.md)

// components/orchestrator/search/SearchSection.tsx
// (Use the complete implementation from orchestrator_component_specifications.md)
```

### Step 6: Route Configuration
Add the orchestrator route to the routing system.

```typescript
// routes/orchestrator.tsx
import { createFileRoute } from '@tanstack/react-router';
import { OrchestratorLandingPage } from '@/components/orchestrator/OrchestratorLandingPage';

export const Route = createFileRoute('/orchestrator')({
  component: OrchestratorLandingPage,
  beforeLoad: async ({ context }) => {
    // Ensure user is authenticated
    if (!context.auth.isAuthenticated) {
      throw redirect({
        to: '/login',
        search: {
          redirect: '/orchestrator',
        },
      });
    }
  },
});
```

### Step 7: Styling Configuration
Update Tailwind configuration for the dark theme.

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        orchestrator: {
          bg: '#181111',
          card: '#261C1C',
          border: '#382929',
          accent: '#e82626',
          'accent-hover': '#d01f1f',
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
};
```

### Step 8: Performance Optimizations

#### Virtual List Implementation
```typescript
// components/orchestrator/common/VirtualList.tsx
// (Use the implementation from orchestrator_landing_architecture.md)
```

#### Debounced Search Hook
```typescript
// hooks/useOrchestratorSearch.ts
import { useCallback, useEffect, useMemo } from 'react';
import { useOrchestratorStore } from '@/store/orchestratorStore';
import { debounce } from '@/utils/debounce';

export const useOrchestratorSearch = () => {
  const { search, actions } = useOrchestratorStore();
  
  const debouncedSearch = useMemo(
    () => debounce(actions.performSearch, 300),
    [actions.performSearch]
  );
  
  const debouncedFetchSuggestions = useMemo(
    () => debounce(actions.fetchSuggestions, 200),
    [actions.fetchSuggestions]
  );
  
  useEffect(() => {
    if (search.query.length > 2) {
      debouncedFetchSuggestions(search.query);
    }
  }, [search.query, debouncedFetchSuggestions]);
  
  return {
    search,
    performSearch: debouncedSearch,
    setQuery: actions.setQuery,
    setMode: actions.setSearchMode,
  };
};
```

### Step 9: Error Handling

```typescript
// components/orchestrator/common/ErrorBoundary.tsx
import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Orchestrator Error:', error, errorInfo);
    // Send to error tracking service
  }
  
  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-8 text-center">
          <h2 className="text-xl text-white mb-4">Something went wrong</h2>
          <p className="text-gray-400">{this.state.error?.message}</p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-4 px-4 py-2 bg-[#e82626] text-white rounded"
          >
            Try again
          </button>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

### Step 10: Testing Setup

```typescript
// components/orchestrator/__tests__/SearchInput.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SearchInput } from '../search/SearchInput';

describe('SearchInput', () => {
  it('should handle search submission', async () => {
    const onSubmit = jest.fn();
    const onChange = jest.fn();
    
    render(
      <SearchInput
        value="test query"
        onChange={onChange}
        onSubmit={onSubmit}
      />
    );
    
    const input = screen.getByRole('textbox', { name: /search query/i });
    fireEvent.keyDown(input, { key: 'Enter' });
    
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalled();
    });
  });
  
  it('should show character count', () => {
    render(
      <SearchInput
        value="test"
        onChange={() => {}}
        onSubmit={() => {}}
        maxLength={100}
      />
    );
    
    expect(screen.getByText('4/100')).toBeInTheDocument();
  });
});
```

## Performance Checklist

- [ ] Implement code splitting for voice and file sections
- [ ] Add virtual scrolling for search results and file lists
- [ ] Implement request deduplication in API client
- [ ] Add response caching with TTL
- [ ] Optimize bundle size with tree shaking
- [ ] Implement progressive image loading
- [ ] Add service worker for offline support
- [ ] Use React.memo for expensive components
- [ ] Implement proper error boundaries
- [ ] Add performance monitoring

## Accessibility Checklist

- [ ] All interactive elements have proper ARIA labels
- [ ] Keyboard navigation works throughout the app
- [ ] Focus management for modals and panels
- [ ] Screen reader announcements for dynamic content
- [ ] Color contrast meets WCAG 2.1 AA standards
- [ ] All images have alt text
- [ ] Form inputs have associated labels
- [ ] Error messages are announced
- [ ] Loading states are communicated
- [ ] Skip navigation links provided

## Security Checklist

- [ ] Input sanitization for all user inputs
- [ ] XSS protection in search results rendering
- [ ] CSRF tokens for all mutations
- [ ] File upload validation (type, size, content)
- [ ] Rate limiting on all endpoints
- [ ] Secure WebSocket authentication
- [ ] Content Security Policy headers
- [ ] HTTPS enforcement
- [ ] Token refresh mechanism
- [ ] Session timeout handling

## Deployment Considerations

### Environment Variables
```bash
# .env.production
VITE_API_URL=https://api.orchestrator.com
VITE_WS_URL=wss://api.orchestrator.com/ws
VITE_MAX_FILE_SIZE=10485760
VITE_ALLOWED_FILE_TYPES=image/*,application/pdf,text/*
VITE_VOICE_LANGUAGES=en-US,es-ES,fr-FR,de-DE
```

### Build Optimization
```json
// vite.config.ts additions
{
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'orchestrator-voice': ['./src/components/orchestrator/voice'],
          'orchestrator-files': ['./src/components/orchestrator/files'],
          'vendor-audio': ['wavesurfer.js', 'recorder.js'],
        },
      },
    },
    target: 'es2020',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
  },
}
```

### Monitoring Setup
```typescript
// utils/monitoring.ts
export const trackPerformance = (metric: string, value: number) => {
  // Send to analytics service
  if (window.gtag) {
    window.gtag('event', 'timing_complete', {
      name: metric,
      value: Math.round(value),
      event_category: 'orchestrator',
    });
  }
};

export const trackError = (error: Error, context?: any) => {
  // Send to error tracking service
  if (window.Sentry) {
    window.Sentry.captureException(error, {
      tags: {
        component: 'orchestrator',
      },
      extra: context,
    });
  }
};
```

## Next Steps for Code Agent

1. **Start with core infrastructure**
   - Set up types and interfaces
   - Create Zustand store
   - Implement base API client

2. **Build search functionality first**
   - Search input component
   - Mode selectors
   - Results display
   - Real-time suggestions

3. **Add voice capabilities**
   - Recording interface
   - Transcription display
   - Voice synthesis

4. **Implement file management**
   - Drag-and-drop upload
   - Progress tracking
   - Download table

5. **Connect WebSocket for real-time**
   - Search progress
   - File upload status
   - System notifications

6. **Polish and optimize**
   - Performance improvements
   - Accessibility audit
   - Cross-browser testing

## Success Metrics

- Initial page load < 2s
- Time to interactive < 3s
- Search response < 500ms
- Voice recognition latency < 1s
- 100% keyboard navigable
- WCAG 2.1 AA compliant
- 95%+ test coverage
- Zero critical security vulnerabilities

This completes the comprehensive architecture and implementation guide for the Orchestrator Landing Page. The code agent can now proceed with implementation following this detailed blueprint.