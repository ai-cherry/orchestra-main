# conductor Troubleshooting Guide

This guide provides solutions for common issues encountered in the conductor codebase, particularly those related to the technical debt patterns identified in the [Codebase Health Assessment](./CODEBASE_HEALTH_ASSESSMENT.md).

## Common Issues and Solutions

### Circular Import Errors

**Issue**: `ImportError: cannot import name 'X' from 'Y'` or similar circular import errors.

**Causes**:

- Direct imports of singleton instances between modules
- Circular dependencies between components
- Missing dependency injection

**Solutions**:

1. **Use lazy imports**:

   ```python
   # Instead of this at the module level
   from core.conductor.src.services.registry import get_service_registry

   # Do this inside functions
   def my_function():
       from core.conductor.src.services.registry import get_service_registry
       registry = get_service_registry()
   ```

2. **Use the unified service registry**:

   ```python
   from core.conductor.src.services.unified_registry import require

   def my_function():
       # Get the service by type
       service = require(MyServiceType)
   ```

3. **Use type annotations instead of imports for type hints**:

   ```python
   # Instead of this
   from module_a import ClassA

   def function(param: ClassA) -> None:
       pass

   # Do this
   from typing import TYPE_CHECKING

   if TYPE_CHECKING:
       from module_a import ClassA

   def function(param: 'ClassA') -> None:
       pass
   ```

### Service Initialization Failures

**Issue**: Services fail to initialize properly, or resources aren't available when needed.

**Causes**:

- Incorrect initialization order
- Missing initialization calls
- Dependency on uninitialized services

**Solutions**:

1. **Explicitly initialize services**:

   ```python
   # Get registry and ensure initialization
   from core.conductor.src.services.unified_registry import get_service_registry

   registry = get_service_registry()
   registry.initialize_all()
   ```

2. **Use the Service interface for new services**:

   ```python
   from core.conductor.src.services.unified_registry import Service, register

   class MyService(Service):
       def initialize(self) -> None:
           # Initialize resources
           pass

       def close(self) -> None:
           # Release resources
           pass

   # Register service
   service = MyService()
   register(service)
   ```

3. **Check service registry for proper registration**:

   ```python
   from core.conductor.src.services.unified_registry import get_service_registry

   registry = get_service_registry()
   service_names = registry.get_service_names()
   print(f"Registered services: {service_names}")
   ```

### Resource Leaks

**Issue**: Memory leaks, file handles remaining open, or connections not being released.

**Causes**:

- Missing close/cleanup calls
- Exceptions preventing cleanup
- No consistent shutdown sequence

**Solutions**:

1. **Use context managers for resources**:

   ```python
   class ResourceManager:
       def __enter__(self):
           self.resource = acquire_resource()
           return self.resource

       def __exit__(self, exc_type, exc_val, exc_tb):
           release_resource(self.resource)

   with ResourceManager() as resource:
       use_resource(resource)
   ```

2. **Implement proper close methods**:

   ```python
   def close(self) -> None:
       try:
           # Close primary resources
           self._primary_resource.close()
       except Exception as e:
           logger.error(f"Error closing primary resource: {e}")
       finally:
           try:
               # Always try to close secondary resources
               self._secondary_resource.close()
           except Exception as e:
               logger.error(f"Error closing secondary resource: {e}")
   ```

3. **Register shutdown handlers**:

   ```python
   import atexit

   def cleanup_resources():
       # Close all resources
       pass

   # Register cleanup function
   atexit.register(cleanup_resources)
   ```

### Async/Sync Confusion

**Issue**: Deadlocks, blocking code in async functions, or "coroutine was never awaited" warnings.

**Causes**:

- Mixing async and sync code incorrectly
- Missing await statements
- Blocking operations in async code

**Solutions**:

1. **Use asyncio.run_in_executor for blocking operations**:

   ```python
   import asyncio

   async def async_function():
       # Run blocking code in a thread pool
       loop = asyncio.get_running_loop()
       result = await loop.run_in_executor(None, blocking_function, arg1, arg2)
       return result
   ```

2. **Ensure proper awaiting of coroutines**:

   ```python
   # Wrong
   async def function():
       result = async_operation()  # Missing await!

   # Correct
   async def function():
       result = await async_operation()
   ```

3. **Check for proper async method naming**:
   Methods that are async should have names that indicate this, like `initialize_async()` vs `initialize()`.

### Configuration Issues

**Issue**: Missing configuration values, invalid configuration, or configuration not loading.

**Causes**:

- Environment variables not set
- Configuration files missing
- Multiple configuration sources with conflicts

**Solutions**:

1. **Validate configuration at startup**:

   ```python
   from core.conductor.src.config.config import get_settings

   def validate_config():
       settings = get_settings()
       required_fields = ['API_KEY', 'DATABASE_URL']

       for field in required_fields:
           if not hasattr(settings, field) or not getattr(settings, field):
               raise ValueError(f"Missing required configuration: {field}")

   # Call this at application startup
   validate_config()
   ```

2. **Set default values for optional configuration**:

   ```python
   class Settings:
       API_TIMEOUT: int = 30  # Default value

       def __init__(self):
           # Override from environment if available
           self.API_TIMEOUT = int(os.getenv('API_TIMEOUT', self.API_TIMEOUT))
   ```

