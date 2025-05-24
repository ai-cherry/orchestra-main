# Canonical Workflows for Orchestra AI

## Active Workflows

### Primary Workflow
- **main.yml**: The primary CI/CD workflow for deployment to GCP Cloud Run. Triggers on pushes to main branch and handles:
  - Authentication via Workload Identity Federation
  - Python testing and linting
  - Cloud Build submission using `cloudbuild.yaml`
  - Deployment to Cloud Run service `ai-orchestra-minimal`

### Component-Specific Workflows
- **admin-interface/.github/workflows/deploy.yml**: Deployment workflow for the React/TypeScript admin interface
- **gcp-ide-sync/.github/workflows/deploy.yml**: Deployment workflow for GCP IDE synchronization components
- **mcp_server/.github/workflows/deploy.yml**: Deployment workflow for MCP (Model Context Protocol) servers

## Best Practices

- Validate all workflow YAMLs with `yamllint` and `actionlint` before pushing.
- Use the appropriate workflow for your component:
  - Main application changes: Triggers `main.yml` automatically
  - Admin interface changes: Use `admin-interface/` workflow
  - MCP server changes: Use `mcp_server/` workflow
  - GCP IDE sync changes: Use `gcp-ide-sync/` workflow
- All GCP secrets must be referenced directly in workflow steps.
- Docker build context and COPY paths must be explicit and correct.
- Run `terraform validate` and `poetry check` in CI to catch errors early.

## Service Deployment Targets

- **Main Application**: Deploys to `ai-orchestra-minimal` Cloud Run service in `us-central1`
- **Admin Interface**: Deploys to dedicated admin interface service
- **MCP Servers**: Deploy to individual MCP service endpoints

## Workflow Coordination

All workflows use Workload Identity Federation for secure GCP authentication and follow the same general pattern:
1. Checkout code
2. Authenticate to GCP
3. Build and test (if applicable)
4. Deploy to appropriate Cloud Run service