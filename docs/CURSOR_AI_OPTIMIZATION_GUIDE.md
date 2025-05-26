# Cursor AI Optimization Guide for AI Orchestra

## Overview

This guide provides specific prompts, workflows, and best practices for leveraging Cursor AI to maximize productivity in the AI Orchestra project. Think of Cursor as your lazy but brilliant intern who needs precise instructions.

## Table of Contents

1. [Setup and Configuration](#setup-and-configuration)
2. [Effective Prompting Strategies](#effective-prompting-strategies)
3. [Task-Specific Prompts](#task-specific-prompts)
4. [Agent Mode Automation](#agent-mode-automation)
5. [Integration Workflows](#integration-workflows)
6. [Debugging with AI](#debugging-with-ai)
7. [Performance Tips](#performance-tips)

## Setup and Configuration

### 1. Project Context Setup

First, ensure Cursor understands your project structure:

```bash
# Create a .cursorrules file in your project root
cat > .cursorrules << 'EOF'
# AI Orchestra Project Rules for Cursor

## Project Context
- Python 3.10 (NOT 3.11+) - system constraint
- Pulumi for infrastructure (Python SDK)
- SuperAGI for agent orchestration
- MCP for natural language data access
- GCP as cloud provider

## Code Standards
- Type hints for all functions
- Google-style docstrings
- Black formatting
- Comprehensive error handling

## Architecture
- Modular Pulumi components in infra/components/
- MCP integration in scripts/mcp_integration.py
- SuperAGI deployment via Kubernetes
- DragonflyDB for short-term memory
- MongoDB for structured data
- Weaviate for semantic search

## Forbidden
- Docker/docker-compose files (use Kubernetes)
- Poetry/Pipfile (use pip/venv)
- Complex metaclasses
- Synchronous code in async contexts
EOF
```

### 2. Enable Agent Mode

In Cursor settings:
- Enable "Agent Mode" for automated task completion
- Set context window to maximum (100k tokens)
- Enable "Include project context" option

## Effective Prompting Strategies

### The CLEAR Framework

Use this framework for all prompts:

- **C**ontext: Provide relevant background
- **L**anguage: Be specific about technical requirements
- **E**xample: Include input/output examples
- **A**ction: Clearly state what you want done
- **R**estrictions: Specify what NOT to do

### Example CLEAR Prompt

```
Context: I'm working on the MCP integration module that connects MongoDB and Weaviate for natural language queries.

Language: Use Python 3.10 with async/await, type hints, and proper error handling.

Example:
Input: "Show all active agents created last week"
Output: MongoDB query result with agent documents

Action: Create an async function that parses natural language queries and routes them to the appropriate MCP server (MongoDB for structured, Weaviate for semantic).

Restrictions: Don't use synchronous HTTP calls, don't hardcode endpoints, don't skip error handling.
```

## Task-Specific Prompts

### 1. Pulumi Infrastructure Code

```
Write a Pulumi component in Python that deploys a Weaviate cluster on GKE with:
- 3 replicas for high availability
- Persistent storage using GCP disks
- Horizontal pod autoscaling based on CPU/memory
- Integration with existing MongoDB and SuperAGI components
- Proper health checks and readiness probes

Use the existing DatabaseComponent pattern in infra/components/database_component.py as reference.
```

### 2. MCP Server Integration

```
Implement an MCP server adapter for DragonflyDB that:
- Exposes natural language query capabilities
- Supports TTL-based cache operations
- Provides tools for pattern matching and key scanning
- Integrates with the existing MCPIntegration class

Follow the MCP protocol specification and use async Python throughout.
```

### 3. SuperAGI Agent Creation

```
Create a SuperAGI agent configuration for a "DevOps Assistant" that:
- Monitors Kubernetes cluster health
- Responds to natural language queries about infrastructure status
- Can execute Pulumi commands via approved workflows
- Uses MCP to query deployment history from MongoDB

Include proper tool definitions and memory configuration.
```

### 4. API Endpoint Development

```
Add a FastAPI endpoint to orchestra_api that:
- Accepts natural language queries
- Routes to appropriate MCP servers
- Implements rate limiting and authentication
- Returns structured JSON responses with metadata
- Includes OpenAPI documentation

Follow the existing router pattern in orchestra_api/routers/.
```

## Agent Mode Automation

### 1. Multi-File Refactoring

```
@agent refactor the database components to:
1. Extract common patterns into a base class
2. Add comprehensive logging
3. Implement retry logic with exponential backoff
4. Add Prometheus metrics for monitoring
5. Update all imports and tests

Start with infra/components/ and update all dependent files.
```

### 2. Test Generation

```
@agent generate comprehensive tests for the MCP integration module:
1. Unit tests for each method with mocking
2. Integration tests using test containers
3. Performance benchmarks
4. Error scenario coverage
5. Async test patterns

Create tests in tests/unit/test_mcp_integration.py and tests/integration/test_mcp_e2e.py
```

### 3. Documentation Generation

```
@agent document the entire SuperAGI deployment:
1. Architecture diagram in Mermaid
2. API reference with examples
3. Deployment guide with prerequisites
4. Troubleshooting section
5. Performance tuning guide

Create docs/SUPERAGI_DEPLOYMENT_GUIDE.md with proper formatting.
```

## Integration Workflows

### 1. New Feature Development

```
Workflow: Add Prometheus monitoring to all components

Step 1: "Add Prometheus client to requirements and create metrics module"
Step 2: "Instrument DatabaseComponent with connection pool metrics"
Step 3: "Add HTTP request metrics to SuperAGI component"
Step 4: "Create Grafana dashboard configuration"
Step 5: "Update Pulumi to deploy Prometheus operator"
```

### 2. Bug Investigation

```
Debug the MCP connection timeout issue:
1. Add detailed logging around connection establishment
2. Implement connection health checks
3. Add retry logic with jittered backoff
4. Create unit tests for timeout scenarios
5. Add metrics to track connection failures

Focus on scripts/mcp_integration.py lines 44-62.
```

## Debugging with AI

### 1. Error Analysis

```
Analyze this error and provide a fix:
[paste full error traceback]

Consider:
- Python 3.10 compatibility
- Async context issues
- GCP permission problems
- Kubernetes RBAC

Provide the exact code changes needed.
```

### 2. Performance Optimization

```
Profile this function and optimize it:
[paste function code]

Requirements:
- Maintain the same interface
- Add caching where appropriate
- Use connection pooling
- Minimize memory allocations
- Keep it readable

Show before/after with benchmarks.
```

## Performance Tips

### 1. Context Management

- Use `@file` references instead of pasting code
- Leverage Cursor's indexing by keeping files under 500 lines
- Use clear file naming conventions

### 2. Prompt Efficiency

- Start specific, then broaden if needed
- Use examples from your codebase
- Reference existing patterns
- Break complex tasks into steps

### 3. Iteration Speed

- Use Cmd+K for quick edits
- Leverage multi-cursor for repetitive changes
- Use agent mode for cross-file changes
- Keep test files open for immediate validation

## Common Patterns and Templates

### 1. Async Service Pattern

```
Create an async service class for [SERVICE_NAME] that:
- Implements connection pooling
- Has retry logic
- Includes health checks
- Provides metrics
- Uses proper typing

Base it on the pattern in scripts/mcp_integration.py
```

### 2. Pulumi Component Pattern

```
Create a Pulumi component for [RESOURCE_NAME] that:
- Follows the modular pattern
- Includes all necessary IAM bindings
- Has configurable resource limits
- Exports relevant outputs
- Includes proper error handling

Use infra/components/database_component.py as template
```

### 3. API Router Pattern

```
Add a new router for [FEATURE_NAME] that:
- Validates input with Pydantic
- Implements proper error responses
- Includes authentication
- Has comprehensive logging
- Returns consistent JSON structure

Follow orchestra_api/routers/ patterns
```

## Troubleshooting Cursor

### Issue: Cursor not understanding project context

Solution:
```
1. Ensure .cursorrules is in project root
2. Re-index the project (Cmd+Shift+P -> "Reload Window")
3. Use explicit file references with @file
4. Start prompts with context reminders
```

### Issue: Agent mode making incorrect changes

Solution:
```
1. Break the task into smaller steps
2. Provide more specific examples
3. Use restrictions to prevent unwanted changes
4. Review changes incrementally
```

### Issue: Slow response times

Solution:
```
1. Reduce context by closing unnecessary files
2. Use more specific file references
3. Clear conversation history if too long
4. Disable unused extensions
```

## Best Practices Summary

1. **Be Specific**: Vague prompts get vague results
2. **Use Examples**: Show what you want with real code
3. **Leverage Context**: Reference existing patterns
4. **Iterate Quickly**: Start simple, refine as needed
5. **Trust but Verify**: Always review AI-generated code
6. **Document Intent**: Add comments explaining why, not just what

Remember: Cursor is powerful but needs guidance. Treat it like a skilled junior developer who needs clear requirements and examples to excel.
