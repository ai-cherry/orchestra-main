# Testing Strategy for AI Orchestration System

This document outlines the testing approach for the AI orchestration system, providing guidance on test organization, mocking strategies, and best practices.

## Testing Layers

The testing strategy is organized into three main layers:

1. **Unit Tests**: Testing individual components in isolation
2. **Integration Tests**: Testing interactions between components
3. **Functional Tests**: Testing complete workflows from API to response

## Directory Structure

Tests are organized by type and functionality:

```
tests/
├── test_agents/         # Tests for agent components
├── test_api/            # Tests for API endpoints
├── test_core/           # Tests for core orchestration
├── test_personas/       # Tests for persona management
├── test_services/       # Tests for service components
│   └── test_llm/        # Tests for LLM-specific services
├── test_setup.py        # Environment initialization tests
├── test_health.py       # System health check tests
├── test_memory.py       # Memory management tests
├── test_personas.py     # Persona loading/management tests
├── test_enhancements.py # Tests for enhanced components
├── test_integration.py  # Cross-component integration tests
└── conftest.py          # Shared fixtures and utilities
```

## Mocking Approach

### Dependency Injection through Service Registry

The unified service registry makes testing easier by allowing dependency replacement:

```python
# Replace a service with a mock for testing
from core.orchestrator.src.services.unified_registry import register, get
from unittest.mock import MagicMock

def test_with_mock_service():
    # Create and register mock
    mock_service = MagicMock()
    register(mock_service)

    # Test component that uses the service
    component = ComponentUnderTest()
    result = component.do_something()

    # Verify mock was called correctly
    mock_service.some_method.assert_called_once_with(expected_args)
```

### Testing LLM Components

For LLM components, we use predictable mock responses:

```python
# Test LLM agent with mock provider
def test_llm_agent():
    # Create mock LLM provider
    mock_provider = MagicMock()
    mock_provider.generate_chat_completion.return_value = {
        "content": "Mocked response",
        "model": "test-model",
        "provider": "mock-provider",
        "usage": {"total_tokens": 10}
    }

    # Patch the provider factory
    with patch("core.orchestrator.src.services.llm.providers.get_llm_provider",
               return_value=mock_provider):
        # Create agent and test
        agent = LLMAgent()
        result = agent.process(test_context)

        assert result.text == "Mocked response"
        assert result.confidence > 0.5
```

### Testing Event-Driven Components

For event-driven components, we use event capture:

```python
# Test event-driven component with event capture
def test_event_subscriber():
    # Create event capture
    captured_events = []

    def event_capture(event_data):
        captured_events.append(event_data)

    # Subscribe capture to events
    from core.orchestrator.src.services.unified_event_bus import subscribe
    handler_id = subscribe("test_event", event_capture)

    # Trigger component that publishes events
    component = ComponentUnderTest()
    component.trigger_event()

    # Verify correct events were published
    assert len(captured_events) == 1
    assert captured_events[0]["key"] == "expected_value"
```

## Test Fixtures

Common fixtures are defined in `conftest.py`:

```python
@pytest.fixture
def service_registry():
    """Provide a clean service registry for each test."""
    from core.orchestrator.src.services.unified_registry import get_service_registry
    registry = get_service_registry()
    # Clean state before test
    registry.close_all()
    yield registry
    # Clean up after test
    registry.close_all()

@pytest.fixture
def test_persona():
    """Provide a test persona configuration."""
    from packages.shared.src.models.base_models import PersonaConfig
    return PersonaConfig(
        id="test-persona",
        name="Test Persona",
        background="For testing purposes",
        interaction_style="Precise and direct",
        traits={"adaptability": 80}
    )

@pytest.fixture
def mock_llm_provider():
    """Provide a mock LLM provider."""
    from unittest.mock import MagicMock
    provider = MagicMock()
    provider.provider_name = "mock-provider"
    provider.generate_chat_completion.return_value = {
        "content": "Mock response",
        "model": "mock-model",
        "provider": "mock-provider",
        "usage": {"total_tokens": 5}
    }
    return provider
```

## Testing with Environment Variables

For tests that require configuration settings:

```python
def test_with_environment(monkeypatch):
    """Test component with specific environment configuration."""
    # Set environment variables for the test
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("DEFAULT_LLM_MODEL", "test-model")

    # Import the component (after environment is set)
    from core.orchestrator.src.services.llm.providers import get_llm_provider

    # Test component with the environment settings
    provider = get_llm_provider()
    assert provider.default_model == "test-model"
```

## Test Support Utilities

The `core/orchestrator/src/config/test_support.py` module provides utilities for testing:

```python
from core.orchestrator.src.config.test_support import (
    create_test_context,
    create_test_agent,
    mock_external_services
)

def test_with_support_utilities():
    # Create test context
    context = create_test_context(
        user_input="Test message",
        persona_id="test-persona"
    )

    # Create test agent
    agent = create_test_agent("persona_agent")

    # Run test with mocked external services
    with mock_external_services():
        result = agent.process(context)
        assert result.text.startswith("This is a test response")
```

## Testing Async Components

For testing async components, use pytest-asyncio:

```python
@pytest.mark.asyncio
async def test_async_component():
    """Test asynchronous component."""
    # Import async component
    from core.orchestrator.src.services.unified_event_bus import publish_async

    # Test async operations
    result = await publish_async("test_event", {"test": True})
    assert result >= 0
```

## Snapshot Testing

For testing complex response structures:

```python
def test_complex_response(snapshot):
    """Test complex response structure using snapshots."""
    # Generate complex response
    component = ComponentUnderTest()
    result = component.generate_complex_structure()

    # Compare with snapshot
    snapshot.assert_match(result)
```

## Best Practices

1. **Test Isolation**: Each test should run independently without relying on shared state
2. **Clear Assertions**: Use descriptive assertion messages to clarify test failures
3. **Focused Tests**: Test one behavior per test function
4. **Comprehensive Coverage**: Test happy paths, edge cases, and error conditions
5. **Mock External Dependencies**: Always mock external services for deterministic tests
6. **Clean Fixtures**: Clean up resources in fixtures to prevent test interference
7. **Descriptive Names**: Use descriptive test names that explain the behavior being tested
8. **Test API Contracts**: Focus tests on the public API, not implementation details
9. **Parameterized Tests**: Use parameterization for testing multiple inputs
10. **Integration Coverage**: Ensure key integration points are tested across components

### Local Quick Start
Run tests locally with your environment loaded:
```bash
source .env
python -m pytest
```

## Continuous Integration

Tests are automatically run in the CI pipeline:

```bash
# Run all tests
python -m pytest

# Run specific test category
python -m pytest tests/test_agents/

# Run with coverage
python -m pytest --cov=core
```

## Creating New Tests

When creating new tests:

1. Place unit tests in the appropriate category directory
2. For new components, create specific test files
3. Use existing fixtures from conftest.py when possible
4. Follow the mocking patterns established in existing tests
5. Ensure tests are deterministic and don't rely on external services
