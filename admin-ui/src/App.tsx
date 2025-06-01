// Remove the old App function.
// The root component is now defined in src/routes/__root.tsx
// main.tsx will directly use the router.
// This file might be removed or repurposed later if not needed by router setup.

// For now, to satisfy the subtask "Update admin-ui/src/App.tsx to use the TanStack Router provider and render the router."
// we will make this file provide the router. However, a more common TanStack Router pattern
// is to have main.tsx set up the RouterProvider.

import React, { Suspense } from 'react';
import { RouterProvider } from '@tanstack/react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { router } from './routes'; // Assuming routes.tsx exports the router instance

// Create a query client with conservative settings
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (was cacheTime)
    },
    mutations: {
      retry: 1,
    },
  },
});

// Loading component
const AppLoader = () => (
  <div className="flex min-h-screen items-center justify-center bg-gray-50">
    <div className="text-center">
      <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      <p className="mt-4 text-gray-600">Loading Cherry Admin UI...</p>
    </div>
  </div>
);

// Error fallback component
const AppError = ({ error, resetError }: { error: Error; resetError: () => void }) => (
  <div className="flex min-h-screen items-center justify-center bg-gray-50">
    <div className="text-center max-w-md p-6 bg-white rounded-lg shadow-lg">
      <h1 className="text-2xl font-bold text-red-600 mb-4">Application Error</h1>
      <p className="text-gray-600 mb-4">
        The application encountered an error. Please try refreshing the page.
      </p>
      <details className="text-left mb-4">
        <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
          Technical details
        </summary>
        <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-auto">
          {error.message}
        </pre>
      </details>
      <div className="space-x-4">
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Refresh Page
        </button>
        <button
          onClick={resetError}
          className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
        >
          Try Again
        </button>
      </div>
    </div>
  </div>
);

// Error boundary with retry capability
class AppErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('App Error Boundary caught:', error, errorInfo);
  }

  resetError = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      return <AppError error={this.state.error} resetError={this.resetError} />;
    }

    return this.props.children;
  }
}

function App() {
  return (
    <AppErrorBoundary>
      <Suspense fallback={<AppLoader />}>
        <QueryClientProvider client={queryClient}>
          <RouterProvider router={router} />
        </QueryClientProvider>
      </Suspense>
    </AppErrorBoundary>
  );
}

export default App;
