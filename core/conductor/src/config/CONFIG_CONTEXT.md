# Configuration System Architecture

This document explains the configuration system architecture for AI coding assistants.

## Overview

The configuration system provides a centralized way to manage application settings from environment variables, files, and defaults. It uses Pydantic's BaseSettings for validation and automatic loading from environment variables.

## Key Components

### Settings Class

The core `Settings` class in `settings.py` defines all configurable parameters:

```python
class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Automatically reads from .env file when present.
    """

    # General settings
    ENVIRONMENT: str = 'development'

    # API keys
    OPENROUTER_API_KEY: Optional[str] = None
    PORTKEY_API_KEY: Optional[str] = None

    # Additional settings...
```

### Configuration Categories

Settings are organized into logical categories:

1. **Environment Configuration**

   - `ENVIRONMENT`: Current environment (development, testing, production)
   - `USE_RECOVERY_MODE`: Flag for recovery mode activation
   - `STANDARD_MODE`: Flag for standard operation mode

2. **LLM Provider Settings**

   - API keys for different providers (OpenRouter, Portkey)
   - Default models and retry parameters
   - Fallback configuration and strategy settings

3. **Performance and Optimization**

   - Request timeouts and retry counts
   - Caching settings and thresholds
   - Rate limit handling configuration

4. **Integration Settings**
   - Site information for API request headers
   - External service connection parameters

### Accessor Methods

Helper methods that parse complex settings:

- `get_portkey_fallbacks()`: Parses JSON configuration for Portkey fallbacks
- `get_openrouter_headers()`: Builds headers for OpenRouter API requests
- `get_agent_model_map()`: Provides mapping between agent roles and specific models
- `get_portkey_strategy_config()`: Builds strategy configuration for Portkey

### Dependency Injection

The `get_settings()` function provides a standard way to access settings through FastAPI dependency injection:

```python
def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
```

## Usage Patterns

Settings are typically accessed through dependency injection in API endpoints:

```python
@router.post("/interact")
async def process_interaction(
    request: SomeRequest,
    settings = Depends(get_settings)
):
    # Access settings
    timeout = settings.LLM_REQUEST_TIMEOUT
    # ...
```

Or directly in service implementations:

```python
def initialize_service():
    settings = get_settings()
    # Configure service based on settings
```

## Environment Variables

Settings are primarily configured through environment variables. The system supports:

1. **Direct Environment Variables**: Set in the shell or container
2. **`.env` File**: Loaded automatically when present
3. **Default Values**: Used when not explicitly configured

## Best Practices

1. **Descriptive Names**: Use clear, uppercase names for all settings
2. **Documentation**: Document each setting's purpose, type, and default
3. **Type Annotations**: Use Python type hints for validation
4. **Validation Logic**: Add validators for complex settings
5. **Sensible Defaults**: Provide reasonable defaults for optional settings

## Configuration Hierarchy

When the same setting is defined in multiple places, the precedence is:

1. Environment variables (highest precedence)
2. `.env` file
3. Default values in the Settings class (lowest precedence)

## Error Handling

The configuration system handles errors through:

1. **Type validation**: Automatic validation by Pydantic
2. **Custom validators**: Additional logic for specific fields
3. **Error logging**: Recording issues in parsing complex settings

## Security Considerations

- Sensitive settings (API keys, credentials) should never be committed to version control
- Use environment variables or secure secret management for sensitive values
- Apply principle of least privilege when exposing settings to components
