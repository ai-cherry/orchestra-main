# Migration Guide: Unified Components

This guide provides instructions for migrating from the original and enhanced components to the new unified components. The unified components combine the best features of both implementations while addressing technical debt and improving overall architecture.

## Overview

The unified components provide:

1. **Cleaner Architecture**: Consolidated interfaces and implementations
2. **Better Type Safety**: Comprehensive use of Python typing
3. **Consistent Async Support**: Unified approach to async/sync operations
4. **Improved Lifecycle Management**: Proper initialization and cleanup
5. **Enhanced Error Handling**: Consistent error reporting and recovery

## Components Overview

| Original Components | Enhanced Components          | Unified Component           |
| ------------------- | ---------------------------- | --------------------------- |
| `registry.py`       | `enhanced_registry.py`       | `unified_registry.py`       |
| `event_bus.py`      | `enhanced_event_bus.py`      | `unified_event_bus.py`      |
| `agent_registry.py` | `enhanced_agent_registry.py` | `unified_agent_registry.py` |

## Migration Strategy

We recommend a gradual migration approach:

1. **Use Unified Components for New Code**
2. **Refactor Existing Code Incrementally**
3. **Maintain Backward Compatibility During Transition**

## Unified Service Registry Migration

### Before:

```python
from core.conductor.src.services.registry import get_service_registry
# or
from core.conductor.src.services.enhanced_registry import get_enhanced_service_registry

registry = get_service_registry()  # or get_enhanced_service_registry()
registry.register(my_service)
```

### After:

```python
from core.conductor.src.services.unified_registry import register, get, require

# Simple registration
registered_service = register(my_service)

# Type-safe service lookup
service = get(ServiceType)  # Returns Optional[ServiceType]
required_service = require(ServiceType)  # Raises if not found
```

### Key Differences:

- More ergonomic helper functions
- Type-based service lookup
- Improved error handling
- Consistent lifecycle methods

## Unified Event Bus Migration

### Before:

```python
from core.conductor.src.services.event_bus import get_event_bus
# or
from core.conductor.src.services.enhanced_event_bus import get_enhanced_event_bus

event_bus = get_event_bus()  # or get_enhanced_event_bus()
handler_id = event_bus.subscribe("event_type", handler_function)
event_bus.publish("event_type", {"data": value})
```

### After:

```python
from core.conductor.src.services.unified_event_bus import (
    subscribe, publish, publish_async, EventPriority
)

# Subscribe with priority
handler_id = subscribe("event_type", handler_function, EventPriority.HIGH)

# Synchronous publish
count = publish("event_type", {"data": value})

# Asynchronous publish
count = await publish_async("event_type", {"data": value})
```

### Key Differences:

- Simpler API with helper functions
- Priority-based event handling
- Better statistics and monitoring
- More robust error handling

## Unified Agent Registry Migration

### Before:

```python
from core.conductor.src.agents.agent_registry import get_agent_registry
# or
from core.conductor.src.agents.enhanced_agent_registry import get_enhanced_agent_registry

registry = get_agent_registry()  # or get_enhanced_agent_registry()
agent = registry.get_agent("agent_type")
agent = registry.select_agent_for_context(context)
```

### After:

```python
from core.conductor.src.agents.unified_agent_registry import (
    get_agent, select_agent_for_context, register_agent, AgentCapability
)

# Register agent with capabilities
register_agent(
    agent, "agent_type",
    [AgentCapability.TEXT_GENERATION, AgentCapability.QUESTION_ANSWERING],
    priority=50, is_default=True
)

# Get agent by type
agent = get_agent("agent_type")

# Select based on context
agent = select_agent_for_context(context)
```

### Key Differences:

- Capability-based agent selection
- Improved selection algorithm
- Better lifecycle management
- Simplified dependency injection

## Service Lifecycle Integration

### Before:

Manual initialization and cleanup, often with inconsistent patterns:

```python
# Initialization
agent.initialize()
service.start()

# Cleanup - often missing or incomplete
service.stop()
```

### After:

Automatic lifecycle management through the service registry:

