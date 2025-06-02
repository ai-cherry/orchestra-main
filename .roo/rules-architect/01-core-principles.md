# Architecture Principles for Roo AI (Project Symphony)

## Core Design Philosophy
- **Performance-First**: Design for performance from the start
- **Zero Junk Policy**: No temporary artifacts without lifecycle management
- **Integration Over Isolation**: Extend existing modules rather than creating standalone components

## System Architecture
- **Database**: 
  - PostgreSQL via `shared.database.UnifiedDatabase` for relational data
  - Weaviate for vector embeddings and similarity search
  - All queries must be analyzed with EXPLAIN ANALYZE
  - Connection pooling and query optimization required
- **Caching**: Application-level caching strategy awareness
- **API Design**: RESTful with performance targets (P99 < 250ms)

## File & Code Organization
- **Module Structure**: Follow existing patterns in `core/`, `services/`, `shared/`
- **No Standalone Scripts**: Integrate utilities into existing modules or CLI
- **Automation**: Register all automation via `scripts/automation_manager.py`
- **Configuration**: Centralized in `config/` with validation

## Performance Requirements
- **Algorithms**: O(n log n) or better complexity preferred
- **Database Operations**: Must include query plans and optimization
- **Resource Usage**: Monitor CPU/memory for intensive operations
- **Benchmarking**: Required for critical paths and complex functions

## Infrastructure as Code
- **Tool**: Pulumi with Python
- **Provider**: Vultr (default)
- **Principles**: Declarative, version-controlled, testable

## File Lifecycle Management
- **Temporary Files**: Must use `transient_file` decorator
- **Generated Artifacts**: Register in `.cleanup_registry.json`
- **Logs**: Use centralized logging, no ad-hoc log files
- **Reports**: Output to `docs/` or `reports/` directories

## Integration Patterns
- **Database Access**: Only through UnifiedDatabase class
- **Error Handling**: Integrate with project logging system
- **Configuration**: Use validated YAML/JSON in `config/`
- **Testing**: Comprehensive test coverage required

## Anti-Patterns to Avoid
- ❌ Creating new database connection methods
- ❌ Standalone utility scripts
- ❌ Temporary files without cleanup
- ❌ Direct file I/O for logs
- ❌ Unoptimized database queries
- ❌ Heavy dependencies for simple tasks

## Required Patterns
- ✅ Extend existing service modules
- ✅ Use dependency injection
- ✅ Implement circuit breakers for external services
- ✅ Add performance metrics collection
- ✅ Document architectural decisions
- ✅ Plan for horizontal scaling

## Decision Framework
When designing new features:
1. Can this extend an existing module?
2. What's the performance impact?
3. How does this handle failures?
4. What's the cleanup strategy?
5. Is this the simplest solution?

## Monitoring & Observability
- Performance metrics collection required
- Health check endpoints for all services
- Structured logging with correlation IDs
- Distributed tracing for complex workflows

## Integration First:
Prioritize extending existing modules (`scripts/`, `core/`, `services/`, `shared/`) over creating new standalone components or scripts.

## Database:
Use only PostgreSQL (via `shared.database.UnifiedDatabase`) for relational data and Weaviate for vector data.

## Performance:
Design for performance. All database operations must be analyzed (`EXPLAIN ANALYZE`). CPU/memory intensive operations should be flagged.

## Simplicity:
Solutions should be simple, stable, and maintainable, leveraging existing project patterns.

## IaC:
Infrastructure as Code must use Pulumi with Python for Vultr.

## File Management:
- Strictly no temporary files without explicit, automated lifecycle management (e.g., `transient_file` decorator, registration with cleanup service).
- All significant generated files must declare purpose and an expiration/review date.
- Prefer in-memory processing for intermediate data over temporary file-based workflows.

## Configuration:
Use `config/` directory for configurations. Validate with `scripts/config_validator.py`.

## Automation:
New automation tasks should be integrated into `scripts/orchestra.py` or existing scheduled jobs, not as new standalone cron entries without registration.