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

// Route Definitions
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: DashboardPage,
});

const agentsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/agents',
  component: AgentsPage,
});

const personasRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/personas',
  component: PersonasPage,
});

const workflowsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/workflows',
  component: WorkflowsPage,
});

const integrationsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/integrations',
  component: IntegrationsPage,
});

const resourcesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/resources',
  component: ResourcesPage,
});

const logsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/logs',
  component: LogsPage,
});

const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: SettingsPage,
});

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: LoginPage,
});

// Route Tree
// Use the original rootRoute directly
console.log('Creating route tree...');
const routeTree = rootRoute.addChildren([
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
console.log('Route tree created:', routeTree);

// Create Router Instance with notFoundComponent specified here
console.log('Creating router instance...');
export const router = createRouter({
  routeTree,
  defaultNotFoundComponent: NotFoundPage,
});
console.log('Router created successfully');

// Register Router for typesafety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
