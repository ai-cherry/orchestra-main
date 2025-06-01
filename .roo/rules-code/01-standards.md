# Coding Standards for Developer Mode

## Python Standards
- Always use Python 3.10+ features and syntax
- Type hints are mandatory for all functions and methods
- Use PEP 484 type annotations
- Follow Google-style docstrings
- Use Black for formatting, isort for imports
- Implement proper error handling with specific exceptions

## Code Organization
- Keep functions under 50 lines
- Classes should have single responsibility
- Use dependency injection for testability
- Implement interfaces/protocols for abstractions
- Group related functionality into modules

## Performance Best Practices
- Use generators for large data processing
- Implement connection pooling for databases
- Cache expensive computations
- Use async/await for I/O operations
- Profile before optimizing

## Testing Requirements
- Write tests first (TDD approach)
- Minimum 80% code coverage
- Use pytest for all Python tests
- Mock external dependencies
- Test edge cases and error conditions

## Documentation
- Every public API must be documented
- Include usage examples in docstrings
- Keep README files up to date
- Document design decisions in code
- Use type hints as documentation 