# Phidata/Agno LLM Integration with Portkey

This package provides integration between Phidata/Agno LLM models and Portkey, enabling the use of Portkey's routing, observability, and fallback capabilities with Phidata's model library.

## Features

- **Unified Interface**: Common interface for working with multiple LLM providers
- **Portkey Integration**: Leverage Portkey's gateway URL and authentication headers
- **Provider Support**: Implementations for OpenAI, Anthropic, and OpenRouter
- **Automatic Configuration**: Dynamic configuration from environment variables
- **Dependency Injection**: Seamless integration with the Orchestra system

## Directory Structure

```
packages/llm/
├── __init__.py
├── README.md
└── src/
    ├── __init__.py
    ├── config.py                  # Configuration utilities
    ├── portkey_integration.py     # Core Portkey integration functionality
    ├── test_phidata_integration.py # Test script for integration
    └── models/                    # Model-specific implementations
        ├── __init__.py
        ├── anthropic.py           # Anthropic Claude implementation
        ├── openai.py              # OpenAI implementation 
        └── openrouter.py          # OpenRouter implementation
```

## Usage

### Environment Variables

Configure the following environment variables to control the integration:

```
# Required
PORTKEY_API_KEY=your-portkey-api-key

# Provider-specific virtual keys (at least one should be set)
PORTKEY_VIRTUAL_KEY_OPENAI=your-openai-virtual-key
PORTKEY_VIRTUAL_KEY_ANTHROPIC=your-anthropic-virtual-key
PORTKEY_VIRTUAL_KEY_OPENROUTER=your-openrouter-virtual-key

# Default models to use
DEFAULT_LLM_MODEL_PRIMARY=openai/gpt-4o
DEFAULT_LLM_MODEL_FALLBACK_OPENAI=gpt-4o
DEFAULT_LLM_MODEL_FALLBACK_ANTHROPIC=claude-3-5-sonnet-20240620

# Control which provider to use by default
PREFERRED_LLM_PROVIDER=openrouter  # Options: openai, anthropic, openrouter
```

### Direct Usage

You can use the model factories directly:

```python
from core.orchestrator.src.config.settings import Settings
from packages.llm.src.models.openai import create_openai_model
from packages.llm.src.models.anthropic import create_anthropic_model
from packages.llm.src.models.openrouter import create_openrouter_model

# Load settings
settings = Settings()

# Create a model
openai_model = create_openai_model(settings)
# or
anthropic_model = create_anthropic_model(settings)
# or
openrouter_model = create_openrouter_model(settings)

# Use the model
async def example():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, who are you?"}
    ]
    response = await openai_model.invoke(messages)
    print(response)
```

### Dependency Injection

The models are automatically available through dependency injection:

```python
from fastapi import Depends
from core.orchestrator.src.api.dependencies.llm import get_llm_client

async def my_endpoint(llm_model=Depends(get_llm_client)):
    """The LLM model will be injected automatically."""
    messages = [...]
    response = await llm_model.invoke(messages)
    return {"response": response}
```

## Testing

To test the integration, run:

```bash
python -m packages.llm.src.test_phidata_integration
```

This will test all configured models.

## Switching Between Legacy and New Implementation

To control which implementation is used:

- By default, the system will try to use the Phidata/Agno models with Portkey integration
- If the required packages are not available, it will fall back to the legacy PortkeyClient
- You can force the use of the legacy client by setting `USE_LEGACY_LLM_CLIENT=true` in your environment

## Extending to Support Additional Providers

To add support for a new provider:

1. Create a new file in `src/models/` for the provider
2. Implement a factory function that uses `configure_model_from_settings()` 
3. Update `get_phidata_llm_model()` in `dependencies/llm.py` to use the new factory
