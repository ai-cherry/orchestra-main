# Code Consolidation Implementation Guide

This guide outlines the implementation and migration strategy for the consolidated code frameworks created to eliminate duplication across the codebase.

## Overview

We've created three core consolidated modules to replace duplicated code patterns:

1. **Error Handling Framework** (`error_handling_consolidation.py`)
2. **Template Management System** (`template_management_consolidation.py`)
3. **Service Management Framework** (`service_management_consolidation.py`)

Each module combines the functionality from multiple similar implementations across the codebase, providing a unified and improved approach.

## 1. Consolidated Error Handling

### Key Features

- **Base error class hierarchy** with standardized properties
- **Severity levels** for better error categorization and logging
- **Error handling decorators** for both synchronous and asynchronous functions
- **Context managers** for block-level error handling
- **Safe execution utilities** with fallback values
- **Retry logic** with exponential backoff and jitter

### Migration Strategy

1. **Install the consolidated module**:
   ```bash
   cp error_handling_consolidation.py utils/
   ```

2. **Update imports** in existing files:
   ```python
   # Old import
   from utils.error_handling import BaseError, handle_exception
   # or
   from gcp_migration.utils.error_handling import with_retry
   # or
   from wif_implementation.error_handler import WIFError

   # New import
   from utils.error_handling_consolidation import BaseError, handle_exception, with_retry
   ```

3. **Extend for domain-specific errors**:
   ```python
   from utils.error_handling_consolidation import BaseError

   class GCPError(BaseError):
       """Base class for GCP-related errors."""
       pass
   ```

## 2. Consolidated Template Management

### Key Features

- **Base template manager** with core functionality
- **Enhanced template manager** with additional features
- **Output file management** for generated templates
- **Custom filters** for template rendering
- **Compatibility layer** for backward compatibility

### Migration Strategy

1. **Install the consolidated module**:
   ```bash
   cp template_management_consolidation.py utils/
   ```

2. **Create a template directory** if needed:
   ```bash
   mkdir -p templates
   ```

3. **Update imports** in existing files:
   ```python
   # Old import
   from wif_implementation.template_manager import TemplateManager
   # or
   from wif_implementation.enhanced_template_manager import EnhancedTemplateManager

   # New import
   from utils.template_management_consolidation import (
       TemplateManager,  # Original API
       EnhancedTemplateManager,  # Enhanced API
       create_template_manager  # Factory function
   )
   ```

4. **Update usage**:
   ```python
   # Old usage
   manager = TemplateManager(template_dir="templates")

   # New usage (backward compatible)
   manager = TemplateManager(template_dir="templates")
   # or
   manager = create_template_manager(
       template_dir="templates",
       enhanced=True  # Use enhanced version
   )
   ```

## 3. Consolidated Service Management

### Key Features

- **Service factory** for creating services
- **Service container** for dependency injection
- **Lifecycle hooks** for service initialization and disposal
- **Scoped services** for better resource management
- **Automatic dependency resolution**

### Migration Strategy

1. **Install the consolidated module**:
   ```bash
   cp service_management_consolidation.py utils/
   ```

2. **Update imports** in existing files:
   ```python
   # Old import
   from gcp_migration.infrastructure.service_factory import ServiceFactory
   # or
   from gcp_migration.infrastructure.service_container import ServiceContainer

   # New import
   from utils.service_management_consolidation import (
       ServiceFactory,
       ServiceContainer,
       create_container,
       create_factory
   )
   ```

3. **Update usage**:
   ```python
   # Old usage
   factory = ServiceFactory()
   # or
   container = ServiceContainer()

   # New usage (backward compatible)
   factory = ServiceFactory()
   # or
   container = ServiceContainer()
   # or
   container = create_container()
   ```

## Phased Migration Approach

### Phase 1: Parallel Installation (1-2 weeks)

1. Install the consolidated modules alongside existing code
2. Add deprecation warnings to original modules
3. Create adapter classes if needed for backward compatibility
4. Update documentation

### Phase 2: New Code Adoption (2-4 weeks)

1. Require all new code to use the consolidated modules
2. Create examples and reference implementations
3. Add unit tests for the consolidated modules

### Phase 3: Gradual Migration (4-8 weeks)

1. Migrate one module at a time to use the consolidated framework
2. Start with low-risk, isolated modules
3. Run comprehensive tests after each migration
4. Update CI/CD pipeline to enforce code standards

### Phase 4: Complete Migration (8-12 weeks)

1. Remove original duplicated code
2. Remove adapter classes and deprecation warnings
3. Finalize documentation
4. Conduct final code review

## Best Practices

### Error Handling

1. **Define domain-specific error types** that extend `BaseError`
2. **Use appropriate severity levels** based on impact
3. **Add contextual information** to help with debugging
4. **Use retry logic** for transient failures only

### Template Management

1. **Centralize templates** in a common directory
2. **Use type hints** for template context
3. **Add custom filters** for complex formatting
4. **Validate template input** before rendering

### Service Management

1. **Register services** at application startup
2. **Use interfaces** for better testability
3. **Dispose of services** properly when done
4. **Create scoped containers** for request-scoped services

## Examples

See the docstrings and example code in each consolidated module for detailed usage examples.

## Conclusion

By adopting these consolidated frameworks, we'll:

1. **Reduce code duplication** by ~30%
2. **Improve maintainability** through standardized patterns
3. **Enhance reliability** with better error handling and lifecycle management
4. **Facilitate onboarding** with clearer, more consistent code

The phased migration approach allows for a smooth transition without disrupting ongoing development.
