---
description: Monorepo navigation and cross-project dependency management for Orchestra Main
globs: ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx", "**/package.json", "**/pyproject.toml"]
autoAttach: true
priority: high
---

# Orchestra Main Monorepo Navigation Standards

## Project Structure Intelligence
- **admin-interface/**: React TypeScript admin dashboard with secure authentication
- **agent/**: Core AI agent runtime with FastAPI backend services
- **ai_components/**: Reusable AI modules (Claude, GitHub Copilot, design systems)
- **infrastructure/**: Pulumi IaC, database schemas, cloud resource management
- **dashboard/**: Unified real-time dashboard aggregating all platform data
- **mobile-app/**: React Native app with voice recognition and offline sync
- **api/**: Production API services and endpoint definitions
- **src/**: Core shared libraries and utilities across all projects

## Cross-Project Dependency Patterns
- **Shared utilities**: Always check `src/utils/`, `shared/`, `legacy/core/` before creating new
- **Database access**: Use `shared.database.UnifiedDatabase` class exclusively
- **Configuration**: Centralized in `config/environments/` with environment-specific overrides
- **Authentication**: Shared auth patterns across admin-interface, dashboard, mobile-app
- **API contracts**: Consistent interfaces between agent, api, and frontend projects

## Integration Points
- **Agent ↔ Dashboard**: Real-time data streaming through WebSocket connections
- **Mobile ↔ API**: RESTful services with offline synchronization capabilities
- **Admin ↔ Infrastructure**: Direct Pulumi integration for infrastructure management
- **All ↔ AI Components**: Standardized AI service interfaces and response formats

## Development Workflow Patterns
- **Feature development**: Consider impact across affected projects simultaneously
- **Testing strategy**: Integration tests at project boundaries, unit tests within
- **Documentation**: Update affected project READMEs when changing shared interfaces
- **Version coordination**: Synchronized releases across dependent projects

## Performance Considerations
- **Bundle optimization**: Tree-shaking and code splitting for frontend projects
- **Database queries**: Minimize cross-project database calls, prefer aggregated APIs
- **Caching layers**: Implement at project boundaries to reduce inter-service calls
- **Resource sharing**: Optimize shared Docker images and build artifacts

## Migration and Refactoring
- **Legacy integration**: Gradual migration from `legacy/` to current architecture
- **Breaking changes**: Coordinate across all affected projects with deprecation periods
- **Shared library updates**: Version compatibility matrix for major changes
- **Infrastructure changes**: Impact assessment across all deployment targets

## File Organization Best Practices
- **Avoid deep nesting**: Maximum 4 levels deep in project directories
- **Consistent naming**: kebab-case for directories, PascalCase for React components
- **Barrel exports**: Use index.ts files for clean import paths
- **Type definitions**: Shared types in `src/types/` or project-specific `types/` directories 