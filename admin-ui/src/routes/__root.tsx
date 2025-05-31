import React from 'react';
import { Outlet, createRootRoute, redirect, useLocation } from '@tanstack/react-router';
import AppLayout from '@/components/layout/AppLayout';
import { ThemeProvider } from '@/context/ThemeContext';
import { useAuthStore } from '@/store/authStore'; // Import auth store

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
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-red-600">Something went wrong!</h1>
            <p className="mt-2 text-gray-600">Please refresh the page or try again.</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
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
  beforeLoad: async ({ location }) => {
    const { isAuthenticated } = useAuthStore.getState(); // Get latest auth state

    console.log('Root beforeLoad: isAuthenticated', isAuthenticated, 'location.pathname', location.pathname);

    if (!isAuthenticated && location.pathname !== '/login') {
      console.log('User not authenticated, redirecting to /login');
      throw redirect({
        to: '/login',
        // Optional: pass the original intended path to redirect back after login
        search: {
          redirect: location.pathname,
        },
      });
    }
    // If authenticated and trying to access /login, redirect to dashboard
    // This case is better handled in LoginPage.tsx itself using useEffect to avoid flashing login page.
    // However, it can also be enforced here.
    // if (isAuthenticated && location.pathname === '/login') {
    //   console.log('User authenticated, redirecting from /login to /');
    //   throw redirect({
    //     to: '/',
    //   });
    // }
  },
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
