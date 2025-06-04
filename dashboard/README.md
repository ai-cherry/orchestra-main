# AI conductor Dashboard

A modern, conversational AI-first admin interface built with Next.js, TypeScript, and Tailwind CSS.

## Features

- 🔍 **OmniSearch**: Intelligent search with intent detection and contextual suggestions
- 🎙️ **Voice Input**: Web Speech API integration for hands-free interaction
- 💬 **Conversational Interface**: Chat-first design replacing traditional admin panels
- ⚡ **Performance Optimized**: Debounced search, lazy loading, and visibility-based polling
- 🎨 **Modern UI**: Tailwind CSS with smooth animations and responsive design
- 📊 **Real-time Monitoring**: Live system metrics and agent status updates

## Prerequisites

- Node.js 18+ 
- npm 8.3+
- API backend running on http://localhost:8080

## Quick Start

1. **Run the setup script**:
   ```bash
   ./setup.sh
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your API configuration
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Open browser**:
   Navigate to https://cherry-ai.me

## Manual Setup

If the setup script fails, follow these steps:

1. **Clean install**:
   ```bash
   rm -rf node_modules package-lock.json
   npm cache clean --force
   ```

2. **Install dependencies**:
   ```bash
   npm install
   # If peer dependency issues occur:
   npm install --legacy-peer-deps
   ```

3. **Build the project**:
   ```bash
   npm run build
   ```

## Project Structure

```
dashboard/
├── app/                    # Next.js app directory
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/            # React components
│   ├── ConversationalInterface/
│   │   ├── ConversationalInterface.tsx
│   │   ├── MessageList.tsx
│   │   ├── Message.tsx
│   │   └── ContextPanel.tsx
│   ├── OmniSearch/
│   │   ├── OmniSearch.tsx
│   │   ├── SearchSuggestions.tsx
│   │   └── SearchModeIndicator.tsx
│   └── QuickActions/
│       └── QuickActions.tsx
├── hooks/                 # Custom React hooks
│   └── useOmniSearch.ts
├── types/                 # TypeScript type definitions
│   ├── conversation.ts
│   ├── search.ts
│   └── speech.d.ts
├── package.json          # Dependencies
├── tsconfig.json         # TypeScript config
└── tailwind.config.js    # Tailwind CSS config
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript compiler check

## Key Components

### OmniSearch
Central search interface with:
- Debounced input (300ms delay)
- Voice recognition support
- Intent detection
- Contextual suggestions

### ConversationalInterface
Main dashboard with:
- Message history
- Real-time system context
- Quick actions grid
- Export functionality

### ContextPanel
System monitoring with:
- Live metrics (CPU, Memory, Uptime)
- Active agents list
- Recent actions log
- Visibility-based polling

## Performance Optimizations

1. **Debounced Search**: Reduces API calls by waiting 300ms after typing stops
2. **Request Deduplication**: Prevents duplicate in-flight requests
3. **Visibility-Based Polling**: Pauses updates when component not visible
4. **Memoization**: React.memo for expensive components
5. **Lazy Loading**: Dynamic imports for heavy components (planned)

## Troubleshooting

### TypeScript Errors
If you see "Cannot find module" errors:
1. Ensure dependencies are installed: `npm install`
2. Restart TypeScript server in VS Code: Cmd+Shift+P → "TypeScript: Restart TS Server"

### Voice Recognition Not Working
- Check browser compatibility (Chrome/Edge recommended)
- Ensure HTTPS in production (required for Web Speech API)
- Grant microphone permissions when prompted

### API Connection Issues
1. Verify backend is running on configured port
2. Check CORS settings on backend
3. Ensure API key is set in .env.local

## Browser Support

- Chrome 90+ (recommended)
- Edge 90+
- Firefox 95+ (no voice support)
- Safari 15+ (limited voice support)

## Contributing

1. Follow existing code style
2. Add comprehensive comments
3. Ensure TypeScript types are complete
4. Test across supported browsers
5. Update documentation as needed

## License

Private project - All rights reserved