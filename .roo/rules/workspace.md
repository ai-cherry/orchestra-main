# Orchestra AI Ecosystem Workspace Rules
# Unified rules for Cursor, Roo, and Continue integration

## Project Context
- This is a single-developer AI orchestration project
- Focus on performance over security (basic security sufficient)
- All code must be AI-agent friendly and well-documented
- Primary stack: PostgreSQL + Weaviate + Redis + Lambda Labs

## Cross-Tool Standards

### Code Quality
- Always use Python 3.10 features and syntax (NOT 3.11+)
- Type hints mandatory for all functions (PEP 484)
- Google-style docstrings for all public modules, classes, functions
- Black formatting, isort for imports
- Max line length: 88 characters

### AI Agent Compatibility
- All functions must have clear docstrings for AI understanding
- Use descriptive variable names and function names
- Include usage examples in docstrings
- Maintain context files for complex operations

### MCP Integration
- Always use MCP servers for data operations
- Route operations through appropriate MCP servers:
  - Memory operations → enhanced-memory
  - Code analysis → code-intelligence
  - Git operations → git-intelligence
  - Infrastructure → infrastructure-manager
  - Web research → web-scraping
  - Personal tasks → cherry-domain
  - Financial operations → sophia-payready

### Context Management
- Maintain context sharing between all tools (Cursor, Roo, Continue)
- Use unified MCP server for cross-tool communication
- Document all architectural decisions in markdown
- Keep project knowledge in searchable format (Weaviate)

### Performance Standards
- Prefer O(n log n) or better algorithms
- Use EXPLAIN ANALYZE for all new PostgreSQL queries
- Benchmark functions with loops > 1000 iterations
- Cache frequently accessed data in Redis

### Documentation Standards
- Write for AI agents as primary audience
- Use clear, structured markdown
- Include code examples liberally
- Maintain single source of truth
- Version documentation with code

## Tool-Specific Guidelines

### Cursor Usage
- Primary tool for coding, debugging, file navigation
- Use for real-time code editing and immediate feedback
- Leverage native AI integration for quick iterations

### Roo Usage
- Use for complex workflows and boomerang tasks
- Leverage specialized modes for different task types
- Use orchestrator mode for task decomposition
- Enable auto-approve for trusted operations

### Continue Usage
- Primary tool for UI generation with UI-GPT-4o
- Use for React/TypeScript component creation
- Leverage custom commands: /ui, /persona, /mcp, /review
- Focus on rapid prototyping and iteration

## Persona-Specific Considerations

### Cherry (Life Companion)
- Focus on personal, wellness, and ranch management features
- Prioritize user experience and emotional intelligence
- Use warm, friendly language in interfaces

### Sophia (Business Intelligence)
- Focus on financial analysis and business operations
- Prioritize data accuracy and performance
- Use professional, efficient interfaces

### Karen (Healthcare)
- Focus on clinical research and healthcare operations
- Prioritize data security and compliance
- Use clinical, precise language and interfaces

## Error Handling Standards
- Use specific exception types, not generic Exception
- Log all errors with context information
- Implement graceful degradation for non-critical failures
- Use MCP servers for error reporting and analysis

## Testing Standards
- Unit tests for all public functions
- Integration tests for MCP server interactions
- Performance tests for critical paths
- Use pytest framework consistently

## Security Guidelines
- Basic security sufficient for single-developer project
- Use environment variables for all secrets
- No hardcoded API keys or passwords
- Validate all external inputs

## Deployment Standards
- Use Pulumi for all infrastructure as code
- Target Lambda Labs for GPU-accelerated workloads
- Implement proper state management
- Document all infrastructure decisions

