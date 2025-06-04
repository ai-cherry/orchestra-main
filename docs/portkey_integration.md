# Portkey Integration Guide

This guide explains how to use Portkey with cherry_ai, including virtual keys management
for multiple LLM providers, enhanced caching, rate limiting, and smart routing capabilities.

## Overview

Portkey is an advanced API gateway for LLMs that provides the following capabilities:

- **Virtual Keys**: Secure management of API keys for multiple providers
- **Smart Routing**: Fallback strategies, load balancing, and cost-aware routing
- **Semantic Caching**: Cache responses based on prompt similarity
- **Rate Limit Handling**: Graceful handling of rate limits across multiple providers
- **Budget Controls**: Set spending limits and receive alerts
- **Observability**: Unified logging and monitoring

This integration allows you to leverage these features throughout cherry_ai.

## Installation

To use Portkey, you need to install the Portkey SDK:

```bash
pip install portkey-ai
```

## Virtual Keys

### What Are Virtual Keys?

Virtual Keys are a Portkey feature that provides a secure way to manage LLM provider API keys. Instead of directly using
provider keys (like OpenAI, Anthropic, etc.) in your code, you create virtual keys in Portkey that
reference these provider keys. Benefits include:

- **Security**: Your actual API keys are stored securely on Portkey's servers
- **Rotation**: Rotate provider keys without changing your application code
- **Budget Controls**: Set spending limits for each virtual key
- **Monitoring**: Track usage and costs per provider
- **Multi-provider support**: Manage keys for multiple LLM providers in one place

### Setting Up Virtual Keys

You can create and manage virtual keys in two ways:

#### 1. Using the CLI Tool

We provide a CLI tool to manage your virtual keys:

```bash
# Set your Portkey Admin API key
export MASTER_PORTKEY_ADMIN_KEY="your-admin-key"

# Create a virtual key for OpenAI
python scripts/manage_portkey_keys.py create-key --name "OpenAI-Prod" --provider openai --key "sk-..."

# Create a virtual key for Anthropic
python scripts/manage_portkey_keys.py create-key --name "Anthropic-Prod" --provider anthropic --key "sk-..."

# List all virtual keys
python scripts/manage_portkey_keys.py list-keys

# Rotate a key (update the provider API key without changing the virtual key ID)
python scripts/manage_portkey_keys.py rotate-key --id "vk_..." --new-key "sk-..."
```

#### 2. Using the Portkey Dashboard

