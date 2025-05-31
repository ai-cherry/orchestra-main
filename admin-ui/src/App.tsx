// Remove the old App function.
// The root component is now defined in src/routes/__root.tsx
// main.tsx will directly use the router.
// This file might be removed or repurposed later if not needed by router setup.

// For now, to satisfy the subtask "Update admin-ui/src/App.tsx to use the TanStack Router provider and render the router."
// we will make this file provide the router. However, a more common TanStack Router pattern
// is to have main.tsx set up the RouterProvider.

import { RouterProvider } from '@tanstack/react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { router } from './routes'; // Assuming routes.tsx exports the router instance

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  console.log('App component rendering...');
  try {
    return (
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    );
  } catch (error) {
    console.error('Error rendering router:', error);
    return (
      <div className="p-4 text-red-600">
        <h1 className="text-2xl font-bold">Router Error</h1>
        <pre className="mt-2">{error instanceof Error ? error.message : 'Unknown error'}</pre>
      </div>
    );
  }
}

export default App;
