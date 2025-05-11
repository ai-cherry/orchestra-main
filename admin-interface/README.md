p# AI Orchestra Admin Interface

A modern, responsive admin interface for the AI Orchestra project, providing management capabilities for memory systems, agent registry, conversation exploration, and MCP monitoring.

## Features

- **Dashboard**: System overview with key metrics, memory usage, and agent activity charts
- **Memory Management**: Detailed visibility into hot, warm, and cold memory tiers with usage analytics
- **Agent Registry**: Management of AI agents with performance metrics and activity tracking
- **Conversation Explorer**: Access to conversation history with filtering and analytics
- **MCP Monitoring**: Monitoring of Model Context Protocol servers and connected tools
- **Dark/Light Mode**: Theme support with system preference detection
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **React**: UI library
- **TypeScript**: Type safety
- **React Router**: Navigation
- **Tailwind CSS**: Utility-first styling
- **Recharts**: Data visualization
- **Axios**: API client
- **Zustand**: State management
- **Vite**: Build tool

## Project Structure

```
admin-interface/
├── public/             # Static assets
├── src/
│   ├── components/     # Reusable UI components
│   │   ├── layout/     # Layout components (Header, Sidebar)
│   │   ├── ui/         # UI components (Button, Card, etc.)
│   │   └── theme-provider.tsx # Theme management
│   ├── lib/            # Utilities and hooks
│   │   ├── api.ts      # API service
│   │   ├── hooks.ts    # Custom React hooks
│   │   └── utils.ts    # Utility functions
│   ├── modules/        # Feature modules
│   │   ├── agents/     # Agent registry module
│   │   ├── conversations/ # Conversation explorer module
│   │   ├── dashboard/  # Dashboard module
│   │   ├── mcp/        # MCP monitoring module
│   │   ├── memory/     # Memory management module
│   │   └── NotFound.tsx # 404 page
│   ├── App.tsx         # Main application component
│   ├── index.css       # Global styles
│   └── main.tsx        # Entry point
└── Configuration files (package.json, tsconfig.json, etc.)
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## API Integration

The admin interface connects to the AI Orchestra backend API to fetch data and perform operations. The API service is implemented in `src/lib/api.ts` and provides the following features:

- Error handling with fallback to mock data during development
- Type-safe API responses
- Centralized API client configuration

## Custom Hooks

The project includes several custom hooks to improve code organization and reusability:

- `useFetch`: Generic hook for data fetching with loading and error states
- `useMultiFetch`: Hook for fetching multiple data sources in parallel
- `usePagination`: Hook for managing pagination
- `useSearchAndFilter`: Hook for managing search and filter state

## Improvements

### Code Quality

- Type-safe API service with proper error handling
- Custom hooks for data fetching and state management
- Consistent component structure with proper documentation
- Responsive design with mobile support

### Performance

- Optimized data fetching with parallel requests
- Memoization of static data
- Lazy loading of routes

### User Experience

- Loading states for better feedback
- Error handling with retry functionality
- Consistent design language
- Dark/Light mode support

## Integration with AI Orchestra

The admin interface is designed to work seamlessly with the AI Orchestra backend API, providing a user-friendly interface for administrators to:

1. Monitor system health and performance
2. Manage memory tiers and optimize memory usage
3. Register and configure AI agents
4. Explore conversation history and analytics
5. Monitor MCP servers and tools