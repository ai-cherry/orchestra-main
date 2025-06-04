 # Code Agent Handoff: conductor Landing Page Implementation

## Overview
Implement the conductor Landing Page based on the comprehensive architecture designed by the architect agent. This is a high-priority implementation that will serve as the primary entry point for the coordination system.

## Architecture Documents
Please review these documents created by the architect:
- `conductor_landing_architecture.md` - Core architecture and patterns
- `conductor_component_specifications.md` - Detailed component specs
- `conductor_api_integration.md` - API contracts and WebSocket design
- `conductor_implementation_guide.md` - Step-by-step implementation
- `conductor_architecture_summary.md` - Executive summary

## Implementation Priority Order

### Phase 1: Core Components (Day 1)
1. **Create Landing Page Route**
   - Add route to `admin-ui/src/routes.tsx`
   - Update navigation in `Sidebar.tsx`
   - Create `conductorLandingPage.tsx`

2. **Implement Base Layout**
   - Dark theme with #181111 background
   - Header with navigation
   - Main content area with proper spacing
   - Responsive grid layout

3. **Create Search Interface**
   ```typescript
   // Components to implement:
   - SearchInterface.tsx
   - SearchInput.tsx
   - InputModeSelector.tsx
   - SearchModeSelector.tsx
   ```

### Phase 2: State Management (Day 1-2)
1. **Create Zustand Store**
   ```typescript
   // admin-ui/src/store/conductorStore.ts
   interface conductorStore {
     // Search state
     searchQuery: string;
     searchMode: 'creative' | 'deep' | 'super_deep';
     inputMode: 'text' | 'voice' | 'file';
     suggestions: string[];
     
     // Voice state
     isRecording: boolean;
     selectedVoice: string;
     
     // File state
     uploads: FileUpload[];
     downloads: FileDownload[];
     
     // Actions
     setSearchQuery: (query: string) => void;
     setSearchMode: (mode: SearchMode) => void;
     startRecording: () => void;
     stopRecording: () => void;
     // ... other actions
   }
   ```

2. **Integrate with Existing Stores**
   - Connect to auth store for user context
   - Share state with persona store if needed

### Phase 3: Advanced Features (Day 2-3)
1. **Voice Components**
   ```typescript
   - VoiceRecorder.tsx (Web Speech API)
   - VoiceSynthesizer.tsx (Text-to-Speech)
   - VoiceIndicator.tsx (Visual feedback)
   ```

2. **File Management**
   ```typescript
   - FileUploader.tsx (React Dropzone)
   - FileProgressTable.tsx
   - FileStatusIndicator.tsx
   ```

3. **Suggestions System**
   ```typescript
   - SuggestionsPanel.tsx
   - SuggestionChip.tsx
   - useSuggestions.ts (custom hook)
   ```

### Phase 4: API Integration (Day 3-4)
1. **Create API Client**
   ```typescript
   // admin-ui/src/services/conductorService.ts
   export const conductorService = {
     search: (query: SearchRequest) => api.post('/conductor/search', query),
     getSuggestions: (context: SearchContext) => api.get('/conductor/suggestions'),
     transcribeAudio: (audio: Blob) => api.post('/conductor/voice/transcribe', audio),
     synthesizeSpeech: (text: string, voice: string) => api.post('/conductor/voice/synthesize', { text, voice }),
     uploadFile: (file: File) => api.post('/conductor/files/upload', file),
     getFileStatus: (id: string) => api.get(`/conductor/files/${id}/status`),
   };
   ```

2. **WebSocket Integration**
   ```typescript
   // admin-ui/src/services/websocketManager.ts
   - Connection management
   - Auto-reconnect logic
   - Event handlers for real-time updates
   ```

### Phase 5: Polish & Optimization (Day 4-5)
1. **Performance Optimizations**
   - Implement React.memo for expensive components
   - Add virtual scrolling for file lists
   - Lazy load voice and file components
   - Debounce search input

2. **Accessibility**
   - Add ARIA labels and roles
   - Implement keyboard navigation
   - Test with screen readers
   - Ensure proper focus management

3. **Error Handling**
   - Add error boundaries
   - Implement retry logic
   - User-friendly error messages
   - Fallback UI states

## Component File Structure
```
admin-ui/src/
├── pages/
│   └── conductorLandingPage.tsx
├── components/
│   └── conductor/
│       ├── SearchInterface/
│       │   ├── index.tsx
│       │   ├── SearchInput.tsx
│       │   ├── InputModeSelector.tsx
│       │   └── SearchModeSelector.tsx
│       ├── Voice/
│       │   ├── VoiceRecorder.tsx
│       │   ├── VoiceSynthesizer.tsx
│       │   └── VoiceIndicator.tsx
│       ├── FileManagement/
│       │   ├── FileUploader.tsx
│       │   ├── FileProgressTable.tsx
│       │   └── FileStatusIndicator.tsx
│       └── Suggestions/
│           ├── SuggestionsPanel.tsx
│           └── SuggestionChip.tsx
├── hooks/
│   ├── useconductorSearch.ts
│   ├── useVoiceRecording.ts
│   └── useFileUpload.ts
├── services/
│   ├── conductorService.ts
│   └── websocketManager.ts
└── store/
    └── conductorStore.ts
```

## Styling Guidelines
```css
/* Key color variables */
--bg-primary: #181111;
--bg-secondary: #261C1C;
--border-color: #382929;
--accent-red: #e82626;
--text-primary: #ffffff;
--text-secondary: #b89d9d;
```

## Testing Requirements
1. Unit tests for all components
2. Integration tests for API calls
3. E2E tests for critical user flows
4. Performance benchmarks
5. Accessibility audits

## Success Criteria
- [ ] All components match the provided HTML design
- [ ] Dark theme properly implemented
- [ ] Voice features work across browsers
- [ ] File upload/download with progress tracking
- [ ] Real-time updates via WebSocket
- [ ] Page loads in < 2 seconds
- [ ] Fully accessible (WCAG 2.1 AA)
- [ ] Responsive on all devices

## Dependencies to Install
```json
{
  "react-dropzone": "^14.3.8",  // Already installed
  "react-speech-kit": "^3.0.1",  // For voice features
  "@tanstack/react-query": "^5.77.2",  // Already installed
  "socket.io-client": "^4.7.2"  // For WebSocket
}
```

## API Endpoints to Mock (if backend not ready)
```typescript
// Use MSW (Mock Service Worker) for development
const handlers = [
  rest.post('/api/conductor/search', (req, res, ctx) => {
    return res(ctx.json({ results: [], suggestions: ['Example suggestion'] }));
  }),
  // ... other endpoints
];
```

## Next Steps After Implementation
1. Debug agent will validate functionality
2. Quality agent will check performance
3. Implementation agent will handle deployment
4. Documentation agent will update user guides

Please begin implementation following the priority order above. Focus on getting the core search interface working first, then progressively enhance with voice and file features.