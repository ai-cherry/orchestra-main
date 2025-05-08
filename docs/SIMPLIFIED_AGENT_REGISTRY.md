# Simplified Agent Registry

This document describes the Simplified Agent Registry implementation for the AI Orchestra project, which provides a streamlined approach to agent management without the security overhead of the original implementations.

## Overview

The Simplified Agent Registry is a lightweight alternative to the more complex agent registry implementations in the codebase. It focuses on core functionality while removing security-related features like circuit breakers, extensive error handling, and complex lifecycle management.

Key benefits:
- **Simplified Code**: Easier to understand and maintain
- **Improved Performance**: Less overhead from security checks and error handling
- **Faster Development**: Simpler API for registering and using agents
- **Reduced Dependencies**: Fewer external dependencies

## Comparison with Other Implementations

| Feature | Original Registry | Enhanced Registry | Simplified Registry |
|---------|------------------|-------------------|---------------------|
| Agent Registration | ✅ | ✅ | ✅ |
| Agent Selection | ✅ | ✅ | ✅ |
| Capability-based Selection | ❌ | ✅ | ✅ |
| Circuit Breaker | ✅ | ❌ | ❌ |
| Fallback Handling | ✅ | ❌ | ❌ |
| Incident Reporting | ✅ | ❌ | ❌ |
| Lifecycle Management | ❌ | ✅ | ❌ |
| Event-based Communication | ❌ | ✅ | ❌ |
| Dependency Injection | ✅ | ✅ | ✅ |
| Agent Factory | ❌ | ✅ | ❌ |

## When to Use

Use the Simplified Agent Registry when:
- You need maximum performance
- You're working in a trusted environment
- You don't need advanced features like circuit breakers or event-based communication
- You want to minimize dependencies and complexity

Use the original or enhanced registries when:
- You need robust error handling and fallbacks
- You're working in a production environment with strict reliability requirements
- You need advanced features like lifecycle management or event-based communication

## Usage

### Basic Usage

```python
from core.orchestrator.src.agents.simplified_agent_registry import (
    get_simplified_agent_registry,
    register_default_agents,
    AgentCapability
)

# Get the registry and register default agents
registry = get_simplified_agent_registry()
register_default_agents()

# Get an agent by type
agent = registry.get_agent("llm_agent")

# Process user input
response = await agent.process("Hello, how can I help you?")
```

### Agent Selection

```python
from core.orchestrator.src.agents.agent_base import AgentContext

# Create a context
context = AgentContext(
    user_input="Write a function to calculate fibonacci numbers",
    metadata={},
    conversation_id="test-conversation",
    message_id="test-message"
)

# Select an agent for this context
agent = registry.select_agent_for_context(context)

# Process the input
response = await agent.process(context.user_input)
```

### Custom Agent Registration

```python
class CustomAgent:
    def __init__(self):
        self.agent_type = "custom_agent"
        self.capabilities = [AgentCapability.TEXT_GENERATION]
    
    async def process(self, user_input: str) -> str:
        return f"CustomAgent processed: {user_input}"

# Register the custom agent
custom_agent = CustomAgent()
registry.register_agent(custom_agent)
```

## Implementation Details

### Agent Capabilities

The simplified registry uses a basic set of capabilities for agent selection:

- `TEXT_GENERATION`: General text generation
- `QUESTION_ANSWERING`: Answering questions
- `SUMMARIZATION`: Summarizing content
- `CODE_GENERATION`: Generating code
- `GENERAL`: Basic capabilities for simple agents

### Agent Selection Logic

The agent selection logic is simplified to use basic keyword matching:

1. Check if a specific agent is requested in the context metadata
2. Look for code-related keywords to select a code generation agent
3. Look for question marks or question words to select a question answering agent
4. Look for summarization keywords to select a summarization agent
5. Fall back to a text generation agent
6. If no suitable agent is found, use the default agent

### Performance Considerations

The simplified registry is designed for performance:

- No circuit breaker overhead
- No complex error handling
- No event-based communication
- Simple, direct agent selection logic
- Minimal logging

## Example

See `examples/simplified_agent_example.py` for a complete example of using the simplified agent registry.

## Migration Guide

To migrate from the original or enhanced registry to the simplified registry:

1. Update imports:
   ```python
   # From
   from core.orchestrator.src.agents.agent_registry import get_agent_registry
   # To
   from core.orchestrator.src.agents.simplified_agent_registry import get_simplified_agent_registry
   ```

2. Update agent registration:
   ```python
   # From
   registry = get_agent_registry()
   registry.register_agent_type("my_agent", MyAgentClass)
   # To
   registry = get_simplified_agent_registry()
   registry.register_agent_type("my_agent", MyAgentClass)
   ```

3. Update agent selection:
   ```python
   # From
   agent = registry.select_agent_for_context(context)
   # To
   agent = registry.select_agent_for_context(context)
   # (No change needed)
   ```

4. Remove any code that depends on circuit breakers or fallback handling

## Conclusion

The Simplified Agent Registry provides a streamlined approach to agent management that focuses on core functionality while removing security-related features. This makes it easier to understand, maintain, and extend, while also improving performance.