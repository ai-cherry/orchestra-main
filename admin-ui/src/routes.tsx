import { createRouter, createRoute } from '@tanstack/react-router';

// Import the Root Route
import { Route as rootRoute } from './routes/__root';

// Import Page Components
import { DashboardPage } from './pages/DashboardPage';
import { AgentsPage } from './pages/AgentsPage';
import { PersonasPage } from './pages/PersonasPage';
import { WorkflowsPage } from './pages/WorkflowsPage';
import { IntegrationsPage } from './pages/IntegrationsPage';
import { ResourcesPage } from './pages/ResourcesPage';
import { LogsPage } from './pages/LogsPage';
import { SettingsPage } from './pages/SettingsPage';
import { LoginPage } from './pages/LoginPage';
import { NotFoundPage } from './pages/NotFoundPage';

// Update rootRoute to include NotFoundPage as the default notFoundComponent
const rootRouteWithNotFound = createRoute({
    ...rootRoute.options, // Spread existing options like component
    notFoundComponent: NotFoundPage, // Add default notFoundComponent
});


// Route Definitions
const indexRoute = createRoute({
  getParentRoute: () => rootRouteWithNotFound,
  path: '/',
  component: DashboardPage,
});

const agentsRoute = createRoute({
  getParentRoute: () => rootRouteWithNotFound,
  path: '/agents',
  component: AgentsPage,
});

const personasRoute = createRoute({
  getParentRoute: () => rootRouteWithNotFound,
  path: '/personas',
  component: PersonasPage,
});

const workflowsRoute = createRoute({
  getParentRoute: () => rootRouteWithNotFound,
  path: '/workflows',
  component: WorkflowsPage,
});

const integrationsRoute = createRoute({
  getParentRoute: () => rootRouteWithNotFound,
  path: '/integrations',
  component: IntegrationsPage,
});

const resourcesRoute = createRoute({
  getParentRoute: () => rootRouteWithNotFound,
  path: '/resources',
  component: ResourcesPage,
});

const logsRoute = createRoute({
  getParentRoute: () => rootRouteWithNotFound,
  path: '/logs',
  component: LogsPage,
});

const settingsRoute = createRoute({
  getParentRoute: () => rootRouteWithNotFound,
  path: '/settings',
  component: SettingsPage,
});

const loginRoute = createRoute({
  getParentRoute: () => rootRouteWithNotFound, // Login might eventually have a different root or no root layout
  path: '/login',
  component: LoginPage,
});

// Route Tree
// Note: The rootRoute used here is the one with notFoundComponent
const routeTree = rootRouteWithNotFound.addChildren([
  indexRoute,
  agentsRoute,
  personasRoute,
  workflowsRoute,
  integrationsRoute,
  resourcesRoute,
  logsRoute,
  settingsRoute,
  loginRoute,
]);

// Create Router Instance
export const router = createRouter({
  routeTree,
  // Optionally, configure a default notFoundComponent at router level if not on root.
  // defaultNotFoundComponent: NotFoundPage,
});

// Register Router for typesafety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
