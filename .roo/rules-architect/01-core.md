# Core Principles for Architect Mode

## Design Philosophy
- Always design for hot-swappable modules and clear interfaces
- Use EXPLAIN ANALYZE for Postgres query optimization
- Index all code and docs in Weaviate for rapid retrieval
- Pulumi stacks must target Vultr and be modular
- Context sharing via MCP is required for all architecture diagrams and planning

## Architecture Standards
- Follow Domain-Driven Design principles
- Implement hexagonal architecture patterns
- Use event-driven patterns for inter-service communication
- Design for horizontal scalability from day one
- All services must be stateless where possible

## Performance Requirements
- Design for sub-100ms response times
- Plan for 10x growth without major refactoring
- Use caching strategies at every layer
- Optimize for read-heavy workloads
- Implement proper database indexing strategies

## Integration Patterns
- All external APIs must use circuit breakers
- Implement retry logic with exponential backoff
- Use message queues for async operations
- Design idempotent operations wherever possible
- Document all integration points thoroughly 