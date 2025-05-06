# Rate Limit Handling with Automatic Fallbacks

This guide explains how to configure Orchestra's LLM client to automatically handle rate limits by falling back to free models and implementing semantic caching.

## Overview of Rate Limit Strategies

Orchestra provides two complementary approaches to handle rate limits:

1. **Direct OpenRouter Fallbacks**: Configure OpenRouter to automatically fall back to free models when your primary model hits rate limits.
2. **Portkey-Enhanced Routing**: Use Portkey's advanced routing capabilities for more sophisticated fallback strategies, load balancing, and semantic caching.

## Option 1: OpenRouter Direct Fallbacks

### Configuration

Add the following environment variables to your `.env` file:

```bash
# Primary configuration
OPENROUTER_API_KEY="your-openrouter-api-key"  
PREFERRED_LLM_PROVIDER="openrouter"
OPENROUTER_DEFAULT_MODEL="anthropic/claude-3-opus-20k"  # Your primary paid model

# Free model fallbacks (comma-separated)
OPENROUTER_FREE_FALLBACKS="google/gemini-2.5-flash:free,mistralai/mixtral-8x7b:free"
```

### How It Works

When your primary model encounters a rate limit (429 error):

1. OpenRouter automatically routes the request to the first free model in your fallback list
2. If that model is also rate-limited, it tries the next one, and so on
3. The system handles this transparently - your application code remains unchanged

### Important Limitations

- Free models have strict limits (2 RPM/20 RPD)
- Free fallbacks only trigger on 429 errors
- No automatic caching - each request counts against your limits

## Option 2: Portkey Enhanced Routing (Recommended for Production)

### Configuration

Add the following environment variables:

```bash
# Primary configuration
PORTKEY_API_KEY="your-portkey-api-key"
PREFERRED_LLM_PROVIDER="portkey"

# Fallback configuration (JSON string)
PORTKEY_FALLBACKS='[
  {"provider":"openrouter", "model":"anthropic/claude-3-opus-20k", "weight": 70},
  {"provider":"openrouter", "model":"google/gemini-2.5-flash:free", "weight": 20},
  {"provider":"groq", "model":"mixtral-8x7b-32768", "weight": 10}
]'

# Strategy: "fallback", "loadbalance", or "cost_aware"
PORTKEY_STRATEGY="fallback"

# Enable semantic caching to reduce API calls
PORTKEY_CACHE_ENABLED=true

# Rate limit handling configuration
LLM_MAX_RETRIES=3
LLM_RETRY_DELAY=1.0
LLM_RETRY_MAX_DELAY=60.0
```

### Advanced Strategies

#### 1. Fallback Strategy

```bash
PORTKEY_STRATEGY="fallback"
```

Attempts each model in the order specified in `PORTKEY_FALLBACKS`. If the first model fails (rate limit, timeout, etc.), it automatically tries the next one.

#### 2. Load Balancing Strategy

```bash
PORTKEY_STRATEGY="loadbalance"
```

Distributes requests across models according to their weights. This can help avoid hitting rate limits by spreading your requests across different models/providers.

#### 3. Cost-Aware Strategy

```bash
PORTKEY_STRATEGY="cost_aware"
```

Automatically selects the most cost-effective model for each request type, while respecting rate limits.

### Semantic Caching

Enabling `PORTKEY_CACHE_ENABLED` activates Portkey's semantic caching, which can:

- Reduce API calls by 40-60% for similar requests
- Completely avoid rate limits for similar queries
- Improve response times dramatically for cached responses

The cache uses semantic similarity to match similar queries, not just exact matches.

## Implementation Details

### Agent-Specific Model Routing

For multi-agent systems, you can specify different models for different agent types:

```bash
AGENT_MODEL_MAP='{"researcher":"anthropic/claude-3-opus-20k","executor":"openai/gpt-4o","validator":"mistralai/mistral-large-2"}'
```

Then when making API calls, include the `agent_type` parameter:

```python
response = await llm_client.generate_chat_completion(
    messages=[{"role": "user", "content": "Your query"}],
    agent_type="researcher"  # Will use claude-3-opus-20k
)
```

### Monitoring Credit Usage

Use the monitoring API to check your credit balance and usage:

```python
from core.orchestrator.src.services.llm.providers import get_llm_provider

async def check_credits():
    provider = get_llm_provider("portkey")
    return await provider.monitor_credits()
```

## Best Practices

1. **Production Usage**:
   - Do not rely solely on free model fallbacks for production systems
   - Use Portkey with paid models and load balancing for reliable production use

2. **Optimizing for Costs**:
   - Enable semantic caching to reduce redundant API calls
   - Use load balancing to avoid hitting rate limits on any single model

3. **Monitoring**:
   - Regularly check your credit usage and rate limit errors in logs
   - Adjust your strategies if seeing too many fallbacks or rate limit errors

4. **Error Handling**:
   - Even with fallbacks, handle potential failures in your application code
   - Implement graceful degradation for situations where all fallbacks fail

## Troubleshooting

If you encounter issues with the fallback configuration:

1. Check your API keys and credit balance in OpenRouter dashboard
2. Verify the environment variables are correctly formatted (especially JSON strings)
3. Review the application logs for specific error messages
4. Ensure your Portkey API key has proper permissions

Remember that free models are subject to strict rate limits (2 RPM/20 RPD) and should not be relied upon for production workloads.

## Related Documentation

- [OpenRouter Pro Tier Configuration](/docs/openrouter_pro_tier.md)
- [Portkey Integration Guide](/docs/portkey_integration.md)