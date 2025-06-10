---
description: Global foundation rules for Project Symphony AI Orchestra development
globs: ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"]
autoAttach: true
priority: critical
---

# Project Symphony AI Orchestra - Global Development Standards

## Core Development Philosophy
- **Quality over speed**: Stability and maintainability are paramount
- **Single developer optimization**: Prioritize automation and intelligent assistance
- **Cloud-first**: All development assumes cloud server environment
- **Infrastructure as Code**: Every deployment decision goes through Pulumi

## Python 3.10+ Mandatory Standards
- **Type hints required** for all function signatures and class attributes
- **Google-style docstrings** for all public interfaces
- **Black + isort formatting** enforced automatically
- **Async/await patterns** preferred over threading for I/O operations
- **Dataclasses/Pydantic models** for structured data

## Monorepo Navigation Intelligence
- **Cross-project dependencies**: Always consider impact across admin-interface, agent, ai_components, infrastructure
- **Shared utilities**: Prefer extending existing modules in `src/`, `shared/`, `legacy/core/`
- **Database consistency**: Use `shared.database.UnifiedDatabase` class exclusively
- **Configuration patterns**: Environment-specific configs in `config/environments/`

## Performance Requirements
- **Algorithm complexity**: O(n log n) or better for core operations
- **Memory awareness**: Profile data processing operations > 1MB
- **Database queries**: Include EXPLAIN ANALYZE for PostgreSQL queries
- **Caching strategies**: Implement for repeated computations > 100ms

## Infrastructure Integration
- **Pulumi patterns**: All cloud resources defined in `infrastructure/pulumi/`
- **Environment consistency**: Dev/staging/prod parity through IaC
- **Security first**: Secrets through Pulumi config, never hardcoded
- **Cost optimization**: Monitor resource usage in cloud deployments

## Forbidden Patterns
- Python 3.11+ features (match/case, tomllib)
- MongoDB usage (PostgreSQL + Weaviate only)
- Docker/Poetry in development (pip/venv only)
- Standalone scripts without integration paths
- Temporary files without @transient_file decorator 