# Factory AI Architect Droid

## Overview
The Architect Droid specializes in system design, architecture planning, and integration design. It provides high-level architectural guidance and ensures system coherence.

## Capabilities
- **System Design**: Creates comprehensive system architectures following best practices
- **Architecture Planning**: Develops scalable, maintainable architectural patterns
- **Integration Design**: Designs seamless integrations between components
- **Pattern Recognition**: Identifies and applies appropriate design patterns
- **Performance Optimization**: Suggests architectural improvements for performance

## Integration with 
- Maps to: `conductor_server.py`
- Context sharing: Full system architecture context
- Fallback: 's architect mode handles requests if Factory AI is unavailable

## Request Format
```json
{
  "droid": "architect",
  "task": "design_system",
  "context": {
    "project_type": "string",
    "requirements": ["array", "of", "requirements"],
    "constraints": {
      "performance": "object",
      "scalability": "object"
    }
  },
  "options": {
    "detail_level": "high|medium|low",
    "include_diagrams": true
  }
}
```

## Response Format
```json
{
  "architecture": {
    "overview": "string",
    "components": ["array"],
    "patterns": ["array"],
    "diagrams": {
      "system": "mermaid_diagram",
      "data_flow": "mermaid_diagram"
    }
  },
  "implementation_plan": {
    "phases": ["array"],
    "dependencies": ["array"]
  },
  "recommendations": ["array"]
}
```

## Performance Characteristics
- Average response time: 2-5 seconds
- Token usage: 2000-4000 per request
- Caching: Architecture decisions cached for 1 hour
- Concurrency: Supports up to 10 parallel requests

## Best Practices
1. Provide comprehensive context for better architectural decisions
2. Use incremental design for complex systems
3. Validate architecture against non-functional requirements
4. Consider future scalability in all designs
5. Document architectural decisions and rationale