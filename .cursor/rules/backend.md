---
description: Backend development standards for API services, agent runtime, and database operations
globs: ["agent/**/*.py", "api/**/*.py", "src/**/*.py", "legacy/core/**/*.py"]
autoAttach: true
priority: high
---

# Backend Development Standards

## FastAPI Service Patterns
- **Route organization**: Group related endpoints in separate router modules
- **Dependency injection**: Use FastAPI dependencies for auth, database, configuration
- **Response models**: Pydantic models for all API responses, consistent error formats
- **Async patterns**: Async/await for all I/O operations, connection pooling
- **Documentation**: Auto-generated OpenAPI docs with comprehensive examples

## Database Integration Patterns
- **UnifiedDatabase usage**: Use `shared.database.UnifiedDatabase` class exclusively
- **Connection management**: Context managers for database sessions
- **Transaction handling**: Explicit transaction boundaries, rollback on errors
- **Query optimization**: EXPLAIN ANALYZE for complex queries, proper indexing
- **Migration strategy**: Versioned migrations with rollback procedures

## Authentication and Security
- **JWT implementation**: Short-lived access tokens, refresh token rotation
- **Permission models**: Role-based access control with granular permissions
- **Input validation**: Pydantic models for request validation, SQL injection prevention
- **Rate limiting**: Per-user and per-endpoint rate limiting
- **Audit logging**: Comprehensive audit trails for sensitive operations

## AI Agent Integration
- **Model management**: Centralized LLM configuration and connection pooling
- **Context handling**: Efficient context window management, conversation state
- **Error handling**: Graceful degradation when AI services are unavailable
- **Performance monitoring**: Token usage tracking, response time monitoring
- **Safety measures**: Content filtering, output validation, usage quotas

## Background Task Patterns
- **Celery integration**: Async task processing for long-running operations
- **Queue management**: Proper task prioritization and retry logic
- **Monitoring**: Task status tracking, failure alerting
- **Resource management**: Memory and CPU limits for background tasks
- **Error recovery**: Comprehensive error handling and retry strategies

## API Design Standards
- **RESTful conventions**: Proper HTTP methods, status codes, resource naming
- **Versioning strategy**: URL-based versioning for breaking changes
- **Pagination**: Cursor-based pagination for large datasets
- **Filtering**: Query parameter standards for search and filtering
- **Caching**: HTTP caching headers, Redis for expensive computations

## Error Handling and Logging
- **Structured logging**: JSON-formatted logs with correlation IDs
- **Error classification**: Differentiate user errors, system errors, external service errors
- **Exception handling**: Custom exception classes with proper HTTP status mapping
- **Monitoring integration**: Sentry for error tracking, metrics for performance
- **Debug information**: Sanitized debug info in development, secure in production

## Testing Standards
- **Unit tests**: Comprehensive coverage for business logic
- **Integration tests**: Database and external service integration testing
- **API tests**: Full request/response cycle testing
- **Performance tests**: Load testing for critical endpoints
- **Security tests**: Vulnerability scanning, penetration testing 