You can also manage virtual keys through the [Portkey Dashboard](https://app.portkey.ai/):

1. Log in to your Portkey account
2. Navigate to "Virtual Keys" in the sidebar
3. Click "Add Key" to create a new virtual key
4. Enter a name, select the provider, and paste your API key
5. (Optional) Set budget limits and rate limits

### Using Virtual Keys in cherry_ai

After creating virtual keys, configure them in your `.env` file:

```bash
# Portkey API key
PORTKEY_API_KEY="your-portkey-api-key"

# Admin API key (only needed for management operations)
MASTER_PORTKEY_ADMIN_KEY="your-portkey-admin-key"

# Virtual keys for different providers
PORTKEY_VIRTUAL_KEY_OPENAI="vk_openai_..."
PORTKEY_VIRTUAL_KEY_ANTHROPIC="vk_anthropic_..."
PORTKEY_VIRTUAL_KEY_MISTRAL="vk_mistral_..."
# Add more provider virtual keys as needed
```

The `PortkeyClient` will automatically select the appropriate virtual key based on the model being used:

```python
# In your code, simply use the model name
response = await portkey_client.generate_response(
    model="gpt-4",  # Will automatically use PORTKEY_VIRTUAL_KEY_OPENAI
    messages=[{"role": "user", "content": "Hello, GPT-4!"}]
)
```

## Basic Setup

Enable Portkey when initializing the Redis client:

```python
from packages.shared.src.storage.redis_client import RedisClient

# Initialize Redis client with Portkey enabled
redis_client = RedisClient(
    host="your-redis-host",
    port=6379,
    use_portkey=True,
    portkey_api_key="your-portkey-api-key",
    portkey_cache_ttl=3600  # Default cache TTL in seconds
)
```

Or configure via environment variables:

```bash
export PORTKEY_API_KEY="your-portkey-api-key"
export PREFERRED_LLM_PROVIDER="portkey"
```

## Configuration

Configure the Portkey client with your desired routing strategy:

```python
# Define fallback model configurations
fallbacks = [
    {
        "provider": "openai",
        "model": "gpt-4-turbo",
        "api_key": "your-openai-api-key"
    },
    {
        "provider": "anthropic",
        "model": "claude-3-opus",
        "api_key": "your-anthropic-api-key"
    }
]

# Configure Portkey with fallback strategy and caching
await redis_client.setup_portkey_config(
    strategy="fallback",
    fallbacks=fallbacks,
    cache_enabled=True
)
```

### Routing Strategies

Portkey supports several routing strategies:

1. **Fallback Strategy** - Try models in sequence until success

```python
await redis_client.setup_portkey_config(
    strategy="fallback",
    fallbacks=fallbacks
)
```

2. **Load Balancing** - Distribute requests across models

```python
await redis_client.setup_portkey_config(
    strategy="loadbalance",
    fallbacks=fallbacks
)
```

3. **Cost-Aware Routing** - Choose models based on cost considerations

```python
await redis_client.setup_portkey_config(
    strategy="cost_aware",
    fallbacks=fallbacks
)
```

## Using Semantic Cache

Semantic cache allows you to retrieve responses based on semantic similarity of queries:

```python
# Try to get from semantic cache
cached_response = await redis_client.portkey_semantic_cache(
    query="What is the capital of France?"
)

if cached_response:
    # Use cached response
    return cached_response
else:
    # Generate new response with your LLM
    response = await generate_llm_response(query)

    # Store in semantic cache for future use
    await redis_client.portkey_store_semantic_cache(
        query="What is the capital of France?",
        response=response
    )

    return response
```

You can also provide custom cache keys and TTLs:

```python
# Store with custom key and TTL
await redis_client.portkey_store_semantic_cache(
    query="What is the capital of France?",
    response=response,
    cache_key="geography:france:capital",
    ttl=86400  # 24 hours
)
```

## Clearing the Cache

To clear the Portkey semantic cache:

```python
await redis_client.clear_portkey_cache()
```

## Checking Portkey Status

Check if Portkey is enabled and properly initialized:

```python
if await redis_client.is_portkey_enabled():
    # Use Portkey features
    # ...
else:
    # Use alternative approach
    # ...
```

## Error Handling

Handle Portkey-related errors:

```python
from packages.shared.src.storage.redis_client import PortkeyError

try:
    await redis_client.setup_portkey_config(strategy="fallback")
except RuntimeError:
    # Portkey not enabled or initialized
    print("Portkey is not enabled")
except PortkeyError as e:
    # Portkey API error
    print(f"Portkey API error: {e}")
```

## Gateway Configurations

Portkey Gateway Configurations allow you to set up advanced routing and fallback strategies between
multiple LLM providers or models. This is especially powerful when combined with virtual keys.

### Creating Gateway Configurations

You can create gateway configurations using the CLI tool:

```bash
# Create a fallback gateway configuration
python scripts/manage_portkey_keys.py create-config --name "Fallback Config" --strategy fallback --providers '[
  {"virtual_key": "vk_openai_...", "models": ["gpt-4", "gpt-3.5-turbo"]},
  {"virtual_key": "vk_anthropic_...", "models": ["claude-3-opus", "claude-3-sonnet"]}
]'

# Create a load balancing gateway configuration
python scripts/manage_portkey_keys.py create-config --name "Load Balance Config" --strategy loadbalance --providers '[
  {"virtual_key": "vk_openai_...", "models": ["gpt-4"], "weight": 2},
  {"virtual_key": "vk_anthropic_...", "models": ["claude-3-opus"], "weight": 1}
]'

# List all gateway configurations
python scripts/manage_portkey_keys.py list-configs
```

### Using Gateway Configurations

After creating a gateway configuration, add it to your `.env` file:

```bash
# Set the gateway configuration ID
PORTKEY_CONFIG_ID="gw_config_..."
```

The `PortkeyClient` will automatically apply this configuration to all requests.

## Environment Variable Configuration

You can configure Portkey through environment variables:

```bash
# Required for Portkey
PORTKEY_API_KEY="your-portkey-api-key"
PREFERRED_LLM_PROVIDER="portkey"

# Admin API key for virtual key management
MASTER_PORTKEY_ADMIN_KEY="your-portkey-admin-key"

# Virtual keys for different providers
PORTKEY_VIRTUAL_KEY_OPENAI="vk_openai_..."
PORTKEY_VIRTUAL_KEY_ANTHROPIC="vk_anthropic_..."
PORTKEY_VIRTUAL_KEY_MISTRAL="vk_mistral_..."
PORTKEY_VIRTUAL_KEY_HUGGINGFACE="vk_huggingface_..."
PORTKEY_VIRTUAL_KEY_COHERE="vk_cohere_..."
PORTKEY_VIRTUAL_KEY_OPENROUTER="vk_openrouter_..."
PORTKEY_VIRTUAL_KEY_PERPLEXITY="vk_perplexity_..."
PORTKEY_VIRTUAL_KEY_DEEPSEEK="vk_deepseek_..."
PORTKEY_VIRTUAL_KEY_CODESTRAL="vk_codestral_..."
PORTKEY_VIRTUAL_KEY_CODY="vk_cody_..."
PORTKEY_VIRTUAL_KEY_CONTINUE="vk_continue_..."
PORTKEY_VIRTUAL_KEY_GROK="vk_grok_..."
PORTKEY_VIRTUAL_KEY_GOOGLE="vk_google_..."
PORTKEY_VIRTUAL_KEY_AZURE="vk_azure_..."
PORTKEY_VIRTUAL_KEY_AWS="vk_aws_..."

# Gateway configuration
PORTKEY_CONFIG_ID="gw_config_..."

# Legacy fallback configuration (JSON string) - consider using virtual keys and gateway configs instead
PORTKEY_FALLBACKS='[
    {"provider": "openai", "model": "gpt-4-turbo", "api_key": "key1"},
    {"provider": "anthropic", "model": "claude-3-opus", "api_key": "key2"}
]'

# Routing strategy
PORTKEY_STRATEGY="fallback"  # or "loadbalance" or "cost_aware"

# Cache configuration
PORTKEY_CACHE_ENABLED=true
```

## Testing Portkey Integration

You can use our test suite to verify that Portkey is working correctly:

```bash
# Run all Portkey-related tests
python -m unittest tests/test_portkey_integration.py
```

## Best Practices

1. **Virtual Keys**: Use virtual keys instead of raw API keys for better security and management

   - Create separate virtual keys for different environments (dev, staging, prod)
   - Set budget limits to prevent unexpected costs
   - Rotate provider keys regularly without affecting your application

2. **Gateway Configurations**: Create gateway configurations for reliable LLM access

   - Use fallback strategies to handle provider outages or rate limits
   - Use load balancing to distribute traffic across providers
   - Use cost-aware routing to optimize for budget constraints

3. **TTL Selection**: Choose appropriate cache TTLs based on your data's freshness needs

   - Use shorter TTLs for time-sensitive information
   - Use longer TTLs for stable knowledge

4. **Monitoring**: Set up proper logging and monitoring for Portkey operations
   - Review usage statistics regularly
   - Set up budget alerts to prevent unexpected costs
   - Monitor performance across different providers

## Troubleshooting

Common issues and solutions:

1. **"Portkey library not available"**: Install with `pip install portkey-ai`
2. **"Portkey API key is required"**: Set the API key in the constructor or via environment variable
3. **"Portkey is not enabled or not initialized"**: Check that `use_portkey=True` is set
4. **Cache misses**: Verify that caching is enabled and TTL is appropriate

## Additional Resources

- [Official Portkey Documentation](https://portkey.ai/docs)
- [Rate Limit Handling Guide](./rate_limit_handling.md)
- [Redis Client API Reference](../packages/shared/src/storage/redis_client.py)
