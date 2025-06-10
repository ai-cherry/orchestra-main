---
description: Performance optimization patterns for cloud server development and monorepo efficiency
globs: ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"]
autoAttach: true
priority: medium
---

# Performance-First Development Standards

## Algorithm and Data Structure Requirements
- **Time complexity**: O(n log n) maximum for core operations, O(n²) forbidden
- **Space complexity**: Consider memory usage for operations > 1MB data
- **Data structures**: Use appropriate collections (sets for membership, deques for queues)
- **Lazy evaluation**: Prefer generators and iterators for large datasets
- **Caching strategies**: Memoization for expensive computations, TTL for dynamic data

## Database Performance Patterns
- **Query optimization**: EXPLAIN ANALYZE all PostgreSQL queries in development
- **Index strategy**: Compound indexes for common query patterns
- **Connection pooling**: Reuse connections, monitor pool saturation
- **Batch operations**: Group INSERT/UPDATE operations, avoid N+1 queries
- **Pagination**: Cursor-based pagination for large result sets

## Frontend Performance (React/TypeScript)
- **Bundle optimization**: Code splitting at route level, tree-shaking verification
- **Rendering optimization**: useMemo/useCallback for expensive computations
- **State management**: Minimize re-renders, normalize state shape
- **Asset optimization**: WebP images, lazy loading, service worker caching
- **Network optimization**: Request deduplication, optimistic updates

## Cloud Server Optimization
- **Resource monitoring**: CPU/memory/disk usage tracking in production
- **Network efficiency**: Compression, CDN utilization, connection keep-alive
- **I/O optimization**: Async patterns, batch file operations, streaming for large data
- **Process optimization**: Worker processes for CPU-intensive tasks
- **Memory management**: Garbage collection tuning, memory leak detection

## API Performance Standards
- **Response times**: < 200ms for data queries, < 500ms for complex operations
- **Rate limiting**: Implement to prevent resource exhaustion
- **Caching layers**: Redis for session data, application-level caching for computed results
- **Compression**: gzip/brotli for API responses > 1KB
- **Connection efficiency**: HTTP/2, connection pooling, circuit breakers

## Mobile App Performance (React Native)
- **Bundle size**: < 50MB total app size, code splitting for features
- **Memory usage**: Monitor JavaScript heap, optimize image handling
- **Battery optimization**: Efficient background processing, location services
- **Offline performance**: Smart caching, background sync, conflict resolution
- **Navigation**: Lazy screen loading, gesture optimization

## Development Environment Performance
- **Build optimization**: Incremental builds, parallel processing, caching
- **Hot reload**: Fast refresh configuration, minimal rebuild triggers
- **Testing efficiency**: Parallel test execution, smart test selection
- **Development server**: Efficient file watching, memory usage monitoring
- **Code analysis**: Fast linting, type checking optimization

## Monitoring and Profiling
- **Performance metrics**: Core Web Vitals, custom business metrics
- **Profiling integration**: Python profilers, React DevTools, Chrome DevTools
- **Alerting thresholds**: Response time degradation, error rate increases
- **Load testing**: Regular performance regression testing
- **Resource tracking**: Cost optimization through usage analysis 