```python
from core.conductor.src.services.unified_registry import Service, register, get_service_registry

class MyService(Service):
    def initialize(self) -> None:
        # Initialize resources

    def close(self) -> None:
        # Release resources

# Register the service
service = MyService()
register(service)

# The service registry handles initialization and cleanup
registry = get_service_registry()
registry.initialize_all()
registry.close_all()
```

## Application Integration

The main application entry point has been updated to use the unified components while maintaining backward compatibility:

```python
# Original components (maintained for backward compatibility)
from core.conductor.src.agents.agent_registry import register_default_agents

# Unified components
from core.conductor.src.services.unified_registry import get_service_registry, register
from core.conductor.src.services.unified_event_bus import get_event_bus
from core.conductor.src.agents.unified_agent_registry import get_agent_registry

def initialize_services() -> None:
    """Initialize and register unified services."""
    # Get the service registry
    registry = get_service_registry()

    # Register core services
    event_bus = get_event_bus()
    register(event_bus)

    agent_registry = get_agent_registry()
    register(agent_registry)

    # Initialize all registered services
    registry.initialize_all()
```

## Testing with Unified Components

The unified components make testing easier:

```python
import pytest
from core.conductor.src.services.unified_registry import get_service_registry

@pytest.fixture
def service_registry():
    """Provide a clean service registry for each test."""
    registry = get_service_registry()
    yield registry
    registry.close_all()

@pytest.fixture
def mock_service(service_registry):
    """Provide a mock service registered with the registry."""
    service = MockService()
    service_registry.register(service)
    return service

def test_service_interaction(mock_service):
    # Test with the registered mock service
    assert mock_service.some_method() == expected_result
```

## Complete Migration Example

1. **Define a Service Using the Service Interface**:

```python
from core.conductor.src.services.unified_registry import Service

class DataProcessingService(Service):
    def __init__(self):
        self.resources = []

    def initialize(self) -> None:
        self.resources = ["database", "cache", "workers"]
        print("DataProcessingService initialized")

    def process(self, data):
        return f"Processed: {data}"

    def close(self) -> None:
        self.resources = []
        print("DataProcessingService resources released")
```

2. **Register and Use the Service**:

```python
from core.conductor.src.services.unified_registry import register, require

# Register the service
service = DataProcessingService()
register(service)

# Get the service when needed
processing_service = require(DataProcessingService)
result = processing_service.process("raw data")
```

3. **Use the Event Bus for Communication**:

```python
from core.conductor.src.services.unified_event_bus import subscribe, publish

# Register an event handler
def data_processed_handler(event_data):
    print(f"Data processed: {event_data['result']}")

subscribe("data_processed", data_processed_handler)

# Publish an event
publish("data_processed", {"result": result})
```

4. **Use the Agent Registry**:

```python
from core.conductor.src.agents.unified_agent_registry import (
    register_agent, select_agent_for_context, AgentCapability
)

# Register an agent
register_agent(
    my_agent,
    "data_processing_agent",
    [AgentCapability.TEXT_GENERATION, AgentCapability.FACTUAL_RESPONSE],
    priority=50
)

# Select and use an agent
agent = select_agent_for_context(context)
response = await agent.process(context)
```

## Handling Circular Dependencies

The unified components reduce circular dependencies by using:

1. **Late Imports**: Import only at the function level when needed
2. **Service Registry**: Use the registry for lookups instead of direct imports
3. **Event-Based Communication**: Publish events instead of calling methods directly

## Best Practices

1. **Use Helper Functions**: Prefer the helper functions (`register`, `get`, `require`) over direct registry methods
2. **Implement the Service Interface**: Make your services implement the `Service` interface
3. **Use Capability-Based Selection**: Define clear capabilities for your agents
4. **Leverage Event-Based Communication**: Use the event bus to reduce direct dependencies
5. **Test with Dependency Injection**: Use the service registry for cleaner tests

## Conclusion

Migrating to the unified components will improve the maintainability, testability, and scalability of the AI coordination System. The incremental migration approach allows for a smooth transition without disrupting existing functionality.

For any questions or issues with the migration, please refer to the technical debt assessment document or contact the architecture team.
