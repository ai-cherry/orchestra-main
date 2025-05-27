import React from 'react';
import { Outlet, createRootRoute, redirect, useRouterState } from '@tanstack/react-router';
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
  const { isAuthenticated } = useAuthStore(); // Subscribe to state for re-renders if needed
  const routerState = useRouterState(); // Get router state

  // This useEffect is an alternative/additional way to handle redirection,
  // especially if beforeLoad has timing issues or if you need component context.
  // useEffect(() => {
  //   if (!isAuthenticated && routerState.location.pathname !== '/login') {
  //     router.navigate({ to: '/login', search: { redirect: routerState.location.pathname }});
  //   }
  // }, [isAuthenticated, routerState.location.pathname, router]);

  return (
    <ThemeProvider defaultTheme="neutral" defaultMode="light" storageKey="admin-ui-theme">
      {/* Conditionally render AppLayout only if authenticated, or if it's the login page which might not use AppLayout */}
      {/* This logic can be complex. For now, AppLayout is always rendered by __root, 
          and LoginPage itself doesn't use PageWrapper or relies on AppLayout's structure. */}
      <AppLayout>
        <Outlet />
      </AppLayout>
      {/* <React.Suspense fallback={null}>
        <TanStackRouterDevtools position="bottom-right" />
      </React.Suspense> */}
    </ThemeProvider>
  );
}
