# Python Development Standards for Orchestra AI

## Code Quality Requirements

### Type Hints (Mandatory)
- ALL function parameters must have type hints
- ALL return values must have type hints  
- Use `typing` module for complex types: `List`, `Dict`, `Optional`, `Union`
- Use Python 3.10+ features: `str | None` instead of `Optional[str]`

### Error Handling
- Use specific exception types, never bare `except:`
- Implement proper error propagation with context
- Include helpful error messages with debugging information
- Use logging for error tracking: `logger.error("Context: %s", error_info)`

### Documentation Standards
- Google-style docstrings for ALL public functions and classes
- Include parameter descriptions, return value descriptions, and example usage
- Document any side effects or state changes
- Include complexity notes for algorithms

### Performance Considerations
- Use generators for large data processing
- Implement caching where appropriate
- Consider memory usage in data structure choices
- Profile performance-critical sections

## Orchestra AI Specific Requirements

### Integration Patterns
- All database operations must use async/await patterns
- MCP server interactions must include proper error handling
- Use dependency injection for external services
- Implement retry mechanisms for external API calls

### Logging and Monitoring
- Use structured logging with context information
- Include request IDs for traceability
- Log performance metrics for optimization
- Never log sensitive information (API keys, passwords)

### Testing Requirements
- Write unit tests for all new functions
- Include integration tests for API endpoints
- Use pytest fixtures for test data
- Maintain >90% code coverage 