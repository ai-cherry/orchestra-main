# conductor Landing Page Components

This directory contains all components for the conductor Landing Page, a sophisticated multi-modal search interface with voice, text, and file input capabilities.

## Overview

The conductor Landing Page provides:
- Multi-modal input (text, voice, file)
- Three search modes (Creative, Deep, Super Deep)
- Real-time suggestions
- File upload/download with progress tracking
- Voice recording and synthesis
- WebSocket support for real-time updates

## Component Structure

```
conductor/
├── SearchInterface/
│   ├── index.tsx           # Main search interface container
│   ├── SearchInput.tsx     # Multi-modal input component
│   ├── InputModeSelector.tsx # Toggle between text/voice/file
│   └── SearchModeSelector.tsx # Select search depth
├── Voice/                  # Voice components (Phase 3)
├── FileManagement/         # File upload/download (Phase 3)
└── Suggestions/            # Suggestion system (Phase 3)
```

## Key Features

### 1. Search Interface
The main component that cherry_aites all search functionality:
- Manages search state through Zustand store
- Handles mode selection and input type switching
- Displays suggestions dynamically

### 2. Input Modes
- **Text**: Traditional text input with debouncing
- **Voice**: Web Speech API integration for voice commands
- **File**: Drag-and-drop file upload with progress tracking

### 3. Search Modes
- **Creative**: Fast, innovative responses
- **Deep**: Thorough analysis with detailed insights
- **Super Deep**: Comprehensive research with exhaustive coverage

## Styling

The components use a custom dark theme defined in `conductor.css`:
- Background: `#181111`
- Secondary: `#261C1C`
- Border: `#382929`
- Accent: `#e82626`
- Text: `#ffffff` / `#b89d9d`

## State Management

Uses Zustand store (`conductorStore.ts`) for:
- Search query and mode management
- Voice recording state
- File upload/download tracking
- Suggestions and results
- Error handling

## API Integration

The `conductorService.ts` provides:
- Search operations
- Suggestion fetching
- Voice transcription/synthesis
- File upload/download with progress callbacks

## Usage Example

```tsx
import { conductorLandingPage } from './pages/conductorLandingPage';

// In your routes
<Route path="/conductor" component={conductorLandingPage} />
```

## Development Status

### ✅ Completed (Phase 1-2)
- [x] Base layout with dark theme
- [x] Search interface components
- [x] Multi-modal input switching
- [x] Search mode selection
- [x] Zustand store integration
- [x] Basic API service structure
- [x] Custom CSS styling

### 🚧 In Progress (Phase 3-4)
- [ ] Voice recording with Web Speech API
- [ ] Voice synthesis
- [ ] File upload with React Dropzone
- [ ] Progress tracking
- [ ] WebSocket integration
- [ ] Advanced suggestions

### 📋 TODO (Phase 5)
- [ ] Performance optimizations
- [ ] Virtual scrolling for results
- [ ] Lazy loading
- [ ] Accessibility improvements
- [ ] E2E tests
- [ ] Error boundaries

## Performance Considerations

1. **Debouncing**: Search input is debounced to reduce API calls
2. **Lazy Loading**: Voice and file components load on demand
3. **Memoization**: Expensive components use React.memo
4. **Virtual Scrolling**: Large result sets use virtualization

## Accessibility

- ARIA labels on all interactive elements
- Keyboard navigation support
- Focus management
- Screen reader compatibility
- High contrast mode support

## Testing

Run tests with:
```bash
npm test -- --coverage src/components/conductor
```

## Contributing

When adding new features:
1. Follow the existing component structure
2. Update this README
3. Add appropriate tests
4. Ensure accessibility compliance
5. Document any new API endpoints