3. **Use a centralized configuration utility**:

   ```python
   from core.conductor.src.config.config import get_settings

   def get_config_value(key, default=None):
       settings = get_settings()
       return getattr(settings, key, default)
   ```

### Testing Services with Dependencies

**Issue**: Difficulty testing components due to complex dependencies or global state.

**Causes**:

- Direct imports of singleton instances
- Missing dependency injection
- Global state affecting tests

**Solutions**:

1. **Use the service registry for dependency injection in tests**:

   ```python
   import pytest
   from core.conductor.src.services.unified_registry import get_service_registry, register

   @pytest.fixture
   def mock_service():
       # Create the mock
       mock = MagicMock(spec=RealService)

       # Get registry and register the mock
       registry = get_service_registry()
       register(mock)

       yield mock

       # Clean up after test
       registry.unregister(mock)

   def test_with_dependency(mock_service):
       # Test code that uses the service
       mock_service.method.return_value = "test"
       result = function_under_test()
       assert result == "expected"
   ```

2. **Create test-specific subclasses**:

   ```python
   class TestableService(RealService):
       def __init__(self):
           super().__init__()
           self.test_state = {}

       def test_helper(self):
           # Helper methods for testing
           pass
   ```

3. **Use dependency injection in constructors**:

   ```python
   class MyComponent:
       def __init__(self, service=None):
           if service is None:
               from core.conductor.src.services.unified_registry import require
               self._service = require(ServiceType)
           else:
               self._service = service

   # In tests
   def test_component():
       mock_service = MagicMock()
       component = MyComponent(service=mock_service)
       # Test with the mock
   ```

## Debugging Techniques

### Identifying Component Issues

To identify which component is causing problems:

1. **Enable debug logging**:

   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Trace service initialization**:

   ```python
   from core.conductor.src.services.unified_registry import get_service_registry

   registry = get_service_registry()
   print(f"Services: {registry.get_service_names()}")

   # Initialize with more detailed logging
   registry.initialize_all()
   ```

3. **Check event subscriptions**:

   ```python
   from core.conductor.src.services.unified_event_bus import get_event_bus

   event_bus = get_event_bus()
   print(f"Subscription counts: {event_bus.get_handler_stats()}")
   ```

### Diagnosing Async Issues

Async code can be particularly difficult to debug:

1. **Use asyncio debug mode**:

   ```python
   import asyncio

   # Enable debug mode
   asyncio.get_event_loop().set_debug(True)
   ```

2. **Add synchronization points for debugging**:

   ```python
   async def function():
       # Add explicit synchronization for debugging
       print("Before operation")
       await asyncio.sleep(0)  # Yield to event loop
       result = await async_operation()
       print("After operation")
       await asyncio.sleep(0)  # Yield to event loop
       return result
   ```

3. **Use asyncio.gather with return_exceptions=True for parallel tasks**:

   ```python
   results = await asyncio.gather(task1(), task2(), return_exceptions=True)

   # Check if any tasks raised exceptions
   for result in results:
       if isinstance(result, Exception):
           print(f"Task failed: {result}")
   ```

## Common Error Messages and Solutions

| Error Message                                          | Likely Cause                 | Solution                                                 |
| ------------------------------------------------------ | ---------------------------- | -------------------------------------------------------- |
| `ImportError: cannot import name X`                    | Circular imports             | Use lazy imports or dependency injection                 |
| `AttributeError: 'NoneType' object has no attribute Y` | Uninitialized service        | Ensure service initialization order, check registration  |
| `RuntimeError: This event loop is already running`     | Nested event loops           | Use `asyncio.run_in_executor` for blocking code          |
| `TypeError: object X is not subscriptable`             | Type hints issue             | Fix generic type parameters, use proper container types  |
| `ResourceWarning: unclosed file`                       | Resource leak                | Implement proper cleanup, use context managers           |
| `RuntimeError: Event loop is closed`                   | Using event loop after close | Create proper shutdown sequence, cleanup resources first |

## How to Report Issues

When encountering issues that are not covered by this guide:

1. **Collect relevant information**:

   - Full error message and stack trace
   - Component and functionality affected
   - Steps to reproduce
   - Environment details (OS, Python version, etc.)

2. **Check existing documentation**:

   - Review this troubleshooting guide
   - Check the [Codebase Health Assessment](./CODEBASE_HEALTH_ASSESSMENT.md)
   - Look at the [Technical Debt Remediation Plan](./TECHNICAL_DEBT_REMEDIATION_PLAN.md)

3. **Open an issue** with the collected information, including:
   - Clear title describing the issue
   - Detailed description with all relevant details
   - Code sample that reproduces the issue (if possible)
   - Proposed solution (if you have one)

## Contributing to Technical Debt Reduction

Everyone can help reduce technical debt:

1. **Follow the patterns** in the unified components
2. **Migrate code** from legacy to unified implementations
3. **Improve tests** for components you work with
4. **Update documentation** when you discover solutions
5. **Report inconsistencies** or gaps in the architecture

By working together on technical debt reduction, we can improve the codebase for everyone.
