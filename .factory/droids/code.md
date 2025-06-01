# Factory AI Code Droid

## Overview
The Code Droid specializes in code generation, refactoring, and optimization. It produces high-quality, maintainable code following best practices and project standards.

## Capabilities
- **Code Generation**: Creates new code from specifications
- **Refactoring**: Improves existing code structure without changing functionality
- **Optimization**: Enhances code performance and efficiency
- **Pattern Implementation**: Applies design patterns appropriately
- **Standards Compliance**: Ensures code follows project conventions

## Integration with Roo
- Maps to: `tools_server.py`
- Context sharing: Code style, project structure, dependencies
- Fallback: Roo's code mode handles requests if Factory AI is unavailable

## Request Format
```json
{
  "droid": "code",
  "task": "generate|refactor|optimize",
  "context": {
    "language": "python|typescript|javascript",
    "framework": "string",
    "existing_code": "string",
    "requirements": ["array"],
    "constraints": {
      "style_guide": "string",
      "performance_targets": "object"
    }
  },
  "options": {
    "include_tests": true,
    "documentation_level": "full|basic|none",
    "optimization_level": "aggressive|balanced|conservative"
  }
}
```

## Response Format
```json
{
  "code": {
    "main": "string",
    "tests": "string",
    "documentation": "string"
  },
  "analysis": {
    "complexity": "object",
    "performance": "object",
    "maintainability": "object"
  },
  "suggestions": ["array"],
  "dependencies": ["array"]
}
```

## Performance Characteristics
- Average response time: 1-3 seconds
- Token usage: 1000-8000 per request
- Caching: Common patterns cached for 24 hours
- Concurrency: Supports up to 20 parallel requests

## Best Practices
1. Provide clear specifications and examples
2. Include relevant context (existing code, patterns)
3. Specify target language version and features
4. Request tests alongside implementation
5. Review generated code for project-specific adjustments

## Code Quality Standards
- **Python**: PEP 8, type hints, Google docstrings
- **TypeScript**: ESLint rules, strict mode, JSDoc
- **Testing**: Minimum 80% coverage, edge cases
- **Documentation**: Clear, concise, with examples
- **Performance**: O(n) or better for common operations