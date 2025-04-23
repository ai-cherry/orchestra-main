# OpenRouter Pro Tier Configuration Guide

This guide explains how to configure your Orchestra system to leverage OpenRouter's Pro Tier features for improved performance, reliability, and model access.

## Benefits of OpenRouter Pro Tier

When you maintain at least a $10 balance, OpenRouter Pro Tier provides:

- **Higher Daily Call Limits**: 1000 calls/day (vs 50 in Free Tier)
- **Higher Rate Limits**: 60 RPM (vs 20 in Free Tier)
- **Access to 300+ Models**: Including specialized models that may not be available in Free Tier
- **Priority Routing**: For faster response times and higher availability

## Step-by-Step Upgrade Process

### 1. Add Credits to Your OpenRouter Account

1. Log into [OpenRouter.ai](https://openrouter.ai)
2. Navigate to Account → Billing
3. Purchase credits ($10+ minimum for increased limits)
   - Recommended: $50 for team usage (~500,000 tokens @ average $0.10/1k tokens)

### 2. Update Environment Configuration

Configure the following environment variables to optimize your OpenRouter integration:

#### Essential Configuration Variables

```bash
# OpenRouter API Key
OPENROUTER_API_KEY="sk-or-your-api-key"

# Use OpenRouter as the default provider
PREFERRED_LLM_PROVIDER="openrouter"

# Default model to use when not specified
OPENROUTER_DEFAULT_MODEL="openai/gpt-4o"
```

#### Advanced Configuration Variables

```bash
# Custom Headers (optional - as JSON string)
OPENROUTER_HEADERS='{"HTTP-Referer":"https://yourdomain.com","X-Title":"Your Project Name"}'

# Agent-specific model mapping (JSON string mapping agent roles to models)
AGENT_MODEL_MAP='{"researcher":"anthropic/claude-3-opus-20k","validator":"openai/gpt-4o","executor":"meta-llama/llama-3-70b-instruct"}'

# Rate limit handling configuration
LLM_REQUEST_TIMEOUT=30
LLM_MAX_RETRIES=3
LLM_RETRY_DELAY=1.0
LLM_RETRY_MAX_DELAY=60.0
LLM_RETRYABLE_ERRORS="connection_error,timeout_error,rate_limit_error,service_error"
```

#### Fallback Configuration with Portkey

For multi-model fallback capabilities, you can also configure Portkey:

```bash
# Portkey integration (required for fallbacks)
PORTKEY_API_KEY="pk-your-portkey-api-key"

# Optional Portkey-specific settings
TRACE_ID="your-trace-id"
VIRTUAL_KEY="your-virtual-key"

# Fallback configuration as JSON string
PORTKEY_FALLBACKS='[{"provider":"openai","model":"gpt-4o"},{"provider":"anthropic","model":"claude-3-haiku-20k"},{"provider":"google","model":"gemini-1.5-pro"}]'
```

## Agent-Specific Model Routing

With the Pro Tier access to 300+ models, you can optimize your agents by assigning specialized models to different agent roles. This is configured through the `AGENT_MODEL_MAP` environment variable.

For example, you can configure:
- Research-intensive agents to use Claude models with larger context windows
- Creative tasks to use GPT-4o
- Cost-efficient tasks to use Llama 3 or Gemini models

The system automatically routes requests to the appropriate model based on the `agent_type` parameter in API calls.

## Rate Limit Mitigation

The system implements advanced retry logic with exponential backoff for transient errors:

1. Connection issues and timeouts are automatically retried
2. Rate limit errors use a configurable backoff strategy
3. Maximum retries and delays are configurable through environment variables

This ensures optimal usage of your increased rate limits (60 RPM) while gracefully handling any temporary issues.

## Usage and Monitoring

The system logs detailed information about each API call, including:
- Model used
- Token usage
- Response time
- Any errors and retry attempts

This helps you monitor your usage and optimize your OpenRouter Pro Tier subscription.

## Troubleshooting

If you experience issues with the OpenRouter Pro Tier configuration:

1. Verify your API key and balance in the OpenRouter dashboard
2. Check that your environment variables are correctly formatted (especially JSON strings)
3. Review logs for any specific error messages
4. Ensure you have the latest version of the dependencies installed

## Further Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [Portkey Documentation](https://docs.portkey.ai/) (for fallback configuration)
- [Orchestra Configuration Guide](./configuration.md)