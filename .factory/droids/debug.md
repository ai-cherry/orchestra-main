# Factory AI Debug Droid

## Overview
The Debug Droid specializes in error analysis, debugging, and performance profiling. It helps identify and resolve issues in code, providing detailed diagnostics and solutions.

## Capabilities
- **Debugging**: Provides step-by-step debugging strategies
- **Performance Profiling**: Analyzes performance bottlenecks
- **Memory Analysis**: Detects memory leaks and optimization opportunities
- **Trace Analysis**: Interprets stack traces and execution paths

## Integration with 
- Maps to: `tools_server.py`
- Context sharing: Error logs, stack traces, system metrics
- Fallback: 's debug mode handles requests if Factory AI is unavailable

## Request Format
```json
{
  "droid": "debug",
  "task": "analyze_error|profile_performance|debug_issue",
  "context": {
    "error_type": "string",
    "stack_trace": "string",
    "code_snippet": "string",
    "environment": {
      "language": "string",
      "version": "string",
      "dependencies": ["array"]
    },
    "symptoms": ["array"],
    "reproduction_steps": ["array"]
  },
  "options": {
    "analysis_depth": "shallow|deep|exhaustive",
    "include_fixes": true,
    "performance_metrics": ["cpu", "memory", "io"]
  }
}
```

## Response Format
```json
{
  "diagnosis": {
    "contributing_factors": ["array"],
    "impact_analysis": "object"
  },
  "solutions": [
    {
      "description": "string",
      "code_fix": "string",
      "confidence": 0.95,
      "side_effects": ["array"]
    }
  ],
  "debugging_steps": ["array"],
  "performance_report": {
    "bottlenecks": ["array"],
    "optimization_suggestions": ["array"],
    "metrics": "object"
  }
}
```

## Performance Characteristics
- Average response time: 2-4 seconds
- Token usage: 1500-3000 per request
- Caching: Common error patterns cached for 12 hours
- Concurrency: Supports up to 15 parallel requests

## Best Practices
1. Include complete error messages and stack traces
2. Provide minimal reproducible examples
3. Specify environment details (versions, dependencies)
4. Include relevant logs and metrics
5. Describe expected vs. actual behavior

## Debugging Strategies
- **Binary Search**: Isolate issues by halving the problem space
- **Logging Enhancement**: Add strategic logging for visibility
- **State Analysis**: Examine variable states at key points
- **Performance Profiling**: Use appropriate tools for the language

## Common Issues Handled
- Null pointer exceptions
- Memory leaks
- Performance degradation
- Race conditions
- API integration errors
- Database query optimization
- Async/await issues