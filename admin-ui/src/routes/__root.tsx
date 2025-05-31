import React from 'react';
import { Outlet, createRootRoute, useLocation } from '@tanstack/react-router';
import AppLayout from '@/components/layout/AppLayout';
import { ThemeProvider } from '@/context/ThemeContext';
// import { useAuthStore } from '@/store/authStore'; // Temporarily commented out

// Placeholder for TanStack Query Devtools
// const TanStackRouterDevtools =
//   process.env.NODE_ENV === 'production'
//     ? () => null
//     : React.lazy(() =>
//         import('@tanstack/router-devtools').then((res) => ({
//           default: res.TanStackRouterDevtools,
//         })),
//       );

// Simple error boundary component
class ErrorBoundary extends React.Component<
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
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50">
          <div className="text-center max-w-md p-6 bg-white rounded-lg shadow-lg">
            <h1 className="text-2xl font-bold text-red-600 mb-4">Something went wrong!</h1>
            <p className="mt-2 text-gray-600 mb-4">Please refresh the page or try again.</p>
            {/* Show error details in development */}
            {this.state.error && (
              <details className="text-left mb-4">
                <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                  Error details (click to expand)
                </summary>
                <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-auto">
                  {this.state.error.message}
                  {'\n\n'}
                  {this.state.error.stack}
                </pre>
              </details>
            )}
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export const Route = createRootRoute({
  // Temporarily disable auth check to debug
  // beforeLoad: async ({ location }) => {
  //   // Only check auth for non-login routes
  //   if (location.pathname !== '/login') {
  //     const { isAuthenticated } = useAuthStore.getState();
      
  //     console.log('Root beforeLoad: checking auth for', location.pathname, 'isAuthenticated:', isAuthenticated);
      
  //     if (!isAuthenticated) {
  //       console.log('Not authenticated, redirecting to login');
  //       throw redirect({
  //         to: '/login',
  //         search: {
  //           redirect: location.pathname,
  //         },
  //       });
  //     }
  //   }
  // },
  component: RootComponent,
  // Add notFoundComponent to the root route options if not already defined in routes.tsx
  // notFoundComponent: () => <NotFoundPage />, // Assuming NotFoundPage is imported
});

function RootComponent() {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';
  
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="neutral" defaultMode="light" storageKey="admin-ui-theme">
        {/* Only wrap with AppLayout if not on login page */}
        {isLoginPage ? (
          <Outlet />
        ) : (
          <AppLayout>
            <Outlet />
          </AppLayout>
        )}
        {/* <React.Suspense fallback={null}>
          <TanStackRouterDevtools position="bottom-right" />
        </React.Suspense> */}
      </ThemeProvider>
    </ErrorBoundary>
  );
}
