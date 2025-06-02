import { createRouter, createRoute } from '@tanstack/react-router';

// Import the Root Route
import { Route as rootRoute } from './routes/__root';

// Import Page Components
import { DashboardPage } from './pages/DashboardPage';
import { AgentsPage } from './pages/AgentsPage';
import { PersonasPage } from './pages/PersonasPage';
import { PersonaCustomizationPage } from './pages/PersonaCustomizationPage';
import { WorkflowsPage } from './pages/WorkflowsPage';
import { IntegrationsPage } from './pages/IntegrationsPage';
import { ResourcesPage } from './pages/ResourcesPage';
import { LogsPage } from './pages/LogsPage';
import { SettingsPage } from './pages/SettingsPage';
import { LoginPage } from './pages/LoginPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { OrchestrationPage } from './pages/OrchestrationPage';
import { MonitoringPage } from './pages/MonitoringPage';
import { OrchestratorLandingPage } from './pages/OrchestratorLandingPage';

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

const personaCustomizationRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/personas/$personaId',
  component: PersonaCustomizationPage,
});

const workflowsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/workflows',
  component: WorkflowsPage,
});

const orchestrationRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/orchestration',
  component: OrchestrationPage,
});

const monitoringRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/monitoring',
  component: MonitoringPage,
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

const orchestratorLandingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/orchestrator',
  component: OrchestratorLandingPage,
});

// Route Tree
// Use the original rootRoute directly
console.log('Creating route tree...');
const routeTree = rootRoute.addChildren([
  indexRoute,
  agentsRoute,
  personasRoute,
  personaCustomizationRoute,
  workflowsRoute,
  orchestrationRoute,
  orchestratorLandingRoute,
  monitoringRoute,
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
